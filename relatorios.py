"""
Módulo de Relatórios do Game Runner - Por uma Gota: Um Sertão Radioativo
Responsável por:
- Geração e exportação de relatórios analíticos em formato CSV (compatível com Excel).
- Geração e exportação de relatórios em formato PDF de alta qualidade com formatação visual e paginação.
- Filtros e consolidação de estatísticas de speedruns.
"""

import os
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPdfWriter, QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF


def gerar_relatorio_csv(
    arg1: Any = None,
    arg2: Any = None,
    filtro_categoria: str = "todas",
    filtro_status: str = "todos",
    ordenacao: str = "melhor_tempo",
    speedruns: Optional[List[Dict[str, Any]]] = None,
    caminho_arquivo: Optional[str] = None
) -> str:
    """
    Exporta a lista de speedruns para arquivo CSV formatado.
    Utiliza codificação UTF-8 com BOM (utf-8-sig) e separador ponto-e-vírgula (;)
    para abertura imediata no Microsoft Excel e LibreOffice Calc.
    Aceita:
      - gerar_relatorio_csv(caminho_arquivo, filtro_categoria=..., ...)
      - gerar_relatorio_csv(speedruns, caminho_arquivo)
    """
    from banco_dados import banco

    if isinstance(arg1, (list, tuple)):
        lista_runs = arg1
        caminho_final = arg2 or caminho_arquivo
    elif isinstance(arg1, (str, Path)):
        caminho_final = str(arg1)
        lista_runs = speedruns or (arg2 if isinstance(arg2, (list, tuple)) else None)
    else:
        caminho_final = str(caminho_arquivo or arg2 or "")
        lista_runs = speedruns

    if lista_runs is None:
        lista_runs = banco.listar_speedruns_detalhado(
            categoria=filtro_categoria,
            status_conclusao=filtro_status,
            ordenacao=ordenacao,
            limite=1000
        )

    if not caminho_final:
        raise ValueError("Caminho do arquivo CSV de destino não informado.")

    caminho = Path(caminho_final).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    cabecalhos = [
        "ID da Corrida",
        "Posição no Filtro",
        "Jogador / Usuário",
        "E-mail",
        "Tempo Formatado",
        "Tempo em Milissegundos",
        "Inimigos Derrotados",
        "Total de Inimigos da Fase",
        "Taxa de Inimigos (%)",
        "Status da Fuga",
        "Categoria da Partida",
        "Data e Hora do Registro"
    ]

    with open(caminho, mode="w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(cabecalhos)

        for pos, s in enumerate(lista_runs, start=1):
            tot_inim = s.get("total_inimigos") or s.get("total_inimigos_fase") or 0
            inim = s.get("inimigos_derrotados") or 0
            pct_inim = f"{(inim / tot_inim * 100):.1f}%" if tot_inim > 0 else "0.0%"

            concluido = s.get("concluido") if "concluido" in s else s.get("concluiu_jogo", 1)
            status_str = "Concluída (Fuga)" if concluido else "Não Concluída (Falha)"
            categoria_str = "Com Auxílio GM (Cheat)" if s.get("usou_gm") else "Oficial (Sem Trapaça)"

            escritor.writerow([
                s.get("id"),
                pos,
                s.get("username", "Desconhecido"),
                s.get("email", "-"),
                s.get("tempo_formatado", "--:--.---"),
                s.get("tempo_ms", 0),
                inim,
                tot_inim,
                pct_inim,
                status_str,
                categoria_str,
                str(s.get("data_registro", "-"))[:19]
            ])

    return str(caminho)


def gerar_relatorio_pdf(
    arg1: Any = None,
    arg2: Any = None,
    arg3: Any = None,
    filtro_categoria: str = "todas",
    filtro_status: str = "todos",
    ordenacao: str = "melhor_tempo",
    nome_gm: str = "Game Master",
    gm_solicitante: Optional[str] = None,
    filtros_aplicados: str = "Todas as Corridas",
    speedruns: Optional[List[Dict[str, Any]]] = None,
    estatisticas: Optional[Dict[str, Any]] = None,
    caminho_arquivo: Optional[str] = None
) -> str:
    """
    Gera um relatório profissional em formato PDF com o motor nativo do PyQt6.
    Inclui cabeçalho institucional, sumário de KPIs analíticos, tabela de registros
    e nota de integridade e auditoria.
    Suporta:
      - gerar_relatorio_pdf(caminho_arquivo, filtro_categoria=..., gm_solicitante=...)
      - gerar_relatorio_pdf(speedruns, estatisticas, caminho_arquivo, nome_gm=...)
    """
    from banco_dados import banco

    if isinstance(arg1, (list, tuple)):
        lista_runs = arg1
        stats = arg2 if isinstance(arg2, dict) else (estatisticas or {})
        caminho_final = arg3 or caminho_arquivo
        gm_nome = gm_solicitante or nome_gm
    elif isinstance(arg1, (str, Path)):
        caminho_final = str(arg1)
        lista_runs = speedruns or (arg2 if isinstance(arg2, (list, tuple)) else None)
        stats = estatisticas or (arg3 if isinstance(arg3, dict) else None)
        gm_nome = gm_solicitante or nome_gm
    else:
        caminho_final = str(caminho_arquivo or arg3 or "")
        lista_runs = speedruns
        stats = estatisticas
        gm_nome = gm_solicitante or nome_gm

    if lista_runs is None:
        lista_runs = banco.listar_speedruns_detalhado(
            categoria=filtro_categoria,
            status_conclusao=filtro_status,
            ordenacao=ordenacao,
            limite=1000
        )

    if stats is None:
        stats = banco.obter_estatisticas_gerais_speedrun()

    if not caminho_final:
        raise ValueError("Caminho do arquivo PDF de destino não informado.")

    caminho = Path(caminho_final).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance()
    if not app:
        app = QApplication([])

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    # Montagem do HTML com estilização elegante
    linhas_tabela = []
    for pos, s in enumerate(lista_runs, start=1):
        tot_i = s.get("total_inimigos") or s.get("total_inimigos_fase") or 0
        i = s.get("inimigos_derrotados") or 0

        bg_cor = "#f7faf7" if (pos % 2 == 0) else "#ffffff"
        concluido = s.get("concluido") if "concluido" in s else s.get("concluiu_jogo", 1)
        cor_tempo = "#006600" if concluido and not s.get("usou_gm") else "#222222"

        status_badge = (
            "<span style='color: #007700; font-weight: bold;'>✔ Concluída</span>"
            if concluido
            else "<span style='color: #aa2222;'>✖ Falhou</span>"
        )

        categ_badge = (
            "<span style='color: #aa5500; font-weight: bold;'>⚠️ Com GM</span>"
            if s.get("usou_gm")
            else "<span style='color: #0055aa; font-weight: bold;'>★ Oficial</span>"
        )

        linhas_tabela.append(f"""
            <tr style="background-color: {bg_cor};">
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0;">#{pos}</td>
                <td style="padding: 6px; border: 1px solid #d0dcd0; font-weight: bold;">{s.get('username')}</td>
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0; font-family: monospace; color: {cor_tempo}; font-weight: bold;">{s.get('tempo_formatado')}</td>
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0;">{i}/{tot_i}</td>
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0;">{status_badge}</td>
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0;">{categ_badge}</td>
                <td style="text-align: center; padding: 6px; border: 1px solid #d0dcd0; font-size: 10px;">{str(s.get('data_registro', ''))[:16]}</td>
            </tr>
        """)

    conteudo_tabela = "\n".join(linhas_tabela) if linhas_tabela else """
        <tr><td colspan="7" style="text-align: center; padding: 20px; color: #777;">Nenhuma corrida corresponde aos filtros aplicados.</td></tr>
    """

    total_corridas = stats.get("total_corridas", 0)
    melhor_tempo = stats.get("melhor_tempo_oficial_formatado", "--:--.---")
    media_tempo = stats.get("media_tempo_formatado", "--:--.---")
    taxa_conclusao = stats.get("taxa_conclusao_pct", 0.0)
    total_jogadores = stats.get("total_jogadores", 0)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #222222;
                margin: 0;
                padding: 0;
            }}
            .cabecalho {{
                border-bottom: 3px solid #234d20;
                padding-bottom: 12px;
                margin-bottom: 16px;
            }}
            .titulo {{
                color: #123d10;
                font-size: 20px;
                font-weight: bold;
                margin: 0;
            }}
            .subtitulo {{
                color: #3e683b;
                font-size: 13px;
                font-weight: bold;
                margin-top: 4px;
            }}
            .meta-info {{
                font-size: 10px;
                color: #555555;
                margin-top: 8px;
            }}
            .kpi-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 18px;
            }}
            .kpi-table td {{
                background-color: #eaf3ea;
                border: 1px solid #c0d8c0;
                padding: 10px;
                text-align: center;
                width: 25%;
            }}
            .kpi-valor {{
                font-size: 16px;
                font-weight: bold;
                color: #0b3d0a;
            }}
            .kpi-label {{
                font-size: 10px;
                color: #446644;
                text-transform: uppercase;
                margin-top: 3px;
            }}
            .tabela-dados {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
            }}
            .tabela-dados th {{
                background-color: #193818;
                color: #ffffff;
                padding: 8px 6px;
                border: 1px solid #193818;
                text-align: center;
                font-size: 11px;
            }}
            .rodape {{
                margin-top: 24px;
                border-top: 1px solid #cccccc;
                padding-top: 8px;
                font-size: 9px;
                color: #777777;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="cabecalho">
            <h1 class="titulo">POR UMA GOTA - UM SERTÃO RADIOATIVO</h1>
            <div class="subtitulo">RELATÓRIO DE DESEMPENHO E AUDITORIA DO GAME RUNNER</div>
            <div class="meta-info">
                <b>Emissão:</b> {agora} &nbsp;|&nbsp; 
                <b>Game Master Responsável:</b> {gm_nome} &nbsp;|&nbsp; 
                <b>Filtros:</b> {filtros_aplicados} &nbsp;|&nbsp;
                <b>Registros no Relatório:</b> {len(lista_runs)}
            </div>
        </div>

        <table class="kpi-table">
            <tr>
                <td>
                    <div class="kpi-valor">{melhor_tempo}</div>
                    <div class="kpi-label">Recorde Oficial</div>
                </td>
                <td>
                    <div class="kpi-valor">{media_tempo}</div>
                    <div class="kpi-label">Tempo Médio Concluído</div>
                </td>
                <td>
                    <div class="kpi-valor">{taxa_conclusao}%</div>
                    <div class="kpi-label">Taxa de Conclusão</div>
                </td>
                <td>
                    <div class="kpi-valor">{total_corridas} ({total_jogadores} jogadores)</div>
                    <div class="kpi-label">Total de Corridas</div>
                </td>
            </tr>
        </table>

        <table class="tabela-dados">
            <thead>
                <tr>
                    <th style="width: 7%;">Pos</th>
                    <th style="width: 22%;">Jogador</th>
                    <th style="width: 18%;">Tempo</th>
                    <th style="width: 15%;">Abates</th>
                    <th style="width: 15%;">Status</th>
                    <th style="width: 11%;">Modalidade</th>
                    <th style="width: 12%;">Data</th>
                </tr>
            </thead>
            <tbody>
                {conteudo_tabela}
            </tbody>
        </table>

        <div class="rodape">
            Relatório gerado automaticamente pelo Módulo Administrativo de Game Master (GM) - Por uma Gota: Um Sertão Radioativo.<br>
            Os dados deste documento são protegidos por integridade referencial com validação criptográfica (SQLite).
        </div>
    </body>
    </html>
    """

    doc = QTextDocument()
    doc.setHtml(html)

    writer = QPdfWriter(str(caminho))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(12, 12, 12, 12)
    )
    writer.setPageLayout(layout)
    doc.print(writer)

    return str(caminho)


if __name__ == "__main__":
    print("Testando módulo de relatórios...")
    dados_mock = [
        {
            "id": 1,
            "username": "Kaique",
            "email": "kaique@sertao.com",
            "tempo_ms": 75420,
            "tempo_formatado": "01:15.420",
            "inimigos_derrotados": 6,
            "total_inimigos": 9,
            "concluido": 1,
            "usou_gm": 0,
            "data_registro": "2026-11-17 18:00:00"
        },
        {
            "id": 2,
            "username": "jogador",
            "email": "jogador@sertao.com",
            "tempo_ms": 98230,
            "tempo_formatado": "01:38.230",
            "inimigos_derrotados": 4,
            "total_inimigos": 9,
            "concluido": 1,
            "usou_gm": 0,
            "data_registro": "2026-11-17 18:10:00"
        }
    ]
    kpis_mock = {
        "total_corridas": 2,
        "total_jogadores": 2,
        "melhor_tempo_oficial_formatado": "01:15.420",
        "media_tempo_formatado": "01:26.825",
        "taxa_conclusao_pct": 100.0,
        "total_inimigos": 10
    }

    caminho_csv = gerar_relatorio_csv(dados_mock, "teste_relatorio.csv")
    print("CSV gerado em:", caminho_csv)
    caminho_pdf = gerar_relatorio_pdf(dados_mock, kpis_mock, "teste_relatorio.pdf", "Kaique")
    print("PDF gerado em:", caminho_pdf)

    # Limpeza
    os.remove(caminho_csv)
    os.remove(caminho_pdf)
    print("Módulo de relatórios: SUCESSO!")
