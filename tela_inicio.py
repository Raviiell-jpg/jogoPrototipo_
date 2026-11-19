"""
========================================================================
                      POR UMA GOTA - UM SERTÃO RADIOATIVO
========================================================================
Menu Principal Integrado (PyQt6)
Unifica:
- Design e layout moderno em 1600x900 com trilha sonora e estilo cyberpunk
- Navegação fluida para a História / Cutscenes (historia/cena1.py)
- Autenticação e Cadastro com validação de dados (interface_usuarios_gm.py)
- Modo Speedrun competitivo com integração SQLite (banco_dados.py)
- Painel Administrativo de Game Master (GM)
- Totalmente portátil (executável a partir de qualquer diretório)
"""

import sys
from pathlib import Path

import pygame
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QColor, QFont, QPixmap, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Caminho relativo portátil
PASTA_PROJETO = Path(__file__).resolve().parent
if str(PASTA_PROJETO) not in sys.path:
    sys.path.insert(0, str(PASTA_PROJETO))

from banco_dados import BancoDados
from interface_usuarios_gm import (
    DialogLoginCadastro,
    DialogRanking,
    JanelaPainelGM,
)
from historia.navegacao import abrir_pagina, mostrar_janela


class Menu(QWidget):
    def __init__(self):
        super().__init__()
        self.banco = BancoDados()
        self.sessao_atual = self.banco.obter_sessao_atual()

        # Áudio com tratamento gracioso de erros
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            caminho_musica = PASTA_PROJETO / "musicas" / "noImNotaHuman.mp3"
            if caminho_musica.is_file():
                pygame.mixer.music.load(str(caminho_musica))
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Aviso de áudio (não crítico): {e}")

        self.setWindowTitle("Por uma Gota - Menu Principal")
        self.setFixedSize(1600, 900)

        # 1. Imagem de Fundo
        self.fundo = QLabel(self)
        caminho_fundo = PASTA_PROJETO / "fundos" / "fundo.png"
        if caminho_fundo.is_file():
            imagem = QPixmap(str(caminho_fundo))
            self.fundo.setPixmap(
                imagem.scaled(
                    1600,
                    900,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.fundo.setGeometry(0, 0, 1600, 900)

        # 2. Barra Superior de Usuário (Top-Right)
        self._construir_barra_usuario()

        # 3. Título Principal com Brilho Radioativo
        self.titulo1 = QLabel("Por uma Gota", self)
        self.titulo1.setGeometry(0, 325, 1600, 50)
        self.titulo1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo1.setFont(QFont("Press Start 2P", 44, QFont.Weight.Bold))
        self.titulo1.setStyleSheet("color: #70FF50; background: transparent;")

        brilho_t1 = QGraphicsDropShadowEffect(self)
        brilho_t1.setBlurRadius(40)
        brilho_t1.setColor(QColor(57, 255, 20, 240))
        brilho_t1.setOffset(0, 0)
        self.titulo1.setGraphicsEffect(brilho_t1)

        # 4. Subtítulo
        self.titulo2 = QLabel("UM SERTÃO RADIOATIVO", self)
        self.titulo2.setGeometry(0, 375, 1600, 50)
        self.titulo2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo2.setFont(QFont("Press Start 2P", 20, QFont.Weight.Bold))
        self.titulo2.setStyleSheet("color: #C0FFB0; background: transparent;")

        brilho_t2 = QGraphicsDropShadowEffect(self)
        brilho_t2.setBlurRadius(25)
        brilho_t2.setColor(QColor(57, 255, 20, 200))
        brilho_t2.setOffset(0, 0)
        self.titulo2.setGraphicsEffect(brilho_t2)

        # 5. Painel Central de Botões Estilizados
        self._construir_botoes_menu()

        # 6. Atalho Exclusivo do Game Master (CTRL+F12)
        self.atalho_gm = QShortcut(QKeySequence("Ctrl+F12"), self)
        self.atalho_gm.activated.connect(self.abrir_painel_gm)

    def _construir_barra_usuario(self):
        """Cria o widget de status e login no canto superior direito."""
        self.container_usuario = QWidget(self)
        self.container_usuario.setGeometry(1050, 25, 520, 60)
        layout_u = QHBoxLayout(self.container_usuario)
        layout_u.setContentsMargins(10, 5, 10, 5)
        layout_u.setSpacing(12)

        self.lbl_usuario = QLabel("", self.container_usuario)
        self.lbl_usuario.setFont(QFont("Press Start 2P", 10, QFont.Weight.Bold))
        self.lbl_usuario.setStyleSheet(
            "color: #D9FFD0; background-color: rgba(10, 30, 15, 210); "
            "border: 2px solid #39FF14; border-radius: 4px; padding: 8px 12px;"
        )
        layout_u.addWidget(self.lbl_usuario)

        self.btn_login_perfil = QPushButton("LOGIN / CONTA", self.container_usuario)
        self.btn_login_perfil.setFont(QFont("Press Start 2P", 8, QFont.Weight.Bold))
        self.btn_login_perfil.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #003300, stop: 0.5 #008000, stop: 1 #39FF14);
                color: #D9FFD0;
                border: 2px solid #39FF14;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop: 0 #39FF14, stop: 1 #ADFF2F);
                color: #002200;
                border: 2px solid #CCFF00;
            }
        """)
        self.btn_login_perfil.clicked.connect(self._acao_login_perfil)
        layout_u.addWidget(self.btn_login_perfil)

        self.btn_logout = QPushButton("SAIR", self.container_usuario)
        self.btn_logout.setFont(QFont("Press Start 2P", 10, QFont.Weight.Bold))
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 15, 15, 220);
                color: #FFB0B0;
                border: 2px solid #FF4040;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #FF4040;
                color: #FFFFFF;
                border: 2px solid #FFA0A0;
            }
        """)
        self.btn_logout.clicked.connect(self._fazer_logout)
        layout_u.addWidget(self.btn_logout)

        self._atualizar_interface_usuario()

    def _atualizar_interface_usuario(self):
        """Atualiza rótulos e visibilidade com base na sessão salva."""
        self.sessao_atual = self.banco.obter_sessao_atual()
        if self.sessao_atual:
            nome = self.sessao_atual["usuario"]
            papel = self.sessao_atual["papel"].upper()
            cor_papel = "#39FF14" if papel == "GM" else "#70D0FF"
            self.lbl_usuario.setText(f"👤 {nome} [{papel}]")
            self.lbl_usuario.setStyleSheet(
                f"color: {cor_papel}; background-color: rgba(10, 30, 15, 210); "
                f"border: 2px solid {cor_papel}; border-radius: 4px; padding: 8px 12px;"
            )
            self.btn_login_perfil.setText("MEU PERFIL")
            self.btn_logout.setVisible(True)
        else:
            self.lbl_usuario.setText("Visitante")
            self.lbl_usuario.setFont(QFont("Press Start 2P", 10, QFont.Weight.Bold))
            self.lbl_usuario.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_usuario.setStyleSheet(
                "color: #A0C0A0; background-color: rgba(10, 20, 15, 200); "
                "border: 2px solid #507050; border-radius: 4px; padding: 8px 12px;"
            )
            self.btn_login_perfil.setText("LOGIN / CADASTRO")
            self.btn_logout.setVisible(False)

    def _acao_login_perfil(self):
        """Abre janela de login/cadastro ou exibe opções de conta."""
        if self.sessao_atual:
            nome = self.sessao_atual.get("usuario", "")
            papel = self.sessao_atual.get("papel", "jogador").upper()
            QMessageBox.information(
                self,
                "Perfil do Jogador",
                f"👤 Usuário Conectado: {nome}\n"
                f"🔰 Nível de Acesso: {papel}\n\n"
                "Para trocar de usuário, clique no botão SAIR ao lado."
            )
        else:
            dlg = DialogLoginCadastro(self)
            dlg.exec()
            self._atualizar_interface_usuario()

    def _fazer_logout(self):
        """Encerra a sessão atual e atualiza a interface."""
        self.banco.encerrar_sessao()
        self._atualizar_interface_usuario()
        QMessageBox.information(self, "Logout", "Sessão encerrada com sucesso!")

    def _construir_botoes_menu(self):
        """Cria e posiciona verticalmente os botões principais do jogo (sem botões de GM visíveis)."""
        largura_botoes = 420
        altura_botao = 54
        pos_x = (self.width() - largura_botoes) // 2

        estilo_botoes = """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #003300, stop: 0.5 #008000, stop: 1 #39FF14);
                color: #D9FFD0;
                border-radius: 4px;
                font-size: 15px;
                border: 3px solid #39FF14;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop: 0 #39FF14, stop: 1 #ADFF2F);
                color: #002200;
                border: 3px solid #CCFF00;
            }
        """

        y_base = 355
        espaco_y = 68

        # 1. Iniciar Jogo (História completa com cutscenes)
        self.btn_iniciar = QPushButton("INICIAR HISTÓRIA", self)
        self.btn_iniciar.setGeometry(610, 475, 300, altura_botao)
        self.btn_iniciar.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        self.btn_iniciar.setStyleSheet(estilo_botoes)
        self.btn_iniciar.clicked.connect(self.abrir_historia)

        # 2. Modo Speedrun (Inicia fase direto com cronômetro de precisão)
        self.btn_speedrun = QPushButton("MODO SPEEDRUN", self)
        self.btn_speedrun.setGeometry(30, 25, 280, altura_botao)
        self.btn_speedrun.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        self.btn_speedrun.setStyleSheet(estilo_botoes)
        self.btn_speedrun.clicked.connect(self.iniciar_speedrun)

        # 3. Recordes / Ranking de Speedrun (SQLite)
        self.btn_ranking = QPushButton("RANKING", self)
        self.btn_ranking.setGeometry(30, 25 + altura_botao + 12, 280, altura_botao)
        self.btn_ranking.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        self.btn_ranking.setStyleSheet(estilo_botoes)
        self.btn_ranking.clicked.connect(self.abrir_ranking)

        # 4. Tutorial / Instruções
        self.btn_tutorial = QPushButton("TUTORIAL", self)
        self.btn_tutorial.setGeometry(610, 555, 300, altura_botao)
        self.btn_tutorial.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        self.btn_tutorial.setStyleSheet(estilo_botoes)
        self.btn_tutorial.clicked.connect(self.mostrar_tutorial)

        # 5. Sair
        self.btn_sair = QPushButton("SAIR DO JOGO", self)
        self.btn_sair.setGeometry(610, 635, 300, altura_botao)
        self.btn_sair.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        self.btn_sair.setStyleSheet(estilo_botoes)
        self.btn_sair.clicked.connect(self.close)

        self._atualizar_interface_usuario()

    def abrir_historia(self):
        """Inicia a sequência narrativa pelas cutscenes em historia/cena1.py."""
        caminho_historia = PASTA_PROJETO / "historia" / "cena1.py"
        abrir_pagina(self, caminho_historia, self.btn_iniciar)

    def iniciar_speedrun(self):
        """Inicia a fase principal diretamente em modo Speedrun."""
        caminho_main = PASTA_PROJETO / "mainSpeed.py"
        usuario = self.sessao_atual["usuario"] if self.sessao_atual else "Speedrunner"
        args = [str(caminho_main), "--modo", "speedrun", "--usuario", usuario]

        iniciou, _ = QProcess.startDetached(
            sys.executable,
            args,
            str(PASTA_PROJETO),
        )
        if not iniciou:
            QMessageBox.critical(self, "Erro", "Não foi possível iniciar o modo Speedrun.")
            return

        janela = self.window()
        janela.close()

    def abrir_ranking(self):
        """Abre a tabela de recordes de Speedrun do banco de dados SQLite."""
        janela = DialogRanking(self)
        janela.exec()

    def abrir_painel_gm(self):
        """Abre o painel administrativo de Game Master exclusivamente via atalho CTRL+F12."""
        self.sessao_atual = self.banco.obter_sessao_atual()

        # Se NÃO estiver logado em conta GM, abre diretamente a tela de login
        if not (self.sessao_atual and self.sessao_atual.get("is_gm")):
            dlg = DialogLoginCadastro(self)
            dlg.exec()
            self._atualizar_interface_usuario()
            self.sessao_atual = self.banco.obter_sessao_atual()

            # Se não for GM (ou logou em conta que não é GM), exibe mensagem solicitada
            if not (self.sessao_atual and self.sessao_atual.get("is_gm")):
                msg = QMessageBox(self)
                msg.setWindowTitle("Acesso Negado")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Você não tem acesso a essas funções!!\nCaba Safado!!!")
                msg.exec()
                return

        # Se já estiver logado (ou acabou de logar) como GM, abre a interface
        janela = JanelaPainelGM(usuario_gm=self.sessao_atual, parent=self)
        janela.exec()
        self._atualizar_interface_usuario()

    def mostrar_tutorial(self):
        """Exibe o diálogo de tutorial completo e instruções de controle."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Tutorial & Controles - Por uma Gota")
        msg.setText("Sobrevivência no Sertão Radioativo")

        msg.setInformativeText(
            "OBJETIVO:\n"
            "• Desça pelo edifício contaminado sobrevivendo aos perigos do sertão radioativo.\n"
            "• Supere os monstros mutantes e alcance a zona de fuga.\n\n"
            "CONTROLES DO JOGADOR:\n"
            "• Movimento: Teclas A / D ou Setas Esquerda / Direita\n"
            "• Pulo: Barra de Espaço ou Seta Cima\n"
            "• Ataque: Tecla J ou Z\n"
            "• Defesa: Tecla K ou X \n\n"
            "INTERAÇÕES COM O MAPA:\n"
            "• Portas Blindadas: Pressione [E] para abrir ou fechar as portas de segurança.\n"
            "• Escadas de Incêndio: Use W/S ou Cima/Baixo para subir e descer pelas longarinas.\n"
            "• Armadilhas do Teto: Tremores e poeira avisam desabamentos iminentes.\n"
            "• Kits Médicos de Cura: Passe sobre eles para restaurar sua vida.\n\n"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = mostrar_janela(Menu())
    sys.exit(app.exec())
