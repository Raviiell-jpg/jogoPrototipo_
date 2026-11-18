import sys
from pathlib import Path

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
        self.setWindowTitle("Por uma Gota - História")
        self.setFixedSize(1600, 900)

        caminho_imagem = PASTA_PROJETO / "fundos" / "cena2.png"
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
            "Não havia mais esperança de encontrar água potável."
            "",
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
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3498DB,
                    stop: 0.55 #27AE60,
                    stop: 1 #2ECC71
                );
                color: white;
                border: 3px solid #239B56;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2980B9,
                    stop: 0.55 #229954,
                    stop: 1 #28B463
                );
                color: white;
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
        self.btn_pular.clicked.connect(self.pular_historia)

        self.fundo.lower()

    def iniciar_jogo(self):
        caminho_jogo = PASTA_PROJETO / "historia" / "cena4.py"
        abrir_pagina(self, caminho_jogo, self.continuar)

    def pular_historia(self):
        caminho_jogo = PASTA_PROJETO / "main.py"
        abrir_pagina(self, caminho_jogo, self.btn_pular)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = mostrar_janela(CenaHistoria())
    sys.exit(app.exec())
