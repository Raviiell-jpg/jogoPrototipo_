"""
Biblioteca SQLite para gerenciamento de dados do jogo 'Por uma Gota'.
Gerencia usuários, autenticação com hash/salt, validação de dados,
permissões de Game Master (GM), logs de GM e rankings de Speedrun.
"""

import os
import re
import sqlite3
import secrets
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

PASTA_RAIZ = Path(__file__).resolve().parent
CAMINHO_BANCO_PADRAO = PASTA_RAIZ / "jogo.db"
CAMINHO_SESSAO = PASTA_RAIZ / "sessao.json"


# ==========================================
# FUNÇÕES DE VALIDAÇÃO DE DADOS
# ==========================================

def validar_username(username: str) -> Tuple[bool, str]:
    """
    Valida o nome de usuário:
    - 3 a 20 caracteres
    - Apenas letras, números e sublinhados (_)
    """
    if not username or not isinstance(username, str):
        return False, "O nome de usuário não pode ficar em branco."
    username = username.strip()
    if len(username) < 3 or len(username) > 20:
        return False, "O nome de usuário deve ter entre 3 e 20 caracteres."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "O nome de usuário deve conter apenas letras, números e sublinhados (_)."
    return True, ""


def validar_email(email: str) -> Tuple[bool, str]:
    """
    Valida formato de e-mail usando expressão regular padrão.
    """
    if not email or not isinstance(email, str):
        return False, "O e-mail não pode ficar em branco."
    email = email.strip()
    padrao = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(padrao, email):
        return False, "Por favor, insira um endereço de e-mail válido (ex: usuario@email.com)."
    return True, ""


def validar_senha(senha: str) -> Tuple[bool, str]:
    """
    Valida a complexidade da senha:
    - Mínimo de 6 caracteres
    - Pelo menos uma letra e um número
    """
    if not senha or not isinstance(senha, str):
        return False, "A senha não pode ficar em branco."
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    if not any(c.isalpha() for c in senha):
        return False, "A senha deve conter pelo menos uma letra."
    if not any(c.isdigit() for c in senha):
        return False, "A senha deve conter pelo menos um número."
    return True, ""


def formatar_tempo_ms(tempo_ms: int) -> str:
    """Converte milissegundos em formato MM:SS.mmm"""
    minutos = tempo_ms // 60000
    segundos = (tempo_ms % 60000) // 1000
    milis = tempo_ms % 1000
    return f"{minutos:02d}:{segundos:02d}.{milis:03d}"


def converter_para_ms(minutos: int, segundos: int, milissegundos: int) -> int:
    """Converte minutos, segundos e milissegundos para total de milissegundos."""
    return (int(minutos) * 60000) + (int(segundos) * 1000) + int(milissegundos)


def desmembrar_ms(tempo_ms: int) -> Tuple[int, int, int]:
    """Retorna tupla (minutos, segundos, milissegundos) a partir de ms."""
    tempo_ms = max(0, int(tempo_ms))
    minutos = tempo_ms // 60000
    segundos = (tempo_ms % 60000) // 1000
    milis = tempo_ms % 1000
    return minutos, segundos, milis


def validar_registro_speedrun(
    tempo_ms: int,
    *args,
    inimigos_derrotados: Optional[int] = None,
    total_inimigos: Optional[int] = None,
    **kwargs
) -> Tuple[bool, Optional[str]]:
    """
    Valida a integridade dos dados de uma corrida de speedrun:
    - Tempo deve ser positivo (> 0)
    - Valores numéricos não podem ser negativos
    - Quantidade de inimigos derrotados não pode exceder o total da fase
    """
    # Desambiguação de argumentos legados
    if len(args) >= 4:
        # Chamada antiga: moedas_coletadas, total_moedas, inimigos_derrotados, total_inimigos
        i_derr_val = args[2]
        t_inim_val = args[3]
    elif len(args) == 2:
        i_derr_val = args[0]
        t_inim_val = args[1]
    else:
        i_derr_val = inimigos_derrotados if inimigos_derrotados is not None else kwargs.get("inimigos_derrotados", 0)
        t_inim_val = total_inimigos if total_inimigos is not None else kwargs.get("total_inimigos", 4)

    try:
        t_ms = int(tempo_ms)
        i_derr = int(i_derr_val)
        t_inim = int(t_inim_val)
    except (ValueError, TypeError):
        return False, "Todos os valores numéricos devem ser números inteiros válidos."

    if t_ms <= 0:
        return False, "O tempo da corrida deve ser maior que 0 milissegundos."
    if i_derr < 0:
        return False, "O número de inimigos derrotados não pode ser negativo."
    if t_inim < 0:
        return False, "O total de inimigos da fase não pode ser negativo."
    if i_derr > t_inim:
        return False, f"Inimigos derrotados ({i_derr}) não podem exceder o total da fase ({t_inim})."

    return True, None


# ==========================================
# CLASSE PRINCIPAL DO BANCO DE DADOS
# ==========================================

class BancoDados:
    def __init__(self, caminho_banco: Optional[Path] = None):
        self.caminho = Path(caminho_banco) if caminho_banco else CAMINHO_BANCO_PADRAO
        self.inicializar_banco()

    def conectar(self) -> sqlite3.Connection:
        """Cria e retorna uma conexão com o SQLite com fábrica de linhas em dicionário."""
        conexao = sqlite3.connect(str(self.caminho))
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON;")
        return conexao

    def inicializar_banco(self):
        """Cria as tabelas necessárias e popula contas padrão caso não existam."""
        with self.conectar() as conn:
            cursor = conn.cursor()

            # Tabela de Usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    senha_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    nome_completo TEXT,
                    is_gm INTEGER NOT NULL DEFAULT 0,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_login TIMESTAMP
                );
            """)

            # Tabela de Speedruns (Registros de corridas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS speedruns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    tempo_ms INTEGER NOT NULL,
                    tempo_formatado TEXT NOT NULL,
                    inimigos_derrotados INTEGER DEFAULT 0,
                    total_inimigos INTEGER DEFAULT 0,
                    concluido INTEGER DEFAULT 1,
                    usou_gm INTEGER DEFAULT 0,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                );
            """)

            # Migração: remover colunas de moedas se ainda existirem na tabela
            try:
                cursor.execute("PRAGMA table_info(speedruns);")
                cols = [c["name"] for c in cursor.fetchall()]
                if "moedas_coletadas" in cols:
                    cursor.execute("ALTER TABLE speedruns DROP COLUMN moedas_coletadas;")
                if "total_moedas" in cols:
                    cursor.execute("ALTER TABLE speedruns DROP COLUMN total_moedas;")
            except Exception:
                pass

            # Tabela de Logs do Game Master (GM)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gm_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    comando TEXT NOT NULL,
                    detalhes TEXT,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
                );
            """)

            # Tabela de Configurações Gerais
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                );
            """)

            conn.commit()

        # Seed inicial com usuários GM e jogador padrão
        self._popular_dados_iniciais()
        self.expurgar_gms_antigos_e_configurar_padroes()

    def _gerar_hash_senha(self, senha: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Gera o salt e hash SHA-256 seguro da senha."""
        if salt is None:
            salt = secrets.token_hex(16)
        conteudo = (senha + salt).encode("utf-8")
        senha_hash = hashlib.sha256(conteudo).hexdigest()
        return senha_hash, salt

    def _popular_dados_iniciais(self):
        """Cria usuários padrão (GMs Kaique e Rafael, e jogador comum) para avaliação facilitada."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM usuarios;")
            total = cursor.fetchone()["total"]

            if total == 0:
                # 1. Usuário GM Kaique
                hash_k, salt_k = self._gerar_hash_senha("Kaique123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES (?, ?, ?, ?, ?, 1);
                """, ("Kaique", hash_k, salt_k, "kaique@sertao.com", "Kaique (Game Master)"))
                id_kaique = cursor.lastrowid

                # 2. Usuário GM Rafael
                hash_r, salt_r = self._gerar_hash_senha("Rafael123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES (?, ?, ?, ?, ?, 1);
                """, ("Rafael", hash_r, salt_r, "rafael@sertao.com", "Rafael (Game Master)"))
                id_rafael = cursor.lastrowid

                # 3. Usuário Jogador comum
                hash_jogador, salt_jogador = self._gerar_hash_senha("jogador123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES (?, ?, ?, ?, ?, 0);
                """, ("jogador", hash_jogador, salt_jogador, "jogador@sertao.com", "Sobrevivente do Sertão"))
                id_jogador = cursor.lastrowid

                # Speedruns de demonstração
                cursor.execute("""
                    INSERT INTO speedruns (usuario_id, tempo_ms, tempo_formatado, inimigos_derrotados, total_inimigos, concluido, usou_gm)
                    VALUES (?, 75420, '01:15.420', 6, 9, 1, 0);
                """, (id_kaique,))

                cursor.execute("""
                    INSERT INTO speedruns (usuario_id, tempo_ms, tempo_formatado, inimigos_derrotados, total_inimigos, concluido, usou_gm)
                    VALUES (?, 98230, '01:38.230', 4, 9, 1, 0);
                """, (id_jogador,))

                # Log inicial
                cursor.execute("""
                    INSERT INTO gm_logs (usuario_id, comando, detalhes)
                    VALUES (?, 'SISTEMA_INICIADO', 'Banco de dados inicializado com contas GM Kaique e Rafael.');
                """, (id_kaique,))

                conn.commit()

    def expurgar_gms_antigos_e_configurar_padroes(self):
        """
        Garante a exclusão de contas GM antigas (como 'admin') e estabelece
        Kaique e Rafael como os Game Masters autorizados.
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            # 1. Encontrar e remover contas GM antigas que não sejam Kaique ou Rafael (ex: 'admin')
            cursor.execute("""
                SELECT id, username FROM usuarios
                WHERE LOWER(username) = 'admin' OR (is_gm = 1 AND username NOT IN ('Kaique', 'Rafael'));
            """)
            antigos = cursor.fetchall()
            for r in antigos:
                uid = r["id"]
                cursor.execute("DELETE FROM speedruns WHERE usuario_id = ?;", (uid,))
                cursor.execute("DELETE FROM gm_logs WHERE usuario_id = ?;", (uid,))
                cursor.execute("DELETE FROM usuarios WHERE id = ?;", (uid,))

            # 2. Assegurar conta Kaique como GM
            cursor.execute("SELECT id FROM usuarios WHERE username = 'Kaique';")
            row_k = cursor.fetchone()
            if not row_k:
                h_k, s_k = self._gerar_hash_senha("Kaique123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES ('Kaique', ?, ?, 'kaique@sertao.com', 'Kaique (Game Master)', 1);
                """, (h_k, s_k))
            else:
                cursor.execute("UPDATE usuarios SET is_gm = 1 WHERE username = 'Kaique';")

            # 3. Assegurar conta Rafael como GM
            cursor.execute("SELECT id FROM usuarios WHERE username = 'Rafael';")
            row_r = cursor.fetchone()
            if not row_r:
                h_r, s_r = self._gerar_hash_senha("Rafael123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES ('Rafael', ?, ?, 'rafael@sertao.com', 'Rafael (Game Master)', 1);
                """, (h_r, s_r))
            else:
                cursor.execute("UPDATE usuarios SET is_gm = 1 WHERE username = 'Rafael';")

            # 4. Assegurar jogador comum
            cursor.execute("SELECT id FROM usuarios WHERE username = 'jogador';")
            row_j = cursor.fetchone()
            if not row_j:
                h_j, s_j = self._gerar_hash_senha("jogador123")
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                    VALUES ('jogador', ?, ?, 'jogador@sertao.com', 'Sobrevivente do Sertão', 0);
                """, (h_j, s_j))

            conn.commit()

    # ==========================================
    # GERENCIAMENTO DE USUÁRIOS & AUTENTICAÇÃO
    # ==========================================

    def cadastrar_usuario(
        self,
        username: str,
        senha: str,
        email: str,
        nome_completo: str = "",
        is_gm: bool = False,
    ) -> Dict[str, Any]:
        """
        Valida e cadastra um novo usuário no banco de dados SQLite.
        Regra de segurança: Novos usuários NÃO podem ser cadastrados diretamente como GM.
        O status de GM é concedido exclusivamente por outro GM ativo via painel administrativo.
        """
        username = (username or "").strip()
        email = (email or "").strip().lower()
        nome_completo = (nome_completo or "").strip()

        # Validações
        valido_u, msg_u = validar_username(username)
        if not valido_u:
            raise ValueError(msg_u)

        valido_e, msg_e = validar_email(email)
        if not valido_e:
            raise ValueError(msg_e)

        valido_s, msg_s = validar_senha(senha)
        if not valido_s:
            raise ValueError(msg_s)

        # Checar duplicidade antes de inserir
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, email FROM usuarios WHERE username = ? OR email = ?;", (username, email))
            existente = cursor.fetchone()
            if existente:
                if existente["username"].lower() == username.lower():
                    raise ValueError(f"O nome de usuário '{username}' já está em uso. Escolha outro.")
                if existente["email"].lower() == email.lower():
                    raise ValueError(f"O e-mail '{email}' já está cadastrado em outra conta.")

            # Garantia mandatória: novos cadastros são SEMPRE jogadores comuns (is_gm = 0)
            is_gm_final = 0

            senha_hash, salt = self._gerar_hash_senha(senha)
            cursor.execute("""
                INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (username, senha_hash, salt, email, nome_completo, is_gm_final))
            novo_id = cursor.lastrowid
            conn.commit()

        return {
            "id": novo_id,
            "username": username,
            "email": email,
            "nome_completo": nome_completo,
            "is_gm": False
        }

    def autenticar_usuario(self, login_identificador: str, senha: str) -> Optional[Dict[str, Any]]:
        """
        Autentica o usuário por username ou por e-mail.
        Retorna o dicionário de dados do usuário autenticado ou None se inválido.
        """
        login_identificador = (login_identificador or "").strip()
        if not login_identificador or not senha:
            return None

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, senha_hash, salt, email, nome_completo, is_gm
                FROM usuarios
                WHERE username = ? OR email = ?;
            """, (login_identificador, login_identificador.lower()))
            usuario = cursor.fetchone()

            if not usuario:
                return None

            # Valida hash com o salt armazenado
            hash_calculado, _ = self._gerar_hash_senha(senha, usuario["salt"])
            if hash_calculado != usuario["senha_hash"]:
                return None

            # Atualiza data/hora do último login
            cursor.execute("""
                UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = ?;
            """, (usuario["id"],))
            conn.commit()

            return {
                "id": usuario["id"],
                "username": usuario["username"],
                "email": usuario["email"],
                "nome_completo": usuario["nome_completo"] or usuario["username"],
                "is_gm": bool(usuario["is_gm"])
            }

    def obter_usuario_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo ID."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, nome_completo, is_gm, data_cadastro, ultimo_login
                FROM usuarios WHERE id = ?;
            """, (usuario_id,))
            u = cursor.fetchone()
            if u:
                return dict(u)
            return None

    def obter_usuario_por_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo nome de usuário."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, nome_completo, is_gm, data_cadastro, ultimo_login
                FROM usuarios WHERE username = ?;
            """, (username,))
            u = cursor.fetchone()
            if u:
                return dict(u)
            return None

    def listar_usuarios(self, busca: str = "", filtro_perfil: str = "todos") -> List[Dict[str, Any]]:
        """
        Lista usuários com suporte a filtro textual (username, email, nome)
        e filtro por perfil ('todos', 'gm', 'jogador').
        """
        clausulas = []
        params = []

        if busca:
            termo = f"%{busca.strip()}%"
            clausulas.append("(username LIKE ? OR email LIKE ? OR nome_completo LIKE ?)")
            params.extend([termo, termo, termo])

        if filtro_perfil == "gm":
            clausulas.append("is_gm = 1")
        elif filtro_perfil == "jogador":
            clausulas.append("is_gm = 0")

        where_sql = ("WHERE " + " AND ".join(clausulas)) if clausulas else ""
        sql = f"""
            SELECT id, username, email, nome_completo, is_gm, data_cadastro, ultimo_login
            FROM usuarios
            {where_sql}
            ORDER BY id ASC;
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def cadastrar_usuario_gm(
        self,
        username: str,
        senha: str,
        email: str,
        nome_completo: str = "",
        is_gm: bool = False,
        gm_executor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cadastro administrativo executado diretamente por um GM no painel.
        Permite definir se o usuário é Jogador ou GM e registra a auditoria.
        """
        username = (username or "").strip()
        email = (email or "").strip().lower()
        nome_completo = (nome_completo or "").strip()

        valido_u, msg_u = validar_username(username)
        if not valido_u:
            raise ValueError(msg_u)

        valido_e, msg_e = validar_email(email)
        if not valido_e:
            raise ValueError(msg_e)

        valido_s, msg_s = validar_senha(senha)
        if not valido_s:
            raise ValueError(msg_s)

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, email FROM usuarios WHERE username = ? OR email = ?;", (username, email))
            existente = cursor.fetchone()
            if existente:
                if existente["username"].lower() == username.lower():
                    raise ValueError(f"O nome de usuário '{username}' já está em uso.")
                if existente["email"].lower() == email.lower():
                    raise ValueError(f"O e-mail '{email}' já está cadastrado em outra conta.")

            senha_hash, salt = self._gerar_hash_senha(senha)
            cursor.execute("""
                INSERT INTO usuarios (username, senha_hash, salt, email, nome_completo, is_gm)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (username, senha_hash, salt, email, nome_completo, 1 if is_gm else 0))
            novo_id = cursor.lastrowid
            conn.commit()

        if gm_executor:
            tipo_cad = "Game Master (GM)" if is_gm else "Jogador"
            self.registrar_acao_gm(
                gm_executor,
                "CADASTRAR_USUARIO_GM",
                f"Usuário {username} (ID={novo_id}) cadastrado pelo GM como {tipo_cad}."
            )

        return {
            "id": novo_id,
            "username": username,
            "email": email,
            "nome_completo": nome_completo,
            "is_gm": bool(is_gm)
        }

    def atualizar_usuario(
        self,
        usuario_id: int,
        nome_completo: str,
        email: str,
        is_gm: bool,
        nova_senha: Optional[str] = None,
        gm_executor: Optional[str] = None
    ) -> bool:
        """
        Edição dos dados cadastrais de um usuário pelo Game Master com validação estrita.
        """
        usuario_atual = self.obter_usuario_por_id(usuario_id)
        if not usuario_atual:
            raise ValueError(f"Usuário com ID {usuario_id} não encontrado.")

        email = (email or "").strip().lower()
        nome_completo = (nome_completo or "").strip()

        valido_e, msg_e = validar_email(email)
        if not valido_e:
            raise ValueError(msg_e)

        with self.conectar() as conn:
            cursor = conn.cursor()
            # Verificar se o e-mail já pertence a outro usuário
            cursor.execute("SELECT id, username FROM usuarios WHERE email = ? AND id != ?;", (email, usuario_id))
            dup = cursor.fetchone()
            if dup:
                raise ValueError(f"O e-mail '{email}' já pertence ao usuário '{dup['username']}'.")

            if nova_senha:
                valido_s, msg_s = validar_senha(nova_senha)
                if not valido_s:
                    raise ValueError(msg_s)
                senha_hash, salt = self._gerar_hash_senha(nova_senha)
                cursor.execute("""
                    UPDATE usuarios
                    SET nome_completo = ?, email = ?, is_gm = ?, senha_hash = ?, salt = ?
                    WHERE id = ?;
                """, (nome_completo, email, 1 if is_gm else 0, senha_hash, salt, usuario_id))
            else:
                cursor.execute("""
                    UPDATE usuarios
                    SET nome_completo = ?, email = ?, is_gm = ?
                    WHERE id = ?;
                """, (nome_completo, email, 1 if is_gm else 0, usuario_id))

            conn.commit()

        if gm_executor:
            tipo_cad = "GM" if is_gm else "Jogador"
            detalhe = f"Dados de {usuario_atual['username']} (ID={usuario_id}) alterados: Nome='{nome_completo}', Email='{email}', Perfil={tipo_cad}"
            if nova_senha:
                detalhe += ", Senha redefinida"
            self.registrar_acao_gm(gm_executor, "EDITAR_USUARIO", detalhe)

        return True

    def alterar_status_gm(self, usuario_id: int, novo_status_gm: bool) -> bool:
        """Promove ou rebaixa um usuário como Game Master (GM)."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios SET is_gm = ? WHERE id = ?;
            """, (1 if novo_status_gm else 0, usuario_id))
            conn.commit()
            return cursor.rowcount > 0

    def promover_usuario_a_gm(self, usuario_id: int, gm_executor: Optional[str] = None) -> bool:
        """
        Função exclusiva para uma conta GM conceder privilégios de Game Master a outro usuário.
        Registra auditoria em gm_logs.
        """
        sucesso = self.alterar_status_gm(usuario_id, True)
        if sucesso and gm_executor:
            u = self.obter_usuario_por_id(usuario_id)
            nome_alvo = u["username"] if u else f"ID {usuario_id}"
            self.registrar_acao_gm(gm_executor, "PROMOVER_GM", f"Usuário {nome_alvo} (ID={usuario_id}) promovido a Game Master.")
        return sucesso

    def revogar_status_gm(self, usuario_id: int, gm_executor: Optional[str] = None) -> bool:
        """
        Remove privilégios de Game Master de um usuário.
        Registra auditoria em gm_logs.
        """
        sucesso = self.alterar_status_gm(usuario_id, False)
        if sucesso and gm_executor:
            u = self.obter_usuario_por_id(usuario_id)
            nome_alvo = u["username"] if u else f"ID {usuario_id}"
            self.registrar_acao_gm(gm_executor, "REVOGAR_GM", f"Privilégios de GM do usuário {nome_alvo} (ID={usuario_id}) revogados.")
        return sucesso

    def redefinir_senha(self, usuario_id: int, nova_senha: str) -> bool:
        """Redefine a senha de um usuário existente com validação."""
        valida, msg = validar_senha(nova_senha)
        if not valida:
            raise ValueError(msg)

        senha_hash, salt = self._gerar_hash_senha(nova_senha)
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios SET senha_hash = ?, salt = ? WHERE id = ?;
            """, (senha_hash, salt, usuario_id))
            conn.commit()
            return cursor.rowcount > 0

    def excluir_usuario(self, usuario_id: int) -> bool:
        """Exclui um usuário e seus dados associados em cascata."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?;", (usuario_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================
    # REGISTROS DE SPEEDRUN & LEADERBOARD
    # ==========================================

    def registrar_speedrun(
        self,
        usuario_id: int,
        tempo_ms: int,
        *args,
        inimigos_derrotados: Optional[int] = None,
        total_inimigos: Optional[int] = None,
        concluido: bool = True,
        usou_gm: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Salva o resultado de uma corrida de Speedrun.
        Retorna os detalhes e se bateu recorde pessoal.
        """
        if len(args) >= 4:
            i_derr = args[2]
            t_inim = args[3]
        elif len(args) == 2:
            i_derr = args[0]
            t_inim = args[1]
        else:
            i_derr = inimigos_derrotados if inimigos_derrotados is not None else kwargs.get("inimigos_derrotados", 0)
            t_inim = total_inimigos if total_inimigos is not None else kwargs.get("total_inimigos", 4)

        tempo_formatado = formatar_tempo_ms(tempo_ms)

        with self.conectar() as conn:
            cursor = conn.cursor()

            # Checar recorde anterior
            cursor.execute("""
                SELECT MIN(tempo_ms) as melhor_tempo
                FROM speedruns
                WHERE usuario_id = ? AND concluido = 1 AND usou_gm = 0;
            """, (usuario_id,))
            row = cursor.fetchone()
            melhor_anterior = row["melhor_tempo"] if row and row["melhor_tempo"] is not None else None

            novo_recorde = False
            if concluido and not usou_gm:
                if melhor_anterior is None or tempo_ms < melhor_anterior:
                    novo_recorde = True

            cursor.execute("""
                INSERT INTO speedruns (
                    usuario_id, tempo_ms, tempo_formatado,
                    inimigos_derrotados, total_inimigos, concluido, usou_gm
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                usuario_id, tempo_ms, tempo_formatado,
                i_derr, t_inim,
                1 if concluido else 0, 1 if usou_gm else 0
            ))
            speedrun_id = cursor.lastrowid
            conn.commit()

        return {
            "id": speedrun_id,
            "tempo_ms": tempo_ms,
            "tempo_formatado": tempo_formatado,
            "inimigos_derrotados": i_derr,
            "total_inimigos": t_inim,
            "novo_recorde_pessoal": novo_recorde,
            "usou_gm": usou_gm
        }

    def obter_ranking(self, limite: int = 15, apenas_legitimos: bool = True) -> List[Dict[str, Any]]:
        """
        Retorna a tabela de classificação (Leaderboard) de Speedruns.
        Se apenas_legitimos=True, exclui tentativas onde foram ativados recursos de GM.
        """
        filtro_gm = "AND s.usou_gm = 0" if apenas_legitimos else ""
        sql = f"""
            SELECT 
                s.id,
                u.username,
                s.tempo_ms,
                s.tempo_formatado,
                s.inimigos_derrotados,
                s.total_inimigos,
                s.usou_gm,
                s.data_registro
            FROM speedruns s
            JOIN usuarios u ON u.id = s.usuario_id
            WHERE s.concluido = 1 {filtro_gm}
            ORDER BY s.tempo_ms ASC
            LIMIT ?;
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (limite,))
            resultados = []
            for posicao, row in enumerate(cursor.fetchall(), start=1):
                item = dict(row)
                item["posicao"] = posicao
                resultados.append(item)
            return resultados

    def obter_melhor_tempo_usuario(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """Retorna o melhor tempo registrado de um usuário específico."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tempo_ms, tempo_formatado, data_registro
                FROM speedruns
                WHERE usuario_id = ? AND concluido = 1 AND usou_gm = 0
                ORDER BY tempo_ms ASC
                LIMIT 1;
            """, (usuario_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def excluir_speedrun(self, speedrun_id: int, gm_executor: Optional[str] = None) -> bool:
        """Exclui um registro de speedrun específico."""
        speedrun = self.obter_speedrun_por_id(speedrun_id)
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM speedruns WHERE id = ?;", (speedrun_id,))
            conn.commit()
            sucesso = cursor.rowcount > 0

        if sucesso and gm_executor and speedrun:
            self.registrar_acao_gm(
                gm_executor,
                "EXCLUIR_SPEEDRUN",
                f"Registro ID {speedrun_id} do usuário '{speedrun.get('username')}' ({speedrun.get('tempo_formatado')}) foi excluído pelo GM."
            )

        return sucesso

    def obter_speedrun_por_id(self, speedrun_id: int) -> Optional[Dict[str, Any]]:
        """Busca um registro de speedrun por ID com dados do usuário associado."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.id, s.usuario_id, u.username, u.email,
                    s.tempo_ms, s.tempo_formatado,
                    s.inimigos_derrotados, s.total_inimigos,
                    s.concluido, s.usou_gm, s.data_registro
                FROM speedruns s
                JOIN usuarios u ON u.id = s.usuario_id
                WHERE s.id = ?;
            """, (speedrun_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def cadastrar_speedrun_manual(
        self,
        usuario_id: int,
        tempo_ms: int,
        *args,
        inimigos_derrotados: Optional[int] = None,
        total_inimigos: Optional[int] = None,
        concluido: bool = True,
        usou_gm: bool = False,
        gm_executor: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Insere manualmente um registro de speedrun com validações de consistência.
        """
        if len(args) >= 4:
            i_derr = args[2]
            t_inim = args[3]
        elif len(args) == 2:
            i_derr = args[0]
            t_inim = args[1]
        else:
            i_derr = inimigos_derrotados if inimigos_derrotados is not None else kwargs.get("inimigos_derrotados", 0)
            t_inim = total_inimigos if total_inimigos is not None else kwargs.get("total_inimigos", 4)

        valido, msg = validar_registro_speedrun(
            tempo_ms=tempo_ms, inimigos_derrotados=i_derr, total_inimigos=t_inim
        )
        if not valido:
            raise ValueError(msg)

        u = self.obter_usuario_por_id(usuario_id)
        if not u:
            raise ValueError(f"Usuário ID {usuario_id} não existe.")

        res = self.registrar_speedrun(
            usuario_id=usuario_id,
            tempo_ms=tempo_ms,
            inimigos_derrotados=i_derr,
            total_inimigos=t_inim,
            concluido=concluido,
            usou_gm=usou_gm
        )

        if gm_executor:
            self.registrar_acao_gm(
                gm_executor,
                "CADASTRAR_SPEEDRUN",
                f"Novo registro inserido para {u['username']} (Tempo: {res['tempo_formatado']}, GM={usou_gm})"
            )

        return res

    def atualizar_speedrun(
        self,
        speedrun_id: int,
        tempo_ms: int,
        *args,
        inimigos_derrotados: Optional[int] = None,
        total_inimigos: Optional[int] = None,
        concluido: bool = True,
        usou_gm: bool = False,
        gm_executor: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Atualiza dados de uma corrida de speedrun com validações rigorosas.
        """
        if len(args) >= 4:
            i_derr = args[2]
            t_inim = args[3]
        elif len(args) == 2:
            i_derr = args[0]
            t_inim = args[1]
        else:
            i_derr = inimigos_derrotados if inimigos_derrotados is not None else kwargs.get("inimigos_derrotados", 0)
            t_inim = total_inimigos if total_inimigos is not None else kwargs.get("total_inimigos", 4)

        valido, msg = validar_registro_speedrun(
            tempo_ms=tempo_ms, inimigos_derrotados=i_derr, total_inimigos=t_inim
        )
        if not valido:
            raise ValueError(msg)

        atual = self.obter_speedrun_por_id(speedrun_id)
        if not atual:
            raise ValueError(f"Registro de speedrun com ID {speedrun_id} não encontrado.")

        tempo_formatado = formatar_tempo_ms(tempo_ms)
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE speedruns
                SET tempo_ms = ?, tempo_formatado = ?,
                    inimigos_derrotados = ?, total_inimigos = ?,
                    concluido = ?, usou_gm = ?
                WHERE id = ?;
            """, (
                tempo_ms, tempo_formatado,
                i_derr, t_inim,
                1 if concluido else 0, 1 if usou_gm else 0,
                speedrun_id
            ))
            conn.commit()

        if gm_executor:
            self.registrar_acao_gm(
                gm_executor,
                "EDITAR_SPEEDRUN",
                f"Speedrun ID {speedrun_id} do usuário {atual['username']} atualizado: Novo tempo {tempo_formatado}, Inimigos {i_derr}/{t_inim}, GM={usou_gm}"
            )

        return True

    def listar_speedruns_detalhado(
        self,
        usuario_id: Optional[int] = None,
        categoria: str = "todas",
        status_conclusao: str = "todos",
        ordenacao: str = "tempo_asc",
        busca: str = "",
        limite: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Consulta avançada de speedruns com múltiplos filtros combinados e ordenação.
        """
        clausulas = []
        params = []

        if usuario_id is not None and int(usuario_id) > 0:
            clausulas.append("s.usuario_id = ?")
            params.append(int(usuario_id))

        if categoria == "oficial":
            clausulas.append("s.usou_gm = 0")
        elif categoria == "gm":
            clausulas.append("s.usou_gm = 1")

        if status_conclusao in ("concluido", "concluida"):
            clausulas.append("s.concluido = 1")
        elif status_conclusao in ("falha", "incompleto"):
            clausulas.append("s.concluido = 0")

        if busca:
            termo = f"%{busca.strip()}%"
            clausulas.append("(u.username LIKE ? OR s.tempo_formatado LIKE ? OR s.data_registro LIKE ?)")
            params.extend([termo, termo, termo])

        where_sql = ("WHERE " + " AND ".join(clausulas)) if clausulas else ""

        mapa_ordem = {
            "melhor_tempo": "s.tempo_ms ASC",
            "tempo_asc": "s.tempo_ms ASC",
            "tempo_desc": "s.tempo_ms DESC",
            "mais_recentes": "s.data_registro DESC, s.id DESC",
            "data_desc": "s.data_registro DESC, s.id DESC",
            "mais_antigos": "s.data_registro ASC, s.id ASC",
            "data_asc": "s.data_registro ASC, s.id ASC",
            "inimigos_desc": "s.inimigos_derrotados DESC, s.tempo_ms ASC",
            "mais_inimigos": "s.inimigos_derrotados DESC, s.tempo_ms ASC"
        }
        ordem_sql = mapa_ordem.get(ordenacao, "s.tempo_ms ASC")
        limite_sql = f" LIMIT {int(limite)}" if limite and int(limite) > 0 else ""

        sql = f"""
            SELECT 
                s.id,
                s.usuario_id,
                u.username,
                u.email,
                s.tempo_ms,
                s.tempo_formatado,
                s.inimigos_derrotados,
                s.total_inimigos,
                s.concluido,
                s.usou_gm,
                s.data_registro
            FROM speedruns s
            JOIN usuarios u ON u.id = s.usuario_id
            {where_sql}
            ORDER BY {ordem_sql}{limite_sql};
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            linhas = []
            for pos, r in enumerate(cursor.fetchall(), start=1):
                item = dict(r)
                item["posicao"] = pos
                linhas.append(item)
            return linhas

    def obter_estatisticas_gerais_speedrun(self) -> Dict[str, Any]:
        """
        Retorna estatísticas analíticas consolidadas para o módulo de relatórios.
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_corridas,
                    COUNT(DISTINCT usuario_id) as total_jogadores,
                    SUM(CASE WHEN concluido = 1 THEN 1 ELSE 0 END) as total_concluidas,
                    SUM(CASE WHEN usou_gm = 0 THEN 1 ELSE 0 END) as total_oficiais,
                    SUM(CASE WHEN usou_gm = 1 THEN 1 ELSE 0 END) as total_gm,
                    MIN(CASE WHEN concluido = 1 AND usou_gm = 0 THEN tempo_ms ELSE NULL END) as melhor_tempo_oficial,
                    AVG(CASE WHEN concluido = 1 THEN tempo_ms ELSE NULL END) as media_tempo_ms,
                    SUM(inimigos_derrotados) as total_inimigos
                FROM speedruns;
            """)
            r = cursor.fetchone()

            total_corridas = r["total_corridas"] or 0
            total_concluidas = r["total_concluidas"] or 0
            taxa_conclusao = (total_concluidas / total_corridas * 100) if total_corridas > 0 else 0.0

            melhor_ms = r["melhor_tempo_oficial"]
            media_ms = int(r["media_tempo_ms"]) if r["media_tempo_ms"] is not None else 0

            return {
                "total_corridas": total_corridas,
                "total_jogadores": r["total_jogadores"] or 0,
                "total_concluidas": total_concluidas,
                "total_oficiais": r["total_oficiais"] or 0,
                "total_gm": r["total_gm"] or 0,
                "melhor_tempo_oficial_ms": melhor_ms,
                "melhor_tempo_ms": melhor_ms,
                "melhor_tempo_oficial_formatado": formatar_tempo_ms(melhor_ms) if melhor_ms else "--:--.---",
                "melhor_tempo_formatado": formatar_tempo_ms(melhor_ms) if melhor_ms else "--:--.---",
                "media_tempo_ms": media_ms,
                "tempo_medio_ms": media_ms,
                "media_tempo_formatado": formatar_tempo_ms(media_ms) if media_ms > 0 else "--:--.---",
                "tempo_medio_formatado": formatar_tempo_ms(media_ms) if media_ms > 0 else "--:--.---",
                "taxa_conclusao_pct": round(taxa_conclusao, 1),
                "taxa_conclusao": round(taxa_conclusao, 1),
                "total_inimigos": r["total_inimigos"] or 0,
            }

    def limpar_ranking(self, gm_executor: Optional[str] = None) -> bool:
        """Limpa todos os registros de speedrun (ação de GM)."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM speedruns;")
            conn.commit()

        if gm_executor:
            self.registrar_acao_gm(
                gm_executor,
                "LIMPAR_LEADERBOARD",
                "Todo o leaderboard e histórico de speedruns foi zerado pelo GM."
            )
        return True

    # ==========================================
    # LOGS DE ATIVIDADE DO GAME MASTER (GM)
    # ==========================================

    def registrar_log_gm(self, usuario_id: Optional[int], comando: str, detalhes: str = ""):
        """Grava log de execução de comando ou ação de Game Master."""
        try:
            with self.conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO gm_logs (usuario_id, comando, detalhes)
                    VALUES (?, ?, ?);
                """, (usuario_id, comando, detalhes))
                conn.commit()
        except Exception as e:
            print(f"Erro ao registrar log de GM: {e}")

    def listar_logs_gm(self, limite: int = 50) -> List[Dict[str, Any]]:
        """Retorna os logs mais recentes de ações do Game Master."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.id, l.comando, l.detalhes, l.data_hora, u.username
                FROM gm_logs l
                LEFT JOIN usuarios u ON u.id = l.usuario_id
                ORDER BY l.id DESC
                LIMIT ?;
            """, (limite,))
            return [dict(row) for row in cursor.fetchall()]

    # ==========================================
    # CONTROLE DE SESSÃO ATIVA (COMPARTILHADA)
    # ==========================================

    @staticmethod
    def salvar_sessao_ativa(usuario: Optional[Dict[str, Any]], modo: str = "normal"):
        """Salva a sessão do usuário atual para sincronizar entre telas e o jogo."""
        dados = {
            "usuario": usuario,
            "modo": modo,
            "horario": datetime.now().isoformat()
        }
        try:
            with open(CAMINHO_SESSAO, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar sessao.json: {e}")

    @staticmethod
    def carregar_sessao_ativa() -> Tuple[Optional[Dict[str, Any]], str]:
        """Carrega o usuário e modo da sessão atual."""
        if not CAMINHO_SESSAO.exists():
            return None, "normal"
        try:
            with open(CAMINHO_SESSAO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados.get("usuario"), dados.get("modo", "normal")
        except Exception:
            return None, "normal"

    @staticmethod
    def limpar_sessao_ativa():
        """Desloga o usuário apagando a sessão."""
        if CAMINHO_SESSAO.exists():
            try:
                CAMINHO_SESSAO.unlink()
            except Exception:
                pass

    # ==========================================
    # MÉTODOS DE CONVENIÊNCIA / ALIASES
    # ==========================================

    def obter_sessao_atual(self) -> Optional[Dict[str, Any]]:
        """Retorna os dados normalizados da sessão atual."""
        u, _ = self.carregar_sessao_ativa()
        if not u:
            return None
        return {
            "id": u.get("id"),
            "usuario": u.get("username"),
            "username": u.get("username"),
            "email": u.get("email"),
            "papel": "gm" if u.get("is_gm") else "jogador",
            "is_gm": bool(u.get("is_gm")),
            "nome_completo": u.get("nome_completo")
        }

    def encerrar_sessao(self):
        """Alias para limpar_sessao_ativa."""
        self.limpar_sessao_ativa()

    def obter_usuario_por_nome(self, username: str) -> Optional[Dict[str, Any]]:
        """Retorna o usuário normalizado por nome."""
        u = self.obter_usuario_por_username(username)
        if not u:
            return None
        return {
            "id": u.get("id"),
            "usuario": u.get("username"),
            "username": u.get("username"),
            "email": u.get("email"),
            "papel": "gm" if u.get("is_gm") else "jogador",
            "is_gm": bool(u.get("is_gm")),
            "nome_completo": u.get("nome_completo")
        }

    def obter_recorde_pessoal(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """Retorna o melhor tempo de speedrun do usuário."""
        return self.obter_melhor_tempo_usuario(usuario_id)

    def registrar_acao_gm(self, usuario_gm: str, acao: str, detalhes: str = ""):
        """Registra log de comando de Game Master."""
        u = self.obter_usuario_por_username(usuario_gm)
        uid = u["id"] if u else None
        texto_detalhes = f"[{usuario_gm}] {detalhes}" if detalhes else f"Ação executada por {usuario_gm}"
        self.registrar_log_gm(usuario_id=uid, comando=acao, detalhes=texto_detalhes)



# Instância global para facilitar importação direta
banco = BancoDados()


# ==========================================
# TESTE / CLI QUANDO EXECUTADO DIRETAMENTE
# ==========================================
if __name__ == "__main__":
    print("=== Testando Banco de Dados SQLite do Jogo 'Por uma Gota' ===")
    bd = BancoDados()
    print(f"Banco conectado em: {bd.caminho}")

    usuarios = bd.listar_usuarios()
    print(f"Usuários encontrados ({len(usuarios)}):")
    for u in usuarios:
        tipo = "GM / Administrador" if u["is_gm"] else "Jogador Comum"
        print(f" - [{u['id']}] {u['username']} ({u['email']}) -> {tipo}")

    ranking = bd.obter_ranking()
    print(f"\nLeaderboard Speedrun ({len(ranking)} recordes):")
    for r in ranking:
        print(f" #{r['posicao']} - {r['username']}: {r['tempo_formatado']} (Abates: {r.get('inimigos_derrotados', 0)})")
