# 🛡️ Política de Segurança, Proteção de Dados e Arquitetura de Sessão

Este documento descreve as práticas de segurança, gestão de credenciais, privacidade de dados e a arquitetura de proteção implementada no aplicativo **Cabeça de Droid (v4.0+)**.

---

## 🔒 1. Diagnóstico de Credenciais Sensíveis

O aplicativo opera com duas categorias de credenciais locais:

1. **Chaves de API de IA (`config.json` ou Variáveis de Ambiente):** Chaves do Groq Cloud (`gsk_...`) ou Google Gemini (`AIza...`).
2. **Tokens de Sessão da HoYoLAB (`cookies.enc`):**
   - `ltuid_v2` / `account_id_v2`: Identificador numérico público da conta HoYoLAB.
   - `ltoken_v2`: Token de sessão criptográfica concedido após login oficial. Permite consulta a diários de exploração, roster de personagens, status de resina/energia em tempo real e check-in diário.
   - `cookie_token_v2`: Token complementar necessário para resgate de códigos promocionais e interações em eventos web.

> [!WARNING]
> **Aviso Conceitual de Segurança:**
> Mesmo que esses tokens não permitam alterar diretamente a senha ou o e-mail da conta HoYoVerse (ações restritas a fluxos com `stoken` no app mobile oficial), eles devem ser tratados como **credenciais sensíveis de sessão**. O impacto exato de uma eventual exposição depende dos endpoints e serviços HoYoLAB acessíveis naquele momento e de possíveis mudanças de permissão que a HoYoverse venha a implementar no futuro.

---

## 🏗️ 2. Arquitetura de Segurança Implementada

Todas as medidas abaixo estão **ativas e implementadas no código-fonte atual**:

### 1. 🔐 Cofre Criptográfico Local (Windows DPAPI)
- **Implementação:** Módulo [security_vault.py](security_vault.py).
- **Mecanismo:** Utiliza a Windows Data Protection API (`CryptProtectData` e `CryptUnprotectData` via `ctypes.windll.crypt32`), atrelando a chave mestra de criptografia ao perfil de login do usuário do Windows no hardware atual.
- **Armazenamento em Repouso:** Os cookies são persistidos exclusivamente em formato binário criptografado em `cookies.enc` (AES-256 / HMAC-SHA256).
- **Migração Transparente:** Caso um arquivo legado em texto puro (`cookies.json`) seja detectado na inicialização, ele é automaticamente criptografado em `cookies.enc` e o arquivo legado é apagado com segurança.

### 2. 🎭 Zero-Exposure e Mascaramento de Tokens no Frontend
- **Implementação:** [server.py](server.py) e [static/app.js](static/app.js).
- **Mecanismo:** O endpoint `GET /api/config` **nunca** retorna cookies em texto claro para a interface gráfica. O backend retorna apenas um preview sanitizado (`ltuid_v2=282***47; ltoken_v2=v2_CA***JkXB; cookie_token_v2=***[PROTEGIDO]***`).
- **Buffer de Escrita Descartável:** Ao colar novos cookies na UI, o campo de texto atua exclusivamente como buffer temporário de gravação que é limpo imediatamente após o salvamento.

### 3. 🧹 Sanitização e Redação Automática de Logs em Tempo Real
- **Implementação:** Módulo [log_sanitizer.py](log_sanitizer.py).
- **Mecanismo:** Interceptor com filtros regex que mascara ocorrências de `ltoken_v2`, `cookie_token_v2`, `ltuid_v2`, `account_id`, chaves Groq (`gsk_...`), chaves Gemini (`AIzaSy...`) e headers `Bearer` antes de serem impressos no terminal ou enviados para a interface web via SSE.

### 4. 🌐 Isolamento de Rede por Padrão (Loopback 127.0.0.1)
- **Implementação:** [main.py](main.py) e [server.py](server.py).
- **Mecanismo:** O servidor inicia vinculado estritamente à interface local `127.0.0.1`, impedindo que outros dispositivos na mesma rede Wi-Fi/Ethernet acessem os endpoints ou o dashboard.
- **Controle Explícito:** O acesso por outros dispositivos (`0.0.0.0`) só é habilitado se o usuário ativar intencionalmente o toggle na aba de Configurações.

### 5. 🔑 Autenticação Local por PIN (Opcional)
- **Implementação:** [database.py](database.py), [server.py](server.py) e [static/index.html](static/index.html).
- **Mecanismo:** Permite cadastrar um PIN numérico (4 a 6 dígitos) com hash seguro derivado via `PBKDF2-HMAC-SHA256` (120.000 iterações com salt criptográfico exclusivo no SQLite).
- **Middleware Interceptor:** Quando ativo, requisições sem cookie de sessão recebem status `HTTP 423 (Locked)`, exibindo a tela de bloqueio e emitindo cookie de sessão `hoyo_session` (`HTTP-Only`, `SameSite=Strict`).

### 6. 🗑️ Limpeza Rápida de Credenciais
- **Implementação:** Endpoint `POST /api/security/clear_credentials` e botão na interface web que removem instantaneamente todos os cookies e chaves de IA armazenados no cofre.

### 7. 📖 Transparência de Dados
- **Implementação:** Tabela descritiva na aba de Configurações detalhando a finalidade e sensibilidade de cada dado, reforçando que **senhas pessoais e stoken NUNCA são solicitados ou armazenados**.

---

## ⚠️ 3. Limitações Atuais e Considerações Operacionais

Para garantir transparência técnica com os usuários e desenvolvedores, destacam-se as seguintes limitações do modelo de segurança:

1. **Escopo da Proteção DPAPI (Windows):**
   - A DPAPI protege contra extração de dados *offline* (por exemplo, copiar o arquivo `cookies.enc` para outro computador ou acessar o disco sem estar autenticado no usuário do Windows).
   - No entanto, outros processos maliciosos que estejam rodando sob a mesma conta de usuário do Windows no mesmo computador compartilham do mesmo contexto de descriptografia do sistema operacional.
2. **Uso em Rede Local (Modo LAN):**
   - Ao ativar o acesso de dispositivos móveis na rede local (`0.0.0.0`), a comunicação HTTP interna ocorre em texto claro na sua rede Wi-Fi (a menos que seja utilizado um reverse proxy com HTTPS, como Nginx ou Caddy).
   - Recomenda-se manter o **Bloqueio por PIN ativado** e utilizar apenas redes Wi-Fi privadas e confiáveis.
3. **Chaves de IA no `config.json`:**
   - As chaves de API do Groq/Gemini são mascaradas na UI e nos logs, mas permanecem armazenadas localmente para permitir o funcionamento contínuo do assistente RAG sem exigir redigitação a cada inicialização.

---

## 🛡️ 4. Regras de Proteção no Controle de Versão (`.gitignore`)

Os seguintes arquivos contêm segredos ou estado local e **permanecem rigorosamente ignorados pelo Git**:

* `config.json` e `config.enc`
* `cookies.json` e `cookies.enc`
* `hoyo_app.db`, `hoyo_app.db-wal`, `hoyo_app.db-shm`
* `user_data_google/` e `.venv/`

---

## 🚨 5. Procedimento em Caso de Suspeita de Vazamento

Caso você suspeite que seus tokens ou chaves foram expostos:

1. **Invalidar Sessões HoYoLAB:** Acesse [https://www.hoyolab.com](https://www.hoyolab.com), vá nas configurações de conta e clique em **Sair de Todas as Sessões** (ou altere sua senha HoYoVerse). Isso invalida imediatamente todos os `ltoken_v2` e `cookie_token_v2` nos servidores da miHoYo.
2. **Revogar Chaves de IA:** Delete ou gere novas chaves no painel da [Groq Console](https://console.groq.com/keys) ou [Google AI Studio](https://aistudio.google.com/).
3. **Limpar Cofre Local:** Clique no botão **Limpar Credenciais do Cofre** na aba de Configurações ou apague os arquivos `cookies.enc` e `config.json`.
