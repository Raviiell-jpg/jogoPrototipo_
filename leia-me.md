# Por uma Gota - Um Sertão Radioativo

Projeto Integrado de Jogo 2D com **PyQt6**, **Pygame-CE** e **Banco de Dados SQLite**.  
Desenvolvido para trabalho de conclusão de curso.

Este projeto une design e layout em resolução **1600x900**, trilha sonora dinâmica, cutscenes narrativas e spritesheets animados com banco de dados SQLite, sistema completo de cadastro/autenticação, painel e ferramentas administrativas de **Game Master (GM)** e modo competitivo de **Speedrun**.

> **Totalmente portátil**: executa a partir de qualquer diretório ou computador, sem necessidade de caminhos absolutos ou configuração prévia de servidores.

---

## 1. Instalação de Dependências

Abra o terminal na pasta do jogo e instale as dependências:

```bash
pip install -r requirements.txt
```

### Dependências Oficiais
- `pygame-ce >= 2.5.0` (ou `pygame`)
- `PyQt6 >= 6.5.0`
- `sqlite3` *(incluso nativamente na biblioteca padrão do Python)*

---

## 2. Como Iniciar o Jogo

| Modo de Execução | Comando de Terminal | Descrição |
|---|---|---|
| **Menu Principal** | `python tela_inicio.py` | Interface gráfica completa, autenticação, ranking, tutorial e cutscenes. |
| **Partida Direta** | `python main.py` | Inicia diretamente a fase de sobrevivência no edifício contaminado. |
| **Modo Speedrun** | `python main.py --modo speedrun --usuario Kaique` | Inicia com cronômetro de precisão e ranking ativo. |
| **Testes Automatizados** | `python teste_integracao.py` | Executa a suíte de testes de validação, CRUD, relatórios e física. |

---

## 3. Sistema de Cadastro e Login com Validação de Dados

O sistema possui validação estrita de campos em interface gráfica (**PyQt6**):

- **Nome de Usuário**: 3 a 20 caracteres alfanuméricos e sublinhados (`_`).
- **E-mail**: Validação de formato oficial RFC (ex: `usuario@dominio.com`).
- **Senha**: Mínimo de 6 caracteres, exigindo ao menos uma letra e um número.
- **Confirmação de Senha**: Checagem de correspondência exata.
- **Armazenamento Seguro**: Senhas protegidas com Hash **SHA-256** e Salt criptográfico aleatório.
- **Política de Permissões**: Novos cadastros **não podem** ser Game Master diretamente. Todos os novos usuários são cadastrados como Jogadores comuns. Apenas uma conta GM ativa pode promover outro usuário via painel administrativo.

### Contas Padrão Pré-configuradas no Banco (`jogo.db`)
- **Game Masters** *(Acesso exclusivo via atalho `CTRL+F12`)*:
  1. **Usuário**: `Kaique` | **Senha**: `Kaique123`
  2. **Usuário**: `Rafael` | **Senha**: `Rafael123`
- **Jogador Comum** *(Sobrevivente)*:
  - **Usuário**: `jogador` | **Senha**: `jogador123`

---

## 4. Banco de Dados SQLite (`jogo.db`)

O arquivo portátil `jogo.db` armazena os dados com integridade referencial (`PRAGMA foreign_keys = ON;`):

- **`usuarios`**: Contas cadastradas, e-mails, hashes/salts, data de cadastro e perfil (`is_gm`).
- **`speedruns`**: Histórico e leaderboards com tempo em milissegundos, abates e data.
- **`gm_logs`**: Auditoria completa de todas as ações de Game Master em tempo real.
- **`configuracoes`**: Parâmetros do sistema e controle de versão.
- **`sessao.json`**: Sessão ativa sincronizada entre o PyQt6 e o loop do Pygame.

---

## 5. Modo Speedrun e Leaderboards

- **Cronômetro de Alta Precisão**: Formato `MM:SS.mmm` em tempo real no canto superior direito.
- **Contador de Monstros**: Monitoramento em tempo real de abates e sobrevivência.
- **Fuga pelo Reservatório**: O speedrun é concluído ao atravessar a saída no subsolo.
- **Leaderboard Oficial**: Pressione `[TAB]` durante a partida ou acesse o botão **RANKING** no menu.
- **Anti-Cheat**: O uso de trapaças/comandos GM desclassifica a corrida do leaderboard oficial.

---

## 6. Ferramentas do Game Master (GM) - Atalho Exclusivo `CTRL+F12`

O atalho `[CTRL+F12]` está disponível exclusivamente para as contas GM ativas (**Kaique** e **Rafael**):
- **Se já estiver logado como GM**: abre diretamente a interface administrativa / menu de comandos.
- **Se não for GM ou não estiver logado**: exibe a tela de login. Caso tente acessar com uma conta comum, o acesso é bloqueado com a mensagem:
  > *"Você não tem acesso a essas funções!!*  
  > *Caba Safado!!!"*

### Estrutura dos 4 Pilares Funcionais

#### [Pilar 1] Gerenciamento de Usuários
- Cadastro de novos usuários diretamente pelo GM (definindo papel GM ou Jogador).
- Listagem e busca com filtros (Todos, GMs, Jogadores).
- Edição de dados cadastrais, e-mail e redefinição de senha com validações obrigatórias.
- Exclusão de usuários com integridade referencial em cascata.
- Promoção e revogação de privilégios de Game Master com auditoria.

#### [Pilar 2] Gerenciamento de Dados (Speedruns)
- Listagem com filtros combinados (Oficiais / GM, Concluídas / Falha, ordenações).
- Cadastro manual e edição de corridas (tempo em ms e monstros eliminados).
- Visualização analítica detalhada com percentuais e status.
- Exclusão pontual ou limpeza total do histórico com confirmação.

#### [Pilar 3] Relatórios do Game Runner (PDF e CSV)
- Painel de KPIs analíticos (Total de Corridas, Recorde Oficial, Tempo Médio, Taxa de Conclusão e Monstros Abatidos).
- **Exportação em PDF**: Documento A4 formatado com sumário de métricas, tabela analítica e termo de integridade.
- **Exportação em CSV**: Planilha em UTF-8 com BOM (compatível diretamente com Excel e LibreOffice Calc).

#### [Pilar 4] Banco de Dados e Auditoria
- Operações transacionais ACID com rastreabilidade total de comandos em `gm_logs`.

### Menu In-Game do GM (Pressione `CTRL+F12` durante a partida)

| Tecla de Atalho | Comando GM | Descrição |
|---|---|---|
| `[1]` ou `[F2]` | **Modo Deus (God Mode)** | Invencibilidade total contra dano e armadilhas. |
| `[2]` ou `[F3]` | **Cura Total Instantânea** | Restaura 100% da vida/saúde. |
| `[3]` ou `[F4]` | **Insta-Kill** | Elimina todos os monstros mutantes ativos na fase. |
| `[4]` ou `[F5]` | **Teleporte Topo** | Retorna imediatamente ao terraço inicial. |
| `[5]` ou `[F6]` | **Teleporte Reservatório** | Teletransporta direto para a saída no subsolo. |
| `[6]` ou `[F7]` | **Coleta Total** | Coleta todos os kits de cura e restaura a saúde. |
| `[7]` ou `[F8]` | **Depurador de Hitbox** | Exibe caixas de colisão, ataque e escudo. |
| `[8]` ou `[F10]` | **Super Velocidade (Turbo)** | Alterna entre velocidade normal e turbo (10px). |
| `[9]` ou `[F11]` | **Painel Administrativo GM** | Abre a interface completa (Usuários, Dados e Relatórios). |
| `[Botão Direito]` | **Teleporte Livre** | Move o personagem para a posição do cursor do mouse. |
| `[CTRL+F12]` / `[ESC]` | **Fechar Menu** | Fecha o menu de Game Master e retorna ao jogo. |

---

## 7. Mecânicas do Mapa: Portas, Escadas e Armadilhas

- **Portas de Segurança Blindadas**:
  - Interação com tecla `[E]`: Abre ou fecha a porta mais próxima.
  - Texturas oficiais com transparência alfa (sem fundo preto): Fechada (36x64 px) e Aberta em perfil (16x64 px).
  - Sensor anti-esmagamento: a porta não se fecha enquanto o jogador estiver no vão.
  - Bloqueio físico real para jogador e monstros.
- **Escadas Industriais**:
  - Subida (`W` / `Cima`) e Descida (`S` / `Baixo`) com suspensão de gravidade.
  - Pulo (`Espaço`) para desengatar da escada a qualquer momento.
- **Armadilhas de Teto (Lajes Desmoronando)**:
  - Tremores e poeira avisam a proximidade de queda.
  - Aceleração gravitacional com dano por esmagamento.

---

## 8. Controles do Jogador

| Ação | Teclas |
|---|---|
| **Mover para Esquerda / Direita** | `A` / `D` ou `Setas Esquerda / Direita` |
| **Pular** | `Barra de Espaço` ou `Seta Cima` *(com coyote time e buffer)* |
| **Atacar (Espada)** | `J` ou `Z` *(golpe cortante com recuo)* |
| **Defesa (Escudo)** | `K` ou `X` *(absorve 80% do dano e repele inimigos)* |
| **Subir / Descer Escadas** | `W` / `S` ou `Setas Cima / Baixo` |
| **Interagir com Portas** | Tecla `E` |
| **Ranking / Leaderboard** | Tecla `TAB` |
| **Painel de Game Master** | Atalho `CTRL+F12` *(exclusivo Kaique e Rafael)* |
| **Reiniciar Partida** | Tecla `R` *(após vitória ou derrota)* |
