import pygame
import sys
from pathlib import Path
from mapa import Mapa
from saude import SistemaSaude
from combate import SistemaCombate
from inimigos import Inimigo

# 1. Configurações Iniciais
pygame.init()
LARGURA_TELA = 800
ALTURA_TELA = 600
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Prédio 2D - Combate com Hitboxes e Pulo de Recuo")
relogio = pygame.time.Clock()

# Instancia os módulos
mapa = Mapa()
saude = SistemaSaude(vida_maxima=100)
combate = SistemaCombate()

def criar_inimigos():
    return [Inimigo(x, y) for (x, y) in mapa.inimigos_iniciais]

inimigos = criar_inimigos()

# Fundo
try:
    caminho_fundo = Path(__file__).resolve().parent / "fundo.jpg"
    imagem_fundo = pygame.image.load(str(caminho_fundo)).convert()
    imagem_fundo = pygame.transform.scale(imagem_fundo, (LARGURA_TELA, ALTURA_TELA))
    tem_imagem_fundo = True
except pygame.error:
    tem_imagem_fundo = False

# Jogador e Física
jogador_rect = pygame.Rect(mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1], 24, 30)
vel_x = 0
vel_y = 0
vel_recuo_x = 0.0
velocidade_movimento = 5
gravidade = 0.75
forca_pulo = -15.5
no_chao = False

coyote_timer = 0
buffer_pulo_timer = 0
COYOTE_MAX = 7
BUFFER_MAX = 7

def reiniciar_jogo():
    global vel_x, vel_y, vel_recuo_x, no_chao, inimigos
    jogador_rect.topleft = mapa.pos_inicial_jogador
    saude.reiniciar()
    combate.parar_defesa()
    inimigos = criar_inimigos()
    vel_x = 0
    vel_y = 0
    vel_recuo_x = 0.0
    no_chao = False

# Loop Principal
executando = True
while executando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        if evento.type == pygame.KEYDOWN:
            if not saude.esta_vivo():
                if evento.key == pygame.K_r:
                    reiniciar_jogo()
            else:
                if evento.key == pygame.K_SPACE or evento.key == pygame.K_UP:
                    buffer_pulo_timer = BUFFER_MAX
                if evento.key == pygame.K_j or evento.key == pygame.K_z:
                    combate.tentar_atacar()
                if evento.key == pygame.K_k or evento.key == pygame.K_x:
                    combate.iniciar_defesa()

        if evento.type == pygame.KEYUP and saude.esta_vivo():
            if (evento.key == pygame.K_SPACE or evento.key == pygame.K_UP) and vel_y < -4:
                vel_y = -4
            if evento.key == pygame.K_k or evento.key == pygame.K_x:
                combate.parar_defesa()

    # Atualizações enquanto vivo
    if saude.esta_vivo():
        saude.atualizar()

        teclas = pygame.key.get_pressed()
        vel_x = 0
        vel_atual = velocidade_movimento * 0.4 if combate.defendendo else velocidade_movimento

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            vel_x = -vel_atual
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            vel_x = vel_atual

        if abs(vel_recuo_x) < 1.0:
            combate.atualizar_direcao(vel_x)

        # Pulo com tolerâncias
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

        # Gravidade
        vel_y += gravidade
        if vel_y > 15:
            vel_y = 15

        # Desaceleração do recuo
        if abs(vel_recuo_x) > 0.1:
            vel_recuo_x *= 0.80
        else:
            vel_recuo_x = 0.0

        # Colisão Eixo X
        deslocamento_x = int(vel_x + vel_recuo_x)
        jogador_rect.x += deslocamento_x
        for bloco in mapa.blocos:
            if jogador_rect.colliderect(bloco):
                if deslocamento_x > 0:
                    jogador_rect.right = bloco.left
                    vel_recuo_x = 0.0
                elif deslocamento_x < 0:
                    jogador_rect.left = bloco.right
                    vel_recuo_x = 0.0

        # Colisão Eixo Y
        jogador_rect.y += int(vel_y)
        no_chao = False
        for bloco in mapa.blocos:
            if jogador_rect.colliderect(bloco):
                if vel_y > 0:
                    jogador_rect.bottom = bloco.top
                    vel_y = 0
                    no_chao = True
                elif vel_y < 0:
                    jogador_rect.top = bloco.bottom
                    vel_y = 0

        # Atualiza hitboxes do jogador
        combate.atualizar(jogador_rect)

        # Atualização e combate com Inimigos
        for inimigo in inimigos:
            inimigo.atualizar(mapa.blocos, jogador_rect, combate.hitbox_escudo)

            # Se o jogador andar contra o inimigo enquanto defende, aplica pulinho para trás no inimigo
            if combate.defendendo and combate.hitbox_escudo is not None:
                if combate.hitbox_escudo.colliderect(inimigo.rect):
                    if combate.direcao == 1:
                        inimigo.rect.left = combate.hitbox_escudo.right
                    else:
                        inimigo.rect.right = combate.hitbox_escudo.left
                    if inimigo.tempo_atordoado <= 0:
                        inimigo.aplicar_pulinho_recuo(combate.direcao, forca_x=6.5, forca_y=-6.0)
                        inimigo.tempo_atordoado = 25

            # Ataque do jogador acertando o inimigo -> Jogador dá pulinho para trás
            if combate.atacando and combate.hitbox_ataque is not None:
                if combate.hitbox_ataque.colliderect(inimigo.rect):
                    if inimigo.tomar_dano(combate.dano_ataque, combate.direcao):
                        vel_recuo_x = -combate.direcao * combate.forca_recuo_x
                        vel_y = combate.forca_recuo_y
                        no_chao = False

            # Hitbox de Ataque do Inimigo acertando o jogador
            if inimigo.esta_vivo and inimigo.atacando and inimigo.hitbox_ataque is not None:
                if inimigo.hitbox_ataque.colliderect(jogador_rect):
                    bloqueado_pela_frente = (
                        combate.defendendo and
                        ((combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx) or
                         (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx))
                    )
                    if not bloqueado_pela_frente:
                        if saude.tomar_dano(inimigo.dano_ataque):
                            vel_y = -8
                            direcao_impacto = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                            vel_recuo_x = direcao_impacto * 6.5

            # Contato direto do corpo do inimigo no jogador
            if inimigo.esta_vivo and jogador_rect.colliderect(inimigo.rect):
                bloqueado_pela_frente = (
                    combate.defendendo and
                    ((combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx) or
                     (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx))
                )

                if not bloqueado_pela_frente:
                    if saude.tomar_dano(15):
                        vel_y = -8
                        direcao_impacto = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                        vel_recuo_x = direcao_impacto * 6.0

        # Limpa inimigos derrotados
        inimigos = [inimigo for inimigo in inimigos if inimigo.esta_vivo]

        # Dano dos espinhos
        for espinho in mapa.espinhos:
            if jogador_rect.colliderect(espinho):
                dano_calculado = combate.calcular_dano_recebido(25)
                if saude.tomar_dano(dano_calculado):
                    vel_y = -7
                break

        # Coleta de kits médicos
        for kit in mapa.kits_medicos[:]:
            if jogador_rect.colliderect(kit):
                if saude.curar(25):
                    mapa.kits_medicos.remove(kit)

    # Câmera
    camera_x = jogador_rect.centerx - LARGURA_TELA // 2
    camera_y = jogador_rect.centery - ALTURA_TELA // 2
    camera_x = max(0, min(camera_x, mapa.largura - LARGURA_TELA))
    camera_y = max(0, min(camera_y, mapa.altura - ALTURA_TELA))

    # Renderização do fundo
    if tem_imagem_fundo:
        fx = int(-camera_x * 0.25) % LARGURA_TELA
        fy = int(-camera_y * 0.25) % ALTURA_TELA
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy))
        tela.blit(imagem_fundo, (fx, fy))
    else:
        tela.fill((30, 32, 40))

    # Desenho do mapa
    mapa.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA)

    # Desenho dos inimigos
    for inimigo in inimigos:
        inimigo.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA)

    # Desenho do Jogador
    if saude.esta_vivo() and saude.deve_desenhar_jogador():
        jt = pygame.Rect(jogador_rect.x - camera_x, jogador_rect.y - camera_y, jogador_rect.width, jogador_rect.height)
        pygame.draw.rect(tela, (220, 50, 50), jt)
        combate.desenhar(tela, camera_x, camera_y, jogador_rect)

    # HUD e Game Over
    saude.desenhar_hud(tela)
    if not saude.esta_vivo():
        saude.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
sys.exit()