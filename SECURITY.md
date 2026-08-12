#  Política de Segurança e Proteção de Dados

Este documento descreve as práticas de segurança, gestão de credenciais e privacidade de dados no aplicativo **Cabeça de Droid (v3.0)**. Como o sistema processa dados pessoais da sua conta HoYoLAB e integrações com APIs de Inteligência Artificial, é essencial entender como essas informações são tratadas localmente.

---

##  1. Gerenciamento e Armazenamento de Credenciais

### 1.1 Chaves de API de Inteligência Artificial (Groq / Gemini)
Para alimentar o **Assistente de Chat IA**, o **Otimizador de Builds IA** e o **Analisador de Sinergia de Times**, o aplicativo necessita de uma chave de API para os modelos de linguagem (Groq Cloud ou Google Gemini).

Há três maneiras seguras de configurar suas chaves:

1. **Pela Interface Web (Recomendado):**
   - Acesse a aba **Configurações** na interface web (`http://127.0.0.1:8000`).
   - Insira sua chave de API (`gsk_...` para Groq ou `AIzaSy...` para Gemini).
   - Clique em **Salvar Configurações**. Os dados serão gravados localmente no arquivo `config.json`.

2. **Arquivo Local `config.json`:**
   Você pode criar/editar diretamente o arquivo `config.json` na raiz do projeto:
   ```json
   {
       "groq_api_key": "SUA_CHAVE_GROQ_AQUI",
       "gemini_api_key": "SUA_CHAVE_GEMINI_AQUI"
   }
   ```

3. **Variáveis de Ambiente:**
   Defina a variável antes de executar a aplicação:
   - **PowerShell (Windows):** `$env:GROQ_API_KEY="gsk_..."`
   - **CMD (Windows):** `set GROQ_API_KEY=gsk_...`
   - **Linux / macOS:** `export GROQ_API_KEY="gsk_..."`

---

### 1.2 Tokens de Sessão e Cookies da HoYoLAB (`cookies.json`)
Para consultar seu roster de personagens, status de energia em tempo real (Daily Notes) e realizar o auto-check-in diário, o sistema utiliza tokens de sessão oficial da HoYoLAB (`ltuid_v2`, `ltoken_v2`, `ltuid`, `ltoken`).

* **Captura Automática via Playwright:** Na aba **Configurações**, ao clicar em **Login Automático (Navegador)**, o sistema utiliza o Playwright para abrir uma instância Chromium isolada. Você faz o login no site oficial da HoYoLAB e o sistema extrai os cookies de sessão com segurança diretamente para o arquivo `cookies.json`.
* **Inserção Manual:** Alternativamente, os cookies podem ser colados no campo bruto da aba Configurações.

> [!WARNING]  
> **Os cookies de sessão (`cookies.json`) dão acesso direto à leitura dos dados da sua conta HoYoLAB. NUNCA compartilhe esse arquivo com terceiros.**

---

##  2. Persistência de Dados Local (`hoyo_app.db` & SQLite)

- **Execução 100% Local:** O servidor backend roda exclusivamente na interface de loopback (`127.0.0.1:8000`). Nenhum dado de conta ou build é enviado para servidores externos além das chamadas oficiais da API da HoYoLAB e da API de IA configurada.
- **Banco de Dados SQLite (`hoyo_app.db`):** Armazena localmente o histórico das contas, builds de personagens, cache de notas diárias e logs de check-in efetuados.
- **Sem Necessidade de Privilégios Elevados:** O aplicativo roda em nível de usuário comum (User Level) e não exige privilégios de Administrador.

---

##  3. Proteção do `.gitignore`

Os arquivos a seguir contêm dados confidenciais ou cacheados e **DEVEM PERMANECER IGNORADOS** pelo controle de versão:

* `config.json` (Chaves de API)
* `cookies.json` (Tokens de sessão HoYoLAB)
* `hoyo_app.db` (Banco de dados SQLite local)
* `user_data_google/` e `.venv/` (Dados temporários de perfil e ambiente Python)

> [!IMPORTANT]  
> O arquivo `.gitignore` do repositório já contém todas essas regras pré-configuradas. Nunca utilize `git add -f` nesses arquivos para evitar a exposição acidental em repositórios públicos como o GitHub.

---

##  4. O que fazer em caso de vazamento de credenciais?

Se você suspeitar que suas chaves de API ou cookies foram expostos:

1. **Revogar a Chave de API:** Acesse imediatamente o painel da [Groq Cloud Console](https://console.groq.com/keys) ou do [Google AI Studio](https://aistudio.google.com/) e delete a chave comprometida.
2. **Invalidar os Cookies HoYoLAB:** Faça logout da sua conta no site oficial do [HoYoLAB](https://www.hoyolab.com) e efetue um novo login. Isso invalidará instantaneamente todos os tokens `ltoken_v2` antigos salvos localmente.
3. **Deletar os Arquivos Locais:** Remova os arquivos `config.json` e `cookies.json` da pasta do projeto e reconfigure-os.
