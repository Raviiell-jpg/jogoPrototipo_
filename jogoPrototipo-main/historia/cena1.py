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

        caminho_imagem = PASTA_PROJETO / "fundos" / "cenaAntes.jpg"
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
            "Numa antiga cidade situada na região nordeste chamada Serra Talhada, existia um espaço onde o conceito de humanidade conseguia ser usado sem medo, onde a população vivia em harmonia. Ao menos antes de tudo vir a acontecer", self
        )
        self.texto.setGeometry(100, 600, 1400, 150)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setWordWrap(True)
        self.texto.setFont(QFont("Press Start 2P", 14, QFont.Weight.Bold))
        self.texto.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 170); padding: 12px;"
        )

        self.continuar = QPushButton("CONTINUAR", self)
        self.continuar.setGeometry(625, 800, 350, 65)
        self.continuar.setFont(QFont("Press Start 2P", 16, QFont.Weight.Bold))
        self.continuar.setStyleSheet(
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
        self.continuar.clicked.connect(self.abrir_proxima_cena)

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

    def abrir_proxima_cena(self):
        caminho_cena = Path(__file__).with_name("cena2.py")
        abrir_pagina(self, caminho_cena, self.continuar)

    def pular_historia(self):
        caminho_jogo = PASTA_PROJETO / "main.py"
        abrir_pagina(self, caminho_jogo, self.btn_pular)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = mostrar_janela(CenaHistoria())
    sys.exit(app.exec())
