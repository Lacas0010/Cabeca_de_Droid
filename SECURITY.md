# 🛡️ Política de Segurança e Governança de Dados

Este documento descreve as práticas de segurança, gestão de credenciais locais, privacidade e a arquitetura de proteção implementada no **Cabeça de Droid (v5.0+)**.

---

## 🔒 1. Tratamento de Credenciais Sensíveis

O aplicativo opera estritamente de forma **local** com duas categorias de dados:

1. **Tokens de Sessão da HoYoLAB (`cookies.enc`):**
   - `ltuid_v2` / `account_id_v2`: Identificador público da conta no HoYoLAB.
   - `ltoken_v2`: Token de sessão para leitura de Roster, notas diárias (resina/energia) e check-in.
   - `cookie_token_v2`: Token para resgate de códigos promocionais e dados web.
   - **Senhas e `stoken`:** **NUNCA** solicitados, interceptados ou armazenados.

2. **Chaves de API de IA (`config.enc` / `config.json`):**
   - Chaves do Groq Cloud (`gsk_...`) para alimentação do motor RAG local.

> [!CAUTION]
> Mesmo que esses cookies não permitam alteração de senha da sua conta HoYoverse, trate seus arquivos `.enc` como credenciais privadas. Nunca compartilhe dumps de cookies ou seus arquivos cifrados em repositórios públicos.

---

## 🏗️ 2. Medidas de Proteção Implementadas

| Camada de Segurança | Mecanismo Implementado | Arquivo / Módulo |
| :--- | :--- | :--- |
| **1. Cofre Criptográfico DPAPI** | Criptografia em repouso no Windows (`CryptProtectData` via `ctypes.windll.crypt32`) e AES-256 no Linux. | [`core/security.py`](core/security.py) / [`security_vault.py`](security_vault.py) |
| **2. Zero-Exposure no Frontend** | O servidor **nunca** devolve cookies em texto claro para a UI; envia apenas previews mascarados (`ltuid_v2=282***47`). | [`routers/config.py`](routers/config.py) |
| **3. Sanitização de Logs em Tempo Real** | Filtro regex que censura automaticamente tokens, chaves `gsk_` e cabeçalhos `Bearer` antes da saída no terminal/SSE. | [`core/security.py`](core/security.py) |
| **4. Isolamento Loopback Padrão** | Servidor inicia vinculado a `127.0.0.1`. Acesso via rede local (`0.0.0.0`) exige ativação explícita pelo usuário. | [`core/config.py`](core/config.py) / [`main.py`](main.py) |
| **5. Bloqueio Local por PIN** | Proteção por PIN com hash `PBKDF2-HMAC-SHA256` (120.000 iterações com salt individual) e bloqueio HTTP 423. | [`routers/security.py`](routers/security.py) |
| **6. Purga Instantânea de Dados** | Endpoint `POST /api/security/clear_credentials` para exclusão imediata e permanente de todas as credenciais do cofre. | [`routers/security.py`](routers/security.py) |

---

## 🛡️ 3. Regras de Exclusão no Git (`.gitignore`)

Os seguintes arquivos são permanentemente ignorados pelo controle de versão para impedir qualquer vazamento acidental:

```gitignore
config.json
config.enc
cookies.json
cookies.enc
*.enc
*.key
*.pem
hoyo_app.db
hoyo_app.db-wal
hoyo_app.db-shm
user_data_google/
.venv/
```

---

## 🚨 4. Procedimento em Caso de Suspeita de Exposição

Se suspeitar que seus tokens foram expostos:
1. **Invalidar Sessões HoYoLAB:** Acesse [hoyolab.com](https://www.hoyolab.com), vá em configurações de conta e clique em **Sair de Todas as Sessões** (ou altere sua senha HoYoVerse).
2. **Revogar Chaves de IA:** Gere novas chaves no painel da [Groq Console](https://console.groq.com/keys).
3. **Limpar Cofre Local:** Clique no botão **Limpar Credenciais** na aba de Configurações do app.
