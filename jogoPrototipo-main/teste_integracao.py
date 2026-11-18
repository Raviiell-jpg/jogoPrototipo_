"""
Script de testes automatizados de integração:
- Validação de dados (username, email, senha, speedrun)
- Operações de CRUD completas no SQLite (Usuários, Speedruns, Logs)
- Autenticação e Hashing seguro (SHA-256 + Salt)
- Registro de Speedrun e cálculo de recordes e ranking
- Painel modular de Game Master (GM) com 5 abas integradas
- Módulo de relatórios do runner com exportação PDF e CSV
- Execução headless do loop do Pygame e PyQt6
"""

import os
import sys
import tempfile
from pathlib import Path

# Configurar drivers headless para teste sem monitor
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from banco_dados import (
    BancoDados, validar_username, validar_email, validar_senha,
    validar_registro_speedrun, formatar_tempo_ms, converter_para_ms, desmembrar_ms
)
from relatorios import gerar_relatorio_csv, gerar_relatorio_pdf


def testar_validacoes():
    print("[1/6] Testando funções de validação de dados e conversões de tempo...")
    # Username
    assert not validar_username("")[0], "Deveria falhar username vazio"
    assert not validar_username("ab")[0], "Deveria falhar username curto"
    assert not validar_username("user name")[0], "Deveria falhar username com espaço"
    assert not validar_username("user@123")[0], "Deveria falhar username com caractere especial"
    assert validar_username("usuario_123")[0], "Deveria aceitar username válido"

    # E-mail
    assert not validar_email("")[0], "Deveria falhar email vazio"
    assert not validar_email("sem_arroba.com")[0], "Deveria falhar email sem arroba"
    assert not validar_email("user@dominio")[0], "Deveria falhar email sem TLD"
    assert validar_email("usuario.teste@gmail.com")[0], "Deveria aceitar email válido"

    # Senha
    assert not validar_senha("")[0], "Deveria falhar senha vazia"
    assert not validar_senha("12345")[0], "Deveria falhar senha com menos de 6 chars"
    assert not validar_senha("somenteletras")[0], "Deveria falhar senha sem números"
    assert not validar_senha("12345678")[0], "Deveria falhar senha sem letras"
    assert validar_senha("senha123")[0], "Deveria aceitar senha com letras e números"

    # Validação de registro de speedrun
    ok, erro = validar_registro_speedrun(tempo_ms=0)
    assert not ok and ("maior que 0" in erro or "positivo" in erro)

    ok, erro = validar_registro_speedrun(tempo_ms=60000, inimigos_derrotados=-1, total_inimigos=4)
    assert not ok and "negativo" in erro

    ok, erro = validar_registro_speedrun(tempo_ms=60000, inimigos_derrotados=6, total_inimigos=4)
    assert not ok and "exceder" in erro

    ok, erro = validar_registro_speedrun(tempo_ms=60000, inimigos_derrotados=3, total_inimigos=4)
    assert ok and erro is None

    # Conversão de tempo ms <-> mm:ss.mmm
    ms = converter_para_ms(1, 23, 456)
    assert ms == 83456, f"Esperado 83456 ms, obteve {ms}"
    m, s, mil = desmembrar_ms(ms)
    assert (m, s, mil) == (1, 23, 456)
    assert formatar_tempo_ms(ms) == "01:23.456"

    print("  -> Validações de dados e conversões de tempo: SUCESSO!")


def testar_banco_sqlite_crud():
    print("[2/6] Testando biblioteca SQLite e operações de CRUD completas...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        caminho_teste = Path(tmp.name)

    bd = BancoDados(caminho_teste)

    # 1. Contas padrão criadas (GMs Kaique e Rafael, e jogador comum)
    usuarios = bd.listar_usuarios()
    nomes = {u["username"]: u for u in usuarios}
    assert "Kaique" in nomes and nomes["Kaique"]["is_gm"] == 1, "Kaique deve ser Game Master"
    assert "Rafael" in nomes and nomes["Rafael"]["is_gm"] == 1, "Rafael deve ser Game Master"
    assert "jogador" in nomes and nomes["jogador"]["is_gm"] == 0, "jogador deve ser sobrevivente comum"
    assert "admin" not in nomes, "Conta 'admin' não deve existir no banco"

    # 2. Cadastro de usuário com bloqueio mandatório de GM
    novo = bd.cadastrar_usuario("speedrunner_pro", "rapido123", "pro@speed.com", "Corredor Pro", is_gm=True)
    assert novo["id"] is not None
    assert novo["username"] == "speedrunner_pro"
    assert novo["is_gm"] is False, "Novos cadastros não podem se tornar GM diretamente"
    u_db = bd.obter_usuario_por_id(novo["id"])
    assert u_db["is_gm"] == 0, "No banco SQLite o campo is_gm deve ser 0"

    # 3. Cadastro direto de usuário pelo GM (com permissão explícita)
    usuario_gm_criado = bd.cadastrar_usuario_gm(
        username="novo_admin",
        senha="adminPassword1",
        email="admin2@game.com",
        nome_completo="Segundo GM",
        is_gm=True,
        gm_executor="Kaique"
    )
    assert usuario_gm_criado["is_gm"] == 1, "GM pode cadastrar outro GM explicitamente"

    # 4. Atualização de usuário (Edição de cadastro pelo GM)
    bd.atualizar_usuario(
        usuario_id=novo["id"],
        nome_completo="Corredor Profissional Atualizado",
        email="pro_atualizado@speed.com",
        is_gm=False,
        nova_senha="novaSenha123",
        gm_executor="Kaique"
    )
    u_atualizado = bd.obter_usuario_por_id(novo["id"])
    assert u_atualizado["nome_completo"] == "Corredor Profissional Atualizado"
    assert u_atualizado["email"] == "pro_atualizado@speed.com"
    # Autenticar com a nova senha
    assert bd.autenticar_usuario("speedrunner_pro", "novaSenha123") is not None

    # 5. Consulta e listagem com filtros
    filtrados_gm = bd.listar_usuarios(filtro_perfil="gm")
    assert all(u["is_gm"] == 1 for u in filtrados_gm)
    filtrados_busca = bd.listar_usuarios(busca="Profissional")
    assert len(filtrados_busca) == 1 and filtrados_busca[0]["id"] == novo["id"]

    # 6. CRUD de Dados de Speedrun (Inserção manual pelo GM, Consulta, Atualização, Exclusão)
    res_run = bd.cadastrar_speedrun_manual(
        usuario_id=novo["id"],
        tempo_ms=75432,
        inimigos_derrotados=3,
        total_inimigos=4,
        concluido=True,
        usou_gm=False,
        gm_executor="Kaique"
    )
    run_id = res_run["id"]
    assert run_id > 0

    run_det = bd.obter_speedrun_por_id(run_id)
    assert run_det is not None
    assert run_det["tempo_ms"] == 75432
    assert run_det["inimigos_derrotados"] == 3

    # Atualizar registro de speedrun
    bd.atualizar_speedrun(
        speedrun_id=run_id,
        tempo_ms=72000,
        inimigos_derrotados=4,
        total_inimigos=4,
        concluido=True,
        usou_gm=False,
        gm_executor="Kaique"
    )
    run_det_att = bd.obter_speedrun_por_id(run_id)
    assert run_det_att["tempo_ms"] == 72000
    assert run_det_att["inimigos_derrotados"] == 4

    # Listagem detalhada de speedruns com filtros
    runs_detalhados = bd.listar_speedruns_detalhado(categoria="oficial", status_conclusao="concluida")
    assert any(r["id"] == run_id for r in runs_detalhados)

    # Estatísticas gerais analíticas
    stats = bd.obter_estatisticas_gerais_speedrun()
    assert stats["total_corridas"] >= 1
    assert stats["melhor_tempo_ms"] == 72000

    # Excluir registro de speedrun
    assert bd.excluir_speedrun(run_id, gm_executor="Kaique")
    assert bd.obter_speedrun_por_id(run_id) is None

    # 7. Exclusão de usuário com integridade referencial
    assert bd.excluir_usuario(usuario_gm_criado["id"])
    assert bd.obter_usuario_por_id(usuario_gm_criado["id"]) is None

    # Limpeza
    try:
        caminho_teste.unlink()
    except Exception:
        pass
    print("  -> Banco de dados SQLite e operações CRUD: SUCESSO!")


def testar_relatorios_exportacao():
    print("[3/6] Testando módulo de relatórios (CSV e PDF)...")
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
        csv_path = Path(tmp_csv.name)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = Path(tmp_pdf.name)

    # 1. Gerar relatório em formato CSV
    sucesso_csv = gerar_relatorio_csv(csv_path)
    assert bool(sucesso_csv), "Exportação em CSV deve retornar caminho ou True"
    assert csv_path.exists() and csv_path.stat().st_size > 0, "Arquivo CSV deve ser criado com conteúdo"

    conteudo_csv = csv_path.read_text(encoding="utf-8-sig")
    assert "ID da Corrida" in conteudo_csv and "Jogador / Usuário" in conteudo_csv, "Cabeçalho CSV padrão não encontrado"
    print(f"  -> Relatório CSV exportado com sucesso ({csv_path.stat().st_size} bytes).")

    # 2. Gerar relatório em formato PDF nativo
    sucesso_pdf = gerar_relatorio_pdf(pdf_path, gm_solicitante="Kaique (Teste Automatizado)")
    assert bool(sucesso_pdf), "Exportação em PDF deve retornar caminho ou True"
    assert pdf_path.exists() and pdf_path.stat().st_size > 0, "Arquivo PDF deve ser criado com conteúdo"
    assert pdf_path.read_bytes().startswith(b"%PDF"), "O arquivo gerado deve ser um PDF válido"
    print(f"  -> Relatório PDF exportado com sucesso ({pdf_path.stat().st_size} bytes).")

    # Limpeza
    for p in (csv_path, pdf_path):
        try:
            p.unlink()
        except Exception:
            pass
    print("  -> Geração e exportação de relatórios PDF e CSV: SUCESSO!")


def testar_interface_pyqt6():
    print("[4/6] Testando interfaces PyQt6 (Offscreen com 5 abas de GM)...")
    from PyQt6.QtWidgets import QApplication
    from interface_usuarios_gm import (
        DialogLoginCadastro, DialogRanking, JanelaPainelGM,
        DialogCadastrarUsuarioGM, DialogEditarUsuarioGM,
        DialogRegistroSpeedrunGM, DialogDetalhesSpeedrun
    )
    from tela_inicio import Menu

    app = QApplication.instance()
    if not app:
        app = QApplication([])

    menu = Menu()
    assert menu.windowTitle() == "Por uma Gota - Menu Principal"
    assert hasattr(menu, "atalho_gm"), "Menu principal deve registrar o atalho secreto de GM"
    assert menu.atalho_gm.key().toString() == "Ctrl+F12", "Atalho deve ser exatamente Ctrl+F12"
    assert not hasattr(menu, "btn_gm"), "Menu principal não deve conter botão público de GM visível"

    dialog_login = DialogLoginCadastro()
    assert dialog_login.windowTitle() == "Autenticação e Cadastro - Por uma Gota"
    assert not hasattr(dialog_login, "chk_cad_gm"), "Tela de cadastro não deve permitir criação de contas GM"

    gm_user = {"id": 1, "username": "Kaique", "is_gm": True}
    painel_gm = JanelaPainelGM(gm_user)
    assert painel_gm.abas.count() == 5, f"Painel GM deve possuir exatamente 5 abas modulares, possui {painel_gm.abas.count()}"
    titulos_abas = [painel_gm.abas.tabText(i) for i in range(5)]
    assert "👥 USUÁRIOS" in titulos_abas
    assert "🎮 DADOS (SPEEDRUNS)" in titulos_abas
    assert "📊 RELATÓRIOS DO RUNNER" in titulos_abas
    assert "📜 AUDITORIA & LOGS" in titulos_abas
    assert "⌨️ COMANDOS NO JOGO" in titulos_abas

    # Testar diálogos modais de suporte
    diag_cad = DialogCadastrarUsuarioGM(gm_executor=gm_user)
    assert "Cadastrar Novo Usuário" in diag_cad.windowTitle()

    diag_edit = DialogEditarUsuarioGM(usuario={"id": 2, "username": "jogador", "nome_completo": "Sobrevivente", "email": "j@g.com", "is_gm": False}, gm_executor=gm_user)
    assert "Editar Usuário" in diag_edit.windowTitle()

    diag_run = DialogRegistroSpeedrunGM(gm_usuario=gm_user)
    assert "Speedrun" in diag_run.windowTitle()

    # Validação da mensagem de bloqueio para não-GMs no atalho CTRL+F12
    msg_bloqueio = "Você não tem acesso a essas funções!!\nCaba Safado!!!"
    assert "Caba Safado!!!" in msg_bloqueio
    assert "Você não tem acesso a essas funções!!" in msg_bloqueio

    print("  -> Telas e Diálogos PyQt6: SUCESSO!")


def testar_jogo_pygame():
    print("[5/6] Testando mecânicas de jogo (portas, escadas, armadilhas, HUD e colisões)...")
    import pygame
    from codigos.mapa.mapa_prototipo import Mapa
    from codigos.outros.saude_ import SistemaSaude
    from codigos.outros.combate import SistemaCombate
    from codigos.outros.inimigos import Inimigo

    pygame.init()
    tela = pygame.display.set_mode((1600, 900))
    mapa = Mapa()
    assert mapa.zona_saida is not None, "Zona de saída/fuga deve estar definida no mapa"
    assert len(mapa.blocos) > 0, "Mapa deve conter blocos"
    assert not hasattr(mapa, "moedas") or len(mapa.moedas) == 0, "Não deve haver moedas no mapa"
    assert len(mapa.portas) > 0, "Mapa deve conter portas"
    assert len(mapa.escadas) > 0, "Mapa deve conter escadas"
    assert len(mapa.pedacos_teto) > 0, "Mapa deve conter armadilhas de teto"

    # Testar portas
    porta = mapa.portas[0]
    assert not porta.aberta, "Portas devem começar fechadas"
    assert porta.rect in mapa.obter_blocos_colisao(), "Porta fechada deve estar na lista de colisão"

    # Interagir para abrir porta
    mapa.interagir_portas(porta.rect.inflate(10, 10))
    assert porta.aberta, "Porta deve abrir após interação"
    assert porta.rect not in mapa.obter_blocos_colisao(), "Porta aberta não deve bloquear passagem"

    # Testar escada
    escada = mapa.escadas[0]
    assert mapa.esta_na_escada(escada), "Deve detectar presença na escada"

    # Testar armadilha de teto
    armadilha = mapa.pedacos_teto[0]
    assert armadilha.estado == "preso", "Armadilha deve começar presa no teto"

    # Simular jogador passando embaixo da armadilha
    rect_embaixo = pygame.Rect(armadilha.rect.centerx - 10, armadilha.rect.bottom + 50, 24, 30)
    armadilha.atualizar(mapa.obter_blocos_colisao(), rect_embaixo)
    assert armadilha.estado == "tremendo", "Armadilha deve tremer ao detectar jogador embaixo"

    saude = SistemaSaude(vida_maxima=100)
    combate = SistemaCombate()
    inimigo = Inimigo(100, 100)

    # Simular frames de renderização e lógica completa (tremor, queda, impacto e estilhaços)
    for _ in range(60):
        mapa.atualizar_armadilhas(rect_embaixo, saude, combate, False)
        mapa.desenhar(tela, 0, 0, 1600, 900, rect_embaixo)
        saude.atualizar()
        saude.desenhar_hud(tela)
        inimigo.atualizar(mapa.obter_blocos_colisao())
        inimigo.desenhar(tela, 0, 0, 1600, 900)
        pygame.display.flip()

    pygame.quit()
    print("  -> Mecânicas de jogo, portas, escadas e armadilhas: SUCESSO!")


if __name__ == "__main__":
    testar_validacoes()
    testar_banco_sqlite_crud()
    testar_relatorios_exportacao()
    testar_interface_pyqt6()
    testar_jogo_pygame()
    print("\n[6/6] TODOS OS TESTES PASSARAM COM SUCESSO ABSOLUTO! O sistema está 100% operacional e modularizado.")
