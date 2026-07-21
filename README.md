# 🎮 HoYo AI Assistant (Groq RAG Local)

Uma ferramenta de desktop moderna com interface gráfica premium desenvolvida em Python (**CustomTkinter**) projetada para sincronizar rosters de personagens e recordes de Endgames via HoYoLAB, coletar guias analíticos de builds, tier lists e estatísticas do meta (KeqingMains, Prydwen, Game8), e rodar um **Assistente de Chat IA com RAG local integrado** usando a ultra-rápida API da Groq (Llama 3.3).

---

## 🌟 Principais Recursos e Interface (UI/UX)

- **📊 Mini-Dashboards da Conta:** Exibição em tempo real de estatísticas do jogador (UID, Nível da Conta, Total de Personagens e Personagens 5★/Rank S) no topo da tela de cada jogo.
- **📁 Acesso Rápido a Arquivos:** Botão integrado `📁 Pasta (.md)` para abrir a pasta local do jogo diretamente no Windows Explorer.
- **⚡ Status & Barra de Progresso Real (Porcentagem Flutuante):** Barra de progresso `determinate` precisa (0% a 100%) durante downloads e sincronizações de guias.
- **🔀 Rodapé de Logs Isolado por Aba:** Suporte completo a execuções simultâneas em segundo plano. Cada jogo mantém seu próprio indicador e histórico de logs técnicos no rodapé.
- **🛠️ Modo Dev / Painel Retrátil de Logs:** Console escuro em estilo terminal colapsável para inspecionar erros e chamadas HTTP sem poluir a interface do usuário final.
- **🔔 Notificações Toast Flutuantes:** Avisos suaves no canto superior direito informando quando extrações são concluídas.
- **🔑 Validação Inteligente no Chat IA:** Alerta automático no chat caso a chave da Groq não esteja configurada, oferecendo botão de atalho em 1-clique para as Configurações.

---

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Aparência Dark Premium)
- **Modelos de IA e RAG:** Integração oficial com a `groq` (Llama 3.3 70B Versatile).
- **API HoYoLAB:** [genshin.py](https://github.com/seriaati/genshin.py) com suporte a Endgames estendidos (3 times no MoC / Shiyu / Abismo).
- **Coleta de Dados:** BeautifulSoup4 & Requests HTTP resilientes com estratégias de retry automático.
- **Autenticação:** [Playwright](https://playwright.dev/) para captura automatizada e segura de cookies HoYoLAB.
- **Empacotamento:** [PyInstaller](https://pyinstaller.org/) configurado para gerar executáveis autônomos (`.exe` em 1 arquivo só).

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada que inicializa os caminhos de navegadores e inicia a aplicação.
- `gui.py`: Gerenciamento do layout CustomTkinter, navegação por abas e orquestração de threads.
- `status_logger.py`: Componente modular de feedback visual (`StatusLoggerFrame`) com barra de progresso, status amigável e console retrátil dev.
- `groq_rag.py`: Módulo RAG que carrega chaves, consolida e indexa dinamicamente arquivos Markdown locais como contexto para a IA da Groq (Coach de Endgame).
- `auth.py`: Autenticação via navegador do Playwright para capturar os cookies oficiais da sua conta HoYoLAB.
- `extractor.py` & `endgame_extractor.py`: Extratores de Roster e Endgames da API do HoYoLAB.
- `scraper_kqm.py`, `scraper_genshin_meta.py`: Módulos de sincronização de guias e meta para Genshin Impact (KQM e Game8).
- `scraper_prydwen.py`, `scraper_meta.py`: Módulos de sincronização para Honkai: Star Rail (Prydwen).
- `scraper_zzz.py`: Módulos de sincronização para Zenless Zone Zero (Prydwen).

---

## 🚀 Instalação e Execução (Desenvolvimento)

### 1. Criar Ambiente Virtual e Instalar Dependências
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Instalar o Navegador do Playwright
```bash
playwright install chromium
```

### 3. Executar o Aplicativo
```bash
python main.py
```

---

## 📦 Gerando o Executável Autônomo (.exe)

Para compilar o aplicativo completo em um único arquivo `.exe` portátil para distribuição:

```bash
pyinstaller --noconfirm --onefile --windowed --name "HoYoAssistant" --add-data "assets;assets" --collect-all customtkinter --collect-all playwright main.py
```
O executável final será gerado dentro da pasta `dist/HoYoAssistant.exe`.

---

## 🔒 Segurança e Privacidade
Todos os cookies (`cookies.json`), chaves de API (`config.json`) e arquivos markdown gerados são armazenados **exclusivamente no seu computador**. O app é 100% user-level e não requer privilégios de Administrador no Windows.
