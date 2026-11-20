import pygame

class SistemaSaude:
    def __init__(self, vida_maxima=100, tempo_imunidade_max=60):
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.vida_visual = float(vida_maxima)
        self.tempo_invencivel = 0
        self.tempo_imunidade_max = tempo_imunidade_max

        # Fontes do HUD com fallback gracioso e sem warnings de sistema
        self.fonte_hud = pygame.font.SysFont("pressstart2pregular", 16, bold=True)
        self.fonte_game_over = pygame.font.SysFont("pressstart2pregular", 48, bold=True)
        self.fonte_sub = pygame.font.SysFont("pressstart2pregular", 22)

    def tomar_dano(self, quantidade=25):
        """Aplica dano caso o jogador não esteja no período de invulnerabilidade."""
        if self.tempo_invencivel <= 0 and self.vida_atual > 0:
            self.vida_atual = max(0, self.vida_atual - quantidade)
            self.tempo_invencivel = self.tempo_imunidade_max
            return True  # Sofreu dano (útil para aplicar recuo)
        return False

    def curar(self, quantidade=25):
        """Restaura vida até o limite máximo."""
        if self.vida_atual > 0 and self.vida_atual < self.vida_maxima:
            self.vida_atual = min(self.vida_maxima, self.vida_atual + quantidade)
            return True
        return False

    def atualizar(self):
        """Atualiza a contagem dos frames de invulnerabilidade."""
        if self.tempo_invencivel > 0:
            self.tempo_invencivel -= 1
        if abs(self.vida_visual - self.vida_atual) > 0.2:
            self.vida_visual += (self.vida_atual - self.vida_visual) * 0.15
        else:
            self.vida_visual = float(self.vida_atual)

    def esta_vivo(self):
        return self.vida_atual > 0

    def deve_desenhar_jogador(self):
        """Efeito de piscar durante a imunidade."""
        if self.tempo_invencivel > 0 and (self.tempo_invencivel // 5) % 2 == 0:
            return False
        return True

    def reiniciar(self):
        self.vida_atual = self.vida_maxima
        self.vida_visual = float(self.vida_maxima)
        self.tempo_invencivel = 0

    def desenhar_hud(self, tela):
        """Desenha a barra de vida fixa na tela."""
        x_barra = 40
        y_barra = 40
        largura_barra = 230
        altura_barra = 30
        percentual = max(0.0, min(1.0, self.vida_visual / self.vida_maxima))
        proporcao = int(percentual * largura_barra)

        # Cor dinâmica: verde, amarelo ou vermelho
        if percentual > 0.5:
            cor_vida = (135, 206, 250)
        elif percentual > 0.25:
            cor_vida = (241, 196, 15)
        else:
            cor_vida = (231, 76, 60)

        # Fundo, barra preenchida e contorno
        pygame.draw.rect(tela, (40, 40, 40), (x_barra, y_barra, largura_barra, altura_barra))
        pygame.draw.rect(tela, cor_vida, (x_barra, y_barra, proporcao, altura_barra))
        pygame.draw.rect(tela, (255, 255, 255), (x_barra, y_barra, largura_barra, altura_barra), 2)

        texto = self.fonte_hud.render(f"Sede: {self.vida_atual}/{self.vida_maxima}", True, (255, 255, 255))
        texto_rect = texto.get_rect(
            center=(
                x_barra + largura_barra // 2,
                y_barra + altura_barra // 2,
            )
        )
        tela.blit(texto, texto_rect)

    def desenhar_game_over(self, tela, largura_tela, altura_tela):
        """Desenha tela translúcida de Game Over com aviso de reinício."""
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        txt_go = self.fonte_game_over.render("GAME OVER", True, (231, 76, 60))
        txt_rst = self.fonte_sub.render("Pressione 'R' para Renascer", True, (255, 255, 255))

        rect_go = txt_go.get_rect(center=(largura_tela // 2, altura_tela // 2 - 25))
        rect_rst = txt_rst.get_rect(center=(largura_tela // 2, altura_tela // 2 + 30))

        tela.blit(txt_go, rect_go)
        tela.blit(txt_rst, rect_rst)