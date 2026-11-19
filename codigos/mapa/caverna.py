import random
from pathlib import Path

import pygame

from codigos.mapa.mapa_prototipo import DADOS_MAPA, INIMIGOS_INICIAIS, TILE_SIZE


DADOS_CAVERNA = DADOS_MAPA
COR_FUNDO = (10, 14, 24)


class Mapa:
    def __init__(self):
        self.tile_size = TILE_SIZE
        largura_grade = len(DADOS_CAVERNA[0])
        if any(len(linha) != largura_grade for linha in DADOS_CAVERNA):
            raise ValueError("Todas as linhas da caverna devem ter a mesma largura.")

        self.largura = largura_grade * self.tile_size
        self.altura = len(DADOS_CAVERNA) * self.tile_size
        self.blocos = []
        self.espinhos = []
        self.moedas = []
        self.kits_medicos = []
        self.pos_inicial_jogador = (64, 128)
        self._processar_dados()

        self.textura_fundo = self._criar_textura_fundo()
        self.textura_mapa = pygame.Surface((self.largura, self.altura))
        self.textura_mapa.fill(COR_FUNDO)
        self._desenhar_rochas()
        self.textura_cura = self._carregar_textura_cura()

    def _processar_dados(self):
        for linha_idx, linha in enumerate(DADOS_CAVERNA):
            for coluna_idx, caractere in enumerate(linha):
                pos_x = coluna_idx * self.tile_size
                pos_y = linha_idx * self.tile_size

                if caractere == "X":
                    self.blocos.append(
                        pygame.Rect(pos_x, pos_y, self.tile_size, self.tile_size)
                    )
                elif caractere == "P":
                    self.pos_inicial_jogador = (pos_x, pos_y)
                elif caractere == "M":
                    pass  # Moedas removidas
                elif caractere == "S":
                    self.espinhos.append(
                        pygame.Rect(pos_x, pos_y + 16, self.tile_size, 16)
                    )
                elif caractere == "H":
                    self.kits_medicos.append(
                        pygame.Rect(pos_x + 6, pos_y + 6, 20, 20)
                    )

        self.inimigos_iniciais = [
            (coluna * self.tile_size, linha * self.tile_size)
            for coluna, linha in INIMIGOS_INICIAIS
        ]

    def _criar_textura_fundo(self):
        textura = pygame.Surface((self.largura, self.altura))
        textura.fill(COR_FUNDO)
        gerador = random.Random(19)

        for x in range(0, self.largura, self.tile_size * 4):
            largura = min(self.tile_size * 4, self.largura - x)
            altura_teto = gerador.randint(18, 54)
            altura_piso = gerador.randint(14, 42)
            pygame.draw.polygon(
                textura,
                (15, 20, 32),
                [
                    (x, 0),
                    (x + largura, 0),
                    (x + largura, altura_teto),
                    (x + largura // 2, altura_teto // 2),
                    (x, altura_teto + 12),
                ],
            )
            pygame.draw.polygon(
                textura,
                (14, 19, 30),
                [
                    (x, self.altura),
                    (x + largura, self.altura),
                    (x + largura, self.altura - altura_piso),
                    (x + largura // 2, self.altura - altura_piso // 2),
                    (x, self.altura - altura_piso - 10),
                ],
            )

        for _ in range(220):
            x = gerador.randrange(self.largura)
            y = gerador.randrange(self.altura)
            raio = gerador.randint(1, 2)
            cor = gerador.choice(
                [(30, 43, 61), (32, 47, 64), (43, 39, 67)]
            )
            pygame.draw.circle(textura, cor, (x, y), raio)

        return textura

    def _desenhar_rochas(self):
        gerador = random.Random(37)
        cores_rocha = [
            (39, 48, 62),
            (45, 50, 67),
            (42, 55, 66),
            (50, 48, 65),
        ]

        for bloco in self.blocos:
            x = bloco.x
            y = bloco.y
            base = gerador.choice(cores_rocha)
            realce = tuple(min(255, canal + 18) for canal in base)
            sombra = tuple(max(0, canal - 17) for canal in base)
            pygame.draw.rect(self.textura_mapa, base, bloco)
            pygame.draw.polygon(
                self.textura_mapa,
                realce,
                [
                    (x, y + 6),
                    (x + 6, y + 1),
                    (x + 22, y + 3),
                    (x + 31, y + 8),
                    (x + 25, y + 17),
                    (x + 8, y + 15),
                ],
            )
            pygame.draw.polygon(
                self.textura_mapa,
                sombra,
                [
                    (x + 8, y + 15),
                    (x + 25, y + 17),
                    (x + 31, y + 8),
                    (x + 31, y + 31),
                    (x + 4, y + 31),
                ],
            )
            pygame.draw.line(
                self.textura_mapa,
                (24, 31, 44),
                (x + gerador.randint(5, 15), y + 18),
                (x + gerador.randint(16, 27), y + 25),
                1,
            )

    def _carregar_textura_cura(self):
        pasta_projeto = Path(__file__).resolve().parents[2]
        caminho_textura = pasta_projeto / "cenario" / "cura.png"
        if not caminho_textura.is_file():
            return None

        textura = pygame.image.load(str(caminho_textura)).convert_alpha()
        return pygame.transform.scale(
            textura, (self.tile_size, self.tile_size)
        )

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        tela.fill(COR_FUNDO)
        area_fundo = pygame.Rect(
            camera_x,
            camera_y,
            min(largura_tela, self.largura - camera_x),
            min(altura_tela, self.altura - camera_y),
        )
        if area_fundo.width > 0 and area_fundo.height > 0:
            tela.blit(self.textura_fundo, (0, 0), area=area_fundo)

        for bloco in self.blocos:
            bx = bloco.x - camera_x
            by = bloco.y - camera_y
            if (
                -self.tile_size < bx < largura_tela
                and -self.tile_size < by < altura_tela
            ):
                tela.blit(self.textura_mapa, (bx, by), area=bloco)

        for espinho in self.espinhos:
            ex = espinho.x - camera_x
            ey = espinho.y - camera_y
            if (
                -self.tile_size < ex < largura_tela
                and -self.tile_size < ey < altura_tela
            ):
                base_y = ey + espinho.height
                for centro, meia_largura, altura in (
                    (ex + 8, 8, 11),
                    (ex + 24, 9, 15),
                ):
                    pontos = [
                        (centro - meia_largura, base_y),
                        (centro, base_y - altura),
                        (centro + meia_largura, base_y),
                    ]
                    pygame.draw.polygon(tela, (34, 83, 91), pontos)
                    pygame.draw.polygon(tela, (74, 164, 157), pontos, 2)

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
                    pygame.draw.rect(
                        tela, (194, 213, 208), visual_cura, border_radius=4
                    )
                    pygame.draw.rect(
                        tela,
                        (45, 142, 126),
                        (visual_cura.x + 13, visual_cura.y + 5, 6, 22),
                    )
                    pygame.draw.rect(
                        tela,
                        (45, 142, 126),
                        (visual_cura.x + 5, visual_cura.y + 13, 22, 6),
                    )