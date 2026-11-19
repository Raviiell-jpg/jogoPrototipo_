import random
import pygame
from pathlib import Path

TILE_SIZE = 32

# Lista original mantida para não quebrar seu código atual (coluna, linha)
INIMIGOS_INICIAIS = [
    (39, 4), (9, 10), (43, 10), (70, 10),
    (15, 16), (43, 22), (9, 28), (63, 28),
    (38, 34), (73, 40), (17, 46), (40, 52),
    (15, 58), (42, 64), (62, 64),
]

# Nova lista detalhada caso queira instanciar cada monstro específico: (coluna, linha, tipo)
INIMIGOS_DETALHADOS = [
    (39, 4, "moco"),
    (9, 10, "tatu"), (43, 10, "calango"), (70, 10, "moco"),
    (15, 16, "calango"),
    (43, 22, "tatu"),
    (9, 28, "moco"), (63, 28, "calango"),
    (38, 34, "tatu"),
    (73, 40, "calango"),
    (17, 46, "tatu"),
    (40, 52, "moco"),
    (15, 58, "calango"),
    (42, 64, "tatu"),
    (62, 64, "boss"),  # Sapo Boss guardando a saída no Térreo!
]

# Legenda do Mapa:
# X = Parede/Chão | L = Escada | D = Porta | R = Teto caindo (Escombro)
# M = Moeda       | S = Espinho| H = Cura  | P = Jogador | E = Saída/Reservatório
DADOS_MAPA = [
    # Topo / Terraço
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X           M                          H                            M          X",
    "X                         XXXXXXXXX                    XXXXXXXXX               X",
    "X                                                                              X",
    "X  P M             H     SSSS      M            M               M              X",
    "XXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXX",
    # 10º Andar
    "X      R         LLL    X         R         LLL                XLLL     R      X",
    "X      XXXXX     LLL    X          XXXXX    LLL                XLLL      XXXXX X",
    "X                LLL    X                   LLL                XLLL            X",
    "X              XXXXX    D      H            LLL  XXXXX         DLLL H    XXXXX X",
    "X                       D   XXXXXXXX        LLL                DLLL XXXXX      X",
    "XXXXXLLLXXXXXXXXXXXXXXXXX                   XXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXX",
    # 9º Andar
    "X    LLL     R          X            R                         XLLL      R     X",
    "X    LLL   H            X              M                       XLLL   M        X",
    "X    LLLXXXXXXX         X          XXXXXXX                     XLLL   XXXXXXX  X",
    "X    LLL                D                                      DLLL            X",
    "X  XXXXX                D      XXXXX           SSSS            DLLL  XXXXX     X",
    "XXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXX",
    # 8º Andar
    "X         R      LLL    X         R      LLL                   X   LLL   R     X",
    "X              M LLL    X              H LLL                   X   LLL   M     X",
    "X          XXXXX LLL    X          XXXXX LLL                   X   LLL XXXXX   X",
    "X                LLL    D                LLL                   D   LLL         X",
    "X    XXXXX      SSSS    D      XXXXX     LLL                   D   LLL XXXXX   X",
    "XXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXX",
    # 7º Andar
    "X    LLL      R         X        LLL       R                   XLLL      R     X",
    "X    LLL  M             X        LLL   M                       XLLL   M        X",
    "X    LLLXXXX            X        LLLXXXX                       XLLL   XXXXXX   X",
    "X    LLL                D        LLL                           DLLL            X",
    "X    LLL        XXXXX   D        LLL   XXXXX                   DLLL     XXXXX  X",
    "XXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXX",
    # 6º Andar
    "X          R     LLL    X          R     LLL                   X   LLL    R    X",
    "X  XXXXX         LLL    X      XXXXX     LLL  H                X   LLL XXXXX   X",
    "X                LLL    X              M LLL XXXX              X   LLL   M     X",
    "X            XXXXXX     D          XXXXXXLLL                   D   LLL XXXXXX  X",
    "X                       D                LLL                   D   LLL         X",
    "XXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXX",
    # 5º Andar
    "X    LLL     R          X        LLL      R                    XLLL     R      X",
    "X    LLL   M            X        LLL   M                       XLLL   M        X",
    "X    LLL XXXXX          X        LLL XXXXX                     XLLL   XXXXX    X",
    "X    LLL                D        LLL                           DLLL            X",
    "X  XXXX        SSSSS    D      XXXX                            DLLL  XXXX      X",
    "XXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXX",
    # 4º Andar
    "X         R      LLL    X         R      LLL                   X   LLL    R    X",
    "X              M LLL    X              M LLL                   X   LLL   M     X",
    "X            XXXXX      X          XXXXX LLL                   X   LLL XXXXX   X",
    "X                       D                LLL                   D   LLL         X",
    "X    XXXXX              D      XXXXX     LLL                   D   LLL XXXXX   X",
    "XXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXX",
    # 3º Andar
    "X    LLL      R         X        LLL       R                   XLLL      R     X",
    "X    LLL   M            X        LLL   M                       XLLL   M        X",
    "X    LLLXXXX            X        LLLXXXX                       XLLL   XXXXXX   X",
    "X    LLL                D        LLL                           DLLL            X",
    "X    LLL        XXXXX   D        LLL   XXXXX                   DLLL     XXXXX  X",
    "XXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXX",
    # 2º Andar
    "X          R     LLL    X          R     LLL                   X   LLL    R    X",
    "X  XXXXX         LLL    X      XXXXX     LLL                   X   LLL XXXXX   X",
    "X                LLL    X              M LLL                   X   LLL   M     X",
    "X            XXXXX      D          XXXXX LLL                   D   LLL XXXXX   X",
    "X                       D                LLL                   D   LLL         X",
    "XXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXXXXXXXXXLLLXXXXXXXXXXXXXXXXX",
    # Térreo / Recepção do Prédio e Reservatório (Arena do Boss)
    "X    LLL     R          X        LLL      R                    X   R     R     X",
    "X    LLL   M            X        LLL   M                       X       M       X",
    "X    LLLXXXX  SSSS      X        LLLXXXX     H                 X     XXXXXX    X",
    "X    LLL                D        LLL        XXXX               D               X",
    "X    LLL                D        LLL                           D           E   X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]


# ====================================================================
# CLASSE PORTA DE SEGURANÇA BLINDADA (ESTILO POST-APOCALÍPTICO)
# ====================================================================

# ====================================================================
# CONFIGURAÇÃO DOS SPRITES DA PORTA:
# Por padrão lógico de jogo:
# False: Esquerda = Fechada (visão frontal cobrindo o vão) | Direita = Aberta (perfil aberto para passagem)
# True: Direita = Fechada | Esquerda = Aberta (inverte caso desejado)
# ====================================================================
PORTA_FECHADA_EH_DIREITA = True


class Porta:
    """
    Porta de segurança estilizada com os sprites oficiais fornecidos pelo usuário.
    Suporta os dois estados (aberta e fechada) cobrindo o vão de passagem de 2 andares (64px).
    """
    def __init__(self, x, y, tile_size, pos_vertical="sozinho", grupo_id=""):
        self.rect = pygame.Rect(x, y, tile_size, tile_size)
        self.tile_size = tile_size
        self.aberta = False
        self.pos_vertical = pos_vertical  # 'topo', 'base', 'sozinho'
        self.grupo_id = grupo_id

    def interagir(self, jogador_rect):
        """Alterna estado da porta se o jogador estiver próximo."""
        area_ativacao = self.rect.inflate(36, 16)
        if area_ativacao.colliderect(jogador_rect):
            # Não fecha se o jogador estiver exatamente dentro do vão
            if self.aberta and self.rect.colliderect(jogador_rect):
                return False
            self.aberta = not self.aberta
            return True
        return False

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela, sprite_fechada=None, sprite_aberta=None):
        px = self.rect.x - camera_x
        py = self.rect.y - camera_y

        if -self.tile_size * 2 < px < largura_tela + self.tile_size and -self.tile_size * 2 < py < altura_tela + self.tile_size:
            sprite_atual = sprite_aberta if self.aberta else sprite_fechada

            # 1. Renderização com a imagem oficial fornecida (sem nenhum fundo preto desenhado)
            if sprite_atual is not None:
                if self.pos_vertical in ("topo", "sozinho"):
                    sw = sprite_atual.get_width()
                    offset_x = (sw - self.tile_size) // 2
                    tela.blit(sprite_atual, (px - offset_x, py))
                # O tile 'base' já está coberto pela imagem de 64px
                return

            # 2. Renderização procedural de fallback
            cor_moldura = (30, 36, 38)
            pygame.draw.rect(tela, cor_moldura, (px, py, 4, self.tile_size))
            pygame.draw.rect(tela, cor_moldura, (px + self.tile_size - 4, py, 4, self.tile_size))

            if not self.aberta:
                pygame.draw.rect(tela, (46, 54, 56), (px + 4, py, self.tile_size - 8, self.tile_size))
                if self.pos_vertical in ('topo', 'sozinho'):
                    pygame.draw.circle(tela, (255, 45, 45), (px + self.tile_size // 2, py + self.tile_size // 2), 3)
            else:
                pygame.draw.rect(tela, (16, 22, 20), (px + 4, py, self.tile_size - 8, self.tile_size))
                if self.pos_vertical in ('topo', 'sozinho'):
                    pygame.draw.circle(tela, (57, 255, 20), (px + self.tile_size // 2, py + 6), 3)
                    pygame.draw.circle(tela, (220, 255, 200), (cx, cy), 1)

    def desenhar_prompt_interacao(self, tela, camera_x, camera_y):
        """Desenha indicador '[E] ABRIR' ou '[E] FECHAR' flutuante quando o jogador está perto."""
        px = self.rect.centerx - camera_x
        py = self.rect.y - camera_y - 18

        texto = "[E] FECHAR" if self.aberta else "[E] ABRIR"
        cor_borda = (255, 200, 50) if self.aberta else (57, 255, 20)

        try:
            fonte = pygame.font.SysFont("consolas", 11, bold=True)
            txt_surf = fonte.render(texto, True, cor_borda)
            rect_txt = txt_surf.get_rect(center=(px, py))

            # Fundo translúcido
            bg_rect = rect_txt.inflate(10, 4)
            surf_bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            surf_bg.fill((8, 16, 10, 210))
            tela.blit(surf_bg, (bg_rect.x, bg_rect.y))
            pygame.draw.rect(tela, cor_borda, bg_rect, 1, border_radius=3)
            tela.blit(txt_surf, rect_txt)
        except Exception:
            pass


# ====================================================================
# CLASSE ARMADILHA DO TETO (ESCOMBRO / CONCRETO COM VERGALHÕES)
# ====================================================================

class PedacoTeto:
    """
    Bloco de laje de concreto armado deteriorado que se desprende do teto.
    Quando o jogador se aproxima por baixo:
    - Entra em tremor ('tremendo') e solta particulas de poeira radioativa como aviso previo;
    - Despenca em alta velocidade ('caindo'), renderizando o projetil rochoso (trap3);
    - Ao colidir com o jogador ou chao, explode em estilhacos de concreto e poeira ('quebrado');
    - Regenera apos alguns segundos para manter o perigo no mapa.
    """
    def __init__(self, x, y, tile_size, sprite=None, bloco_teto=None):
        self.x_inicial = x
        self.y_inicial = y
        self.tile_size = tile_size
        self.largura = tile_size - 6
        self.altura = tile_size - 6
        self.rect = pygame.Rect(x + 3, y, self.largura, self.altura)
        self.bloco_teto = bloco_teto
        self.sprite = sprite

        self.estado = "preso"  # "preso", "tremendo", "caindo", "quebrado"
        self.vel_y = 0.0
        self.timer = 0
        self.dano = 25
        self.ja_causou_dano = False

        # Sistema de particulas dinamicas
        self.particulas_poeira = []     # Particulas de poeira caindo durante o tremor
        self.particulas_estilhaco = []   # Pedacos de rocha voando apos bater no chao

    def _gerar_estilhacos(self, centro_x, centro_y, qtd=10):
        """Gera pedrinhas de concreto que se espalham com fisica e gravidade."""
        for _ in range(qtd):
            self.particulas_estilhaco.append({
                "x": float(centro_x + random.randint(-8, 8)),
                "y": float(centro_y + random.randint(-4, 4)),
                "vel_x": random.uniform(-4.5, 4.5),
                "vel_y": random.uniform(-6.0, -1.5),
                "raio": random.randint(2, 4),
                "vida": random.randint(25, 45),
                "cor": random.choice([
                    (85, 90, 88), (115, 120, 116), (150, 85, 40), (57, 255, 20)
                ])
            })

    def atualizar(self, blocos, jogador_rect=None, saude=None, combate=None, god_mode=False):
        """
        Atualiza a fisica da armadilha do teto e particulas.
        Retorna True caso tenha causado dano ao jogador neste frame.
        """
        acertou_jogador = False

        # 1. Atualizar particulas de poeira (aviso previo)
        for p in self.particulas_poeira[:]:
            p["y"] += p["vel_y"]
            p["x"] += p["vel_x"]
            p["vida"] -= 1
            if p["vida"] <= 0:
                self.particulas_poeira.remove(p)

        # 2. Atualizar estilhacos de impacto no chao
        for p in self.particulas_estilhaco[:]:
            p["x"] += p["vel_x"]
            p["y"] += p["vel_y"]
            p["vel_y"] += 0.45  # Gravidade do estilhaco
            p["vida"] -= 1
            if p["vida"] <= 0:
                self.particulas_estilhaco.remove(p)

        # 3. Maquina de Estados da Armadilha
        if self.estado == "preso":
            if jogador_rect is not None:
                dist_x = abs(jogador_rect.centerx - self.rect.centerx)
                dist_y = jogador_rect.top - self.rect.bottom
                # Detecta jogador passando embaixo (largura de 48px e ate 280px abaixo)
                if dist_x < 48 and 0 <= dist_y <= 280:
                    self.estado = "tremendo"
                    self.timer = 24  # ~0.4s de tremor para dar tempo de esquiva/reacao

        elif self.estado == "tremendo":
            self.timer -= 1
            # Gera poeira e pedriscos caindo do teto como aviso telegrafado
            if random.random() < 0.6:
                self.particulas_poeira.append({
                    "x": float(self.rect.x + random.randint(4, self.rect.width - 4)),
                    "y": float(self.rect.bottom),
                    "vel_x": random.uniform(-0.4, 0.4),
                    "vel_y": random.uniform(2.0, 4.0),
                    "raio": random.randint(2, 3),
                    "vida": 30,
                    "cor": random.choice([(140, 135, 120), (95, 90, 80), (57, 255, 20)])
                })

            if self.timer <= 0:
                self.estado = "caindo"
                self.vel_y = 3.0
                self.ja_causou_dano = False

        elif self.estado == "caindo":
            # Aceleracao gravitacional pesada do bloco de concreto
            self.vel_y = min(15.0, self.vel_y + 0.75)
            self.rect.y += int(self.vel_y)

            # Colisao contra o Jogador
            if (
                jogador_rect is not None
                and not self.ja_causou_dano
                and self.rect.colliderect(jogador_rect)
            ):
                self.ja_causou_dano = True
                acertou_jogador = True

                # Calculo de dano com mitigacao por escudo ou god mode
                if not god_mode and saude is not None:
                    dano_final = self.dano
                    if combate is not None and combate.defendendo:
                        dano_final = combate.calcular_dano_recebido(self.dano)
                    saude.tomar_dano(dano_final)

                self._gerar_estilhacos(self.rect.centerx, self.rect.bottom, qtd=8)

            # Colisao contra o Chao ou Plataforma de Concreto (ignora o proprio teto)
            for bloco in blocos:
                if self.bloco_teto is not None and bloco == self.bloco_teto:
                    continue
                if self.rect.colliderect(bloco):
                    self.rect.bottom = bloco.top
                    self.estado = "quebrado"
                    self.timer = 190  # Reaparece no teto apos ~3.2 segundos
                    self._gerar_estilhacos(self.rect.centerx, self.rect.bottom, qtd=14)
                    break

        elif self.estado == "quebrado":
            # Permanece quebrado definitivamente: o bloco no teto mantem a aparencia de buraco (trap2)
            if self.timer > 0:
                self.timer -= 1

        return acertou_jogador

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        # 1. Desenha particulas de poeira (aviso de perigo durante tremor)
        for p in self.particulas_poeira:
            px = int(p["x"] - camera_x)
            py = int(p["y"] - camera_y)
            if -10 < px < largura_tela + 10 and -10 < py < altura_tela + 10:
                pygame.draw.circle(tela, p["cor"], (px, py), p["raio"])

        # 2. Desenha estilhacos voando no impacto com o chao / jogador
        for p in self.particulas_estilhaco:
            px = int(p["x"] - camera_x)
            py = int(p["y"] - camera_y)
            if -10 < px < largura_tela + 10 and -10 < py < altura_tela + 10:
                pygame.draw.rect(tela, p["cor"], (px, py, p["raio"], p["raio"]))

        # 3. Desenha o objeto que causa dano (trap3) SOMENTE quando estiver caindo
        if self.estado != "caindo":
            return

        rx = self.rect.centerx - self.tile_size // 2 - camera_x
        ry = self.rect.centery - self.tile_size // 2 - camera_y

        if -40 < rx < largura_tela + 40 and -40 < ry < altura_tela + 40:
            if self.sprite is not None:
                tela.blit(self.sprite, (rx, ry))
            else:
                w = self.largura
                h = self.altura
                pontos_concreto = [
                    (rx + 2, ry),
                    (rx + w - 2, ry),
                    (rx + w, ry + h - 10),
                    (rx + w - 4, ry + h - 3),
                    (rx + w // 2, ry + h),
                    (rx + 4, ry + h - 5),
                    (rx, ry + h - 12),
                ]
                cor_concreto = (78, 85, 83) if self.estado != "tremendo" else (110, 100, 85)
                cor_borda = (38, 44, 42)
                pygame.draw.polygon(tela, cor_concreto, pontos_concreto)
                pygame.draw.polygon(tela, cor_borda, pontos_concreto, 2)


# ====================================================================
# CLASSE MAPA PRINCIPAL COM ESCADAS, PORTAS E ARMADILHAS INTEGRADAS
# ====================================================================

class Mapa:
    def __init__(self):
        self.tile_size = TILE_SIZE
        pasta_projeto = Path(__file__).resolve().parents[2]
        pasta_cenario = pasta_projeto / "cenario"
        caminho_textura = pasta_cenario / "chao.png"
        if caminho_textura.is_file():
            try:
                self.textura_chao = pygame.image.load(str(caminho_textura)).convert()
            except Exception:
                self.textura_chao = pygame.Surface((self.tile_size, self.tile_size))
                self.textura_chao.fill((50, 45, 40))
        else:
            self.textura_chao = pygame.Surface((self.tile_size, self.tile_size))
            self.textura_chao.fill((50, 45, 40))

        # Carregamento das texturas aleatorias para blocos normais (bloco 1 ao 5)
        self.texturas_blocos = []
        for i in range(1, 6):
            caminho_bloco = pasta_cenario / f"bloco_{i}.png"
            if caminho_bloco.is_file():
                try:
                    img_bloco = pygame.image.load(str(caminho_bloco)).convert()
                    self.texturas_blocos.append(pygame.transform.scale(img_bloco, (self.tile_size, self.tile_size)))
                except Exception as e:
                    print(f"Aviso ao carregar bloco_{i}.png: {e}")

        if not self.texturas_blocos:
            self.texturas_blocos.append(self.textura_chao)

        # Texturas dinamicas para armadilhas do teto (trap1, trap2, trap3)
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

        if self.textura_trap1 is None:
            self.textura_trap1 = self.texturas_blocos[0]
        if self.textura_trap2 is None:
            self.textura_trap2 = self.texturas_blocos[0]

        caminho_textura_cura = pasta_cenario / "cura.png"
        self.textura_cura = None
        if caminho_textura_cura.is_file():
            self.textura_cura = pygame.image.load(
                str(caminho_textura_cura)
            ).convert_alpha()
            self.textura_cura = pygame.transform.scale(
                self.textura_cura, (self.tile_size, self.tile_size)
            )
        self.largura = len(DADOS_MAPA[0]) * self.tile_size
        self.altura = len(DADOS_MAPA) * self.tile_size

        self.blocos = []
        self.escadas = []
        self.portas = []
        self.pedacos_teto = []
        self.espinhos = []
        self.moedas = []
        self.kits_medicos = []
        self.blocos_armadilhas = {}
        self.bloco_texturas = {}
        self.pos_inicial_jogador = (64, 128)
        self.zona_saida = pygame.Rect(2200, 2380, 110, 64)

        # Sprites oficiais das portas
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

                c0 = surf_full.get_at((0, 0))
                if len(c0) == 3 or (len(c0) == 4 and c0[3] == 255):
                    if c0[0] > 235 and c0[1] > 235 and c0[2] > 235:
                        surf_full.set_colorkey((c0[0], c0[1], c0[2]))

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
                print(f"Aviso ao carregar porta.png da raiz: {e}")

        if PORTA_FECHADA_EH_DIREITA:
            self.sprite_porta_fechada = self.sprite_porta_direita
            self.sprite_porta_aberta = self.sprite_porta_esquerda
        else:
            self.sprite_porta_fechada = self.sprite_porta_esquerda
            self.sprite_porta_aberta = self.sprite_porta_direita

        self._processar_dados()
        self.sprite_saida = None
        if self.sprite_porta_esquerda is not None:
            altura_saida = max(1, self.zona_saida.height)
            largura_saida = max(
                1,
                round(
                    altura_saida
                    * self.sprite_porta_esquerda.get_width()
                    / self.sprite_porta_esquerda.get_height()
                ),
            )
            self.sprite_saida = pygame.transform.scale(
                self.sprite_porta_esquerda, (largura_saida, altura_saida)
            )

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
        self.moedas.clear()
        self.kits_medicos.clear()
        self.blocos_armadilhas.clear()
        self.bloco_texturas.clear()

        # Primeiro passo: mapear elementos
        posicoes_portas = []
        posicoes_armadilhas = []

        for linha_idx, linha in enumerate(DADOS_MAPA):
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
                elif caractere == "M":
                    pass  # Moedas descontinuadas e removidas do jogo
                elif caractere == "S":
                    self.espinhos.append(pygame.Rect(pos_x, pos_y + 16, self.tile_size, 16))
                elif caractere == "H":
                    self.kits_medicos.append(pygame.Rect(pos_x + 6, pos_y + 6, 20, 20))
                elif caractere == "E":
                    self.zona_saida = pygame.Rect(pos_x, pos_y - self.tile_size, self.tile_size * 3, self.tile_size * 2)

        # Segundo passo: agrupar portas verticais adjacentes para operarem juntas
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
                grupo_id = f"porta_col_{c}_g{g_idx}_{grupo[0][0]}"
                for i, (l, px, py) in enumerate(grupo):
                    if len(grupo) > 1:
                        pos_vert = "topo" if i == 0 else "base"
                    else:
                        pos_vert = "sozinho"
                    self.portas.append(Porta(px, py, self.tile_size, pos_vertical=pos_vert, grupo_id=grupo_id))

        # Terceiro passo: configurar armadilhas de teto e associar aos blocos de laje
        for pos_x, pos_y in posicoes_armadilhas:
            pos_teto_y = pos_y - self.tile_size
            rect_teto = pygame.Rect(pos_x, pos_teto_y, self.tile_size, self.tile_size)
            if rect_teto not in self.blocos:
                self.blocos.append(rect_teto)

            pedaco = PedacoTeto(pos_x, pos_y, self.tile_size, sprite=self.sprite_trap3, bloco_teto=rect_teto)
            self.pedacos_teto.append(pedaco)
            self.blocos_armadilhas[(pos_x, pos_teto_y)] = pedaco

        # Quarto passo: atribuicao de texturas aleatorias dos blocos 1 ao 5
        # Garantindo regra estrita: sem repetir a mesma imagem mais que 3 vezes seguidas
        blocos_ordenados = sorted(self.blocos, key=lambda b: (b.y, b.x))
        bloco_anterior = None
        ultimo_idx = -1
        cont_consecutivo = 0

        for bloco in blocos_ordenados:
            chave = (bloco.x, bloco.y)
            if chave in self.blocos_armadilhas:
                continue

            opcoes = list(range(len(self.texturas_blocos)))

            # Checagem horizontal consecutiva
            eh_adjacente = (
                bloco_anterior is not None
                and bloco.y == bloco_anterior.y
                and bloco.x == bloco_anterior.x + self.tile_size
            )
            if eh_adjacente and cont_consecutivo >= 3 and ultimo_idx in opcoes and len(opcoes) > 1:
                opcoes.remove(ultimo_idx)

            # Checagem vertical consecutiva
            t1 = self.bloco_texturas.get((bloco.x, bloco.y - self.tile_size))
            t2 = self.bloco_texturas.get((bloco.x, bloco.y - 2 * self.tile_size))
            t3 = self.bloco_texturas.get((bloco.x, bloco.y - 3 * self.tile_size))
            if t1 is not None and t1 == t2 == t3:
                for idx_tex, tex in enumerate(self.texturas_blocos):
                    if tex is t1 and idx_tex in opcoes and len(opcoes) > 1:
                        opcoes.remove(idx_tex)
                        break

            idx_escolhido = random.choice(opcoes)
            tex_escolhida = self.texturas_blocos[idx_escolhido]
            self.bloco_texturas[chave] = tex_escolhida

            if eh_adjacente and idx_escolhido == ultimo_idx:
                cont_consecutivo += 1
            else:
                ultimo_idx = idx_escolhido
                cont_consecutivo = 1

            bloco_anterior = bloco

        self.inimigos_iniciais = [
            (coluna * self.tile_size, linha * self.tile_size)
            for coluna, linha in INIMIGOS_INICIAIS
        ]
        self.dados_inimigos_iniciais = [
            (coluna * self.tile_size, linha * self.tile_size, tipo)
            for coluna, linha, tipo in INIMIGOS_DETALHADOS
        ]

    def obter_blocos_colisao(self):
        """Retorna todas as paredes sólidas + todas as portas que estão FECHADAS no momento."""
        return self.blocos + [p.rect for p in self.portas if not p.aberta]

    @property
    def colisoes_com_portas(self):
        """Propriedade para compatibilidade total com colisões de portas fechadas."""
        return self.obter_blocos_colisao()

    def esta_na_escada(self, rect_jogador):
        """Retorna True se o retângulo do jogador estiver tocando em qualquer degrau de escada."""
        for esc in self.escadas:
            if rect_jogador.colliderect(esc):
                return True
        return False

    def interagir_portas(self, jogador_rect):
        """
        Abre ou fecha o vão de porta mais próximo do jogador.
        Abre/fecha os tiles superior e inferior juntos em sincronia.
        """
        portas_proximas = [
            p for p in self.portas if p.rect.inflate(44, 20).colliderect(jogador_rect)
        ]
        if not portas_proximas:
            return False

        # Identifica grupos próximos
        grupos_afetados = {p.grupo_id for p in portas_proximas}

        for gid in grupos_afetados:
            membros_grupo = [p for p in self.portas if p.grupo_id == gid]
            qualquer_fechada = any(not p.aberta for p in membros_grupo)
            novo_estado = qualquer_fechada  # Se alguma estiver fechada, abre; se todas abertas, fecha

            # Proteção: não fechar se o jogador estiver pisando exatamente no vão da porta
            if not novo_estado:
                if any(p.rect.colliderect(jogador_rect) for p in membros_grupo):
                    return False

            for p in membros_grupo:
                p.aberta = novo_estado

        return True

    def atualizar_armadilhas(self, jogador_rect=None, saude=None, combate=None, god_mode=False):
        """
        Atualiza física, partículas e detecção de todas as armadilhas de teto.
        Aplica dano com redução de escudo ou god mode se acertar o jogador.
        """
        blocos_colisao = self.obter_blocos_colisao()
        acertou_algum = False
        for pedaco in self.pedacos_teto:
            if pedaco.atualizar(blocos_colisao, jogador_rect, saude, combate, god_mode):
                acertou_algum = True
        return acertou_algum

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela, jogador_rect=None):
        # 1. Blocos de Parede/Chão e Armadilhas Dinamicas de Teto
        for bloco in self.blocos:
            bx = bloco.x - camera_x
            by = bloco.y - camera_y
            if -self.tile_size < bx < largura_tela and -self.tile_size < by < altura_tela:
                chave = (bloco.x, bloco.y)
                if chave in self.blocos_armadilhas:
                    pedaco = self.blocos_armadilhas[chave]
                    if pedaco.estado in ("preso", "tremendo"):
                        tremor_x = random.choice([-2, -1, 1, 2]) if pedaco.estado == "tremendo" else 0
                        tela.blit(self.textura_trap1, (bx + tremor_x, by))
                    else:  # "caindo" ou "quebrado" (apenas o buraco na laje)
                        tela.blit(self.textura_trap2, (bx, by))
                else:
                    tela.blit(self.textura_mapa, (bx, by), area=bloco)

        # 2. Escadas de Incêndio / Aço Industrial ('L')
        cor_trilho = (48, 56, 58)
        cor_trilho_borda = (78, 92, 96)
        cor_degrau = (58, 66, 68)
        cor_aviso = (185, 145, 30)

        for esc in self.escadas:
            lx = esc.x - camera_x
            ly = esc.y - camera_y
            if -self.tile_size < lx < largura_tela and -self.tile_size < ly < altura_tela:
                # Longarinas verticais de aço reforçado
                pygame.draw.rect(tela, cor_trilho, (lx + 4, ly, 4, self.tile_size))
                pygame.draw.rect(tela, cor_trilho_borda, (lx + 4, ly, 4, self.tile_size), 1)
                pygame.draw.rect(tela, cor_trilho, (lx + self.tile_size - 8, ly, 4, self.tile_size))
                pygame.draw.rect(tela, cor_trilho_borda, (lx + self.tile_size - 8, ly, 4, self.tile_size), 1)

                # Degraus com ranhuras antiderrapantes e listras de aviso
                for degrau_y in (ly + 6, ly + 16, ly + 26):
                    largura_degrau = self.tile_size - 14
                    x_degrau = lx + 7
                    pygame.draw.rect(tela, cor_degrau, (x_degrau, degrau_y, largura_degrau, 4))
                    pygame.draw.rect(tela, (20, 25, 26), (x_degrau, degrau_y, largura_degrau, 4), 1)
                    # Listra de segurança no centro
                    pygame.draw.rect(tela, cor_aviso, (x_degrau + largura_degrau // 2 - 3, degrau_y + 1, 6, 2))

        # 3. Portas Blindadas ('D') com Sprites Oficiais
        porta_para_prompt = None
        for porta in self.portas:
            porta.desenhar(
                tela, camera_x, camera_y, largura_tela, altura_tela,
                self.sprite_porta_fechada, self.sprite_porta_aberta
            )
            if jogador_rect is not None and porta.rect.inflate(44, 20).colliderect(jogador_rect):
                if porta.pos_vertical in ("topo", "sozinho"):
                    porta_para_prompt = porta

        # Exibir prompt [E] ABRIR / [E] FECHAR se o jogador estiver ao lado da porta
        if porta_para_prompt is not None:
            porta_para_prompt.desenhar_prompt_interacao(tela, camera_x, camera_y)

        # 4. Pedaços do Teto Caindo / Armadilha ('R')
        for pedaco in self.pedacos_teto:
            pedaco.desenhar(tela, camera_x, camera_y, largura_tela, altura_tela)

        # 5. Espinhos ('S')
        for esp in self.espinhos:
            ex = esp.x - camera_x
            ey = esp.y - camera_y
            if -self.tile_size < ex < largura_tela and -self.tile_size < ey < altura_tela:
                pontos = [(ex, ey + 16), (ex + 16, ey), (ex + 32, ey + 16)]
                pygame.draw.polygon(tela, (180, 50, 50), pontos)
                pygame.draw.polygon(tela, (230, 90, 90), pontos, 2)

        # 6. Kits Médicos ('H')
        for kit in self.kits_medicos:
            x_centro = kit.centerx - camera_x
            y_centro = kit.centery - camera_y
            if (
                -self.tile_size < x_centro < largura_tela + self.tile_size
                and -self.tile_size < y_centro < altura_tela + self.tile_size
            ):
                visual_cura = pygame.Rect(0, 0, self.tile_size, self.tile_size)
                visual_cura.center = (x_centro, y_centro)
                if self.textura_cura is not None:
                    tela.blit(self.textura_cura, visual_cura)
                else:
                    pygame.draw.rect(tela, (240, 240, 240), visual_cura, border_radius=4)
                    pygame.draw.rect(
                        tela, (46, 204, 113),
                        (visual_cura.x + 13, visual_cura.y + 5, 6, 22)
                    )
                    pygame.draw.rect(
                        tela, (46, 204, 113),
                        (visual_cura.x + 5, visual_cura.y + 13, 22, 6)
                    )

        # 7. Zona de Fuga / Reservatório de Água ('E')
        if self.zona_saida:
            zx = self.zona_saida.x - camera_x
            zy = self.zona_saida.y - camera_y
            if -120 < zx < largura_tela + 120 and -120 < zy < altura_tela + 120:
                centro_x = zx + self.zona_saida.width // 2
                if self.sprite_saida is not None:
                    porta_rect = self.sprite_saida.get_rect(
                        midbottom=(
                            centro_x,
                            zy + self.zona_saida.height,
                        )
                    )
                    tela.blit(self.sprite_saida, porta_rect)
                else:
                    porta_rect = pygame.Rect(
                        zx + self.zona_saida.width // 4,
                        zy,
                        self.zona_saida.width // 2,
                        self.zona_saida.height,
                    )
                    pygame.draw.rect(tela, (75, 58, 45), porta_rect)
                    pygame.draw.rect(
                        tela, (25, 34, 31), porta_rect.inflate(-10, -8)
                    )
                    pygame.draw.line(
                        tela,
                        (100, 82, 57),
                        (centro_x, porta_rect.top + 6),
                        (centro_x, porta_rect.bottom - 6),
                        3,
                    )

                try:
                    fonte_tag = pygame.font.SysFont("consolas", 13, bold=True)
                    tag_texto = fonte_tag.render("SAIDA / RESERVATORIO", True, (57, 255, 20))
                    tag_rect = tag_texto.get_rect(center=(centro_x, zy - 15))
                    tela.blit(tag_texto, tag_rect)
                except Exception:
                    pass
