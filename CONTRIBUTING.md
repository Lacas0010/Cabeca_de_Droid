# Guia de Contribuição

Valeu pelo interesse em ajudar no **Cabeça de Droid**. Aqui está o básico de como o projeto está organizado e das regras que mantemos no código.

---

## 1. Regras do projeto

- **Privacidade local:** Tokens e cookies não vão para serviços de terceiros. Ficam criptografados em disco (DPAPI no Windows, AES-256 no Linux) e nunca aparecem sem máscara (`mask_token`) em logs ou respostas HTTP.
- **Testes offline:** Toda mudança precisa manter a suíte passando (`python -m unittest discover tests`). Chamadas externas (HoYoLAB, Prydwen, GitHub Releases) devem ser mockadas com `unittest.mock.patch`.
- **Sem misturar lógica no router:** `routers/` só valida entrada/saída com os modelos de `schemas/` e chama `services/`.
- **Sem dados de jogo hardcoded em Python:** Listas de personagens, tier lists, multiplicadores ou materiais não ficam hardcoded em dicionários Python. Devem ser puxados pelos scrapers para os JSONs em `static_data/`.
- **Banco e performance:** Evite `SELECT *` em tabelas grandes e use paginação (`LIMIT ? OFFSET ?`) em históricos.
- **Funcionamento offline:** O frontend precisa continuar carregando sem internet usando os arquivos locais de `static_data/` e `static/vendor/sakuga-vfx/`.

---

## 2. Subindo o ambiente local

```bash
git clone https://github.com/Lacas0010/Cabeca_de_Droid.git
cd Cabeca_de_Droid

python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux / macOS:      source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

---

## 3. Onde cada coisa fica

```text
hoyo-projetos/
├── core/                    # Config, caminhos (%APPDATA% / MEIPASS), tray e segurança
├── calculators/             # Cálculos de gacha, breakpoints de status e lacunas de conta
├── schemas/                 # Modelos Pydantic v2
├── services/                # Regras de negócio, cálculo de RV, gacha, sync e ciclo de vida
├── routers/                 # Rotas FastAPI
├── static_data/             # Cache local em JSON gerado pelos scrapers
├── static/                  # SPA Vanilla (HTML5, CSS3, ES6+ e Sakuga VFX)
│   ├── vendor/sakuga-vfx/   # 11 Web Components locais
│   ├── js/app.js            # Ponto de entrada do frontend
│   ├── js/modules/          # Módulos ES6
│   ├── css/                 # Folhas modulares
│   ├── style.css            # Variáveis :root e layout principal
│   └── index.html           # Página principal
├── assets/                  # Ícones oficiais, elementos e banners
├── scrapers/                # Coleta de guias e banners (Prydwen, Genshin, HSR, ZZZ)
├── scripts/                 # Helpers, Nginx e serviço systemd
├── tests/                   # Testes unitários offline (unittest)
├── .github/workflows/       # Build e release Windows via GitHub Actions
├── build.py                 # Gera .exe e Cabeca_de_Droid-Windows-x64.zip
├── version.py               # Versão atual do app
├── updater.py               # Checagem de releases e atualização do .exe no Windows
├── server.py                # App FastAPI e hooks de inicialização
└── main.py                  # Ponto de entrada CLI / desktop
```

---

## 4. Padrões de código

1. **Python:** Use type hints, `schemas/` nos endpoints, `HTTPException` com status coerente e `mask_token` ao logar dados sensíveis.
2. **Frontend (Vanilla JS/CSS):**
   - Sem React, Vue ou Tailwind.
   - Reaproveite os componentes em `static/vendor/sakuga-vfx/`.
   - Mantenha modais abaixo de `canvas.sakuga-fx` (`z-index < 2147483000`) e não quebre o scroll interno de modais nem do `#build-inspector`.
   - Ao editar CSS ou JS em `static/`, atualize o `?v=` correspondente em `static/index.html` e `static/js/app.js`.
   - Mantenha estilos responsivos para celular (`<= 768px`) usando as variáveis `:root`.
3. **Horários de virada de banner (`database.get_banner_schedule_time`):**
   - **Término da 1ª fase / chegada da 2ª fase (`phase=2`):** Genshin `20:00`, HSR `14:00`, ZZZ `14:00`
   - **Término da 2ª fase ou Patch Inteiro / chegada de nova atualização (`phase=1`):** `23:30` nos 3 jogos
4. **Releases:** Só crie tag/release (`v*.*.*`) quando solicitado. No dia a dia, acumule as mudanças normalmente na `main`.

---

## 5. Rodando os testes

```bash
# Suíte completa
python -m unittest discover tests

# Arquivos específicos
python -m unittest tests.test_security_vault_suite
python -m unittest tests.test_updater_suite
python -m unittest tests.test_packaging_suite
```

---

## 6. Padrão de commits e PR

Use [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/) (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).

Checklist antes de abrir PR:
- [ ] `python -m unittest discover tests` passa sem erros.
- [ ] Testado no desktop e no mobile (`<= 768px`).
- [ ] Nenhum arquivo de credencial (`config.json`, `cookies.enc`, `*.key`, `*.db`) entrou no commit.
- [ ] Documentação atualizada se houver mudança visível.
