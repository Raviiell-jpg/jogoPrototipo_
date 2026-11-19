"""
========================================================================
                      POR UMA GOTA - UM SERTÃO RADIOATIVO
========================================================================
Loop Principal do Jogo (Pygame)
Unifica:
- Resolução 1600x900 com física suave (Coyote time, Jump buffer)
- Animações em spritesheet do jogador (pulo, corrida, ataque e defesa)
- Monstros mutantes animados (tatu, rato, lagartixa) com IA e recuo
- Sistema de portas de segurança com interação [E] e sprites oficiais
- Escadas industriais funcionais com subida/descida vertical
- Armadilhas de teto desabando com partículas de aviso radioativo
- Sistema completo de Speedrun (cronômetro, recordes e salvamento SQLite)
- Ferramentas integradas de Game Master (CTRL+F12, God Mode, Insta-kill, Teleporte)
- Totalmente portátil (sem caminhos absolutos, funciona em qualquer pasta)
"""

import argparse
import random
import sys
import time
from pathlib import Path

import pygame

# Diretório raiz portátil
PASTA_PROJETO = Path(__file__).resolve().parent
if str(PASTA_PROJETO) not in sys.path:
    sys.path.insert(0, str(PASTA_PROJETO))

from banco_dados import BancoDados
from codigos.mapa.mapa_prototipo import Mapa
from codigos.outros.combate import SistemaCombate
from codigos.outros.inimigos import Inimigo
from codigos.outros.monstros import (
    carregar_imagens_monstros,
    separar_spritesheet,
)
from codigos.outros.saude_ import SistemaSaude

# ------------------------------------------------------------------------
# 1. PARÂMETROS DE LINHA DE COMANDO E SESSÃO DO USUÁRIO
# ------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Por uma Gota - Um Sertão Radioativo")
parser.add_argument("--modo", choices=["normal", "speedrun"], default="normal", help="Modo de jogo")
parser.add_argument("--usuario", type=str, default="", help="Nome do jogador")
args, _ = parser.parse_known_args()

banco = BancoDados()
sessao_salva = banco.obter_sessao_atual()

if args.usuario:
    nome_usuario = args.usuario
    usuario_info = banco.obter_usuario_por_nome(nome_usuario)
    papel_usuario = usuario_info.get("papel", "jogador") if usuario_info else "jogador"
    usuario_id = usuario_info.get("id") if usuario_info else None
elif sessao_salva:
    nome_usuario = sessao_salva.get("usuario", "Sobrevivente")
    papel_usuario = sessao_salva.get("papel", "jogador")
    usuario_id = sessao_salva.get("id")
else:
    nome_usuario = "Sobrevivente"
    papel_usuario = "jogador"
    usuario_id = None

eh_gm = (papel_usuario.lower() == "gm")
modo_speedrun = (args.modo == "speedrun")

# ------------------------------------------------------------------------
# 2. INICIALIZAÇÃO DE VÍDEO, ÁUDIO E FONTES
# ------------------------------------------------------------------------
pygame.init()
LARGURA_TELA = 1600
ALTURA_TELA = 900
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Por uma Gota - Um Sertão Radioativo")
relogio = pygame.time.Clock()

# Trilha sonora
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    caminho_musica = PASTA_PROJETO / "musicas" / "sallyFace.mp3"
    if caminho_musica.is_file():
        pygame.mixer.music.load(str(caminho_musica))
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Aviso de áudio (não crítico): {e}")

# Fontes do sistema
def carregar_fonte(tamanho, negrito=True):
    try:
        return pygame.font.SysFont("Press Start 2P", tamanho, bold=negrito)
    except Exception:
        return pygame.font.SysFont("consolas", tamanho + 2, bold=negrito)

fonte_titulo = carregar_fonte(32)
fonte_media = carregar_fonte(14)
fonte_timer = carregar_fonte(18)
fonte_pequena = carregar_fonte(10)
fonte_status = carregar_fonte(9, negrito=False)

# ------------------------------------------------------------------------
# 3. CARREGAMENTO DE SPRITES E ANIMAÇÕES
# ------------------------------------------------------------------------
# Fundo com paralaxe
try:
    imagem_fundo = pygame.image.load(str(PASTA_PROJETO / "fundos" / "predio.png")).convert()
    tem_imagem_fundo = True
except Exception:
    tem_imagem_fundo = False

# Sprites do Jogador
PASTA_SPRITES = PASTA_PROJETO / "prites"
TAMANHO_SPRITE = (48, 92)

def carregar_quadros_spritesheet(nome_arquivo, quantidade_quadros, largura_fixa=None):
    caminho = PASTA_SPRITES / nome_arquivo
    if not caminho.is_file():
        surf_padrao = pygame.Surface((48, 92), pygame.SRCALPHA)
        surf_padrao.fill((57, 255, 20, 180))
        return [surf_padrao] * quantidade_quadros

    folha = pygame.image.load(str(caminho)).convert_alpha()
    largura_folha, altura_folha = folha.get_size()
    quadros = []

    for indice in range(quantidade_quadros):
        inicio_x = indice * largura_folha // quantidade_quadros
        fim_x = (indice + 1) * largura_folha // quantidade_quadros
        quadro = folha.subsurface((inicio_x, 0, fim_x - inicio_x, altura_folha)).copy()
        limites_visiveis = quadro.get_bounding_rect(min_alpha=8)
        if limites_visiveis.width > 0 and limites_visiveis.height > 0:
            quadro = quadro.subsurface(limites_visiveis).copy()

        largura = largura_fixa if largura_fixa else round(quadro.get_width() * TAMANHO_SPRITE[1] / max(1, quadro.get_height()))
        quadros.append(pygame.transform.scale(quadro, (max(1, largura), TAMANHO_SPRITE[1])))

    return quadros

quadros_pulo = carregar_quadros_spritesheet("pulo.png", 2)
quadros_andando = carregar_quadros_spritesheet("adnar.png", 4, largura_fixa=48)
quadros_ataque = carregar_quadros_spritesheet("luta.png", 3)
quadros_defesa = carregar_quadros_spritesheet("defesa.png", 2)

sprite_parado = quadros_andando[0]

quadros_andando_esq = [pygame.transform.flip(q, True, False) for q in quadros_andando]
quadros_ataque_esq = [pygame.transform.flip(q, True, False) for q in quadros_ataque]
quadros_defesa_esq = [pygame.transform.flip(q, True, False) for q in quadros_defesa]
quadros_pulo_esq = [pygame.transform.flip(q, True, False) for q in quadros_pulo]
sprite_parado_esq = pygame.transform.flip(sprite_parado, True, False)

# Sprites dos Monstros Mutantes
monstros_quadros = {}
try:
    imgs_monstros = carregar_imagens_monstros()
    GRADE_MONSTROS = {"tatu": (2, 2), "rato": (2, 2), "lagartixa": (1, 4)}
    for nome, (lin, col) in GRADE_MONSTROS.items():
        if nome in imgs_monstros:
            q_norm = separar_spritesheet(imgs_monstros[nome], lin, col)
            atk_key = nome + "Ataque"
            q_atk = separar_spritesheet(imgs_monstros[atk_key], lin, col) if atk_key in imgs_monstros else None
            monstros_quadros[nome] = (q_norm, q_atk)
except Exception as e:
    print(f"Aviso ao carregar sprites de monstros: {e}")

# ------------------------------------------------------------------------
# 4. INSTANCIAÇÃO DOS MÓDULOS DE JOGO
# ------------------------------------------------------------------------
mapa = Mapa()
saude = SistemaSaude(vida_maxima=100)
combate = SistemaCombate()

total_inimigos_fase = len(mapa.inimigos_iniciais)

def criar_inimigos():
    lista = []
    nomes_disponiveis = list(monstros_quadros.keys()) if monstros_quadros else []
    for x, y in mapa.inimigos_iniciais:
        if nomes_disponiveis:
            nome_escolhido = random.choice(nomes_disponiveis)
            q_n, q_a = monstros_quadros[nome_escolhido]
            lista.append(Inimigo(x, y, quadros=q_n, quadros_ataque=q_a))
        else:
            lista.append(Inimigo(x, y))
    return lista

inimigos = criar_inimigos()

# ------------------------------------------------------------------------
# 5. FÍSICA E ESTADOS DO JOGADOR
# ------------------------------------------------------------------------
jogador_rect = pygame.Rect(mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1], 24, 30)
vel_x = 0
vel_y = 0
vel_recuo_x = 0.0
velocidade_movimento = 5
gravidade = 0.75
forca_pulo = -15.5
no_chao = False
pulando = False
direcao_jogador = 1

coyote_timer = 0
buffer_pulo_timer = 0
COYOTE_MAX = 7
BUFFER_MAX = 7

# ------------------------------------------------------------------------
# 6. ESTADOS DE SPEEDRUN E GAME MASTER
# ------------------------------------------------------------------------
# Speedrun
tempo_inicio_ms = pygame.time.get_ticks()
tempo_final_ms = None
corrida_finalizada = False
novo_recorde = False
inimigos_derrotados = 0
recorde_pessoal = banco.obter_recorde_pessoal(usuario_id) if usuario_id else None

# Game Master
god_mode = False
insta_kill = False
super_velocidade = False
hitbox_debug = False
gm_menu_aberto = False
usou_gm = False
tempo_toast_gm = 0
mensagem_gm_toast = ""
exibir_ranking_tab = False

def notificar_gm(mensagem):
    global tempo_toast_gm, mensagem_gm_toast
    tempo_toast_gm = 150
    mensagem_gm_toast = mensagem

def registrar_acao_gm(acao, detalhes=""):
    global usou_gm
    usou_gm = True
    banco.registrar_acao_gm(
        usuario_gm=nome_usuario,
        acao=acao,
        detalhes=f"{detalhes} | Speedrun desclassificado" if modo_speedrun else detalhes,
    )
    notificar_gm(f"GM: {acao} | {detalhes}")

def formatar_tempo_ms(ms):
    if ms is None:
        return "--:--.---"
    total_seg = ms / 1000.0
    minutos = int(total_seg // 60)
    segundos = int(total_seg % 60)
    miliseg = int((ms % 1000))
    return f"{minutos:02d}:{segundos:02d}.{miliseg:03d}"

def reiniciar_jogo():
    global vel_x, vel_y, vel_recuo_x, no_chao, pulando, inimigos
    global tempo_inicio_ms, tempo_final_ms, corrida_finalizada, novo_recorde
    global inimigos_derrotados, usou_gm

    jogador_rect.topleft = mapa.pos_inicial_jogador
    saude.reiniciar()
    combate.parar_defesa()
    inimigos = criar_inimigos()
    vel_x = 0
    vel_y = 0
    vel_recuo_x = 0.0
    no_chao = False
    pulando = False

    tempo_inicio_ms = pygame.time.get_ticks()
    tempo_final_ms = None
    corrida_finalizada = False
    novo_recorde = False
    inimigos_derrotados = 0
    usou_gm = False

# ------------------------------------------------------------------------
# 7. LOOP PRINCIPAL DE EVENTOS E ATUALIZAÇÃO
# ------------------------------------------------------------------------
executando = True

while executando:
    # 7.1 Processamento de Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        if evento.type == pygame.KEYDOWN:
            # Menu de Ajuda / Ranking
            if evento.key == pygame.K_TAB:
                exibir_ranking_tab = not exibir_ranking_tab

            # Alternar Menu GM exclusivamente com atalho CTRL+F12
            eh_ctrl = (evento.mod & pygame.KMOD_CTRL) != 0
            if evento.key == pygame.K_F12 and eh_ctrl:
                sessao_atual = banco.obter_sessao_atual()
                if sessao_atual and sessao_atual.get("is_gm"):
                    eh_gm = True
                    nome_usuario = sessao_atual.get("usuario")
                    usuario_id = sessao_atual.get("id")
                    papel_usuario = "gm"
                    gm_menu_aberto = not gm_menu_aberto
                    exibir_ranking_tab = False
                elif eh_gm:
                    gm_menu_aberto = not gm_menu_aberto
                    exibir_ranking_tab = False
                else:
                    # Não é GM: abre a tela de login
                    from PyQt6.QtWidgets import QApplication, QMessageBox
                    from interface_usuarios_gm import DialogLoginCadastro

                    app = QApplication.instance()
                    if not app:
                        app = QApplication(sys.argv)

                    dlg = DialogLoginCadastro()
                    dlg.exec()
                    pygame.event.clear()

                    sessao_atual = banco.obter_sessao_atual()
                    if sessao_atual and sessao_atual.get("is_gm"):
                        eh_gm = True
                        nome_usuario = sessao_atual.get("usuario")
                        usuario_id = sessao_atual.get("id")
                        papel_usuario = "gm"
                        gm_menu_aberto = True
                        exibir_ranking_tab = False
                    else:
                        msg = QMessageBox()
                        msg.setWindowTitle("Acesso Negado")
                        msg.setIcon(QMessageBox.Icon.Warning)
                        msg.setText("Você não tem acesso a essas funções!!\nCaba Safado!!!")
                        msg.setStyleSheet("""
                            QMessageBox {
                                background-color: #101c11;
                                color: #ff5555;
                            }
                            QLabel {
                                color: #ffcccc;
                                font-size: 13px;
                                font-weight: bold;
                            }
                            QPushButton {
                                background-color: #471515;
                                border: 1px solid #ff4444;
                                color: #ffffff;
                                padding: 6px 16px;
                                font-weight: bold;
                            }
                        """)
                        msg.exec()
                        pygame.event.clear()

            # Comandos do Game Master
            if gm_menu_aberto:
                if evento.key == pygame.K_1 or evento.key == pygame.K_F2:
                    god_mode = not god_mode
                    registrar_acao_gm("God Mode", "Ativado" if god_mode else "Desativado")
                elif evento.key == pygame.K_2 or evento.key == pygame.K_F3:
                    saude.vida_atual = saude.vida_maxima
                    saude.vida_visual = saude.vida_maxima
                    registrar_acao_gm("Cura Total", "Vida restaurada a 100%")
                elif evento.key == pygame.K_3 or evento.key == pygame.K_F4:
                    qtd = len(inimigos)
                    inimigos.clear()
                    inimigos_derrotados += qtd
                    registrar_acao_gm("Insta-Kill", f"{qtd} monstros eliminados")
                elif evento.key == pygame.K_4 or evento.key == pygame.K_F5:
                    jogador_rect.topleft = mapa.pos_inicial_jogador
                    vel_x = vel_y = 0
                    registrar_acao_gm("Teleporte", "Topo / Inicio da fase")
                elif evento.key == pygame.K_5 or evento.key == pygame.K_F6:
                    if mapa.zona_saida:
                        jogador_rect.topleft = (mapa.zona_saida.x + 20, mapa.zona_saida.y - 10)
                        vel_x = vel_y = 0
                        registrar_acao_gm("Teleporte", "Reservatorio / Saida final")
                elif evento.key == pygame.K_6 or evento.key == pygame.K_F7:
                    mapa.kits_medicos.clear()
                    saude.curar(100)
                    registrar_acao_gm("Coleta Total", "Todos os kits coletados e vida restaurada")
                elif evento.key == pygame.K_7 or evento.key == pygame.K_F8:
                    hitbox_debug = not hitbox_debug
                    registrar_acao_gm("Hitbox Debug", "Visivel" if hitbox_debug else "Oculto")
                elif evento.key == pygame.K_8 or evento.key == pygame.K_F10:
                    super_velocidade = not super_velocidade
                    registrar_acao_gm("Super Velocidade", "Ativada (10px)" if super_velocidade else "Padrao (5px)")
                elif evento.key == pygame.K_9 or evento.key == pygame.K_F11:
                    from PyQt6.QtWidgets import QApplication
                    from interface_usuarios_gm import JanelaPainelGM
                    app = QApplication.instance()
                    if not app:
                        app = QApplication(sys.argv)
                    u_gm = banco.obter_sessao_atual() or {"id": usuario_id, "username": nome_usuario, "is_gm": True}
                    janela_gm = JanelaPainelGM(usuario_gm=u_gm)
                    janela_gm.exec()
                    pygame.event.clear()
                elif evento.key == pygame.K_ESCAPE or (evento.key == pygame.K_F12 and eh_ctrl):
                    gm_menu_aberto = False

            # Reiniciar partida
            if evento.key == pygame.K_r and (not saude.esta_vivo() or corrida_finalizada):
                reiniciar_jogo()

            # Ações de Jogo normais
            if saude.esta_vivo() and not corrida_finalizada and not gm_menu_aberto:
                # Pulo
                if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    buffer_pulo_timer = BUFFER_MAX

                # Interação com Portas Blindadas (E)
                if evento.key == pygame.K_e:
                    mapa.interagir_portas(jogador_rect)

                # Ataque (J ou Z)
                if evento.key in (pygame.K_j, pygame.K_z):
                    combate.tentar_atacar()

                # Defesa / Escudo (K ou X)
                if evento.key in (pygame.K_k, pygame.K_x):
                    combate.iniciar_defesa()

        if evento.type == pygame.KEYUP:
            if saude.esta_vivo() and not corrida_finalizada:
                # Cancelar altura de pulo ao soltar a tecla
                if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and vel_y < -4:
                    vel_y = -4

                # Soltar defesa
                if evento.key in (pygame.K_k, pygame.K_x):
                    combate.parar_defesa()

        # Teleporte Livre com Clique Direito do GM
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3 and eh_gm:
            mx, my = pygame.mouse.get_pos()
            cam_x = jogador_rect.centerx - LARGURA_TELA // 2
            cam_y = jogador_rect.centery - ALTURA_TELA // 2
            jogador_rect.center = (mx + cam_x, my + cam_y)
            vel_x = vel_y = 0
            registrar_acao_gm("Teleporte Livre", f"Pos ({jogador_rect.x}, {jogador_rect.y})")

    # 7.2 Atualizações Físicas e de Entidades
    if saude.esta_vivo() and not corrida_finalizada:
        saude.atualizar()

        # Armadilhas de Teto Caindo
        blocos_colisao = mapa.obter_blocos_colisao()
        for pedaco in mapa.pedacos_teto:
            pedaco.atualizar(blocos_colisao, jogador_rect, saude, combate, god_mode)

        # Entrada e Movimento
        teclas = pygame.key.get_pressed()
        vel_x = 0

        vel_base = 10 if super_velocidade else velocidade_movimento
        vel_atual = vel_base * 0.4 if combate.defendendo else vel_base

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            vel_x = -vel_atual
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            vel_x = vel_atual

        if abs(vel_recuo_x) < 1.0:
            combate.atualizar_direcao(vel_x)
        if vel_x < 0:
            direcao_jogador = -1
        elif vel_x > 0:
            direcao_jogador = 1

        # Mecânica de Escada Industrial
        na_escada = mapa.esta_na_escada(jogador_rect)
        if na_escada:
            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                vel_y = -4.5
                pulando = False
            elif teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                vel_y = 4.5
                pulando = False
            else:
                vel_y = 0

            if teclas[pygame.K_SPACE]:
                vel_y = forca_pulo * 0.8
                pulando = True
        else:
            # Buffers de salto
            if no_chao:
                coyote_timer = COYOTE_MAX
            elif coyote_timer > 0:
                coyote_timer -= 1

            if buffer_pulo_timer > 0:
                buffer_pulo_timer -= 1

            if buffer_pulo_timer > 0 and coyote_timer > 0:
                vel_y = forca_pulo
                coyote_timer = 0
                buffer_pulo_timer = 0
                no_chao = False
                pulando = True

            # Gravidade padrão
            vel_y += gravidade
            if vel_y > 15:
                vel_y = 15

        if abs(vel_recuo_x) > 0.1:
            vel_recuo_x *= 0.80
        else:
            vel_recuo_x = 0.0

        # Colisão Eixo X (Paredes sólidas + Portas fechadas)
        deslocamento_x = int(vel_x + vel_recuo_x)
        jogador_rect.x += deslocamento_x
        for bloco in mapa.colisoes_com_portas:
            if jogador_rect.colliderect(bloco):
                if deslocamento_x > 0:
                    jogador_rect.right = bloco.left
                    vel_recuo_x = 0.0
                elif deslocamento_x < 0:
                    jogador_rect.left = bloco.right
                    vel_recuo_x = 0.0

        # Colisão Eixo Y (Paredes sólidas + Portas fechadas)
        jogador_rect.y += int(vel_y)
        no_chao = False
        for bloco in mapa.colisoes_com_portas:
            if jogador_rect.colliderect(bloco):
                if vel_y > 0:
                    jogador_rect.bottom = bloco.top
                    vel_y = 0
                    no_chao = True
                elif vel_y < 0:
                    jogador_rect.top = bloco.bottom
                    vel_y = 0

        if no_chao:
            pulando = False

        # Combate e Escudo
        combate.atualizar(jogador_rect)

        # Atualização dos Inimigos
        inimigos_mortos_neste_frame = 0
        for inimigo in inimigos:
            inimigo.atualizar(mapa.colisoes_com_portas, jogador_rect, combate.hitbox_escudo)

            # Escudo empurra inimigo
            if combate.defendendo and combate.hitbox_escudo is not None:
                if combate.hitbox_escudo.colliderect(inimigo.rect):
                    if combate.direcao == 1:
                        inimigo.rect.left = combate.hitbox_escudo.right
                    else:
                        inimigo.rect.right = combate.hitbox_escudo.left
                    if inimigo.tempo_atordoado <= 0:
                        inimigo.aplicar_pulinho_recuo(combate.direcao, forca_x=6.5, forca_y=-6.0)
                        inimigo.tempo_atordoado = 25

            # Ataque do Jogador
            if combate.atacando and combate.hitbox_ataque is not None:
                if combate.hitbox_ataque.colliderect(inimigo.rect):
                    dano_desferido = 9999 if insta_kill else combate.dano_ataque
                    if inimigo.tomar_dano(dano_desferido, combate.direcao):
                        vel_recuo_x = -combate.direcao * combate.forca_recuo_x
                        vel_y = combate.forca_recuo_y
                        no_chao = False

            # Ataque do Inimigo no Jogador
            if not god_mode and inimigo.esta_vivo and inimigo.atacando and inimigo.hitbox_ataque is not None:
                if inimigo.hitbox_ataque.colliderect(jogador_rect):
                    bloqueado = combate.defendendo and (
                        (combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx)
                        or (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx)
                    )
                    if not bloqueado:
                        dano_calc = combate.calcular_dano_recebido(inimigo.dano_ataque)
                        if saude.tomar_dano(dano_calc):
                            vel_y = -8
                            dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                            vel_recuo_x = dir_imp * 6.5

            # Colisão por contato com Inimigo
            if not god_mode and inimigo.esta_vivo and jogador_rect.colliderect(inimigo.rect):
                bloqueado = combate.defendendo and (
                    (combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx)
                    or (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx)
                )
                if not bloqueado:
                    dano_calc = combate.calcular_dano_recebido(15)
                    if saude.tomar_dano(dano_calc):
                        vel_y = -8
                        dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                        vel_recuo_x = dir_imp * 6.0

        # Limpar inimigos mortos e somar estatísticas
        qtd_antes = len(inimigos)
        inimigos = [inimigo for inimigo in inimigos if inimigo.esta_vivo]
        inimigos_derrotados += (qtd_antes - len(inimigos))

        # Espinhos
        if not god_mode:
            for espinho in mapa.espinhos:
                if jogador_rect.colliderect(espinho):
                    dano_calc = combate.calcular_dano_recebido(25)
                    if saude.tomar_dano(dano_calc):
                        vel_y = -7
                    break

        # Coleta de Kits Médicos
        for kit in mapa.kits_medicos[:]:
            if jogador_rect.colliderect(kit):
                if saude.curar(25):
                    mapa.kits_medicos.remove(kit)

        # Vitória / Chegada ao Reservatório de Água (Saída)
        if mapa.zona_saida and jogador_rect.colliderect(mapa.zona_saida) and not corrida_finalizada:
            corrida_finalizada = True
            tempo_final_ms = pygame.time.get_ticks() - tempo_inicio_ms

            # Gravar no SQLite
            if usuario_id is not None:
                novo_recorde = banco.registrar_speedrun(
                    usuario_id=usuario_id,
                    tempo_ms=tempo_final_ms,
                    inimigos_derrotados=inimigos_derrotados,
                    total_inimigos=total_inimigos_fase,
                    usou_gm=usou_gm,
                )
                recorde_pessoal = banco.obter_recorde_pessoal(usuario_id)

    # Toast Timer
    if tempo_toast_gm > 0:
        tempo_toast_gm -= 1

    # --------------------------------------------------------------------
    # 8. RENDERIZAÇÃO GRÁFICA (CÂMERA, CENÁRIO E ENTIDADES)
    # --------------------------------------------------------------------
    # Câmera centralizada no jogador
    camera_x = jogador_rect.centerx - LARGURA_TELA // 2
    camera_y = jogador_rect.centery - ALTURA_TELA // 2
    camera_x = max(0, min(camera_x, mapa.largura - LARGURA_TELA))
    camera_y = max(0, min(camera_y, mapa.altura - ALTURA_TELA))

    # Fundo com paralaxe
    if tem_imagem_fundo:
        fx = int(-camera_x * 0.25) % LARGURA_TELA
        fy = int(-camera_y * 0.25) % ALTURA_TELA
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy))
        tela.blit(imagem_fundo, (fx, fy))
    else:
        tela.fill((16, 22, 18))

    # Desenho do Mapa (blocos, escadas, portas, armadilhas, saída)
    mapa.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA, jogador_rect)

    # Desenho dos Inimigos
    for inimigo in inimigos:
        inimigo.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA)

    # Desenho do Jogador
    if saude.esta_vivo() and saude.deve_desenhar_jogador():
        jt = pygame.Rect(
            jogador_rect.x - camera_x,
            jogador_rect.y - camera_y,
            jogador_rect.width,
            jogador_rect.height,
        )

        if combate.atacando:
            progresso_ataque = combate.duracao_ataque - combate.timer_ataque
            indice_quadro = min(
                progresso_ataque * len(quadros_ataque) // combate.duracao_ataque,
                len(quadros_ataque) - 1,
            )
            sprite_atual = quadros_ataque[indice_quadro] if direcao_jogador > 0 else quadros_ataque_esq[indice_quadro]
        elif combate.defendendo:
            indice_quadro = (pygame.time.get_ticks() // 220) % len(quadros_defesa)
            sprite_atual = quadros_defesa[indice_quadro] if direcao_jogador > 0 else quadros_defesa_esq[indice_quadro]
        elif pulando:
            indice_quadro = (pygame.time.get_ticks() // 180) % len(quadros_pulo)
            sprite_atual = quadros_pulo[indice_quadro] if direcao_jogador > 0 else quadros_pulo_esq[indice_quadro]
        elif vel_x != 0:
            indice_quadro = (pygame.time.get_ticks() // 120) % len(quadros_andando)
            sprite_atual = quadros_andando[indice_quadro] if direcao_jogador > 0 else quadros_andando_esq[indice_quadro]
        else:
            sprite_atual = sprite_parado if direcao_jogador > 0 else sprite_parado_esq

        sprite_rect = sprite_atual.get_rect(midbottom=(jt.centerx, jt.bottom))
        tela.blit(sprite_atual, sprite_rect)

        # Desenhar efeitos visuais do combate (hitbox de ataque e escudo)
        combate.desenhar(tela, camera_x, camera_y, jogador_rect)

    # Depurador de Hitbox do GM
    if hitbox_debug:
        # Jogador
        pygame.draw.rect(tela, (57, 255, 20), jogador_rect.move(-camera_x, -camera_y), 2)
        # Inimigos
        for ini in inimigos:
            pygame.draw.rect(tela, (255, 40, 40), ini.rect.move(-camera_x, -camera_y), 2)
            if ini.hitbox_ataque:
                pygame.draw.rect(tela, (255, 200, 0), ini.hitbox_ataque.move(-camera_x, -camera_y), 1)
        # Portas
        for porta in mapa.portas:
            cor_p = (0, 255, 255) if porta.aberta else (255, 120, 0)
            pygame.draw.rect(tela, cor_p, porta.rect.move(-camera_x, -camera_y), 1)

    # --------------------------------------------------------------------
    # 9. HUD SUPERIOR, ESTATÍSTICAS E PAINÉIS OVERLAY
    # --------------------------------------------------------------------
    # Barra de Saúde/Sede
    saude.desenhar_hud(tela)

    # Painel de Speedrun no Canto Superior Direito
    tempo_atual_ms = tempo_final_ms if corrida_finalizada else (pygame.time.get_ticks() - tempo_inicio_ms)
    largura_hud_timer = 360
    altura_hud_timer = 94
    timer_x = LARGURA_TELA - largura_hud_timer - 30
    timer_y = 30

    surf_timer = pygame.Surface((largura_hud_timer, altura_hud_timer), pygame.SRCALPHA)
    surf_timer.fill((8, 22, 12, 220))
    tela.blit(surf_timer, (timer_x, timer_y))
    cor_borda_timer = (255, 80, 80) if usou_gm else (57, 255, 20)
    pygame.draw.rect(tela, cor_borda_timer, (timer_x, timer_y, largura_hud_timer, altura_hud_timer), 2, border_radius=4)

    # Tempo Formatado
    tempo_str = formatar_tempo_ms(tempo_atual_ms)
    cor_tempo = (255, 220, 100) if corrida_finalizada else (57, 255, 20)
    txt_cronometro = fonte_timer.render(tempo_str, True, cor_tempo)
    tela.blit(txt_cronometro, (timer_x + 16, timer_y + 12))

    # Inimigos Eliminados
    info_stats = f"Inimigos Eliminados: {inimigos_derrotados}/{total_inimigos_fase}"
    txt_stats = fonte_pequena.render(info_stats, True, (200, 240, 200))
    tela.blit(txt_stats, (timer_x + 16, timer_y + 44))

    # Status de Registro / Recorde Pessoal
    if usou_gm:
        txt_status_sr = fonte_status.render("⚠️ GM ATIVO: PARTIDA DESCLASSIFICADA", True, (255, 100, 100))
    else:
        rec_txt = recorde_pessoal["tempo_formatado"] if recorde_pessoal else "--:--.---"
        txt_status_sr = fonte_status.render(f"OFICIAL | Seu Recorde: {rec_txt}", True, (255, 215, 0))
    tela.blit(txt_status_sr, (timer_x + 16, timer_y + 68))

    # Notificação Toast de Ação de GM
    if tempo_toast_gm > 0 and mensagem_gm_toast:
        surf_toast = pygame.Surface((700, 34), pygame.SRCALPHA)
        surf_toast.fill((10, 18, 12, 230))
        tx = (LARGURA_TELA - 700) // 2
        tela.blit(surf_toast, (tx, 130))
        pygame.draw.rect(tela, (255, 215, 0), (tx, 130, 700, 34), 1, border_radius=3)
        lbl_toast = fonte_pequena.render(mensagem_gm_toast, True, (255, 230, 120))
        tela.blit(lbl_toast, lbl_toast.get_rect(center=(LARGURA_TELA // 2, 147)))

    # --------------------------------------------------------------------
    # 10. TELAS DE RESULTADO (GAME OVER E VITÓRIA)
    # --------------------------------------------------------------------
    if not saude.esta_vivo():
        saude.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)

    elif corrida_finalizada:
        surf_vit = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        surf_vit.fill((4, 14, 8, 235))
        tela.blit(surf_vit, (0, 0))

        cx = LARGURA_TELA // 2
        cy = ALTURA_TELA // 2

        txt_v1 = fonte_titulo.render("FUGA BEM-SUCEDIDA!", True, (57, 255, 20))
        tela.blit(txt_v1, txt_v1.get_rect(center=(cx, cy - 160)))

        txt_v2 = fonte_media.render("Você alcançou o reservatório subterrâneo de água pura!", True, (210, 255, 210))
        tela.blit(txt_v2, txt_v2.get_rect(center=(cx, cy - 110)))

        txt_v3 = fonte_timer.render(f"TEMPO FINAL: {formatar_tempo_ms(tempo_final_ms)}", True, (255, 255, 255))
        tela.blit(txt_v3, txt_v3.get_rect(center=(cx, cy - 60)))

        if novo_recorde:
            txt_rec_novo = fonte_media.render("★ NOVO RECORDE PESSOAL SALVO NO BANCO SQLITE! ★", True, (255, 215, 0))
            tela.blit(txt_rec_novo, txt_rec_novo.get_rect(center=(cx, cy - 20)))

        if usou_gm:
            txt_gm_descl = fonte_pequena.render("⚠️ Partida com auxílio de GM (não inclusa no ranking oficial)", True, (255, 120, 120))
            tela.blit(txt_gm_descl, txt_gm_descl.get_rect(center=(cx, cy + 15)))

        estat_str = f"Inimigos Eliminados: {inimigos_derrotados}/{total_inimigos_fase}"
        txt_estat = fonte_pequena.render(estat_str, True, (180, 230, 190))
        tela.blit(txt_estat, txt_estat.get_rect(center=(cx, cy + 50)))

        # Mini Leaderboard do SQLite
        ranking_top = banco.obter_ranking(limite=3, apenas_legitimos=True)
        if ranking_top:
            txt_rk_header = fonte_pequena.render("--- TOP 3 SOBREVIVENTES NO LEADERBOARD SQLITE ---", True, (135, 206, 250))
            tela.blit(txt_rk_header, txt_rk_header.get_rect(center=(cx, cy + 95)))
            for idx, rk in enumerate(ranking_top):
                linha_rk = f"#{rk['posicao']} {rk['username']} - {rk['tempo_formatado']} (Abates: {rk.get('inimigos_derrotados', 0)})"
                txt_lrk = fonte_pequena.render(linha_rk, True, (240, 240, 240))
                tela.blit(txt_lrk, txt_lrk.get_rect(center=(cx, cy + 120 + (idx * 24))))

        txt_controles_v = fonte_pequena.render("[R] JOGAR NOVAMENTE   |   [TAB] VER RANKING COMPLETO   |   [ESC] SAIR", True, (120, 255, 170))
        tela.blit(txt_controles_v, txt_controles_v.get_rect(center=(cx, cy + 225)))

    # --------------------------------------------------------------------
    # 11. MENU OVERLAY DE GAME MASTER (CTRL+F12)
    # --------------------------------------------------------------------
    if gm_menu_aberto:
        largura_gm = 720
        altura_gm = 540
        gm_x = (LARGURA_TELA - largura_gm) // 2
        gm_y = (ALTURA_TELA - altura_gm) // 2

        surf_gm = pygame.Surface((largura_gm, altura_gm), pygame.SRCALPHA)
        surf_gm.fill((10, 20, 14, 245))
        tela.blit(surf_gm, (gm_x, gm_y))
        pygame.draw.rect(tela, (255, 215, 0), (gm_x, gm_y, largura_gm, altura_gm), 3, border_radius=6)

        txt_gm_header = fonte_media.render("👑 FERRAMENTAS DO GAME MASTER (GM / ADMIN)", True, (255, 215, 0))
        tela.blit(txt_gm_header, (gm_x + 30, gm_y + 20))

        linhas_comandos_gm = [
            ("[1 ou F2] Modo Deus (God Mode)", f"Status: {'ATIVO (Invulneravel)' if god_mode else 'DESATIVADO'}"),
            ("[2 ou F3] Restaurar Saúde Completa", "Cura 100% da sede/vida"),
            ("[3 ou F4] Insta-Kill Todos os Monstros", f"Elimina {len(inimigos)} monstros na tela"),
            ("[4 ou F5] Teleporte para o Topo", "Retornar ao terraço inicial"),
            ("[5 ou F6] Teleporte para o Reservatório", "Ir direto à zona de fuga / saída"),
            ("[6 ou F7] Coletar Kits Médicos", "Coleta todos os kits e restaura saúde"),
            ("[7 ou F8] Depurador de Hitbox", f"Status: {'VISIVEL' if hitbox_debug else 'OCULTO'}"),
            ("[8 ou F10] Super Velocidade (Turbo)", f"Status: {'ATIVO (2x)' if super_velocidade else 'PADRAO (5px)'}"),
            ("[9 ou F11] Painel Administrativo GM", "Abre painel completo (Usuários, Relatórios e Dados)"),
            ("[Clique Direito]", "Teleporte livre para o cursor do mouse"),
            ("[CTRL+F12 / ESC]", "Fechar este painel de Game Master"),
        ]

        for i, (tecla, desc) in enumerate(linhas_comandos_gm):
            y_item = gm_y + 60 + (i * 42)
            t_tecla = fonte_pequena.render(tecla, True, (57, 255, 20))
            t_desc = fonte_pequena.render(desc, True, (220, 240, 220))
            tela.blit(t_tecla, (gm_x + 30, y_item))
            tela.blit(t_desc, (gm_x + 330, y_item))

    # --------------------------------------------------------------------
    # 12. OVERLAY DO LEADERBOARD COMPLETO (TAB)
    # --------------------------------------------------------------------
    if exibir_ranking_tab and not gm_menu_aberto:
        largura_rk = 760
        altura_rk = 540
        rk_x = (LARGURA_TELA - largura_rk) // 2
        rk_y = (ALTURA_TELA - altura_rk) // 2

        surf_rk = pygame.Surface((largura_rk, altura_rk), pygame.SRCALPHA)
        surf_rk.fill((8, 18, 12, 245))
        tela.blit(surf_rk, (rk_x, rk_y))
        pygame.draw.rect(tela, (57, 255, 20), (rk_x, rk_y, largura_rk, altura_rk), 3, border_radius=6)

        txt_rk_t = fonte_media.render("🏆 RANKING OFICIAL DE SPEEDRUN (SQLITE)", True, (57, 255, 20))
        tela.blit(txt_rk_t, (rk_x + 30, rk_y + 25))

        linhas_lead = banco.obter_ranking(limite=10, apenas_legitimos=True)
        cabecalho_col = f"{'POS':<6} {'SOBREVIVENTE':<24} {'TEMPO':<16} {'ABATES':<8}"
        tela.blit(fonte_pequena.render(cabecalho_col, True, (255, 215, 0)), (rk_x + 30, rk_y + 65))
        pygame.draw.line(tela, (40, 80, 45), (rk_x + 30, rk_y + 85), (rk_x + largura_rk - 30, rk_y + 85), 2)

        if not linhas_lead:
            txt_vazio = fonte_pequena.render("Nenhum tempo oficial registrado ainda.", True, (180, 180, 180))
            tela.blit(txt_vazio, (rk_x + 30, rk_y + 110))
        else:
            for idx, rk in enumerate(linhas_lead):
                y_pos = rk_y + 100 + (idx * 32)
                linha_t = f"#{rk['posicao']:<5} {rk['username']:<24} {rk['tempo_formatado']:<16} {rk.get('inimigos_derrotados', 0):<8}"
                cor_item = (57, 255, 20) if rk["posicao"] == 1 else (240, 240, 240)
                tela.blit(fonte_pequena.render(linha_t, True, cor_item), (rk_x + 30, y_pos))

        txt_fechar_rk = fonte_pequena.render("Pressione [TAB] para fechar o Ranking", True, (150, 180, 150))
        tela.blit(txt_fechar_rk, (rk_x + 30, rk_y + altura_rk - 35))

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
sys.exit()
