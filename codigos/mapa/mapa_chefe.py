"""
========================================================================
           POR UMA GOTA - MAPA DA CAVERNA DO CHEFE (ARENA FINAL)
========================================================================
Design focado em combate de arena de caverna:
- Dimensões otimizadas para 1600x900 (60x28 tiles = 1920x896 px)
- Entrada com porta de segurança / bloqueio de rocha (D)
- Plataformas naturais de rocha (X) com escadas (L) para combate aéreo e esquiva
- Armadilhas de estalactites / teto caindo (R)
- Fosso de ácido / estalagmites afiadas (S)
- Kit médico de emergência (H)
- Ampla arena aberta para manobra e confronto com o Chefe Mutante
- Zona de saída / nascente de água limpa (E)
========================================================================
"""

import random
from pathlib import Path
import pygame

from codigos.mapa.mapa_prototipo import (
    TILE_SIZE,
    Porta,
    PedacoTeto,
    PORTA_FECHADA_EH_DIREITA,
)

# ------------------------------------------------------------------------
# 1. GRADE DA CAVERNA DO CHEFE (60 colunas x 28 linhas)
# ------------------------------------------------------------------------
# X = Rocha / Parede | L = Escadas | R = Estalactites do Teto
# S = Fosso de Ácido (4 blocos) | H = Cura | P = Jogador | E = Nascente de Água
DADOS_CAVERNA = [
    # Teto de rocha sólido com estalactites instáveis
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X      R                   R                   R           X",
    "X                                                          X",
    "X                                                          X",
    "X          XXXXXXXXXXXX             XXXXXXXXXXXX           X",
    "X          X          X             X          X           X",
    "X          X    H     X             X          X           X",
    "X    LLL   XXXXXXXXXXXX             XXXXXXXXXXXX   LLL     X",
    "X    LLL                                           LLL     X",
    "X    LLL                                           LLL     X",
    "X    LLL                                           LLL     X",
    "X    LLL                                           LLL     X",
    "X    LLL       XXXXXXXXXXXXXXXXXXXXXXXXXXXX        LLL     X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                                          X",
    "X                                              H           X",
    "X  P                                                    E  X",
    "XXXXXXXXXXXSSSSXXXXXXXXXXXXSSSSXXXXXXXXXXXXSSSSXXXXXXXXXXXXX",
]

# Alias para compatibilidade
DADOS_MAPA = DADOS_CAVERNA

# Posição de spawn do Chefe na arena ampla da caverna: (coluna, linha)
INIMIGOS_INICIAIS = [
    (40, 24),  # O Chefe Mutante no centro-direito da arena
]

INIMIGOS_DETALHADOS = [
    (40, 24, "sapo"),  # O Sapo Mutante Gigante (Boss)
]


# ------------------------------------------------------------------------
# 2. CLASSE DA ARENA DA CAVERNA
# ------------------------------------------------------------------------

class MapaChefe:
    """
    Arena da Caverna do Chefe com compatibilidade total à interface Mapa.
    Suporta blocos de rocha texturizados, escadas, portas, armadilhas de estalactite e kits de cura.
    """
    def __init__(self):
        self.tile_size = TILE_SIZE
        pasta_projeto = Path(__file__).resolve().parents[2]
        pasta_cenario = pasta_projeto / "cenario"

        # Textura base do chão de rocha
        caminho_textura = pasta_cenario / "chao.png"
        if caminho_textura.is_file():
            try:
                self.textura_chao = pygame.image.load(str(caminho_textura)).convert()
            except Exception:
                self.textura_chao = pygame.Surface((self.tile_size, self.tile_size))
                self.textura_chao.fill((30, 25, 35))
        else:
            self.textura_chao = pygame.Surface((self.tile_size, self.tile_size))
            self.textura_chao.fill((30, 25, 35))

        # Texturas dos blocos de rocha (bloco 1 ao 5)
        self.texturas_blocos = []
        for i in range(1, 6):
            caminho_bloco = pasta_cenario / f"bloco_{i}.png"
            if caminho_bloco.is_file():
                try:
                    img_bloco = pygame.image.load(str(caminho_bloco)).convert()
                    self.texturas_blocos.append(
                        pygame.transform.scale(img_bloco, (self.tile_size, self.tile_size))
                    )
                except Exception as e:
                    print(f"Aviso ao carregar bloco_{i}.png: {e}")

        if not self.texturas_blocos:
            self.texturas_blocos.append(self.textura_chao)

        # Armadilhas de estalactite / escombros do teto
        self.textura_trap1 = None
        self.textura_trap2 = None
        self.sprite_trap3 = None

        caminho_trap1 = pasta_cenario / "trap1.png"
        if caminho_trap1.is_file():
            try:
                img_t1 = pygame.image.load(str(caminho_trap1)).convert()
                self.textura_trap1 = pygame.transform.scale(img_t1, (self.tile_size, self.tile_size))
            except Exception as e:
                print(f"Aviso ao carregar trap1.png: {e}")

        caminho_trap2 = pasta_cenario / "trap2.png"
        if caminho_trap2.is_file():
            try:
                img_t2 = pygame.image.load(str(caminho_trap2)).convert()
                self.textura_trap2 = pygame.transform.scale(img_t2, (self.tile_size, self.tile_size))
            except Exception as e:
                print(f"Aviso ao carregar trap2.png: {e}")

        caminho_trap3 = pasta_cenario / "trap3.png"
        if caminho_trap3.is_file():
            try:
                img_t3 = pygame.image.load(str(caminho_trap3)).convert_alpha()
                self.sprite_trap3 = pygame.transform.scale(img_t3, (self.tile_size, self.tile_size))
            except Exception as e:
                print(f"Aviso ao carregar trap3.png: {e}")

        # Textura do kit médico / cura
        caminho_textura_cura = pasta_cenario / "cura.png"
        self.textura_cura = None
        if caminho_textura_cura.is_file():
            try:
                self.textura_cura = pygame.image.load(str(caminho_textura_cura)).convert_alpha()
                self.textura_cura = pygame.transform.scale(self.textura_cura, (self.tile_size, self.tile_size))
            except Exception as e:
                print(f"Aviso ao carregar cura.png: {e}")

        # Sprites animados da armadilha de ácido embutida no chão (ocupando 4 quadrados com uma imagem única)
        self.largura_armadilha_padrao = self.tile_size * 4  # 128 px (4 quadrados)
        self.altura_sprite_acido = 54  # 54 px (22 px de bolhas flutuantes + 32 px de base do chão)
        self.offset_acido_y = 22  # 22 px de elevação das bolhas acima do piso
        self.sprites_acido = []
        for i in range(1, 4):
            caminho_acido = pasta_cenario / f"armadilha_acido_{i}.png"
            if caminho_acido.is_file():
                try:
                    img_ac = pygame.image.load(str(caminho_acido)).convert_alpha()
                    if img_ac.get_width() != self.largura_armadilha_padrao or img_ac.get_height() != self.altura_sprite_acido:
                        if img_ac.get_width() >= 512 and img_ac.get_height() >= 512:
                            sub_rect = pygame.Rect(0, int(img_ac.get_height() * 96 / 1024), img_ac.get_width(), int(img_ac.get_height() * 432 / 1024))
                            img_ac = img_ac.subsurface(sub_rect).copy()
                        img_ac = pygame.transform.scale(img_ac, (self.largura_armadilha_padrao, self.altura_sprite_acido))
                    self.sprites_acido.append(img_ac)
                except Exception as e:
                    print(f"Aviso ao carregar armadilha_acido_{i}.png: {e}")

        # Dimensões da caverna
        self.largura = len(DADOS_CAVERNA[0]) * self.tile_size
        self.altura = len(DADOS_CAVERNA) * self.tile_size

        self.blocos = []
        self.escadas = []
        self.portas = []
        self.pedacos_teto = []
        self.espinhos = []
        self.posicoes_acido = []
        self.moedas = []
        self.kits_medicos = []
        self.blocos_armadilhas = {}
        self.bloco_texturas = {}
        self.pos_inicial_jogador = (96, 25 * self.tile_size)
        self.zona_saida = pygame.Rect(55 * self.tile_size, 24 * self.tile_size, self.tile_size * 3, self.tile_size * 3)

        # Sprites das portas
        caminho_fechada = pasta_cenario / "porta_fechada.png"
        caminho_aberta = pasta_cenario / "porta_aberta.png"
        caminho_porta_raiz = pasta_projeto / "porta.png"

        self.sprite_porta_esquerda = None
        self.sprite_porta_direita = None

        if caminho_fechada.is_file() and caminho_aberta.is_file():
            try:
                img_f = pygame.image.load(str(caminho_fechada)).convert_alpha()
                w_f = max(24, int(round(64 * (img_f.get_width() / max(1, img_f.get_height())))))
                self.sprite_porta_esquerda = pygame.transform.scale(img_f, (w_f, 64))

                img_a = pygame.image.load(str(caminho_aberta)).convert_alpha()
                w_a = max(16, int(round(64 * (img_a.get_width() / max(1, img_a.get_height())))))
                self.sprite_porta_direita = pygame.transform.scale(img_a, (w_a, 64))
            except Exception as e:
                print(f"Aviso ao carregar portas de cenario/: {e}")

        if (self.sprite_porta_esquerda is None or self.sprite_porta_direita is None) and caminho_porta_raiz.is_file():
            try:
                surf_full = pygame.image.load(str(caminho_porta_raiz))
                if hasattr(surf_full, "convert_alpha") and pygame.display.get_surface():
                    surf_full = surf_full.convert_alpha()
                fw, fh = surf_full.get_size()
                mid_x = fw // 2
                half_l = surf_full.subsurface(pygame.Rect(0, 0, mid_x, fh))
                half_r = surf_full.subsurface(pygame.Rect(mid_x, 0, fw - mid_x, fh))
                bbox_l = half_l.get_bounding_rect(min_alpha=1)
                bbox_r = half_r.get_bounding_rect(min_alpha=1)
                sub_l = half_l.subsurface(bbox_l) if bbox_l.width > 0 and bbox_l.height > 0 else half_l
                sub_r = half_r.subsurface(bbox_r) if bbox_r.width > 0 and bbox_r.height > 0 else half_r
                w_esq = max(24, int(round(64 * (sub_l.get_width() / max(1, sub_l.get_height())))))
                self.sprite_porta_esquerda = pygame.transform.scale(sub_l, (w_esq, 64))
                w_dir = max(16, int(round(64 * (sub_r.get_width() / max(1, sub_r.get_height())))))
                self.sprite_porta_direita = pygame.transform.scale(sub_r, (w_dir, 64))
            except Exception as e:
                print(f"Aviso ao carregar porta.png: {e}")

        if PORTA_FECHADA_EH_DIREITA:
            self.sprite_porta_fechada = self.sprite_porta_direita
            self.sprite_porta_aberta = self.sprite_porta_esquerda
        else:
            self.sprite_porta_fechada = self.sprite_porta_esquerda
            self.sprite_porta_aberta = self.sprite_porta_direita

        self._processar_dados()

        # Superfície pré-renderizada do mapa
        self.textura_mapa = pygame.Surface((self.largura, self.altura))
        largura_textura, altura_textura = self.textura_chao.get_size()
        for y in range(0, self.altura, altura_textura):
            for x in range(0, self.largura, largura_textura):
                self.textura_mapa.blit(self.textura_chao, (x, y))

        for bloco in self.blocos:
            chave = (bloco.x, bloco.y)
            if chave in self.bloco_texturas:
                self.textura_mapa.blit(self.bloco_texturas[chave], (bloco.x, bloco.y))

    def _processar_dados(self):
        self.blocos.clear()
        self.escadas.clear()
        self.portas.clear()
        self.pedacos_teto.clear()
        self.espinhos.clear()
        self.posicoes_acido.clear()
        self.moedas.clear()
        self.kits_medicos.clear()
        self.blocos_armadilhas.clear()
        self.bloco_texturas.clear()

        posicoes_portas = []
        posicoes_armadilhas = []

        for linha_idx, linha in enumerate(DADOS_CAVERNA):
            for col_idx, caractere in enumerate(linha):
                pos_x = col_idx * self.tile_size
                pos_y = linha_idx * self.tile_size

                if caractere == "X":
                    self.blocos.append(pygame.Rect(pos_x, pos_y, self.tile_size, self.tile_size))
                elif caractere == "L":
                    self.escadas.append(pygame.Rect(pos_x, pos_y, self.tile_size, self.tile_size))
                elif caractere == "D":
                    posicoes_portas.append((col_idx, linha_idx, pos_x, pos_y))
                elif caractere == "R":
                    posicoes_armadilhas.append((pos_x, pos_y))
                elif caractere == "P":
                    self.pos_inicial_jogador = (pos_x, pos_y)
                elif caractere == "S":
                    # Armadilha de ácido embutida no chão (ocupando 4 quadrados com uma única imagem)
                    self.espinhos.append(pygame.Rect(pos_x, pos_y, self.tile_size, 16))
                    self.blocos.append(pygame.Rect(pos_x, pos_y + 16, self.tile_size, 16))
                    if col_idx == 0 or linha[col_idx - 1] != "S":
                        tam_armadilha = 1
                        while col_idx + tam_armadilha < len(linha) and linha[col_idx + tam_armadilha] == "S":
                            tam_armadilha += 1
                        largura_px = tam_armadilha * self.tile_size
                        self.posicoes_acido.append((pos_x, pos_y, largura_px))
                elif caractere == "H":
                    self.kits_medicos.append(pygame.Rect(pos_x + 6, pos_y + 6, 20, 20))
                elif caractere == "E":
                    self.zona_saida = pygame.Rect(pos_x, pos_y - self.tile_size, self.tile_size * 3, self.tile_size * 2)

        # Portas contíguas
        cols_portas = {}
        for c, l, px, py in posicoes_portas:
            cols_portas.setdefault(c, []).append((l, px, py))

        for c, lista in cols_portas.items():
            lista.sort(key=lambda item: item[0])
            grupos_contiguos = []
            grupo_atual = []
            for item in lista:
                if not grupo_atual or item[0] == grupo_atual[-1][0] + 1:
                    grupo_atual.append(item)
                else:
                    grupos_contiguos.append(grupo_atual)
                    grupo_atual = [item]
            if grupo_atual:
                grupos_contiguos.append(grupo_atual)

            for g_idx, grupo in enumerate(grupos_contiguos):
                grupo_id = f"porta_caverna_{c}_{g_idx}"
                for i, (l, px, py) in enumerate(grupo):
                    pos_vert = "topo" if i == 0 else "base" if len(grupo) > 1 else "sozinho"
                    self.portas.append(Porta(px, py, self.tile_size, pos_vertical=pos_vert, grupo_id=grupo_id))

        # Armadilhas de estalactite
        for pos_x, pos_y in posicoes_armadilhas:
            pos_teto_y = pos_y - self.tile_size
            rect_teto = pygame.Rect(pos_x, pos_teto_y, self.tile_size, self.tile_size)
            if rect_teto not in self.blocos:
                self.blocos.append(rect_teto)

            pedaco = PedacoTeto(pos_x, pos_y, self.tile_size, sprite=self.sprite_trap3, bloco_teto=rect_teto)
            self.pedacos_teto.append(pedaco)
            self.blocos_armadilhas[(pos_x, pos_teto_y)] = pedaco

        # Texturas dos blocos com variação
        rng = random.Random(101)
        for bloco in self.blocos:
            if (bloco.x, bloco.y) in self.blocos_armadilhas:
                if self.textura_trap1 is not None and self.textura_trap2 is not None:
                    tex = rng.choice([self.textura_trap1, self.textura_trap2])
                elif self.textura_trap1 is not None:
                    tex = self.textura_trap1
                else:
                    tex = rng.choice(self.texturas_blocos)
            else:
                tex = rng.choice(self.texturas_blocos)
            self.bloco_texturas[(bloco.x, bloco.y)] = tex

        # Posições dos inimigos (Chefe)
        self.inimigos_iniciais = [
            (col * self.tile_size, lin * self.tile_size)
            for col, lin in INIMIGOS_INICIAIS
        ]
        self.inimigos_detalhados = [
            (col * self.tile_size, lin * self.tile_size, tipo)
            for col, lin, tipo in INIMIGOS_DETALHADOS
        ]

    def obter_blocos_colisao(self):
        colisoes = list(self.blocos)
        colisoes.extend(p.rect for p in self.portas if not p.aberta)
        return colisoes

    @property
    def colisoes_com_portas(self):
        return [p.rect for p in self.portas if not p.aberta]

    def esta_na_escada(self, rect_jogador):
        for escada in self.escadas:
            if escada.colliderect(rect_jogador):
                return True
        return False

    def interagir_portas(self, jogador_rect):
        for porta in self.portas:
            area_interacao = porta.rect.inflate(36, 16)
            if area_interacao.colliderect(jogador_rect):
                estado_novo = not porta.aberta
                if not estado_novo and porta.rect.colliderect(jogador_rect):
                    continue
                if porta.grupo_id:
                    for p in self.portas:
                        if p.grupo_id == porta.grupo_id:
                            p.aberta = estado_novo
                else:
                    porta.aberta = estado_novo
                return True
        return False

    def atualizar_armadilhas(self, jogador_rect=None, saude=None, combate=None, god_mode=False):
        blocos_colisao = self.obter_blocos_colisao()
        for pedaco in self.pedacos_teto:
            pedaco.atualizar(
                blocos=blocos_colisao,
                jogador_rect=jogador_rect,
                saude=saude,
                combate=combate,
                god_mode=god_mode,
            )

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela, jogador_rect=None):
        # 1. Base pré-renderizada do mapa
        area_camera = pygame.Rect(
            camera_x,
            camera_y,
            min(largura_tela, max(0, self.largura - camera_x)),
            min(altura_tela, max(0, self.altura - camera_y)),
        )
        if area_camera.width > 0 and area_camera.height > 0:
            tela.blit(self.textura_mapa, (0, 0), area=area_camera)

        # 2. Escadas
        for escada in self.escadas:
            ex = escada.x - camera_x
            ey = escada.y - camera_y
            if -self.tile_size < ex < largura_tela + self.tile_size and -self.tile_size < ey < altura_tela + self.tile_size:
                pygame.draw.rect(tela, (70, 75, 80), (ex + 4, ey, 4, self.tile_size))
                pygame.draw.rect(tela, (70, 75, 80), (ex + self.tile_size - 8, ey, 4, self.tile_size))
                for degrau_y in range(ey + 4, ey + self.tile_size, 8):
                    pygame.draw.line(tela, (130, 140, 145), (ex + 4, degrau_y), (ex + self.tile_size - 5, degrau_y), 2)

        # 3. Portas
        for porta in self.portas:
            porta.desenhar(
                tela,
                camera_x,
                camera_y,
                largura_tela,
                altura_tela,
                sprite_fechada=self.sprite_porta_fechada,
                sprite_aberta=self.sprite_porta_aberta,
            )

        # 4. Armadilhas de estalactite
        for pedaco in self.pedacos_teto:
            pedaco.desenhar(tela, camera_x, camera_y, largura_tela, altura_tela)

        # 5. Armadilha de Ácido embutida no chão ('S') - Ocupando 4 quadrados com uma imagem única
        if self.sprites_acido and self.posicoes_acido:
            idx_frame = (pygame.time.get_ticks() // 150) % len(self.sprites_acido)
            sprite_atual = self.sprites_acido[idx_frame]
            for item in self.posicoes_acido:
                px = item[0]
                py = item[1]
                largura_px = item[2] if len(item) > 2 else self.largura_armadilha_padrao
                sx = px - camera_x
                sy = py - camera_y
                if -largura_px < sx < largura_tela and -64 < sy < altura_tela:
                    if sprite_atual.get_width() != largura_px:
                        sprite_desenho = pygame.transform.scale(sprite_atual, (largura_px, self.altura_sprite_acido))
                    else:
                        sprite_desenho = sprite_atual
                    tela.blit(sprite_desenho, (sx, sy - self.offset_acido_y))

        # 6. Kits médicos
        for kit in self.kits_medicos:
            kx = kit.centerx - camera_x
            ky = kit.centery - camera_y
            if -self.tile_size < kx < largura_tela + self.tile_size and -self.tile_size < ky < altura_tela + self.tile_size:
                rect_visual = pygame.Rect(0, 0, self.tile_size, self.tile_size)
                rect_visual.center = (kx, ky)
                if self.textura_cura is not None:
                    tela.blit(self.textura_cura, rect_visual)
                else:
                    pygame.draw.rect(tela, (200, 220, 210), rect_visual, border_radius=4)
                    pygame.draw.rect(tela, (45, 180, 100), (rect_visual.x + 13, rect_visual.y + 5, 6, 22))
                    pygame.draw.rect(tela, (45, 180, 100), (rect_visual.x + 5, rect_visual.y + 13, 22, 6))

        # 7. Zona de saída / Nascente de Água
        zx = self.zona_saida.x - camera_x
        zy = self.zona_saida.y - camera_y
        if -200 < zx < largura_tela + 200 and -200 < zy < altura_tela + 200:
            surf_saida = pygame.Surface((self.zona_saida.width, self.zona_saida.height), pygame.SRCALPHA)
            surf_saida.fill((30, 160, 255, 80))
            tela.blit(surf_saida, (zx, zy))
            pygame.draw.rect(tela, (50, 200, 255), (zx, zy, self.zona_saida.width, self.zona_saida.height), 3, border_radius=6)
            try:
                fonte = pygame.font.SysFont("consolas", 12, bold=True)
                txt = fonte.render("NASCENTE DE AGUA LIMPA [SAIDA]", True, (200, 240, 255))
                tela.blit(txt, txt.get_rect(center=(zx + self.zona_saida.width // 2, zy + 16)))
            except Exception:
                pass

        # 8. Prompt de interação das portas
        if jogador_rect:
            for porta in self.portas:
                if porta.pos_vertical in ("topo", "sozinho"):
                    if porta.rect.inflate(36, 16).colliderect(jogador_rect):
                        porta.desenhar_prompt_interacao(tela, camera_x, camera_y)


# Aliases padrão
Mapa = MapaChefe
