import pygame


class Inimigo:
    def __init__(self, x, y, largura=26, altura=30, vida=70, velocidade=2):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.vida = vida
        self.vida_maxima = vida
        self.velocidade = velocidade
        self.direcao = 1
        self.vel_y = 0
        self.vel_recuo_x = 0.0
        self.esta_vivo = True

        self.tempo_dano = 0
        self.tempo_atordoado = 0
        self.alcance_visao = 42
        self.atacando = False
        self.timer_preparacao = 0
        self.timer_ataque = 0
        self.cooldown_ataque = 0
        self.hitbox_ataque = None
        self.dano_ataque = 20

    def atualizar(self, blocos, jogador_rect=None, hitbox_escudo=None):
        if not self.esta_vivo:
            return

        if self.tempo_dano > 0:
            self.tempo_dano -= 1

        if self.tempo_atordoado > 0:
            self.tempo_atordoado -= 1

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= 1

        if abs(self.vel_recuo_x) > 0.1:
            self.vel_recuo_x *= 0.82
        else:
            self.vel_recuo_x = 0.0

        if self.timer_preparacao > 0:
            self.timer_preparacao -= 1
            if self.timer_preparacao <= 0:
                self.atacando = True
                self.timer_ataque = 12

        if self.atacando:
            self.timer_ataque -= 1
            largura_golpe = 26
            altura_golpe = 20
            if self.direcao == 1:
                hx = self.rect.right
            else:
                hx = self.rect.left - largura_golpe
            hy = self.rect.centery - (altura_golpe // 2)
            self.hitbox_ataque = pygame.Rect(
                hx, hy, largura_golpe, altura_golpe
            )

            if self.timer_ataque <= 0:
                self.atacando = False
                self.hitbox_ataque = None
                self.cooldown_ataque = 45
        else:
            self.hitbox_ataque = None

        if (
            jogador_rect is not None
            and self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and self.cooldown_ataque <= 0
        ):
            dist_y = abs(self.rect.centery - jogador_rect.centery)
            dist_x = jogador_rect.centerx - self.rect.centerx
            if dist_y < 32 and abs(dist_x) <= self.alcance_visao:
                self.direcao = 1 if dist_x >= 0 else -1
                self.timer_preparacao = 14

        movimento_patrulha = 0
        if (
            self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and abs(self.vel_recuo_x) < 1.0
        ):
            movimento_patrulha = self.direcao * self.velocidade

        deslocamento_x = int(movimento_patrulha + self.vel_recuo_x)
        self.rect.x += deslocamento_x

        for bloco in blocos:
            if self.rect.colliderect(bloco):
                if deslocamento_x > 0:
                    self.rect.right = bloco.left
                    self.vel_recuo_x = 0.0
                    if movimento_patrulha > 0:
                        self.direcao = -1
                elif deslocamento_x < 0:
                    self.rect.left = bloco.right
                    self.vel_recuo_x = 0.0
                    if movimento_patrulha < 0:
                        self.direcao = 1

        bateu_no_escudo = False
        if hitbox_escudo is not None:
            if self.rect.colliderect(hitbox_escudo):
                if self.direcao == 1:
                    self.rect.right = hitbox_escudo.left
                else:
                    self.rect.left = hitbox_escudo.right
                bateu_no_escudo = True
            elif (
                self.hitbox_ataque is not None
                and self.hitbox_ataque.colliderect(hitbox_escudo)
            ):
                self.atacando = False
                self.hitbox_ataque = None
                self.cooldown_ataque = 45
                bateu_no_escudo = True

        if bateu_no_escudo and self.tempo_atordoado <= 0:
            self.aplicar_pulinho_recuo(
                -self.direcao, forca_x=6.5, forca_y=-6.0
            )
            self.tempo_atordoado = 25

        self.vel_y += 0.75
        if self.vel_y > 15:
            self.vel_y = 15

        self.rect.y += int(self.vel_y)
        for bloco in blocos:
            if self.rect.colliderect(bloco):
                if self.vel_y > 0:
                    self.rect.bottom = bloco.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = bloco.bottom
                    self.vel_y = 0

    def aplicar_pulinho_recuo(self, direcao_empurrao, forca_x=6.5, forca_y=-6.0):
        self.vel_recuo_x = direcao_empurrao * forca_x
        self.vel_y = forca_y

    def tomar_dano(self, quantidade, direcao_golpe):
        if self.tempo_dano <= 0 and self.esta_vivo:
            self.vida -= quantidade
            self.tempo_dano = 15
            self.atacando = False
            self.timer_preparacao = 0
            self.hitbox_ataque = None
            self.aplicar_pulinho_recuo(
                direcao_golpe, forca_x=7.0, forca_y=-5.5
            )
            if self.vida <= 0:
                self.esta_vivo = False
            return True
        return False

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        if not self.esta_vivo:
            return

        ix = self.rect.x - camera_x
        iy = self.rect.y - camera_y
        if -40 < ix < largura_tela and -40 < iy < altura_tela:
            if self.tempo_dano > 7:
                cor = (255, 255, 255)
            elif self.timer_preparacao > 0:
                cor = (230, 126, 34)
            else:
                cor = (142, 68, 173)

            pygame.draw.rect(
                tela, cor, (ix, iy, self.rect.width, self.rect.height),
                border_radius=3,
            )

            olho_x = ix + 16 if self.direcao == 1 else ix + 4
            pygame.draw.rect(tela, (255, 255, 255), (olho_x, iy + 6, 6, 6))
            olho_pupila_x = olho_x + (2 if self.direcao == 1 else 0)
            pygame.draw.rect(
                tela, (0, 0, 0), (olho_pupila_x, iy + 8, 3, 3)
            )

            if self.hitbox_ataque is not None:
                hx = self.hitbox_ataque.x - camera_x
                hy = self.hitbox_ataque.y - camera_y
                surf_ataque = pygame.Surface(
                    (self.hitbox_ataque.width, self.hitbox_ataque.height),
                    pygame.SRCALPHA,
                )
                surf_ataque.fill((231, 76, 60, 180))
                tela.blit(surf_ataque, (hx, hy))
                pygame.draw.rect(
                    tela,
                    (255, 100, 100),
                    (hx, hy, self.hitbox_ataque.width, self.hitbox_ataque.height),
                    2,
                )

            largura_barra = self.rect.width
            vida_proporcional = max(
                0, int((self.vida / self.vida_maxima) * largura_barra)
            )
            pygame.draw.rect(
                tela, (40, 40, 40), (ix, iy - 8, largura_barra, 4)
            )
            pygame.draw.rect(
                tela, (231, 76, 60), (ix, iy - 8, vida_proporcional, 4)
            )
