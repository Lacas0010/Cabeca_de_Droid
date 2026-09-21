# 🛡️ Política de Segurança, Proteção de Dados e Arquitetura de Sessão

Este documento descreve as práticas de segurança, gestão de credenciais, privacidade de dados e o **Plano de Blindagem de Tokens e Sessões** no aplicativo **Cabeça de Droid (v4.0+)**.

---

## 🔒 1. Diagnóstico do Modelo Atual e Credenciais Sensíveis

O aplicativo opera com duas categorias críticas de credenciais:
1. **Chaves de API de IA (`config.json` ou Variáveis de Ambiente):** Chaves da Groq Cloud (`gsk_...`) ou Google Gemini (`AIza...`).
2. **Tokens de Sessão da HoYoLAB (`cookies.json`):**
   - `ltuid_v2` / `account_id_v2`: Identificador numérico público da conta HoYoLAB.
   - `ltoken_v2`: Token de sessão criptográfica concedido após login oficial. Permite consulta a diários de exploração, roster de personagens, status de resina/energia em tempo real e auto-check-in.
   - `cookie_token_v2`: Token complementar necessário para resgate de códigos promocionais e interações em eventos web.

> [!WARNING]  
> Embora os tokens `ltoken_v2` **não permitam a troca de senha ou alteração de e-mail da conta miHoYo** (funções restritas a `stoken` no aplicativo mobile oficial), eles concedem acesso de leitura e automação à conta no HoYoLAB. Seu tratamento deve seguir padrões rigorosos de segurança defensiva.

---

## 🏗️ 2. Os 7 Pilares de Segurança para Sessões e Cookies (Roadmap & Arquitetura)

### 1. 🔐 Criptografia Local dos Tokens em Repouso
- **Problema:** O arquivo `cookies.json` é salvo em texto puro JSON. Caso um malware ou usuário local leia o arquivo, os tokens ficam legíveis.
- **Solução Arquitetural:** 
  - Utilizar criptografia simétrica autenticada (**AES-256-GCM** ou **Fernet**) para gravar o payload no disco (`cookies.enc`).
  - Derivar uma chave criptográfica única combinando entropia da máquina (Machine GUID / Hardware ID) com sal criptográfico via PBKDF2/Argon2.

### 2. 🗄️ Armazenamento Seguro Nativo no Sistema Operacional
- **Problema:** Chaves gravadas em arquivos locais podem ser migradas ou lidas por outros processos do mesmo usuário sem isolamento do SO.
- **Solução Arquitetural:**
  - **Windows:** Integração com **Windows DPAPI** (`CryptProtectData` e `CryptUnprotectData` via `ctypes` ou biblioteca `cryptography`), atrelando a chave mestra exclusivamente à credencial de login do usuário logado no Windows.
  - **Multiplataforma (Linux / macOS):** Integração com **Keyring** (`keyring` / `SecretStorage` no Linux via D-Bus Secret Service e **Keychain** no macOS).

### 3. 🧹 Limpeza e Sanitização Automática de Logs Sensíveis
- **Problema:** `print()`, stack traces (`traceback.print_exc()`) e endpoints de monitoramento (`sync_status["logs"]`) podem despejar acidentalmente headers HTTP ou respostas de requisição com cookies.
- **Solução Arquitetural:**
  - **Log Filter Middleware:** Interceptor central de logs que aplica expressões regulares de mascaramento (Redaction):
    - `(ltoken(?:_v2)?=)[^;,\s&]+` ➔ `ltoken_v2=v2_***[REDACTED]***`
    - `(ltuid(?:_v2)?=)[^;,\s&]+` ➔ `ltuid_v2=***[REDACTED]***`
    - `(gsk_[a-zA-Z0-9]{20,})` ➔ `gsk_***[REDACTED]***`
  - Sanitização obrigatória antes de persistir em `database.py` ou enviar via SSE / WebSockets.

### 4. 🎭 Mascaramento de Cookies no Frontend (Zero-Exposure no DOM)
- **Problema:** O endpoint `GET /api/config` retornava a string inteira de cookies em texto puro para preencher o `<textarea>` do frontend.
- **Solução Arquitetural:**
  - O backend **nunca mais envia o token completo** na resposta da API.
  - A API retorna um objeto sanitizado:
    ```json
    {
      "has_cookies": true,
      "valid": true,
      "accounts": [
        {
          "uid_masked": "12***456",
          "nickname": "Desbravador",
          "ltoken_preview": "v2_a9***c3"
        }
      ]
    }
    ```
  - Ao inserir manualmente novos cookies, o frontend envia via `POST /api/auth/manual_cookies`, o backend valida, encripta e responde com confirmação de sucesso sem refletir o segredo no HTML.

### 5. 🌐 Isolamento de Rede e Proteção Contra Dispositivos na LAN
- **Problema:** `uvicorn.run(host="0.0.0.0")` disponibiliza o servidor e todas as APIs administrativas em todas as interfaces de rede locais sem senha.
- **Solução Arquitetural:**
  - **Binding Seguro Padrão:** O backend inicia vinculado estritamente ao Loopback (`127.0.0.1` / `localhost`).
  - **Modo LAN Opcional:** Se o usuário optar conscientemente por liberar acesso para celular na rede Wi-Fi (`0.0.0.0`):
    - Requer autenticação por token de cabeçalho ou PIN.
    - Endpoints de alto risco (`/api/config`, `/api/auth/*`, `/api/reset-data`) passam a exigir verificação de origem loopback ou cabeçalho `X-Local-Secret`.
    - Restrição de CORS: Substituição de `allow_origins=["*"]` por origens locais estritas.

### 6. 🔑 Autenticação Local Opcional (PIN / Master Password)
- **Problema:** Qualquer pessoa com acesso físico ao computador pode abrir o navegador e visualizar detalhes das contas ou alterar rotinas.
- **Solução Arquitetural:**
  - Criação de bloqueio local por PIN de 4 a 6 dígitos ou Master Password.
  - Hash com salt gerado com **Argon2id** ou **PBKDF2-HMAC-SHA256** gravado no SQLite.
  - Emissão de cookie de sessão HTTP-Only (`SameSite=Strict`, `Path=/`) com token efêmero JWT de curta duração (ex: 2 horas de inatividade).

### 7. 📖 Transparência e Explicação Clara do que é Armazenado
- **Problema:** Usuários podem temer que o app armazene senhas de login ou dados bancários/faturamento.
- **Solução Arquitetural:**
  - Inclusão do painel **"Transparência e Privacidade de Dados"** na interface web.
  - Dicionário claro detalhando o propósito de cada item:

| Dado Armazenado | Finalidade | Nível de Risco | Onde é Salvo |
| :--- | :--- | :--- | :--- |
| `ltuid_v2` / `account_id` | Identificar o usuário no ecossistema HoYoLAB | Público / Baixo | `cookies.enc` / SQLite |
| `ltoken_v2` | Consultar perfil, relíquias, diários e notas de resina | Sensível (Sessão de Leitura) | DPAPI / `cookies.enc` |
| `cookie_token_v2` | Efetuar resgate de códigos promocionais | Sensível (Web Token) | DPAPI / `cookies.enc` |
| `groq_api_key` / `gemini_api_key` | Realizar prompts de IA (Builds, Chats e Análises) | Privado | `config.json` / DPAPI |
| `hoyo_app.db` | Histórico de evolução, builds e scores calculados | Não sensível (Dados de Jogo) | SQLite Local |

> [!NOTE]
> O aplicativo **NUNCA** coleta, armazena ou solicita sua senha pessoal da HoYoVerse nem o token mestre `stoken`. O login pelo Playwright é executado diretamente na página oficial `https://www.hoyolab.com`, sem que o aplicativo intercepte teclas digitadas (Keylogging).

---

## 🛡️ 3. Regras de Proteção no Controle de Versão (`.gitignore`)

Os seguintes arquivos contêm credenciais ou estado local e **permanecem ignorados por padrão**:
* `config.json` e `config.enc`
* `cookies.json` e `cookies.enc`
* `hoyo_app.db`, `hoyo_app.db-wal`, `hoyo_app.db-shm`
* `user_data_google/` e `.venv/`

---

## 🚨 4. Procedimento em Caso de Suspeita de Vazamento

1. **Invalidar Sessões HoYoLAB:** Acesse `https://www.hoyolab.com`, acesse as configurações de conta e clique em **Sair de Todas as Sessões** (ou altere sua senha HoYoVerse). Todos os `ltoken_v2` e `cookie_token_v2` salvos localmente serão imediatamente revogados nos servidores da miHoYo.
2. **Revogar Chaves de IA:** Delete as chaves no painel da [Groq Console](https://console.groq.com/keys) ou [Google AI Studio](https://aistudio.google.com/).
3. **Limpar Arquivos Locais:** Remova os arquivos `config.json`, `cookies.json` ou clique no botão **Resetar Todos os Dados** na interface web.
