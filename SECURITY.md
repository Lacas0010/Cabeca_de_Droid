# 🛡️ Política de Segurança e Proteção de Dados

Este documento descreve as práticas de segurança recomendadas e as diretrizes para configuração de credenciais no projeto **Cabeça de Droid**. Como o aplicativo processa informações pessoais da conta HoYoLAB e chaves de API de serviços de Inteligência Artificial, é fundamental seguir estas práticas para proteger seus dados.

---

## 🔑 1. Como Configurar Suas Chaves de API

Para utilizar o Assistente de Chat IA com RAG, você precisa de uma chave de API para o modelo de linguagem (por padrão, Groq ou Gemini). Há três formas seguras de configurar suas chaves:

### Método A: Pela Interface Web (Recomendado)
1. Inicie a aplicação executando `python main.py`.
2. Acesse a interface web em `http://127.0.0.1:8000`.
3. Navegue até o painel de **Configurações**.
4. Insira a sua chave da Groq ou Gemini nos campos indicados e salve. A aplicação gravará os dados localmente de forma segura.

### Método B: Arquivo de Configuração Local (`config.json`)
Você pode criar ou editar o arquivo [config.json](file:///c:/Users/07049770108/Documents/hoyo-projetos/config.json) na raiz do projeto. O arquivo deve ter a seguinte estrutura:

```json
{
    "groq_api_key": "SUA_CHAVE_AQUI",
    "gemini_api_key": "SUA_CHAVE_AQUI"
}
```

> [!NOTE]  
> Caso utilize apenas um dos serviços, você pode deixar a outra chave vazia ou omitir o campo. O RAG prioriza a chave da Groq, fazendo fallback para Gemini se configurado.

### Método C: Variáveis de Ambiente
Você também pode definir a chave de API diretamente no seu sistema operacional ou terminal antes de rodar o aplicativo:

* **Windows (PowerShell):**
  ```powershell
  $env:GROQ_API_KEY="gsk_..."
  ```
* **Windows (Prompt de Comando):**
  ```cmd
  set GROQ_API_KEY=gsk_...
  ```
* **Linux / macOS:**
  ```bash
  export GROQ_API_KEY="gsk_..."
  ```

---

## ⚠️ 2. Proteção do Arquivo `config.json` e `.gitignore`

O arquivo [config.json](file:///c:/Users/07049770108/Documents/hoyo-projetos/config.json) armazena credenciais confidenciais em texto puro para que a aplicação possa consumi-las localmente. 

> [!IMPORTANT]  
> O arquivo [config.json](file:///c:/Users/07049770108/Documents/hoyo-projetos/config.json) **DEVE** constar no arquivo [.gitignore](file:///c:/Users/07049770108/Documents/hoyo-projetos/.gitignore).

* O repositório já vem pré-configurado com a regra `config.json` e `cookies.json` no arquivo [.gitignore](file:///c:/Users/07049770108/Documents/hoyo-projetos/.gitignore).
* **Nunca** remova essas entradas do seu arquivo `.gitignore`.
* Evite utilizar comandos como `git add -f` ou `git commit -a` de forma indiscriminada, para prevenir o envio acidental de arquivos ignorados para repositórios públicos (como o GitHub).

---

## 🚫 3. Nunca Compartilhe Cookies ou Credenciais

Para sincronizar o seu roster de personagens, o aplicativo armazena tokens de sessão no arquivo `cookies.json`.

> [!WARNING]  
> **Os cookies de sessão (`cookies.json`) contêm tokens que dão acesso direto à sua conta do HoYoLAB.**

### Diretrizes Críticas:
* **Não compartilhe ou envie o arquivo `cookies.json` ou `config.json`** em fóruns públicos, Discord, issues do GitHub ou para outros desenvolvedores.
* Se precisar enviar logs de erro ou capturas de tela para suporte, **certifique-se de ocultar ou apagar** qualquer chave de API (`gsk_...`, `AIzaSy...`) ou tokens de cookies expostos no terminal ou nos arquivos de texto.
* Se desconfiar que suas credenciais ou cookies foram expostos:
  1. **Revogue a chave de API** imediatamente nos painéis da Groq ou do Google AI Studio.
  2. **Faça logout da sua conta** no site oficial do HoYoLAB e realize o login novamente. Isso invalidará imediatamente todos os tokens de sessão antigos salvos localmente no `cookies.json`.
