"""
Interface gráfica em PyQt6 para gerenciamento de usuários, autenticação,
painel de Game Master (GM) e tabela de classificação de Speedrun.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox, QInputDialog, QFrame, QScrollArea, QAbstractItemView,
    QComboBox, QSpinBox, QFileDialog
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from banco_dados import (
    banco, validar_username, validar_email, validar_senha,
    validar_registro_speedrun, formatar_tempo_ms, converter_para_ms, desmembrar_ms
)
from relatorios import gerar_relatorio_csv, gerar_relatorio_pdf


ESTILO_BASE = """
    QDialog, QWidget {
        background-color: #0d140e;
        color: #d9ffd0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    QTabWidget::pane {
        border: 2px solid #234d20;
        background-color: #121c13;
    }
    QTabBar::tab {
        background: #182819;
        color: #a8df9e;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #234d20;
        border-bottom: none;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #234d20;
        color: #39ff14;
        border: 2px solid #39ff14;
        border-bottom: none;
    }
    QLineEdit, QComboBox, QSpinBox {
        background-color: #172418;
        border: 2px solid #2d6129;
        border-radius: 4px;
        padding: 6px 10px;
        color: #ffffff;
        font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 2px solid #39ff14;
        background-color: #1e3020;
    }
    QComboBox QAbstractItemView {
        background-color: #111a12;
        selection-background-color: #245722;
        color: #e2fce0;
        border: 1px solid #39ff14;
    }
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #004400, stop:1 #008800);
        color: #eaffea;
        border: 2px solid #39ff14;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008800, stop:1 #39ff14);
        color: #002200;
        border: 2px solid #adff2f;
    }
    QPushButton:disabled {
        background-color: #2b332c;
        border: 1px solid #475448;
        color: #7b887c;
    }
    QTableWidget {
        background-color: #111a12;
        border: 1px solid #285425;
        gridline-color: #1e381c;
        color: #e2fce0;
        font-size: 12px;
        selection-background-color: #245722;
        selection-color: #ffffff;
    }
    QHeaderView::section {
        background-color: #1a2a1b;
        color: #39ff14;
        padding: 6px;
        border: 1px solid #285425;
        font-weight: bold;
    }
    QCheckBox {
        color: #c2efb9;
        font-size: 13px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #39ff14;
        background: #172418;
    }
    QCheckBox::indicator:checked {
        background: #39ff14;
    }
"""


# ====================================================================
# DIÁLOGO DE LOGIN E CADASTRO COM VALIDAÇÃO COMPLETA
# ====================================================================

class DialogLoginCadastro(QDialog):
    login_sucesso = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autenticação e Cadastro - Por uma Gota")
        self.setFixedSize(540, 620)
        self.setStyleSheet(ESTILO_BASE)
        self.usuario_autenticado = None

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(14)

        # Cabeçalho
        titulo = QLabel("ACESSO DE SOBREVIVENTE", self)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #39ff14; letter-spacing: 2px; margin-bottom: 4px;")
        layout_principal.addWidget(titulo)

        subtitulo = QLabel("Identifique-se para registrar tempos de Speedrun ou acessar ferramentas de GM.", self)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: #92bfa0; font-size: 12px; margin-bottom: 8px;")
        layout_principal.addWidget(subtitulo)

        # Abas de Login e Cadastro
        self.abas = QTabWidget(self)
        self.aba_login = QWidget()
        self.aba_cadastro = QWidget()

        self._montar_aba_login()
        self._montar_aba_cadastro()

        self.abas.addTab(self.aba_login, "CONECTAR")
        self.abas.addTab(self.aba_cadastro, "CRIAR CONTA")
        layout_principal.addWidget(self.abas)

        # Botão Convidado no Rodapé
        layout_rodape = QHBoxLayout()
        self.btn_convidado = QPushButton("JOGAR COMO CONVIDADO", self)
        self.btn_convidado.setStyleSheet("""
            QPushButton {
                background: #1d2b1f;
                color: #a0cfa0;
                border: 1px dashed #437a40;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #2b422f;
                color: #ffffff;
                border: 1px solid #39ff14;
            }
        """)
        self.btn_convidado.clicked.connect(self._entrar_como_convidado)
        layout_rodape.addWidget(self.btn_convidado)

        self.btn_cancelar = QPushButton("FECHAR", self)
        self.btn_cancelar.setStyleSheet("background: #331515; border: 1px solid #772222; color: #ff9999;")
        self.btn_cancelar.clicked.connect(self.reject)
        layout_rodape.addWidget(self.btn_cancelar)

        layout_principal.addLayout(layout_rodape)

    # --- ABA DE LOGIN ---
    def _montar_aba_login(self):
        layout = QVBoxLayout(self.aba_login)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Usuário ou E-mail:"))
        self.input_login_usuario = QLineEdit()
        self.input_login_usuario.setPlaceholderText("Ex: Kaique, Rafael ou seu_usuario")
        layout.addWidget(self.input_login_usuario)

        layout.addWidget(QLabel("Senha:"))
        self.input_login_senha = QLineEdit()
        self.input_login_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_login_senha.setPlaceholderText("Digite sua senha cadastrada")
        self.input_login_senha.returnPressed.connect(self._executar_login)
        layout.addWidget(self.input_login_senha)

        self.lbl_msg_login = QLabel("")
        self.lbl_msg_login.setWordWrap(True)
        self.lbl_msg_login.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_msg_login)

        layout.addStretch()

        btn_entrar = QPushButton("ENTRAR NO SISTEMA")
        btn_entrar.clicked.connect(self._executar_login)
        layout.addWidget(btn_entrar)


    # --- ABA DE CADASTRO ---
    def _montar_aba_cadastro(self):
        layout = QVBoxLayout(self.aba_cadastro)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Nome de Usuário (3-20 caracteres alfanuméricos):"))
        self.input_cad_usuario = QLineEdit()
        self.input_cad_usuario.setPlaceholderText("Ex: corredor_sertao")
        layout.addWidget(self.input_cad_usuario)

        layout.addWidget(QLabel("E-mail de Contato:"))
        self.input_cad_email = QLineEdit()
        self.input_cad_email.setPlaceholderText("Ex: meu_email@exemplo.com")
        layout.addWidget(self.input_cad_email)

        layout.addWidget(QLabel("Nome Completo ou Apelido:"))
        self.input_cad_nome = QLineEdit()
        self.input_cad_nome.setPlaceholderText("Ex: Severino Silva")
        layout.addWidget(self.input_cad_nome)

        layout.addWidget(QLabel("Senha (mínimo 6 caracteres, com letra e número):"))
        self.input_cad_senha = QLineEdit()
        self.input_cad_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_cad_senha.setPlaceholderText("Mínimo 6 chars com letras e números")
        layout.addWidget(self.input_cad_senha)

        layout.addWidget(QLabel("Confirmar Senha:"))
        self.input_cad_confirmar = QLineEdit()
        self.input_cad_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_cad_confirmar.setPlaceholderText("Repita a senha exatamente igual")
        layout.addWidget(self.input_cad_confirmar)

        self.lbl_msg_cad = QLabel("")
        self.lbl_msg_cad.setWordWrap(True)
        self.lbl_msg_cad.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_msg_cad)

        btn_cadastrar = QPushButton("CADASTRAR E ENTRAR")
        btn_cadastrar.clicked.connect(self._executar_cadastro)
        layout.addWidget(btn_cadastrar)

    def _executar_login(self):
        identificador = self.input_login_usuario.text().strip()
        senha = self.input_login_senha.text()

        if not identificador or not senha:
            self.lbl_msg_login.setStyleSheet("color: #ff5555;")
            self.lbl_msg_login.setText("Preencha usuário/e-mail e a senha.")
            return

        usuario = banco.autenticar_usuario(identificador, senha)
        if usuario:
            self.usuario_autenticado = usuario
            banco.salvar_sessao_ativa(usuario)
            self.lbl_msg_login.setStyleSheet("color: #39ff14;")
            tipo = "Game Master" if usuario["is_gm"] else "Jogador"
            self.lbl_msg_login.setText(f"Login efetuado com sucesso! Bem-vindo, {usuario['username']} ({tipo})!")
            self.login_sucesso.emit(usuario)
            self.accept()
        else:
            self.lbl_msg_login.setStyleSheet("color: #ff5555;")
            self.lbl_msg_login.setText("Credenciais incorretas! Verifique o nome/e-mail e a senha.")

    def _executar_cadastro(self):
        username = self.input_cad_usuario.text().strip()
        email = self.input_cad_email.text().strip()
        nome = self.input_cad_nome.text().strip()
        senha = self.input_cad_senha.text()
        confirmar = self.input_cad_confirmar.text()
        is_gm = False  # Novos cadastros nunca podem ser GM

        # Validações visuais
        valido_u, msg_u = validar_username(username)
        if not valido_u:
            self.lbl_msg_cad.setStyleSheet("color: #ff5555;")
            self.lbl_msg_cad.setText(f"Erro no Usuário: {msg_u}")
            self.input_cad_usuario.setFocus()
            return

        valido_e, msg_e = validar_email(email)
        if not valido_e:
            self.lbl_msg_cad.setStyleSheet("color: #ff5555;")
            self.lbl_msg_cad.setText(f"Erro no E-mail: {msg_e}")
            self.input_cad_email.setFocus()
            return

        valido_s, msg_s = validar_senha(senha)
        if not valido_s:
            self.lbl_msg_cad.setStyleSheet("color: #ff5555;")
            self.lbl_msg_cad.setText(f"Erro na Senha: {msg_s}")
            self.input_cad_senha.setFocus()
            return

        if senha != confirmar:
            self.lbl_msg_cad.setStyleSheet("color: #ff5555;")
            self.lbl_msg_cad.setText("Erro: As senhas digitadas não coincidem!")
            self.input_cad_confirmar.setFocus()
            return

        try:
            novo_usuario = banco.cadastrar_usuario(
                username=username,
                senha=senha,
                email=email,
                nome_completo=nome,
                is_gm=False
            )
            # Log de cadastro
            banco.registrar_log_gm(novo_usuario["id"], "CADASTRO_USUARIO", f"Usuário {username} cadastrado.")

            # Autenticar automaticamente
            self.usuario_autenticado = novo_usuario
            banco.salvar_sessao_ativa(novo_usuario)
            self.lbl_msg_cad.setStyleSheet("color: #39ff14;")
            self.lbl_msg_cad.setText("Cadastro realizado com sucesso! Entrando...")
            self.login_sucesso.emit(novo_usuario)
            self.accept()
        except ValueError as err:
            self.lbl_msg_cad.setStyleSheet("color: #ff5555;")
            self.lbl_msg_cad.setText(str(err))

    def _entrar_como_convidado(self):
        convidado = {
            "id": None,
            "username": "Convidado",
            "email": "convidado@local",
            "nome_completo": "Sobrevivente Convidado",
            "is_gm": False
        }
        self.usuario_autenticado = convidado
        banco.salvar_sessao_ativa(convidado)
        self.login_sucesso.emit(convidado)
        self.accept()


# ====================================================================
# TELA / DIÁLOGO DE RANKING (LEADERBOARD DO SPEEDRUN)
# ====================================================================

class DialogRanking(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ranking Oficial de Speedrun - Por uma Gota")
        self.setFixedSize(850, 560)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Cabeçalho
        titulo = QLabel("🏆 LEADERBOARD DE SPEEDRUN", self)
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #39ff14; letter-spacing: 2px;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Os sobreviventes mais rápidos a descer a torre e alcançar o reservatório de água pura.", self)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #92bfa0; font-size: 12px;")
        layout.addWidget(subtitulo)

        # Barra de Filtros e Atualizar
        barra_controles = QHBoxLayout()
        self.chk_apenas_oficiais = QCheckBox("")
        self.chk_apenas_oficiais.setChecked(True)
        self.chk_apenas_oficiais.toggled.connect(self.carregar_ranking)
        barra_controles.addWidget(self.chk_apenas_oficiais)

        barra_controles.addStretch()

        btn_atualizar = QPushButton("🔄 Atualizar Ranking")
        btn_atualizar.clicked.connect(self.carregar_ranking)
        barra_controles.addWidget(btn_atualizar)
        layout.addLayout(barra_controles)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Posição", "Jogador", "Tempo", "Inimigos Eliminados", "Data"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabela)

        # Rodapé
        rodape = QHBoxLayout()
        self.lbl_total_recordes = QLabel("")
        self.lbl_total_recordes.setStyleSheet("color: #79a87d;")
        rodape.addWidget(self.lbl_total_recordes)

        rodape.addStretch()

        btn_fechar = QPushButton("FECHAR")
        btn_fechar.clicked.connect(self.accept)
        rodape.addWidget(btn_fechar)
        layout.addLayout(rodape)

        self.carregar_ranking()

    def carregar_ranking(self):
        apenas_legitimos = self.chk_apenas_oficiais.isChecked()
        ranking = banco.obter_ranking(limite=50, apenas_legitimos=apenas_legitimos)

        self.tabela.setRowCount(len(ranking))
        for row_idx, r in enumerate(ranking):
            pos_str = f"#{r['posicao']}"
            if r["posicao"] == 1:
                pos_str = "🥇 #1"
            elif r["posicao"] == 2:
                pos_str = "🥈 #2"
            elif r["posicao"] == 3:
                pos_str = "🥉 #3"

            item_pos = QTableWidgetItem(pos_str)
            item_pos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_user = QTableWidgetItem(r["username"])
            item_user.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_tempo = QTableWidgetItem(r["tempo_formatado"])
            item_tempo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tempo.setForeground(QColor("#39ff14"))
            item_tempo.setFont(QFont("Arial", 11, QFont.Weight.Bold))

            item_inimigos = QTableWidgetItem(str(r.get("inimigos_derrotados", 0)))
            item_inimigos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Data formatada
            data_str = str(r["data_registro"])[:16]
            item_data = QTableWidgetItem(data_str)
            item_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela.setItem(row_idx, 0, item_pos)
            self.tabela.setItem(row_idx, 1, item_user)
            self.tabela.setItem(row_idx, 2, item_tempo)
            self.tabela.setItem(row_idx, 3, item_inimigos)
            self.tabela.setItem(row_idx, 4, item_data)

        self.lbl_total_recordes.setText(f"Total de {len(ranking)} corridas registradas no banco de dados.")


# ====================================================================
# DIÁLOGOS DE GERENCIAMENTO (USUÁRIOS E DADOS DE SPEEDRUN)
# ====================================================================

class DialogCadastrarUsuarioGM(QDialog):
    """Diálogo modal para Game Masters cadastrarem novos usuários."""
    def __init__(self, gm_executor: str, parent=None):
        super().__init__(parent)
        self.gm_executor = gm_executor
        self.setWindowTitle("Cadastrar Novo Usuário (Painel GM)")
        self.setFixedSize(520, 500)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)

        titulo = QLabel("➕ CADASTRAR NOVO USUÁRIO")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #39ff14;")
        layout.addWidget(titulo)

        layout.addWidget(QLabel("Nome de Usuário (3 a 20 caracteres alfanuméricos):"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Ex: novo_corredor")
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("E-mail de Contato:"))
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ex: usuario@sertao.com")
        layout.addWidget(self.input_email)

        layout.addWidget(QLabel("Nome Completo ou Apelido:"))
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: João da Silva")
        layout.addWidget(self.input_nome)

        layout.addWidget(QLabel("Senha Inicial (mínimo 6 caracteres, letras e números):"))
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setPlaceholderText("Mínimo 6 chars com letras e números")
        layout.addWidget(self.input_senha)

        self.chk_gm = QCheckBox("Cadastrar diretamente como Game Master (GM / Administrador)")
        self.chk_gm.setToolTip("Concede privilégios administrativos e cheats via CTRL+F12.")
        layout.addWidget(self.chk_gm)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color: #ff5555; font-weight: bold; font-size: 11px;")
        self.lbl_erro.setWordWrap(True)
        layout.addWidget(self.lbl_erro)

        layout.addStretch()

        botoes = QHBoxLayout()
        btn_salvar = QPushButton("SALVAR CADASTRO")
        btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(btn_salvar)

        btn_cancelar = QPushButton("CANCELAR")
        btn_cancelar.setStyleSheet("background: #331515; border: 1px solid #772222; color: #ff9999;")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)

    def _salvar(self):
        u = self.input_username.text().strip()
        e = self.input_email.text().strip()
        n = self.input_nome.text().strip()
        s = self.input_senha.text()
        is_gm = self.chk_gm.isChecked()

        try:
            banco.cadastrar_usuario_gm(
                username=u,
                senha=s,
                email=e,
                nome_completo=n,
                is_gm=is_gm,
                gm_executor=self.gm_executor
            )
            QMessageBox.information(self, "Sucesso", f"Usuário '{u}' cadastrado com sucesso no banco de dados!")
            self.accept()
        except ValueError as err:
            self.lbl_erro.setText(f"Erro de Validação: {err}")


class DialogEditarUsuarioGM(QDialog):
    """Diálogo modal para edição de dados cadastrais de um usuário existente."""
    def __init__(self, usuario: Dict[str, Any], gm_executor: str, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.gm_executor = gm_executor
        self.setWindowTitle(f"Editar Usuário - {usuario['username']}")
        self.setFixedSize(520, 480)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)

        titulo = QLabel(f"✏️ EDITAR USUÁRIO: {usuario['username']}")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #39ff14;")
        layout.addWidget(titulo)

        layout.addWidget(QLabel("Nome Completo ou Apelido:"))
        self.input_nome = QLineEdit()
        self.input_nome.setText(usuario.get("nome_completo") or "")
        layout.addWidget(self.input_nome)

        layout.addWidget(QLabel("E-mail de Contato:"))
        self.input_email = QLineEdit()
        self.input_email.setText(usuario.get("email") or "")
        layout.addWidget(self.input_email)

        self.chk_gm = QCheckBox("Privilégios de Game Master (GM)")
        self.chk_gm.setChecked(bool(usuario.get("is_gm")))
        layout.addWidget(self.chk_gm)

        layout.addWidget(QLabel("Nova Senha (deixe em branco para manter a senha atual):"))
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setPlaceholderText("Preencha apenas se desejar redefinir")
        layout.addWidget(self.input_senha)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color: #ff5555; font-weight: bold; font-size: 11px;")
        self.lbl_erro.setWordWrap(True)
        layout.addWidget(self.lbl_erro)

        layout.addStretch()

        botoes = QHBoxLayout()
        btn_salvar = QPushButton("SALVAR ALTERAÇÕES")
        btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(btn_salvar)

        btn_cancelar = QPushButton("CANCELAR")
        btn_cancelar.setStyleSheet("background: #331515; border: 1px solid #772222; color: #ff9999;")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)

    def _salvar(self):
        nome = self.input_nome.text().strip()
        email = self.input_email.text().strip()
        is_gm = self.chk_gm.isChecked()
        senha = self.input_senha.text() or None

        try:
            banco.atualizar_usuario(
                usuario_id=self.usuario["id"],
                nome_completo=nome,
                email=email,
                is_gm=is_gm,
                nova_senha=senha,
                gm_executor=self.gm_executor
            )
            QMessageBox.information(self, "Sucesso", f"Dados do usuário '{self.usuario['username']}' atualizados com sucesso!")
            self.accept()
        except ValueError as err:
            self.lbl_erro.setText(f"Erro de Validação: {err}")


class DialogRegistroSpeedrunGM(QDialog):
    """Diálogo para cadastrar ou editar um registro de speedrun."""
    def __init__(
        self,
        gm_executor: Optional[Any] = None,
        dados_edicao: Optional[Dict[str, Any]] = None,
        parent=None,
        gm_usuario: Optional[Any] = None,
        run_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent)
        gm_obj = gm_executor or gm_usuario
        if isinstance(gm_obj, dict):
            self.gm_executor = gm_obj.get("username", "GM")
        else:
            self.gm_executor = str(gm_obj or "GM")

        self.dados_edicao = dados_edicao or run_data
        self.modo_edicao = self.dados_edicao is not None

        titulo_str = "✏️ Editar Registro de Speedrun" if self.modo_edicao else "➕ Novo Registro de Speedrun"
        self.setWindowTitle(titulo_str)
        self.setFixedSize(540, 580)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)

        lbl_titulo = QLabel(titulo_str.upper())
        lbl_titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #39ff14;")
        layout.addWidget(lbl_titulo)

        # Seleção de Usuário
        layout.addWidget(QLabel("Jogador Associado:"))
        self.combo_usuario = QComboBox()
        self.usuarios_mapa = {}
        for u in banco.listar_usuarios():
            label = f"{u['username']} (ID={u['id']}) - {'👑 GM' if u['is_gm'] else 'Sobrevivente'}"
            self.combo_usuario.addItem(label, u["id"])
            self.usuarios_mapa[u["id"]] = u["username"]
        layout.addWidget(self.combo_usuario)

        if self.modo_edicao and self.dados_edicao:
            idx = self.combo_usuario.findData(self.dados_edicao.get("usuario_id"))
            if idx >= 0:
                self.combo_usuario.setCurrentIndex(idx)
            self.combo_usuario.setEnabled(False)

        # Entrada de Tempo (Minutos, Segundos, Milissegundos)
        layout.addWidget(QLabel("Tempo da Corrida (Minutos : Segundos . Milissegundos):"))
        layout_tempo = QHBoxLayout()

        self.spin_minutos = QSpinBox()
        self.spin_minutos.setRange(0, 599)
        self.spin_minutos.setSuffix(" min")

        self.spin_segundos = QSpinBox()
        self.spin_segundos.setRange(0, 59)
        self.spin_segundos.setSuffix(" seg")

        self.spin_milis = QSpinBox()
        self.spin_milis.setRange(0, 999)
        self.spin_milis.setSuffix(" ms")

        layout_tempo.addWidget(self.spin_minutos)
        layout_tempo.addWidget(self.spin_segundos)
        layout_tempo.addWidget(self.spin_milis)
        layout.addLayout(layout_tempo)

        self.lbl_tempo_preview = QLabel("Tempo Formatado: 00:00.000")
        self.lbl_tempo_preview.setStyleSheet("color: #39ff14; font-family: monospace; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.lbl_tempo_preview)

        self.spin_minutos.valueChanged.connect(self._atualizar_preview_tempo)
        self.spin_segundos.valueChanged.connect(self._atualizar_preview_tempo)
        self.spin_milis.valueChanged.connect(self._atualizar_preview_tempo)

        # Inimigos Derrotados / Total
        layout_inimigos = QHBoxLayout()
        vbox_i1 = QVBoxLayout()
        vbox_i1.addWidget(QLabel("Inimigos Abatidos:"))
        self.spin_inimigos = QSpinBox()
        self.spin_inimigos.setRange(0, 999)
        self.spin_inimigos.setValue(5)
        vbox_i1.addWidget(self.spin_inimigos)
        layout_inimigos.addLayout(vbox_i1)

        vbox_i2 = QVBoxLayout()
        vbox_i2.addWidget(QLabel("Total de Inimigos da Fase:"))
        self.spin_total_inimigos = QSpinBox()
        self.spin_total_inimigos.setRange(0, 999)
        self.spin_total_inimigos.setValue(9)
        vbox_i2.addWidget(self.spin_total_inimigos)
        layout_inimigos.addLayout(vbox_i2)
        layout.addLayout(layout_inimigos)

        # Checkboxes de Conclusão e Cheat GM
        self.chk_concluido = QCheckBox("Corrida Concluída com Sucesso (Alcançou o Reservatório)")
        self.chk_concluido.setChecked(True)
        layout.addWidget(self.chk_concluido)

        self.chk_usou_gm = QCheckBox("Partida com Recursos de GM / Cheats (Desclassificada do ranking oficial)")
        self.chk_usou_gm.setChecked(False)
        layout.addWidget(self.chk_usou_gm)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color: #ff5555; font-weight: bold; font-size: 11px;")
        self.lbl_erro.setWordWrap(True)
        layout.addWidget(self.lbl_erro)

        layout.addStretch()

        botoes = QHBoxLayout()
        btn_salvar = QPushButton("SALVAR REGISTRO")
        btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(btn_salvar)

        btn_cancelar = QPushButton("CANCELAR")
        btn_cancelar.setStyleSheet("background: #331515; border: 1px solid #772222; color: #ff9999;")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)

        layout.addLayout(botoes)

        # Preencher se for edição
        if self.modo_edicao and self.dados_edicao:
            t_ms = self.dados_edicao.get("tempo_ms", 0)
            m, s, ms = desmembrar_ms(t_ms)
            self.spin_minutos.setValue(m)
            self.spin_segundos.setValue(s)
            self.spin_milis.setValue(ms)
            self.spin_inimigos.setValue(self.dados_edicao.get("inimigos_derrotados", 0))
            self.spin_total_inimigos.setValue(self.dados_edicao.get("total_inimigos", 9))
            self.chk_concluido.setChecked(bool(self.dados_edicao.get("concluido")))
            self.chk_usou_gm.setChecked(bool(self.dados_edicao.get("usou_gm")))

        self._atualizar_preview_tempo()

    def _atualizar_preview_tempo(self):
        m = self.spin_minutos.value()
        s = self.spin_segundos.value()
        ms = self.spin_milis.value()
        ms_tot = converter_para_ms(m, s, ms)
        self.lbl_tempo_preview.setText(f"Tempo Formatado: {formatar_tempo_ms(ms_tot)}")

    def _salvar(self):
        usuario_id = self.combo_usuario.currentData()
        m = self.spin_minutos.value()
        s = self.spin_segundos.value()
        ms = self.spin_milis.value()
        tempo_ms = converter_para_ms(m, s, ms)

        inimigos = self.spin_inimigos.value()
        tot_inimigos = self.spin_total_inimigos.value()
        concluido = self.chk_concluido.isChecked()
        usou_gm = self.chk_usou_gm.isChecked()

        valido, msg = validar_registro_speedrun(tempo_ms=tempo_ms, inimigos_derrotados=inimigos, total_inimigos=tot_inimigos)
        if not valido:
            self.lbl_erro.setText(f"Erro de Validação: {msg}")
            return

        try:
            if self.modo_edicao:
                banco.atualizar_speedrun(
                    speedrun_id=self.dados_edicao["id"],
                    tempo_ms=tempo_ms,
                    inimigos_derrotados=inimigos,
                    total_inimigos=tot_inimigos,
                    concluido=concluido,
                    usou_gm=usou_gm,
                    gm_executor=self.gm_executor
                )
                QMessageBox.information(self, "Sucesso", "Registro de speedrun atualizado com sucesso!")
            else:
                banco.cadastrar_speedrun_manual(
                    usuario_id=usuario_id,
                    tempo_ms=tempo_ms,
                    inimigos_derrotados=inimigos,
                    total_inimigos=tot_inimigos,
                    concluido=concluido,
                    usou_gm=usou_gm,
                    gm_executor=self.gm_executor
                )
                QMessageBox.information(self, "Sucesso", "Novo registro de speedrun cadastrado com sucesso!")
            self.accept()
        except ValueError as err:
            self.lbl_erro.setText(f"Erro: {err}")


class DialogDetalhesSpeedrun(QDialog):
    """Visualizador detalhado com auditoria completa de uma corrida de speedrun."""
    def __init__(self, speedrun: Optional[Dict[str, Any]] = None, parent=None, run_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.speedrun = speedrun or run_data or {}
        speedrun = self.speedrun
        self.setWindowTitle(f"Detalhes da Corrida #{speedrun.get('id')}")
        self.setFixedSize(500, 440)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        titulo = QLabel(f"👁️ DETALHES DA CORRIDA #{speedrun.get('id')}")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #39ff14;")
        layout.addWidget(titulo)

        tot_i = speedrun.get("total_inimigos") or 0
        i = speedrun.get("inimigos_derrotados") or 0
        pct_i = f"{(i / tot_i * 100):.1f}%" if tot_i > 0 else "0%"

        status_str = "✔ Concluída (Fuga pelo Reservatório)" if speedrun.get("concluido") else "✖ Falha / Não Concluída"
        cor_status = "#39ff14" if speedrun.get("concluido") else "#ff5555"

        categ_str = "⚠️ Partida Desclassificada (Auxílio de GM)" if speedrun.get("usou_gm") else "★ Corrida Oficial Válida"
        cor_categ = "#ffaa00" if speedrun.get("usou_gm") else "#70d0ff"

        itens = [
            ("Jogador:", speedrun.get("username", "-")),
            ("E-mail:", speedrun.get("email", "-")),
            ("Tempo Cronometrado:", f"{speedrun.get('tempo_formatado')} ({speedrun.get('tempo_ms')} ms)"),
            ("Monstros Eliminados:", f"{i} de {tot_i} ({pct_i})"),
            ("Status de Vitória:", status_str),
            ("Classificação:", categ_str),
            ("Data e Hora:", str(speedrun.get("data_registro", "-"))[:19])
        ]

        frame = QFrame()
        frame.setStyleSheet("background-color: #142215; border: 1px solid #285425; border-radius: 6px; padding: 12px;")
        layout_f = QVBoxLayout(frame)
        layout_f.setSpacing(8)

        for rotulo, valor in itens:
            h = QHBoxLayout()
            lbl_r = QLabel(rotulo)
            lbl_r.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl_r.setStyleSheet("color: #adff2f;")
            lbl_r.setFixedWidth(160)

            lbl_v = QLabel(str(valor))
            lbl_v.setFont(QFont("Arial", 11))
            if "Concluída" in str(valor):
                lbl_v.setStyleSheet(f"color: {cor_status}; font-weight: bold;")
            elif "Oficial" in str(valor) or "Desclassificada" in str(valor):
                lbl_v.setStyleSheet(f"color: {cor_categ}; font-weight: bold;")
            else:
                lbl_v.setStyleSheet("color: #ffffff;")
            h.addWidget(lbl_r)
            h.addWidget(lbl_v)
            layout_f.addLayout(h)

        layout.addWidget(frame)
        layout.addStretch()

        btn_ok = QPushButton("FECHAR")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)


# ====================================================================
# PAINEL COMPLETO DO GAME MASTER (GM)
# ====================================================================

class JanelaPainelGM(QDialog):
    def __init__(self, usuario_gm: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.usuario_gm = usuario_gm
        self.setWindowTitle("Painel de Controle do Game Master (GM) - Por uma Gota")
        self.resize(1080, 720)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(ESTILO_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # Cabeçalho GM
        cabecalho = QHBoxLayout()
        titulo = QLabel("👑 PAINEL DE CONTROLE DO GAME MASTER (GM)")
        titulo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #39ff14; letter-spacing: 1px;")
        cabecalho.addWidget(titulo)

        cabecalho.addStretch()

        lbl_gm_info = QLabel(f"GM Conectado: <b>{usuario_gm.get('username', 'GM')}</b>")
        lbl_gm_info.setStyleSheet(
            "color: #adff2f; font-size: 13px; background: #19331b; padding: 6px 14px; "
            "border-radius: 4px; border: 1px solid #39ff14;"
        )
        cabecalho.addWidget(lbl_gm_info)

        layout.addLayout(cabecalho)

        # Abas de Administração Modular
        self.abas = QTabWidget()

        self.aba_usuarios = QWidget()
        self.aba_dados = QWidget()
        self.aba_relatorios = QWidget()
        self.aba_logs = QWidget()
        self.aba_comandos_jogo = QWidget()

        self._montar_aba_usuarios()
        self._montar_aba_dados()
        self._montar_aba_relatorios()
        self._montar_aba_logs()
        self._montar_aba_comandos_jogo()

        self.abas.addTab(self.aba_usuarios, "👥 USUÁRIOS")
        self.abas.addTab(self.aba_dados, "🎮 DADOS (SPEEDRUNS)")
        self.abas.addTab(self.aba_relatorios, "📊 RELATÓRIOS DO RUNNER")
        self.abas.addTab(self.aba_logs, "📜 AUDITORIA & LOGS")
        self.abas.addTab(self.aba_comandos_jogo, "⌨️ COMANDOS NO JOGO")

        # Conectar mudança de aba para recarregar relatórios/logs sob demanda
        self.abas.currentChanged.connect(self._on_aba_alterada)

        layout.addWidget(self.abas)

        # Botão Fechar Painel
        layout_fechar = QHBoxLayout()
        layout_fechar.addStretch()
        btn_fechar = QPushButton("FECHAR PAINEL GM")
        btn_fechar.setStyleSheet(
            "background: #1e3020; border: 1px solid #2f692a; color: #b5f5b0; "
            "padding: 8px 24px; font-weight: bold;"
        )
        btn_fechar.clicked.connect(self.accept)
        layout_fechar.addWidget(btn_fechar)
        layout.addLayout(layout_fechar)

    def _on_aba_alterada(self, indice: int):
        if indice == 0:
            self._carregar_usuarios()
        elif indice == 1:
            self._carregar_dados_runs()
        elif indice == 2:
            self._carregar_relatorio()
        elif indice == 3:
            self._carregar_logs()

    # ====================================================================
    # PILAR 1: GERENCIAMENTO DE USUÁRIOS
    # ====================================================================
    def _montar_aba_usuarios(self):
        layout = QVBoxLayout(self.aba_usuarios)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Barra de Filtros e Consulta
        barra_filtros = QHBoxLayout()
        barra_filtros.setSpacing(8)

        lbl_busca = QLabel("Buscar:")
        barra_filtros.addWidget(lbl_busca)

        self.input_busca_user = QLineEdit()
        self.input_busca_user.setPlaceholderText("Filtrar por usuário, e-mail ou nome...")
        self.input_busca_user.textChanged.connect(self._carregar_usuarios)
        barra_filtros.addWidget(self.input_busca_user)

        lbl_perfil = QLabel("Perfil:")
        barra_filtros.addWidget(lbl_perfil)

        self.combo_filtro_perfil = QComboBox()
        self.combo_filtro_perfil.addItems(["Todos os Perfis", "Apenas Game Masters", "Apenas Jogadores"])
        self.combo_filtro_perfil.currentIndexChanged.connect(self._carregar_usuarios)
        barra_filtros.addWidget(self.combo_filtro_perfil)

        btn_buscar_u = QPushButton("🔍 Atualizar")
        btn_buscar_u.clicked.connect(self._carregar_usuarios)
        barra_filtros.addWidget(btn_buscar_u)

        layout.addLayout(barra_filtros)

        # Tabela de Usuários
        self.tabela_usuarios = QTableWidget()
        self.tabela_usuarios.setColumnCount(6)
        self.tabela_usuarios.setHorizontalHeaderLabels([
            "ID", "Usuário", "E-mail", "Nome Completo", "Perfil", "Último Acesso"
        ])
        self.tabela_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_usuarios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_usuarios.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela_usuarios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_usuarios.doubleClicked.connect(self._editar_usuario)
        layout.addWidget(self.tabela_usuarios)

        # Barra de Ações de Usuários
        barra_acoes = QHBoxLayout()
        barra_acoes.setSpacing(8)

        btn_novo_u = QPushButton("➕ Novo Usuário")
        btn_novo_u.setStyleSheet("background: #113813; border: 1px solid #39ff14; color: #adff2f; font-weight: bold;")
        btn_novo_u.clicked.connect(self._cadastrar_novo_usuario)
        barra_acoes.addWidget(btn_novo_u)

        btn_editar_u = QPushButton("✏️ Editar")
        btn_editar_u.clicked.connect(self._editar_usuario)
        barra_acoes.addWidget(btn_editar_u)

        btn_promover = QPushButton("⭐ Promover a GM")
        btn_promover.setToolTip("Concede privilégios de Game Master ao jogador selecionado")
        btn_promover.clicked.connect(self._promover_usuario_gm)
        barra_acoes.addWidget(btn_promover)

        btn_rebaixar = QPushButton("🔽 Revogar GM")
        btn_rebaixar.setToolTip("Remove os privilégios de Game Master do usuário selecionado")
        btn_rebaixar.clicked.connect(self._rebaixar_usuario_gm)
        barra_acoes.addWidget(btn_rebaixar)

        btn_redefinir = QPushButton("🔑 Redefinir Senha")
        btn_redefinir.clicked.connect(self._redefinir_senha_usuario)
        barra_acoes.addWidget(btn_redefinir)

        btn_excluir = QPushButton("🗑️ Excluir")
        btn_excluir.setStyleSheet("background: #471515; border: 1px solid #ff4444; color: #ffcccc;")
        btn_excluir.clicked.connect(self._excluir_usuario)
        barra_acoes.addWidget(btn_excluir)

        barra_acoes.addStretch()

        btn_recarregar = QPushButton("🔄 Atualizar")
        btn_recarregar.clicked.connect(self._carregar_usuarios)
        barra_acoes.addWidget(btn_recarregar)

        layout.addLayout(barra_acoes)
        self._carregar_usuarios()

    def _obter_filtro_perfil_codigo(self) -> str:
        txt = self.combo_filtro_perfil.currentText()
        if "Game Masters" in txt:
            return "gm"
        elif "Jogadores" in txt:
            return "jogador"
        return "todos"

    def _carregar_usuarios(self):
        busca = self.input_busca_user.text().strip() or None
        filtro_p = self._obter_filtro_perfil_codigo()
        usuarios = banco.listar_usuarios(busca=busca, filtro_perfil=filtro_p)

        self.tabela_usuarios.setRowCount(len(usuarios))
        self.dados_usuarios_tabela = usuarios

        for row_idx, u in enumerate(usuarios):
            item_id = QTableWidgetItem(str(u["id"]))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_user = QTableWidgetItem(u["username"])
            item_user.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            item_email = QTableWidgetItem(u["email"])
            item_nome = QTableWidgetItem(u["nome_completo"] or "-")

            perfil_str = "👑 Game Master" if u["is_gm"] else "Sobrevivente"
            item_perfil = QTableWidgetItem(perfil_str)
            item_perfil.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if u["is_gm"]:
                item_perfil.setForeground(QColor("#39ff14"))
            else:
                item_perfil.setForeground(QColor("#a8df9e"))

            acesso_str = str(u["ultimo_login"] or u["data_cadastro"] or "-")[:16]
            item_acesso = QTableWidgetItem(acesso_str)
            item_acesso.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela_usuarios.setItem(row_idx, 0, item_id)
            self.tabela_usuarios.setItem(row_idx, 1, item_user)
            self.tabela_usuarios.setItem(row_idx, 2, item_email)
            self.tabela_usuarios.setItem(row_idx, 3, item_nome)
            self.tabela_usuarios.setItem(row_idx, 4, item_perfil)
            self.tabela_usuarios.setItem(row_idx, 5, item_acesso)

    def _obter_usuario_selecionado(self) -> Optional[Dict[str, Any]]:
        linha = self.tabela_usuarios.currentRow()
        if linha < 0 or linha >= len(self.dados_usuarios_tabela):
            QMessageBox.warning(self, "Aviso", "Selecione um usuário na tabela primeiro.")
            return None
        return self.dados_usuarios_tabela[linha]

    def _cadastrar_novo_usuario(self):
        diag = DialogCadastrarUsuarioGM(gm_executor=self.usuario_gm, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self._carregar_usuarios()
            self._carregar_logs()

    def _editar_usuario(self):
        u = self._obter_usuario_selecionado()
        if not u:
            return
        diag = DialogEditarUsuarioGM(usuario=u, gm_executor=self.usuario_gm, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self._carregar_usuarios()
            self._carregar_logs()

    def _promover_usuario_gm(self):
        usuario = self._obter_usuario_selecionado()
        if not usuario:
            return

        if usuario["is_gm"]:
            QMessageBox.information(self, "Aviso", f"O usuário '{usuario['username']}' já possui privilégios de Game Master.")
            return

        resp = QMessageBox.question(
            self, "Conceder Acesso de GM",
            f"Deseja conceder privilégios de Game Master (GM) ao usuário '{usuario['username']}'?\n\n"
            "Ele terá acesso total às ferramentas e comandos de GM via atalho CTRL+F12.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            banco.promover_usuario_a_gm(usuario["id"], gm_executor=self.usuario_gm.get("username"))
            QMessageBox.information(self, "Sucesso", f"O usuário '{usuario['username']}' foi promovido a Game Master com sucesso!")
            self._carregar_usuarios()
            self._carregar_logs()

    def _rebaixar_usuario_gm(self):
        usuario = self._obter_usuario_selecionado()
        if not usuario:
            return

        if not usuario["is_gm"]:
            QMessageBox.information(self, "Aviso", f"O usuário '{usuario['username']}' já é um jogador comum.")
            return

        if usuario["id"] == self.usuario_gm.get("id"):
            QMessageBox.warning(self, "Ação Não Permitida", "Você não pode revogar os seus próprios privilégios de GM enquanto conectado.")
            return

        resp = QMessageBox.question(
            self, "Revogar Acesso de GM",
            f"Deseja revogar os privilégios de Game Master do usuário '{usuario['username']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            banco.revogar_status_gm(usuario["id"], gm_executor=self.usuario_gm.get("username"))
            QMessageBox.information(self, "Sucesso", f"Os privilégios de Game Master do usuário '{usuario['username']}' foram revogados.")
            self._carregar_usuarios()
            self._carregar_logs()

    def _redefinir_senha_usuario(self):
        usuario = self._obter_usuario_selecionado()
        if not usuario:
            return

        nova_senha, ok = QInputDialog.getText(
            self, "Redefinir Senha",
            f"Digite a nova senha para o usuário '{usuario['username']}':\n(Mínimo de 6 caracteres, com letra e número)",
            QLineEdit.EchoMode.Password
        )
        if ok and nova_senha:
            try:
                banco.redefinir_senha(usuario["id"], nova_senha)
                banco.registrar_log_gm(
                    self.usuario_gm.get("id"),
                    "REDEFINIR_SENHA",
                    f"Senha do usuário {usuario['username']} foi redefinida pelo GM {self.usuario_gm.get('username')}."
                )
                QMessageBox.information(self, "Sucesso", f"Senha do usuário '{usuario['username']}' atualizada com sucesso!")
                self._carregar_logs()
            except ValueError as e:
                QMessageBox.critical(self, "Erro de Validação", str(e))

    def _excluir_usuario(self):
        usuario = self._obter_usuario_selecionado()
        if not usuario:
            return

        if usuario["id"] == self.usuario_gm.get("id"):
            QMessageBox.warning(self, "Ação Não Permitida", "Você não pode excluir sua própria conta enquanto conectado!")
            return

        resposta = QMessageBox.question(
            self, "Confirmar Exclusão de Usuário",
            f"Tem certeza que deseja EXCLUIR permanentemente o usuário '{usuario['username']}'?\n\n"
            "Todos os registros e speedruns associados serão removidos com integridade referencial.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            banco.excluir_usuario(usuario["id"])
            banco.registrar_log_gm(
                self.usuario_gm.get("id"),
                "EXCLUIR_USUARIO",
                f"Usuário {usuario['username']} (ID={usuario['id']}) foi excluído pelo GM {self.usuario_gm.get('username')}."
            )
            self._carregar_usuarios()
            self._carregar_dados_runs()
            self._carregar_logs()
            QMessageBox.information(self, "Sucesso", f"Usuário '{usuario['username']}' excluído com sucesso.")

    # ====================================================================
    # PILAR 2: GERENCIAMENTO DE DADOS (SPEEDRUNS)
    # ====================================================================
    def _montar_aba_dados(self):
        layout = QVBoxLayout(self.aba_dados)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Filtros de Dados
        barra_filtros = QHBoxLayout()
        barra_filtros.setSpacing(8)

        lbl_busca = QLabel("Jogador:")
        barra_filtros.addWidget(lbl_busca)

        self.input_busca_run = QLineEdit()
        self.input_busca_run.setPlaceholderText("Filtrar por nome do jogador...")
        self.input_busca_run.textChanged.connect(self._carregar_dados_runs)
        barra_filtros.addWidget(self.input_busca_run)

        lbl_categ = QLabel("Categoria:")
        barra_filtros.addWidget(lbl_categ)

        self.combo_categ_run = QComboBox()
        self.combo_categ_run.addItems(["Todas as Categorias", "Apenas Oficiais", "Apenas GM"])
        self.combo_categ_run.currentIndexChanged.connect(self._carregar_dados_runs)
        barra_filtros.addWidget(self.combo_categ_run)

        lbl_status = QLabel("Status:")
        barra_filtros.addWidget(lbl_status)

        self.combo_status_run = QComboBox()
        self.combo_status_run.addItems(["Todos os Status", "Apenas Concluídas", "Apenas Não Concluídas"])
        self.combo_status_run.currentIndexChanged.connect(self._carregar_dados_runs)
        barra_filtros.addWidget(self.combo_status_run)

        lbl_ordem = QLabel("Ordenação:")
        barra_filtros.addWidget(lbl_ordem)

        self.combo_ordem_run = QComboBox()
        self.combo_ordem_run.addItems(["Melhor Tempo", "Mais Recentes", "Mais Antigos", "Mais Inimigos"])
        self.combo_ordem_run.currentIndexChanged.connect(self._carregar_dados_runs)
        barra_filtros.addWidget(self.combo_ordem_run)

        layout.addLayout(barra_filtros)

        # Tabela de Dados
        self.tabela_speedruns = QTableWidget()
        self.tabela_speedruns.setColumnCount(7)
        self.tabela_speedruns.setHorizontalHeaderLabels([
            "ID", "Jogador", "Tempo", "Inimigos Eliminados", "Categoria", "Status", "Data"
        ])
        self.tabela_speedruns.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_speedruns.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_speedruns.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela_speedruns.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_speedruns.doubleClicked.connect(self._ver_detalhes_run)
        layout.addWidget(self.tabela_speedruns)

        # Barra de Operações CRUD
        barra_acoes = QHBoxLayout()
        barra_acoes.setSpacing(8)

        btn_novo_run = QPushButton("➕ Novo Registro")
        btn_novo_run.setStyleSheet("background: #113813; border: 1px solid #39ff14; color: #adff2f; font-weight: bold;")
        btn_novo_run.clicked.connect(self._novo_registro_run)
        barra_acoes.addWidget(btn_novo_run)

        btn_editar_run = QPushButton("✏️ Editar Registro")
        btn_editar_run.clicked.connect(self._editar_registro_run)
        barra_acoes.addWidget(btn_editar_run)

        btn_detalhes_run = QPushButton("👁️ Ver Detalhes")
        btn_detalhes_run.clicked.connect(self._ver_detalhes_run)
        barra_acoes.addWidget(btn_detalhes_run)

        btn_excluir_run = QPushButton("🗑️ Excluir Registro")
        btn_excluir_run.setStyleSheet("background: #471515; border: 1px solid #ff4444; color: #ffcccc;")
        btn_excluir_run.clicked.connect(self._excluir_registro_run)
        barra_acoes.addWidget(btn_excluir_run)

        btn_limpar_tudo = QPushButton("⚠️ Limpar Tudo")
        btn_limpar_tudo.setStyleSheet("background: #551111; border: 1px solid #ff4444; color: #ffcccc;")
        btn_limpar_tudo.clicked.connect(self._limpar_todo_leaderboard)
        barra_acoes.addWidget(btn_limpar_tudo)

        barra_acoes.addStretch()

        btn_att_runs = QPushButton("🔄 Atualizar")
        btn_att_runs.clicked.connect(self._carregar_dados_runs)
        barra_acoes.addWidget(btn_att_runs)

        layout.addLayout(barra_acoes)
        self._carregar_dados_runs()

    def _obter_filtros_runs(self):
        cat_txt = self.combo_categ_run.currentText()
        if "Oficiais" in cat_txt:
            cat = "oficial"
        elif "GM" in cat_txt:
            cat = "gm"
        else:
            cat = "todas"

        st_txt = self.combo_status_run.currentText()
        if "Concluídas" in st_txt:
            st = "concluida"
        elif "Não Concluídas" in st_txt:
            st = "falha"
        else:
            st = "todos"

        ord_txt = self.combo_ordem_run.currentText()
        if "Recentes" in ord_txt:
            ordem = "mais_recentes"
        elif "Antigos" in ord_txt:
            ordem = "mais_antigos"
        elif "Inimigos" in ord_txt:
            ordem = "mais_inimigos"
        else:
            ordem = "melhor_tempo"

        busca = self.input_busca_run.text().strip() or None
        return cat, st, ordem, busca

    def _carregar_dados_runs(self):
        cat, st, ordem, busca = self._obter_filtros_runs()
        runs = banco.listar_speedruns_detalhado(
            categoria=cat,
            status_conclusao=st,
            ordenacao=ordem,
            busca=busca,
            limite=300
        )
        self.dados_speedruns_tabela = runs
        self.tabela_speedruns.setRowCount(len(runs))

        for row_idx, r in enumerate(runs):
            item_id = QTableWidgetItem(str(r["id"]))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_user = QTableWidgetItem(r["username"])
            item_user.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            item_tempo = QTableWidgetItem(r["tempo_formatado"])
            item_tempo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tempo.setForeground(QColor("#39ff14"))
            item_tempo.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            inimigos_txt = f"{r['inimigos_derrotados']}/{r.get('total_inimigos_fase', r.get('total_inimigos', 4))}"
            item_inimigos = QTableWidgetItem(inimigos_txt)
            item_inimigos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            categ_str = "Comandos GM" if r.get("usou_gm") else "Oficial"
            item_categ = QTableWidgetItem(categ_str)
            item_categ.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r.get("usou_gm"):
                item_categ.setForeground(QColor("#ffaa44"))
            else:
                item_categ.setForeground(QColor("#39ff14"))

            st_str = "Concluída" if r.get("concluiu_jogo", 1) else "Falha / Incompleto"
            item_status = QTableWidgetItem(st_str)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r.get("concluiu_jogo", 1):
                item_status.setForeground(QColor("#77ff77"))
            else:
                item_status.setForeground(QColor("#ff6666"))

            data_str = str(r["data_registro"])[:16]
            item_data = QTableWidgetItem(data_str)
            item_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela_speedruns.setItem(row_idx, 0, item_id)
            self.tabela_speedruns.setItem(row_idx, 1, item_user)
            self.tabela_speedruns.setItem(row_idx, 2, item_tempo)
            self.tabela_speedruns.setItem(row_idx, 3, item_inimigos)
            self.tabela_speedruns.setItem(row_idx, 4, item_categ)
            self.tabela_speedruns.setItem(row_idx, 5, item_status)
            self.tabela_speedruns.setItem(row_idx, 6, item_data)

    def _obter_speedrun_selecionada(self) -> Optional[Dict[str, Any]]:
        linha = self.tabela_speedruns.currentRow()
        if linha < 0 or linha >= len(self.dados_speedruns_tabela):
            QMessageBox.warning(self, "Aviso", "Selecione uma corrida na tabela primeiro.")
            return None
        return self.dados_speedruns_tabela[linha]

    def _novo_registro_run(self):
        diag = DialogRegistroSpeedrunGM(gm_usuario=self.usuario_gm, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self._carregar_dados_runs()
            self._carregar_logs()
            if hasattr(self, "lbl_kpi_total"):
                self._carregar_relatorio()

    def _editar_registro_run(self):
        run = self._obter_speedrun_selecionada()
        if not run:
            return
        diag = DialogRegistroSpeedrunGM(gm_usuario=self.usuario_gm, run_data=run, parent=self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self._carregar_dados_runs()
            self._carregar_logs()
            if hasattr(self, "lbl_kpi_total"):
                self._carregar_relatorio()

    def _ver_detalhes_run(self):
        run = self._obter_speedrun_selecionada()
        if not run:
            return
        diag = DialogDetalhesSpeedrun(run_data=run, parent=self)
        diag.exec()

    def _excluir_registro_run(self):
        run = self._obter_speedrun_selecionada()
        if not run:
            return

        resposta = QMessageBox.question(
            self, "Confirmar Exclusão de Registro",
            f"Deseja excluir a corrida #{run['id']} do jogador '{run['username']}' ({run['tempo_formatado']})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            banco.excluir_speedrun(run["id"], gm_executor=self.usuario_gm.get("username"))
            self._carregar_dados_runs()
            self._carregar_logs()
            if hasattr(self, "lbl_kpi_total"):
                self._carregar_relatorio()
            QMessageBox.information(self, "Sucesso", f"Registro #{run['id']} excluído com sucesso.")

    def _limpar_todo_leaderboard(self):
        resposta = QMessageBox.warning(
            self, "Atenção Crítica",
            "Tem certeza que deseja APAGAR TODOS os registros de speedruns do banco de dados?\n\n"
            "Esta ação é irreversível e resetará todo o leaderboard!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            banco.limpar_ranking(gm_executor=self.usuario_gm.get("username"))
            self._carregar_dados_runs()
            self._carregar_logs()
            if hasattr(self, "lbl_kpi_total"):
                self._carregar_relatorio()
            QMessageBox.information(self, "Concluído", "Todo o histórico de corridas foi zerado.")

    # ====================================================================
    # PILAR 3: RELATÓRIOS (DA VERSÃO GAME RUNNER) COM EXPORTAÇÃO PDF E CSV
    # ====================================================================
    def _montar_aba_relatorios(self):
        layout = QVBoxLayout(self.aba_relatorios)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Painel de Cards KPIs
        frame_kpi = QFrame()
        frame_kpi.setStyleSheet("background: #101c11; border: 1px solid #234d20; border-radius: 6px; padding: 10px;")
        layout_kpi = QHBoxLayout(frame_kpi)
        layout_kpi.setSpacing(10)

        self.lbl_kpi_total = QLabel("0\nTotal de Corridas")
        self.lbl_kpi_recorde = QLabel("--:--.---\nRecorde Oficial")
        self.lbl_kpi_media = QLabel("--:--.---\nTempo Médio")
        self.lbl_kpi_conclusao = QLabel("0.0%\nTaxa de Conclusão")
        self.lbl_kpi_inimigos = QLabel("0\nMonstros Abatidos")

        for lbl, cor in [
            (self.lbl_kpi_total, "#ffffff"),
            (self.lbl_kpi_recorde, "#39ff14"),
            (self.lbl_kpi_media, "#adff2f"),
            (self.lbl_kpi_conclusao, "#77ffaa"),
            (self.lbl_kpi_inimigos, "#ffd700"),
        ]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl.setStyleSheet(f"background: #172818; border: 1px solid #285425; border-radius: 4px; padding: 8px; color: {cor};")
            layout_kpi.addWidget(lbl)

        layout.addWidget(frame_kpi)

        # Barra de Filtros do Relatório
        barra_filtros = QHBoxLayout()
        barra_filtros.setSpacing(8)

        lbl_categ = QLabel("Categoria:")
        barra_filtros.addWidget(lbl_categ)

        self.combo_rel_categ = QComboBox()
        self.combo_rel_categ.addItems(["Todas as Categorias", "Apenas Oficiais (Válidas)", "Apenas GM (Desclassificadas)"])
        self.combo_rel_categ.currentIndexChanged.connect(self._carregar_relatorio)
        barra_filtros.addWidget(self.combo_rel_categ)

        lbl_status = QLabel("Status:")
        barra_filtros.addWidget(lbl_status)

        self.combo_rel_status = QComboBox()
        self.combo_rel_status.addItems(["Todos", "Apenas Concluídas", "Apenas Não Concluídas"])
        self.combo_rel_status.currentIndexChanged.connect(self._carregar_relatorio)
        barra_filtros.addWidget(self.combo_rel_status)

        lbl_ordem = QLabel("Ordenação:")
        barra_filtros.addWidget(lbl_ordem)

        self.combo_rel_ordem = QComboBox()
        self.combo_rel_ordem.addItems(["Melhor Tempo", "Mais Recentes", "Mais Inimigos"])
        self.combo_rel_ordem.currentIndexChanged.connect(self._carregar_relatorio)
        barra_filtros.addWidget(self.combo_rel_ordem)

        btn_att_rel = QPushButton("🔄 Atualizar Relatório")
        btn_att_rel.clicked.connect(self._carregar_relatorio)
        barra_filtros.addWidget(btn_att_rel)

        layout.addLayout(barra_filtros)

        # Tabela Prévia do Relatório
        self.tabela_relatorio = QTableWidget()
        self.tabela_relatorio.setColumnCount(7)
        self.tabela_relatorio.setHorizontalHeaderLabels([
            "ID", "Jogador", "Tempo", "Inimigos", "Categoria", "Status", "Data"
        ])
        self.tabela_relatorio.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_relatorio.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_relatorio.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabela_relatorio)

        # Barra de Exportação
        barra_exportar = QHBoxLayout()
        barra_exportar.setSpacing(12)

        lbl_exp = QLabel("Exportar Dados do Relatório:")
        lbl_exp.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_exp.setStyleSheet("color: #adff2f;")
        barra_exportar.addWidget(lbl_exp)

        btn_pdf = QPushButton("📄 EXPORTAR RELATÓRIO EM PDF")
        btn_pdf.setStyleSheet("background: #8b1111; border: 1px solid #ff4444; color: #ffffff; font-weight: bold; padding: 9px 18px;")
        btn_pdf.clicked.connect(self._exportar_relatorio_pdf)
        barra_exportar.addWidget(btn_pdf)

        btn_csv = QPushButton("📊 EXPORTAR RELATÓRIO EM CSV (EXCEL)")
        btn_csv.setStyleSheet("background: #0f4f1f; border: 1px solid #39ff14; color: #ffffff; font-weight: bold; padding: 9px 18px;")
        btn_csv.clicked.connect(self._exportar_relatorio_csv)
        barra_exportar.addWidget(btn_csv)

        barra_exportar.addStretch()
        layout.addLayout(barra_exportar)

        self._carregar_relatorio()

    def _obter_filtros_relatorio_codigos(self):
        cat_txt = self.combo_rel_categ.currentText()
        if "Oficiais" in cat_txt:
            cat = "oficial"
        elif "GM" in cat_txt:
            cat = "gm"
        else:
            cat = "todas"

        st_txt = self.combo_rel_status.currentText()
        if "Concluídas" in st_txt:
            st = "concluida"
        elif "Não Concluídas" in st_txt:
            st = "falha"
        else:
            st = "todos"

        ord_txt = self.combo_rel_ordem.currentText()
        if "Recentes" in ord_txt:
            ordem = "mais_recentes"
        elif "Inimigos" in ord_txt:
            ordem = "mais_inimigos"
        else:
            ordem = "melhor_tempo"

        return cat, st, ordem

    def _carregar_relatorio(self):
        stats = banco.obter_estatisticas_gerais_speedrun()
        self.lbl_kpi_total.setText(f"{stats['total_corridas']}\nTotal de Corridas")
        self.lbl_kpi_recorde.setText(f"{stats['melhor_tempo_formatado']}\nRecorde Oficial")
        self.lbl_kpi_media.setText(f"{stats['tempo_medio_formatado']}\nTempo Médio")
        self.lbl_kpi_conclusao.setText(f"{stats['taxa_conclusao']}%\nTaxa de Conclusão")
        self.lbl_kpi_inimigos.setText(f"{stats.get('total_inimigos', 0)}\nMonstros Abatidos")

        cat, st, ordem = self._obter_filtros_relatorio_codigos()
        runs = banco.listar_speedruns_detalhado(
            categoria=cat,
            status_conclusao=st,
            ordenacao=ordem,
            limite=500
        )
        self.tabela_relatorio.setRowCount(len(runs))

        for row_idx, r in enumerate(runs):
            item_id = QTableWidgetItem(str(r["id"]))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_user = QTableWidgetItem(r["username"])
            item_tempo = QTableWidgetItem(r["tempo_formatado"])
            item_tempo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tempo.setForeground(QColor("#39ff14"))

            inimigos_txt = f"{r['inimigos_derrotados']}/{r.get('total_inimigos_fase', r.get('total_inimigos', 4))}"
            item_inimigos = QTableWidgetItem(inimigos_txt)
            item_inimigos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            categ_str = "Comandos GM" if r.get("usou_gm") else "Oficial"
            item_categ = QTableWidgetItem(categ_str)
            item_categ.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r.get("usou_gm"):
                item_categ.setForeground(QColor("#ffaa44"))
            else:
                item_categ.setForeground(QColor("#39ff14"))

            st_str = "Concluída" if r.get("concluiu_jogo", 1) else "Falha"
            item_status = QTableWidgetItem(st_str)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r.get("concluiu_jogo", 1):
                item_status.setForeground(QColor("#77ff77"))
            else:
                item_status.setForeground(QColor("#ff6666"))

            data_str = str(r["data_registro"])[:16]
            item_data = QTableWidgetItem(data_str)
            item_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela_relatorio.setItem(row_idx, 0, item_id)
            self.tabela_relatorio.setItem(row_idx, 1, item_user)
            self.tabela_relatorio.setItem(row_idx, 2, item_tempo)
            self.tabela_relatorio.setItem(row_idx, 3, item_inimigos)
            self.tabela_relatorio.setItem(row_idx, 4, item_categ)
            self.tabela_relatorio.setItem(row_idx, 5, item_status)
            self.tabela_relatorio.setItem(row_idx, 6, item_data)

    def _exportar_relatorio_pdf(self):
        cat, st, ordem = self._obter_filtros_relatorio_codigos()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sugestao = f"relatorio_speedrun_{ts}.pdf"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar Relatório Analítico em PDF",
            sugestao, "Documento PDF (*.pdf)"
        )
        if not caminho:
            return

        sucesso = gerar_relatorio_pdf(
            caminho_arquivo=caminho,
            filtro_categoria=cat,
            filtro_status=st,
            ordenacao=ordem,
            gm_solicitante=self.usuario_gm.get("username", "GM")
        )

        if sucesso:
            banco.registrar_log_gm(
                self.usuario_gm.get("id"),
                "EXPORTAR_PDF",
                f"Relatório PDF exportado para: {Path(caminho).name}"
            )
            self._carregar_logs()
            QMessageBox.information(
                self, "Relatório PDF Gerado",
                f"Relatório exportado com sucesso em formato PDF!\n\nSalvo em:\n{caminho}"
            )
        else:
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao gerar o arquivo PDF.")

    def _exportar_relatorio_csv(self):
        cat, st, ordem = self._obter_filtros_relatorio_codigos()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sugestao = f"relatorio_speedrun_{ts}.csv"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar Relatório em CSV (Excel)",
            sugestao, "Planilha CSV (*.csv)"
        )
        if not caminho:
            return

        sucesso = gerar_relatorio_csv(
            caminho_arquivo=caminho,
            filtro_categoria=cat,
            filtro_status=st,
            ordenacao=ordem
        )

        if sucesso:
            banco.registrar_log_gm(
                self.usuario_gm.get("id"),
                "EXPORTAR_CSV",
                f"Relatório CSV exportado para: {Path(caminho).name}"
            )
            self._carregar_logs()
            QMessageBox.information(
                self, "Relatório CSV Gerado",
                f"Relatório exportado com sucesso em formato CSV UTF-8 com separador padrão para Excel!\n\nSalvo em:\n{caminho}"
            )
        else:
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao exportar o arquivo CSV.")

    # ====================================================================
    # PILAR 4 & AUDITORIA: LOGS DE AUDITORIA DO GM
    # ====================================================================
    def _montar_aba_logs(self):
        layout = QVBoxLayout(self.aba_logs)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.tabela_logs = QTableWidget()
        self.tabela_logs.setColumnCount(4)
        self.tabela_logs.setHorizontalHeaderLabels([
            "Data/Hora", "Ação / Comando", "Usuário Executor", "Detalhes da Operação"
        ])
        self.tabela_logs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabela_logs.setColumnWidth(0, 160)
        self.tabela_logs.setColumnWidth(1, 180)
        self.tabela_logs.setColumnWidth(2, 140)
        self.tabela_logs.horizontalHeader().setStretchLastSection(True)
        self.tabela_logs.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_logs.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabela_logs)

        barra = QHBoxLayout()
        barra.addStretch()
        btn_att_logs = QPushButton("🔄 Atualizar Logs de Auditoria")
        btn_att_logs.clicked.connect(self._carregar_logs)
        barra.addWidget(btn_att_logs)
        layout.addLayout(barra)

        self._carregar_logs()

    def _carregar_logs(self):
        logs = banco.listar_logs_gm(limite=80)
        self.tabela_logs.setRowCount(len(logs))

        for row_idx, l in enumerate(logs):
            item_data = QTableWidgetItem(str(l["data_hora"])[:19])
            item_cmd = QTableWidgetItem(l["comando"])
            item_cmd.setForeground(QColor("#39ff14"))
            item_cmd.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            item_user = QTableWidgetItem(l["username"] or "Sistema")
            item_det = QTableWidgetItem(l["detalhes"] or "")

            self.tabela_logs.setItem(row_idx, 0, item_data)
            self.tabela_logs.setItem(row_idx, 1, item_cmd)
            self.tabela_logs.setItem(row_idx, 2, item_user)
            self.tabela_logs.setItem(row_idx, 3, item_det)

    # ====================================================================
    # PILAR 5: GUIA DE COMANDOS DE GM NO JOGO & ATALHO CTRL+F12
    # ====================================================================
    def _montar_aba_comandos_jogo(self):
        layout = QVBoxLayout(self.aba_comandos_jogo)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        info = QLabel("🎮 ATALHOS E FERRAMENTAS DO GAME MASTER (GM) DURANTE A PARTIDA")
        info.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        info.setStyleSheet("color: #39ff14;")
        layout.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        conteudo = QWidget()
        layout_conteudo = QVBoxLayout(conteudo)
        layout_conteudo.setSpacing(10)

        comandos = [
            ("CTRL+F12", "Atalho exclusivo: Abrir / Fechar Painel e Funções de GM (no menu principal e durante o jogo)"),
            ("F2", "Modo Deus (God Mode): Invencibilidade total e vida inesgotável"),
            ("F3", "Cura Total: Restaura instantaneamente 100% da sede/vida"),
            ("F4", "Insta-Kill: Elimina todos os inimigos da fase"),
            ("F5", "Teleporte: Ir para o Início / Terraço do Prédio"),
            ("F6", "Teleporte: Ir para a Chegada / Zona de Fuga no Térreo"),
            ("F7", "Coleta Total: Coleta todos os kits de cura do mapa instantaneamente"),
            ("F8", "Depurador de Hitbox: Desenha as caixas de colisão de todos os elementos"),
            ("F9", "Gerar Inimigo: Spawna um inimigo na posição atual"),
            ("F10", "Super Velocidade: Alterna velocidade padrão ou turbo 2.5x"),
            ("Clique Direito", "Teleporte Livre: Clicar com botão direito do mouse teletransporta para o local"),
        ]

        for tecla, descricao in comandos:
            linha = QFrame()
            linha.setStyleSheet("background: #142215; border: 1px solid #234d20; border-radius: 4px; padding: 6px;")
            h = QHBoxLayout(linha)

            lbl_tecla = QLabel(tecla)
            lbl_tecla.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            lbl_tecla.setStyleSheet("color: #adff2f; background: #003300; padding: 4px 8px; border-radius: 3px;")
            lbl_tecla.setFixedWidth(140)

            lbl_desc = QLabel(descricao)
            lbl_desc.setStyleSheet("color: #e2fce0; font-size: 13px;")

            h.addWidget(lbl_tecla)
            h.addWidget(lbl_desc)
            layout_conteudo.addWidget(linha)

        layout_conteudo.addStretch()
        scroll.setWidget(conteudo)
        layout.addWidget(scroll)


# Aliases para compatibilidade entre interfaces
JanelaAutenticacao = DialogLoginCadastro
JanelaRanking = DialogRanking
PainelGM = JanelaPainelGM

