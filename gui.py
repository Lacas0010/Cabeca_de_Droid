import os
import json
import asyncio
import threading
import traceback
import customtkinter as ctk
from auth import capturar_cookies_hoyolab
from extractor import HSRExtractor
from scraper_prydwen import PrydwenScraper
from scraper_meta import PrydwenMetaScraper

# Configurações de Aparência do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração da janela
        self.title("HSR Roster Extractor & Prydwen Scraper")
        self.geometry("580x480")
        self.resizable(False, False)
        self.center_window(580, 480)
        
        # Estado do app
        self.cookies = {}
        self.cookie_file = "cookies.json"
        self.scraper = PrydwenScraper()
        self.character_list = []
        
        # Título Principal
        self.title_label = ctk.CTkLabel(
            self, 
            text="HSR Roster Extractor para NotebookLM", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 2))
        
        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Exporte dados do HoYoLAB e guias de builds do Prydwen.gg",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A3A3A3"
        )
        self.subtitle_label.pack(pady=(0, 10))
        
        # CTkTabview para separar as seções
        self.tab_view = ctk.CTkTabview(self, corner_radius=12)
        self.tab_view.pack(padx=25, pady=(5, 5), fill="both", expand=True)
        
        self.tab_hoyolab = self.tab_view.add("HoYoLAB Extractor")
        self.tab_prydwen = self.tab_view.add("Prydwen Scraper")
        self.tab_notebooklm = self.tab_view.add("NotebookLM Sync")
        
        # --- ABA 1: HoYoLAB Extractor ---
        self.setup_hoyolab_tab()
        
        # --- ABA 2: Prydwen Scraper ---
        self.setup_prydwen_tab()
        
        # --- ABA 3: NotebookLM Sync ---
        self.setup_notebooklm_tab()
        
        # Barra de Progresso (compartilhada, oculta por padrão no rodapé)
        self.progress_bar = ctk.CTkProgressBar(self, height=6, corner_radius=3)
        self.progress_bar.set(0)
        
        # Label de Status (Rodapé compartilhado)
        self.status_label = ctk.CTkLabel(
            self, 
            text="Pronto. Inicializando...", 
            font=ctk.CTkFont(family="Segoe UI", size=12), 
            text_color="#A1A1AA"
        )
        self.status_label.pack(pady=(10, 15))
        
        # Inicializações de background
        self.carregar_cookies_salvos()
        self.start_load_chars_thread()
        
    def center_window(self, width: int, height: int):
        """Centraliza a janela na tela do usuário."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    # ==========================================
    # LOGICA DA ABA 1: HOYOLAB EXTRACTOR
    # ==========================================
    
    def setup_hoyolab_tab(self):
        # Container Central
        self.hoyolab_frame = ctk.CTkFrame(self.tab_hoyolab, corner_radius=12, fg_color="#18181B")
        self.hoyolab_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.hoyolab_frame.grid_columnconfigure(0, weight=1)
        self.hoyolab_frame.grid_columnconfigure(1, weight=1)
        self.hoyolab_frame.grid_rowconfigure((0, 1, 2), weight=1)
        
        # --- COLUNA 1: Login ---
        self.step1_label = ctk.CTkLabel(
            self.hoyolab_frame,
            text="1. Autenticação",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7"
        )
        self.step1_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.login_btn = ctk.CTkButton(
            self.hoyolab_frame,
            text="Fazer Login no HoYoLAB",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42,
            corner_radius=8,
            command=self.start_login_thread
        )
        self.login_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.auth_indicator = ctk.CTkLabel(
            self.hoyolab_frame,
            text="🔒 Não Conectado",
            text_color="#EF4444",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.auth_indicator.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
        
        # --- COLUNA 2: Exportação ---
        self.step2_label = ctk.CTkLabel(
            self.hoyolab_frame,
            text="2. Geração do Relatório",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7"
        )
        self.step2_label.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        
        self.generate_btn = ctk.CTkButton(
            self.hoyolab_frame,
            text="Gerar Arquivo Markdown",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42,
            corner_radius=8,
            state="disabled",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.start_generate_thread
        )
        self.generate_btn.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        
        self.file_indicator = ctk.CTkLabel(
            self.hoyolab_frame,
            text="📄 Relatório não gerado",
            text_color="#71717A",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.file_indicator.grid(row=2, column=1, padx=20, pady=(0, 20), sticky="w")
        
    def carregar_cookies_salvos(self):
        """Carrega cookies salvos localmente na raiz do projeto se existirem."""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                
                has_v2 = "ltuid_v2" in cookies and "ltoken_v2" in cookies
                has_v1 = "ltuid" in cookies and "ltoken" in cookies
                if has_v2 or has_v1:
                    self.cookies = cookies
                    self.auth_indicator.configure(text="✅ Autenticado (cookies.json)", text_color="#10B981")
                    self.generate_btn.configure(state="normal")
                    self.status_label.configure(text="Cookies carregados de cookies.json. Pronto para extrair.", text_color="#10B981")
            except Exception as e:
                print(f"Erro ao carregar cookies locais: {e}")

    def start_login_thread(self):
        """Dispara a thread de login."""
        self.status_label.configure(text="Abrindo o navegador... Faça login manualmente no HoYoLAB.", text_color="#3B82F6")
        self.login_btn.configure(state="disabled")
        
        self.progress_bar.pack(padx=25, pady=(10, 2), fill="x")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.login_task, daemon=True)
        thread.start()
        
    def login_task(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cookies_captured = loop.run_until_complete(capturar_cookies_hoyolab())
            loop.close()
            self.after(0, self.login_completed, cookies_captured)
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.login_failed, str(e))
            
    def login_completed(self, cookies_captured: dict):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        self.cookies = cookies_captured
        self.auth_indicator.configure(text="✅ Autenticado com Sucesso", text_color="#10B981")
        self.generate_btn.configure(state="normal")
        self.login_btn.configure(state="normal")
        self.status_label.configure(text="Autenticado com sucesso! Cookies salvos localmente.", text_color="#10B981")
        
        try:
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies_captured, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar cookies localmente: {e}")
        
    def login_failed(self, error_message: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        self.login_btn.configure(state="normal")
        self.auth_indicator.configure(text="🔒 Falha na Autenticação", text_color="#EF4444")
        self.status_label.configure(text=f"Erro de Login: {error_message}", text_color="#EF4444")
        
    def start_generate_thread(self):
        self.status_label.configure(text="Conectando à API do HoYoLAB...", text_color="#3B82F6")
        self.generate_btn.configure(state="disabled")
        
        self.progress_bar.pack(padx=25, pady=(10, 2), fill="x")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.generate_task, daemon=True)
        thread.start()
        
    def generate_task(self):
        try:
            extractor = HSRExtractor(self.cookies)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            filename = loop.run_until_complete(extractor.extrair_e_salvar())
            loop.close()
            self.after(0, self.generate_completed, True, filename)
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.generate_completed, False, str(e))
            
    def generate_completed(self, success: bool, result: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.generate_btn.configure(state="normal")
        
        if success:
            self.file_indicator.configure(text="✅ Relatório gerado!", text_color="#10B981")
            self.status_label.configure(
                text=f"Sucesso! Arquivo '{result}' gerado no diretório do projeto.",
                text_color="#10B981"
            )
        else:
            self.file_indicator.configure(text="❌ Erro na geração", text_color="#EF4444")
            self.status_label.configure(text=f"Erro: {result}", text_color="#EF4444")
            
    # ==========================================
    # LOGICA DA ABA 2: PRYDWEN SCRAPER
    # ==========================================
    
    def setup_prydwen_tab(self):
        self.prydwen_frame = ctk.CTkFrame(self.tab_prydwen, corner_radius=12, fg_color="#18181B")
        self.prydwen_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.prydwen_frame.grid_columnconfigure(0, weight=1)
        self.prydwen_frame.grid_columnconfigure(1, weight=1)
        self.prydwen_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Título da Seção
        self.prydwen_title = ctk.CTkLabel(
            self.prydwen_frame,
            text="Extração de Builds e Guias (Prydwen.gg)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7"
        )
        self.prydwen_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(12, 2), sticky="w")
        
        # Dropdown Label
        self.char_label = ctk.CTkLabel(
            self.prydwen_frame,
            text="Selecione o Personagem:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA"
        )
        self.char_label.grid(row=1, column=0, padx=20, pady=2, sticky="w")
        
        # ComboBox (Dropdown)
        self.char_combobox = ctk.CTkComboBox(
            self.prydwen_frame,
            values=["Carregando lista..."],
            height=35,
            corner_radius=8,
            state="disabled"
        )
        self.char_combobox.grid(row=1, column=1, padx=20, pady=2, sticky="ew")
        
        # Botão Baixar
        self.download_btn = ctk.CTkButton(
            self.prydwen_frame,
            text="Baixar Guia(s) do Prydwen",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            state="disabled",
            command=self.start_prydwen_thread
        )
        self.download_btn.grid(row=2, column=0, columnspan=2, padx=20, pady=(8, 4), sticky="ew")
        
        # Botão Atualizar Meta (Novo!)
        self.meta_btn = ctk.CTkButton(
            self.prydwen_frame,
            text="Atualizar Tier Lists e Meta Sazonal",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#10B981",
            hover_color="#059669",
            command=self.start_meta_thread
        )
        self.meta_btn.grid(row=3, column=0, columnspan=2, padx=20, pady=(4, 8), sticky="ew")
        
        # Indicador de status interno da aba
        self.prydwen_status = ctk.CTkLabel(
            self.prydwen_frame,
            text="Iniciando raspador...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA"
        )
        self.prydwen_status.grid(row=4, column=0, columnspan=2, padx=20, pady=(2, 10), sticky="w")
        
    def start_load_chars_thread(self):
        """Dispara a busca em background da lista de personagens."""
        self.status_label.configure(text="Carregando lista de personagens do Prydwen...", text_color="#3B82F6")
        thread = threading.Thread(target=self.load_chars_task, daemon=True)
        thread.start()
        
    def load_chars_task(self):
        try:
            chars = self.scraper.get_character_list()
            self.after(0, self.load_chars_completed, chars)
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.load_chars_failed, str(e))
            
    def load_chars_completed(self, chars: list):
        self.character_list = chars
        options = ["Baixar Todos os Personagens"] + [c["name"] for c in chars]
        self.char_combobox.configure(values=options, state="normal")
        self.char_combobox.set("Baixar Todos os Personagens")
        self.download_btn.configure(state="normal")
        self.prydwen_status.configure(text="Pronto para baixar guias.", text_color="#10B981")
        self.status_label.configure(text="Pronto. Lista de personagens do Prydwen carregada.", text_color="#10B981")
        
    def load_chars_failed(self, error_message: str):
        self.prydwen_status.configure(text=f"Erro ao carregar lista: {error_message}", text_color="#EF4444")
        self.status_label.configure(text="Não foi possível carregar a lista do Prydwen.", text_color="#EF4444")
        
    def start_prydwen_thread(self):
        selected_option = self.char_combobox.get()
        self.download_btn.configure(state="disabled")
        self.char_combobox.configure(state="disabled")
        
        self.progress_bar.pack(padx=25, pady=(10, 2), fill="x")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        self.status_label.configure(text="Baixando guias do Prydwen...", text_color="#3B82F6")
        
        thread = threading.Thread(target=self.prydwen_task, args=(selected_option,), daemon=True)
        thread.start()
        
    def prydwen_task(self, selected_option: str):
        try:
            if selected_option == "Baixar Todos os Personagens":
                total = len(self.character_list)
                for idx, c in enumerate(self.character_list, 1):
                    msg = f"Baixando guia de {c['name']} ({idx}/{total})..."
                    self.after(0, self.update_prydwen_progress, msg)
                    
                    try:
                        data = self.scraper.scrape_character_guide(c["name"], c["url"])
                        self.scraper.save_to_markdown(c["name"], data)
                    except Exception as child_err:
                        print(f"Erro ao baixar guia de {c['name']}: {child_err}")
                        
                self.after(0, self.prydwen_completed, True, f"Todos os {total} guias foram baixados com sucesso!")
            else:
                char_data = None
                for c in self.character_list:
                    if c["name"] == selected_option:
                        char_data = c
                        break
                if not char_data:
                    raise Exception(f"Personagem '{selected_option}' não encontrado na lista.")
                    
                msg = f"Baixando guia de {char_data['name']}..."
                self.after(0, self.update_prydwen_progress, msg)
                
                data = self.scraper.scrape_character_guide(char_data["name"], char_data["url"])
                filepath = self.scraper.save_to_markdown(char_data["name"], data)
                self.after(0, self.prydwen_completed, True, f"Guia de '{selected_option}' salvo em '{filepath}'!")
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.prydwen_completed, False, str(e))
            
    def update_prydwen_progress(self, message: str):
        self.prydwen_status.configure(text=message, text_color="#3B82F6")
        self.status_label.configure(text=message, text_color="#3B82F6")
        
    def prydwen_completed(self, success: bool, message: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.download_btn.configure(state="normal")
        self.char_combobox.configure(state="normal")
        
        if success:
            self.prydwen_status.configure(text="Concluído com sucesso!", text_color="#10B981")
            self.status_label.configure(text=message, text_color="#10B981")
        else:
            self.prydwen_status.configure(text="Erro no download.", text_color="#EF4444")
            self.status_label.configure(text=f"Erro: {message}", text_color="#EF4444")
            
    def start_meta_thread(self):
        self.meta_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        
        self.progress_bar.pack(padx=25, pady=(10, 2), fill="x")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        self.update_status_msg("Baixando meta do patch atual...", "#3B82F6")
        
        thread = threading.Thread(target=self.meta_task, daemon=True)
        thread.start()
        
    def meta_task(self):
        try:
            # Sincroniza status para processando tier lists
            self.after(0, self.update_status_msg, "Processando Tier Lists...", "#3B82F6")
            
            scraper_m = PrydwenMetaScraper()
            data = scraper_m.scrape_tier_list()
            filepath_tier = scraper_m.save_meta_markdown(data)
            
            # Sincroniza status para processando relatórios de endgame
            self.after(0, self.update_status_msg, "Processando Relatórios de Endgame...", "#3B82F6")
            reports = scraper_m.scrape_endgame_reports()
            filepath_endgame = scraper_m.save_endgame_markdown(reports)
            
            msg = f"Meta atualizado com sucesso! Arquivos '{os.path.basename(filepath_tier)}' e '{os.path.basename(filepath_endgame)}' gerados."
            self.after(0, self.meta_completed, True, msg)
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.meta_completed, False, str(e))
            
    def update_status_msg(self, message: str, color_hex: str):
        self.prydwen_status.configure(text=message, text_color=color_hex)
        self.status_label.configure(text=message, text_color=color_hex)
        
    def meta_completed(self, success: bool, message: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.meta_btn.configure(state="normal")
        self.download_btn.configure(state="normal")
        
        if success:
            self.prydwen_status.configure(text="Meta atualizado com sucesso!", text_color="#10B981")
            self.status_label.configure(text=message, text_color="#10B981")
        else:
            self.prydwen_status.configure(text="Erro ao atualizar meta.", text_color="#EF4444")
            self.status_label.configure(text=f"Erro: {message}", text_color="#EF4444")
            
    # ==========================================
    # LOGICA DA ABA 3: NOTEBOOKLM SYNC
    # ==========================================
    
    def setup_notebooklm_tab(self):
        self.notebooklm_frame = ctk.CTkFrame(self.tab_notebooklm, corner_radius=12, fg_color="#18181B")
        self.notebooklm_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.notebooklm_frame.grid_columnconfigure(0, weight=1)
        self.notebooklm_frame.grid_columnconfigure(1, weight=3)
        self.notebooklm_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        # Título da Seção
        self.notebooklm_title = ctk.CTkLabel(
            self.notebooklm_frame,
            text="Sincronização com o NotebookLM (Google)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7"
        )
        self.notebooklm_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        
        # Campo de entrada da URL do Notebook
        self.url_label = ctk.CTkLabel(
            self.notebooklm_frame,
            text="URL do Notebook:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA"
        )
        self.url_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.notebook_url_entry = ctk.CTkEntry(
            self.notebooklm_frame,
            placeholder_text="Cole a URL do seu notebook aqui...",
            height=35,
            corner_radius=8
        )
        self.notebook_url_entry.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        
        # Carregar URL persistida se houver
        self.config_file = "config.json"
        self.carregar_configuracao()
        
        # Botão Sincronizar
        self.sync_btn = ctk.CTkButton(
            self.notebooklm_frame,
            text="3. Sincronizar com NotebookLM",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42,
            corner_radius=8,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self.start_sync_thread
        )
        self.sync_btn.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        # Indicador de status interno
        self.notebooklm_status = ctk.CTkLabel(
            self.notebooklm_frame,
            text="Aguardando início...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA"
        )
        self.notebooklm_status.grid(row=3, column=0, columnspan=2, padx=20, pady=(5, 15), sticky="w")
        
    def carregar_configuracao(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                url = config.get("notebook_url", "")
                if url:
                    self.notebook_url_entry.insert(0, url)
            except Exception as e:
                print(f"Erro ao carregar configuracao: {e}")

    def salvar_configuracao(self, url: str):
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["notebook_url"] = url
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configuracao: {e}")

    def start_sync_thread(self):
        url = self.notebook_url_entry.get().strip()
        if not url:
            self.notebooklm_status.configure(text="Erro: Insira uma URL de notebook válida.", text_color="#EF4444")
            self.status_label.configure(text="Erro: URL do notebook vazia.", text_color="#EF4444")
            return
            
        self.salvar_configuracao(url)
        
        self.sync_btn.configure(state="disabled")
        self.progress_bar.pack(padx=25, pady=(10, 2), fill="x")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        self.notebooklm_status.configure(text="Iniciando navegador Playwright...", text_color="#3B82F6")
        self.status_label.configure(text="Carregando Playwright para upload...", text_color="#3B82F6")
        
        thread = threading.Thread(target=self.sync_task, args=(url,), daemon=True)
        thread.start()

    def sync_task(self, url: str):
        try:
            file_paths = []
            
            # 1. Roster
            roster_file = "meus_personagens_hsr.md"
            if os.path.exists(roster_file):
                file_paths.append(roster_file)
                
            # 2. Meta
            meta_file = "meta_e_tierlists_atual.md"
            if os.path.exists(meta_file):
                file_paths.append(meta_file)
                
            # 3. Endgame Report
            endgame_file = "meta_endgame_report.md"
            if os.path.exists(endgame_file):
                file_paths.append(endgame_file)
                
            # 4. Guias consolidados do Prydwen
            guias_dir = "guias_prydwen"
            bundle_file = "todos_os_guias_prydwen.md"
            if os.path.exists(guias_dir) and os.path.isdir(guias_dir):
                md_files = [f for f in os.listdir(guias_dir) if f.endswith(".md")]
                if md_files:
                    file_paths.append(bundle_file)
            
            if not file_paths:
                raise Exception("Nenhum arquivo Markdown (.md) de Roster ou Meta foi encontrado no projeto.")
                
            from notebooklm_uploader import NotebookLMUploader
            uploader = NotebookLMUploader()
            
            self.after(0, self.update_notebooklm_status, "Acessando NotebookLM / Aguardando Login...", "#3B82F6")
            uploader.upload_sources(url, file_paths)
            
            self.after(0, self.sync_completed, True, f"Sincronizados {len(file_paths)} arquivos consolidados com sucesso!")
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.sync_completed, False, str(e))

    def update_notebooklm_status(self, message: str, color_hex: str):
        self.notebooklm_status.configure(text=message, text_color=color_hex)
        self.status_label.configure(text=message, text_color=color_hex)

    def sync_completed(self, success: bool, message: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.sync_btn.configure(state="normal")
        
        if success:
            self.notebooklm_status.configure(text="Concluído com sucesso!", text_color="#10B981")
            self.status_label.configure(text=message, text_color="#10B981")
        else:
            self.notebooklm_status.configure(text="Erro de Sincronização.", text_color="#EF4444")
            self.status_label.configure(text=f"Erro: {message}", text_color="#EF4444")
