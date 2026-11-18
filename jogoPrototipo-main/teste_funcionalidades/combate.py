import pygame

class SistemaCombate:
    def __init__(self):
        self.direcao = 1  # 1 = Direita, -1 = Esquerda
        self.atacando = False
        self.defendendo = False

        self.duracao_ataque = 12
        self.cooldown_ataque = 28
        self.timer_ataque = 0
        self.timer_cooldown = 0

        self.alcance_ataque = 32
        self.altura_ataque = 22
        self.hitbox_ataque = None
        self.hitbox_escudo = None

        self.dano_ataque = 35
        self.forca_recuo_x = 7.5   # Impulso horizontal para trás ao acertar
        self.forca_recuo_y = -6.5  # Impulso vertical (pulinho) ao acertar
        self.reducao_defesa = 1.0

    def atualizar_direcao(self, vel_x):
        if vel_x > 0:
            self.direcao = 1
        elif vel_x < 0:
            self.direcao = -1

    def tentar_atacar(self):
        if self.timer_cooldown <= 0 and not self.defendendo:
            self.atacando = True
            self.timer_ataque = self.duracao_ataque
            self.timer_cooldown = self.cooldown_ataque
            return True
        return False

    def iniciar_defesa(self):
        if not self.atacando:
            self.defendendo = True

    def parar_defesa(self):
        self.defendendo = False
        self.hitbox_escudo = None

    def atualizar(self, jogador_rect):
        if self.timer_ataque > 0:
            self.timer_ataque -= 1
            if self.timer_ataque <= 0:
                self.atacando = False
                self.hitbox_ataque = None

        if self.timer_cooldown > 0:
            self.timer_cooldown -= 1

        # Hitbox de Ataque
        if self.atacando:
            if self.direcao == 1:
                x = jogador_rect.right
            else:
                x = jogador_rect.left - self.alcance_ataque
            y = jogador_rect.centery - (self.altura_ataque // 2)
            self.hitbox_ataque = pygame.Rect(x, y, self.alcance_ataque, self.altura_ataque)
        else:
            self.hitbox_ataque = None

        # Hitbox Física do Escudo
        if self.defendendo:
            largura_escudo = 10
            altura_escudo = jogador_rect.height
            if self.direcao == 1:
                ex = jogador_rect.right
            else:
                ex = jogador_rect.left - largura_escudo
            self.hitbox_escudo = pygame.Rect(ex, jogador_rect.y, largura_escudo, altura_escudo)
        else:
            self.hitbox_escudo = None

    def calcular_dano_recebido(self, dano_base):
        if self.defendendo:
            return int(dano_base * (1.0 - self.reducao_defesa))
        return dano_base

    def desenhar(self, tela, camera_x, camera_y, jogador_rect):
        if self.hitbox_ataque is not None:
            hx = self.hitbox_ataque.x - camera_x
            hy = self.hitbox_ataque.y - camera_y
            superficie_ataque = pygame.Surface((self.hitbox_ataque.width, self.hitbox_ataque.height), pygame.SRCALPHA)
            superficie_ataque.fill((255, 140, 0, 180))
            tela.blit(superficie_ataque, (hx, hy))
            pygame.draw.rect(tela, (255, 200, 50), (hx, hy, self.hitbox_ataque.width, self.hitbox_ataque.height), 2)

        if self.defendendo and self.hitbox_escudo is not None:
            ex = self.hitbox_escudo.x - camera_x
            ey = self.hitbox_escudo.y - camera_y
            escudo_tela = pygame.Rect(ex, ey, self.hitbox_escudo.width, self.hitbox_escudo.height)
            pygame.draw.rect(tela, (0, 191, 255), escudo_tela, border_radius=2)
            pygame.draw.rect(tela, (255, 255, 255), escudo_tela, 2, border_radius=2)