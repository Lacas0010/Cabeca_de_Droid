# Segurança e Proteção Local de Dados

O **Cabeça de Droid** roda localmente e guarda cookies, banco e configurações na sua máquina. Abaixo está como esses dados são protegidos.

---

## 1. Dados sensíveis usados pelo app

1. **Cookies do HoYoLAB (`cookies.enc`):**
   - `ltuid_v2` / `account_id_v2`: ID público da conta no HoYoLAB.
   - `ltoken_v2`: token de sessão usado para ler elenco, notas diárias (Resina, Poder de Desbravamento, Bateria) e fazer check-in.
   - `cookie_token_v2`: token usado para resgate de códigos promocionais e dados web.
   - **Senhas e `stoken`:** nunca são pedidos nem gravados.

2. **Chaves privadas (`*.key` / `*.pem`):**
   - Chaves SSH usadas apenas para deploy em servidor próprio; ficam fora do Git via `.gitignore`.

> [!CAUTION]
> Mesmo sem darem acesso à troca de senha da conta HoYoverse, nunca compartilhe seus arquivos `.enc`, dumps de cookies ou chaves `.key`.

---

## 2. Como o app protege esses dados

| Proteção | Como funciona | Onde está |
| :--- | :--- | :--- |
| **Cofre criptografado** | Criptografa cookies com DPAPI no Windows (`CryptProtectData`) e AES-256 no Linux. | [`core/security.py`](core/security.py), [`security_vault.py`](security_vault.py) |
| **Mascaramento na API e UI** | O servidor nunca devolve cookies brutos para o frontend; envia só um trecho mascarado (`ltuid_v2=282***47`). | [`routers/config.py`](routers/config.py) |
| **Filtro nos logs** | Regex limpa tokens de sessão e cabeçalhos `Bearer` antes de imprimir no console ou SSE. | [`core/security.py`](core/security.py) |
| **Loopback por padrão** | O servidor sobe preso em `127.0.0.1`. Acesso na rede local (`0.0.0.0`) só liga se você ativar. | [`core/config.py`](core/config.py), [`main.py`](main.py) |
| **PIN opcional** | Trava local com hash `PBKDF2-HMAC-SHA256` (120 mil iterações e salt único) e bloqueio HTTP 423. | [`routers/security.py`](routers/security.py) |
| **Limpeza rápida** | `POST /api/security/clear_credentials` apaga todas as credenciais salvas. | [`routers/security.py`](routers/security.py) |
| **Cabeçalhos HTTP** | Bloqueia cache em rotas privadas (`Cache-Control: no-cache, no-store`) e envia `X-Content-Type-Options: nosniff`. | [`core/security.py`](core/security.py) |
| **Checks do Auto-Updater** | Só baixa releases de domínios oficiais do GitHub (`github.com`, `objects.githubusercontent.com`, `release-assets.githubusercontent.com`, `codeload.github.com`) e bloqueia ZipSlip antes de extrair. | [`updater.py`](updater.py) |

---

## 3. Arquivos ignorados no Git (`.gitignore`)

```gitignore
config.json
config.enc
cookies.json
cookies.enc
*.enc
*.enc.bak
test_*.enc
test_*.json
chave de api.txt
*.key
*.pem
*.pfx
hoyo_app.db
*.db
*.db-journal
*.db-shm
*.db-wal
*.sqlite
*.sqlite3
user_data_google/
.venv/
```

---

## 4. Se você achar que algum cookie vazou

1. Entre em [hoyolab.com](https://www.hoyolab.com), vá nas configurações da conta e clique em **Sair de Todas as Sessões** (ou troque sua senha).
2. Clique em **Limpar Credenciais** na aba de Configurações do app.
3. Se tiver vazado uma chave `.key` de servidor, gere um par SSH novo.
