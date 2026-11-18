import importlib
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QWidget,
)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))


def mostrar_janela(pagina: QWidget) -> QStackedWidget:
    if QApplication.instance() is None:
        raise RuntimeError("Crie QApplication antes de mostrar uma tela.")

    janela = QStackedWidget()
    janela.addWidget(pagina)
    janela.setWindowTitle(pagina.windowTitle())
    janela.setFixedSize(pagina.size())
    janela.show()
    return janela


def abrir_pagina(
    pagina_atual: QWidget, caminho: Path, botao: QPushButton
) -> None:
    janela = pagina_atual.window()
    if not isinstance(janela, QStackedWidget):
        raise RuntimeError("A tela não está dentro da janela de navegação.")

    destino = Path(caminho).resolve()
    botao.setEnabled(False)

    if destino.name == "main.py":
        _iniciar_jogo(janela, destino, botao)
        return

    try:
        modulo = importlib.import_module(f"historia.{destino.stem}")
        pagina_nova = modulo.CenaHistoria()
    except (AttributeError, ImportError, OSError) as erro:
        botao.setEnabled(True)
        QMessageBox.critical(
            pagina_atual,
            "Erro ao abrir a próxima tela",
            f"Não foi possível carregar {destino}:\n{erro}",
        )
        return

    pagina_anterior = janela.currentWidget()
    janela.addWidget(pagina_nova)
    janela.setWindowTitle(pagina_nova.windowTitle())
    janela.setFixedSize(pagina_nova.size())
    janela.setCurrentWidget(pagina_nova)
    janela.removeWidget(pagina_anterior)
    pagina_anterior.deleteLater()


def _iniciar_jogo(
    janela: QStackedWidget, caminho: Path, botao: QPushButton
) -> None:
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass

    iniciou, _ = QProcess.startDetached(
        sys.executable,
        [str(caminho)],
        str(RAIZ_PROJETO),
    )
    if not iniciou:
        botao.setEnabled(True)
        QMessageBox.critical(
            janela,
            "Erro ao iniciar o jogo",
            f"Não foi possível iniciar {caminho}.",
        )
        return

    janela.close()
