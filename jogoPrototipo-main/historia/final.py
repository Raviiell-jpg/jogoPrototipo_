import sys
from pathlib import Path

import pygame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QWidget

if __package__:
    from .navegacao import abrir_pagina, mostrar_janela
else:
    from navegacao import abrir_pagina, mostrar_janela


PASTA_PROJETO = Path(__file__).resolve().parents[1]


class CenaHistoria(QWidget):
    def __init__(self):
        super().__init__()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            caminho_m = PASTA_PROJETO / "musicas" / "zelda.mp3"
            if caminho_m.is_file():
                pygame.mixer.music.load(str(caminho_m))
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Aviso de áudio (não crítico): {e}")

        self.setWindowTitle("Por uma Gota - História")
        self.setFixedSize(1600, 900)

        caminho_imagem = PASTA_PROJETO / "fundos" / "final.jpg"
        imagem = QPixmap(str(caminho_imagem))
        if imagem.isNull():
            QMessageBox.critical(
                self,
                "Imagem não encontrada",
                f"Não foi possível carregar a imagem da história:\n{caminho_imagem}",
            )
            raise FileNotFoundError(caminho_imagem)

        self.fundo = QLabel(self)
        self.fundo.setPixmap(
            imagem.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.fundo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fundo.setGeometry(0, 0, self.width(), self.height())

        self.texto = QLabel(
            "Finalmente, após uma longa jornada, paz. Um espaço longe de toda a destruição, um espaço onde novamente é possível recomeçar, onde é possível manter a minha luz ainda brilhando. ",
            self,
        )
        self.texto.setGeometry(100, 620, 1400, 150)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setWordWrap(True)
        self.texto.setFont(QFont("Press Start 2P", 14, QFont.Weight.Bold))
        self.texto.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 170); padding: 12px;"
        )

        self.continuar = QPushButton("Continuar", self)
        self.continuar.setGeometry(625, 800, 350, 65)
        self.continuar.setFont(QFont("Press Start 2P", 16, QFont.Weight.Bold))
        self.continuar.setStyleSheet(
            """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop: 0 #003300,stop: 0.5 #008000,stop: 1 #39FF14);
                                color: white;
                                border-radius: 0px;
                                font-size: 22px;
                                color: #D9FFD0;
                                border: 3px solid #39FF14;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #39FF14,stop: 1 #ADFF2F);
                                color: #003300;
                                border: 3px solid #CCFF00;
            }
            """
        )
        self.continuar.clicked.connect(self.iniciar_jogo)

        # Botão Pular História (canto direito inferior)
        self.btn_pular = QPushButton("PULAR", self)
        self.btn_pular.setGeometry(1340, 800, 210, 65)
        self.btn_pular.setFont(QFont("Press Start 2P", 14, QFont.Weight.Bold))
        self.btn_pular.setStyleSheet(
            """
            QPushButton {
                background-color: lightblue;
                color: white;
                border: 3px solid #2874A6;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5DADE2;
                color: white;
            }
            """
        )
        self.btn_pular.clicked.connect(self.iniciar_jogo)

        self.fundo.lower()

    def iniciar_jogo(self):
        caminho_jogo = PASTA_PROJETO / "main.py"
        abrir_pagina(self, caminho_jogo, self.continuar)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = mostrar_janela(CenaHistoria())
    sys.exit(app.exec())
