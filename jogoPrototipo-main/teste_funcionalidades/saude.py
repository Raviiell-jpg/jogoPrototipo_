import pygame

class SistemaSaude:
    def __init__(self, vida_maxima=100, tempo_imunidade_max=60):
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.vida_visual = float(vida_maxima)  # Suaviza o movimento da barra
        self.tempo_invencivel = 0
        self.tempo_imunidade_max = tempo_imunidade_max

        self.fonte_hud = pygame.font.SysFont("Arial", 16, bold=True)
        self.fonte_game_over = pygame.font.SysFont("Arial", 48, bold=True)
        self.fonte_sub = pygame.font.SysFont("Arial", 22)

    def tomar_dano(self, quantidade=25):
        if self.tempo_invencivel <= 0 and self.vida_atual > 0:
            self.vida_atual = max(0, self.vida_atual - quantidade)
            self.tempo_invencivel = self.tempo_imunidade_max
            return True
        return False

    def curar(self, quantidade=25):
        if 0 < self.vida_atual < self.vida_maxima:
            self.vida_atual = min(self.vida_maxima, self.vida_atual + quantidade)
            return True
        return False

    def atualizar(self):
        if self.tempo_invencivel > 0:
            self.tempo_invencivel -= 1

        # Faz a barra visual deslizar suavemente até a vida real
        if abs(self.vida_visual - self.vida_atual) > 0.2:
            self.vida_visual += (self.vida_atual - self.vida_visual) * 0.15
        else:
            self.vida_visual = float(self.vida_atual)

    def esta_vivo(self):
        return self.vida_atual > 0

    def deve_desenhar_jogador(self):
        if self.tempo_invencivel > 0 and (self.tempo_invencivel // 5) % 2 == 0:
            return False
        return True

    def reiniciar(self):
        self.vida_atual = self.vida_maxima
        self.vida_visual = float(self.vida_maxima)
        self.tempo_invencivel = 0

    def _calcular_cor_degrade(self, percentual):
        """Calcula o degradê contínuo: Verde (1.0) -> Amarelo (0.5) -> Vermelho (0.0)."""
        percentual = max(0.0, min(1.0, percentual))

        cor_verde = (46, 204, 113)
        cor_amarela = (241, 196, 15)
        cor_vermelha = (231, 76, 60)

        if percentual > 0.5:
            # Interpolação entre Amarelo (0.5) e Verde (1.0)
            t = (percentual - 0.5) * 2.0
            r = int(cor_amarela[0] + (cor_verde[0] - cor_amarela[0]) * t)
            g = int(cor_amarela[1] + (cor_verde[1] - cor_amarela[1]) * t)
            b = int(cor_amarela[2] + (cor_verde[2] - cor_amarela[2]) * t)
        else:
            # Interpolação entre Vermelho (0.0) e Amarelo (0.5)
            t = percentual * 2.0
            r = int(cor_vermelha[0] + (cor_amarela[0] - cor_vermelha[0]) * t)
            g = int(cor_vermelha[1] + (cor_amarela[1] - cor_vermelha[1]) * t)
            b = int(cor_vermelha[2] + (cor_amarela[2] - cor_vermelha[2]) * t)

        return (r, g, b)

    def desenhar_hud(self, tela):
        largura_barra = 200
        altura_barra = 22
        
        percentual = self.vida_visual / self.vida_maxima
        proporcao = int(percentual * largura_barra)
        cor_vida = self._calcular_cor_degrade(percentual)

        # Fundo da barra
        pygame.draw.rect(tela, (40, 40, 40), (20, 20, largura_barra, altura_barra))
        
        # Barra de vida com degradê dinâmico
        if proporcao > 0:
            pygame.draw.rect(tela, cor_vida, (20, 20, proporcao, altura_barra))
            
        # Contorno branco
        pygame.draw.rect(tela, (255, 255, 255), (20, 20, largura_barra, altura_barra), 2)

        texto = self.fonte_hud.render(f"HP: {self.vida_atual}/{self.vida_maxima}", True, (255, 255, 255))
        tela.blit(texto, (25, 23))

    def desenhar_game_over(self, tela, largura_tela, altura_tela):
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        txt_go = self.fonte_game_over.render("GAME OVER", True, (231, 76, 60))
        txt_rst = self.fonte_sub.render("Pressione 'R' para Renascer", True, (255, 255, 255))

        rect_go = txt_go.get_rect(center=(largura_tela // 2, altura_tela // 2 - 25))
        rect_rst = txt_rst.get_rect(center=(largura_tela // 2, altura_tela // 2 + 30))

        tela.blit(txt_go, rect_go)
        tela.blit(txt_rst, rect_rst)