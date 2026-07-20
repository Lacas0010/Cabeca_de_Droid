import os
import json
import asyncio
import threading
import traceback
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps
from auth import capturar_cookies_hoyolab
from extractor import MultiGameExtractor
from scraper_prydwen import PrydwenScraper
from scraper_zzz import PrydwenZZZScraper
from scraper_meta import PrydwenMetaScraper

# Configurações de Aparência do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração da janela principal
        self.title("HoYoverse Multi-Game RAG Hub")
        self.geometry("1050x700")
        self.resizable(True, True)
        self.center_window(1050, 700)
        
        # Estado do app
        self.cookies = {}
        self.cookie_file = "cookies.json"
        self.config_file = "config.json"
        
        # --- ESTRUTURA DO LAYOUT ---
        # 1. Sidebar à esquerda (largura ~240px)
        self.setup_sidebar()
        
        # 2. Terminal/Console na Base (altura ~130px)
        self.setup_bottom_terminal()
        
        # 3. Área Principal Dinâmica (Resto do espaço à direita)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#121214")
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Inicializa ScrollableFrames correspondentes aos botões de navegação
        self.setup_frames()
        
        # Seleciona ZZZ por padrão
        self.select_frame("zzz")
        
        # Carrega dados salvos
        self.carregar_cookies_salvos()
        self.carregar_configuracao()
        self.log("Hub Multi-Jogo inicializado com sucesso. Pronto.", "SUCCESS")
        
    def center_window(self, width: int, height: int):
        """Centraliza a janela na tela do usuário."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def load_sidebar_icon(self, icon_path: str):
        """Carrega e redimensiona um ícone de sidebar, retornando um CTkImage ou None."""
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).convert("RGBA")
                return ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
            except Exception as e:
                self.log(f"Erro ao carregar ícone {icon_path}: {e}", "WARN")
        return None

    def hex_to_rgb(self, hex_str: str) -> tuple:
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def create_game_banner(self, banner_path: str, theme_color_hex: str, title: str, subtitle: str, width: int = 750, height: int = 125) -> ctk.CTkImage:
        """
        Preenche 100% do banner com a arte do jogo e adiciona um degradê
        escuro no canto esquerdo para garantir leitura do texto.
        """
        try:
            # 1. Carrega e ajusta a imagem para preencher 100% do container (Crop estilo Cover)
            if os.path.exists(banner_path):
                img = Image.open(banner_path).convert("RGBA")
                
                # Proporção Cover
                target_ratio = width / height
                img_ratio = img.width / img.height
                
                if img_ratio > target_ratio:
                    # Imagem é mais larga: corta as laterais
                    new_height = height
                    new_width = int(new_height * img_ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    left = (new_width - width) // 2
                    img = img.crop((left, 0, left + width, height))
                else:
                    # Imagem é mais alta: corta topo/base
                    new_width = width
                    new_height = int(new_width / img_ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    top = (new_height - height) // 2
                    img = img.crop((0, top, width, top + height))

                # 2. Cria uma camada de sombra escura (Linear Gradient da esquerda pra direita)
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                draw_overlay = ImageDraw.Draw(overlay)
                
                # Transição: do escuro forte na esquerda (210 alpha) até transparente na direita
                for x in range(int(width * 0.65)):
                    alpha = int(210 * (1 - (x / (width * 0.65))))
                    draw_overlay.line([(x, 0), (x, height)], fill=(18, 18, 20, alpha))
                    
                # Aplica a sombra sobre a imagem
                final_banner = Image.alpha_composite(img, overlay)
            else:
                self.log(f"Asset de banner não encontrado: {banner_path}. Usando cor sólida.", "INFO")
                final_banner = Image.new("RGBA", (width, height), theme_color_hex)

        except Exception as e:
            self.log(f"Erro ao carregar banner {banner_path}: {e}", "WARN")
            # Fallback para fundo com a cor temática
            final_banner = Image.new("RGBA", (width, height), theme_color_hex)

        # 3. Escreve os textos
        draw = ImageDraw.Draw(final_banner)
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 22)
            font_sub = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        draw.text((25, 32), title, fill="#FFFFFF", font=font_title)
        draw.text((25, 68), subtitle, fill="#CCCCCC", font=font_sub)

        return ctk.CTkImage(light_image=final_banner, dark_image=final_banner, size=(width, height))



    # ==========================================
    # CONSTRUÇÃO DA SIDEBAR (PAINEL ESQUERDO)
    # ==========================================
    
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#18181C")
        self.sidebar.pack(side="left", fill="y", expand=False)
        self.sidebar.pack_propagate(False)
        
        # Título do App estilizado
        app_logo = ctk.CTkLabel(
            self.sidebar,
            text="⚡ HoYoverse Hub",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#F4F4F5"
        )
        app_logo.pack(padx=20, pady=(25, 5), anchor="w")
        
        app_sub = ctk.CTkLabel(
            self.sidebar,
            text="Hub Pessoal RAG v2.1",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#71717A"
        )
        app_sub.pack(padx=20, pady=(0, 25), anchor="w")
        # Tenta carregar ícones
        icon_zzz = self.load_sidebar_icon("assets/zzz_icon.png")
        icon_genshin = self.load_sidebar_icon("assets/genshin_icon.png")
        icon_hsr = self.load_sidebar_icon("assets/hsr_icon.png")
        icon_config = self.load_sidebar_icon("assets/config_icon.png")
        
        # Botões de Navegação
        self.btn_zzz = ctk.CTkButton(
            self.sidebar,
            text=" Zenless Zone Zero" if icon_zzz else "🟡 Zenless Zone Zero",
            image=icon_zzz,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("zzz")
        )
        self.btn_zzz.pack(padx=15, pady=4, fill="x")
        
        self.btn_genshin = ctk.CTkButton(
            self.sidebar,
            text=" Genshin Impact" if icon_genshin else "🟢 Genshin Impact",
            image=icon_genshin,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("genshin")
        )
        self.btn_genshin.pack(padx=15, pady=4, fill="x")
        
        self.btn_hsr = ctk.CTkButton(
            self.sidebar,
            text=" Honkai: Star Rail" if icon_hsr else "🟣 Honkai: Star Rail",
            image=icon_hsr,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("hsr")
        )
        self.btn_hsr.pack(padx=15, pady=4, fill="x")
        
        self.btn_config = ctk.CTkButton(
            self.sidebar,
            text=" Configurações" if icon_config else "⚙️ Configurações",
            image=icon_config,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("config")
        )
        self.btn_config.pack(padx=15, pady=4, fill="x")
        
        # Painel de Status no Rodapé da Sidebar
        self.status_panel = ctk.CTkFrame(self.sidebar, height=110, corner_radius=10, fg_color="#1E1E24")
        self.status_panel.pack(side="bottom", padx=15, pady=20, fill="x")
        self.status_panel.pack_propagate(False)
        
        panel_title = ctk.CTkLabel(
            self.status_panel,
            text="STATUS DA CONEXÃO",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#A1A1AA"
        )
        panel_title.pack(padx=12, pady=(10, 2), anchor="w")
        
        self.sidebar_auth_badge = ctk.CTkLabel(
            self.status_panel,
            text="🔒 Não Autenticado",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#EF4444"
        )
        self.sidebar_auth_badge.pack(padx=12, pady=2, anchor="w")
        
        version_label = ctk.CTkLabel(
            self.status_panel,
            text="Versão: Build 2026.07",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#71717A"
        )
        version_label.pack(padx=12, pady=(2, 10), anchor="w")

    # ==========================================
    # CONSTRUÇÃO DO TERMINAL DE LOGS (RODAPÉ)
    # ==========================================
    
    def setup_bottom_terminal(self):
        self.terminal = ctk.CTkFrame(self, height=140, corner_radius=0, fg_color="#09090B")
        self.terminal.pack(side="bottom", fill="x", expand=False)
        self.terminal.pack_propagate(False)
        
        # Divisor superior para separar o terminal
        sep = ctk.CTkFrame(self.terminal, height=1, fg_color="#27272A")
        sep.pack(fill="x")
        
        terminal_header = ctk.CTkFrame(self.terminal, height=25, fg_color="transparent")
        terminal_header.pack(fill="x", padx=15, pady=(5, 0))
        
        title = ctk.CTkLabel(
            terminal_header,
            text="LOGS DO SISTEMA EM TEMPO REAL",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#71717A"
        )
        title.pack(side="left")
        
        # Caixa de Texto estilo Terminal
        self.console = ctk.CTkTextbox(
            self.terminal,
            fg_color="#0C0C0E",
            text_color="#F4F4F5",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            border_width=1,
            border_color="#1E1E24"
        )
        self.console.pack(padx=15, pady=(2, 4), fill="both", expand=True)
        self.console.configure(state="disabled")
        
        # Barra de Progresso Fina e Status
        status_bar = ctk.CTkFrame(self.terminal, height=22, fg_color="transparent")
        status_bar.pack(fill="x", padx=15, pady=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Pronto.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#A1A1AA"
        )
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(status_bar, width=150, height=5, corner_radius=2, fg_color="#1E1E24", progress_color="#3B82F6")
        self.progress_bar.pack(side="right", pady=5)
        self.progress_bar.set(0)

    # ==========================================
    # GERENCIAMENTO DE TELA E NAVEGAÇÃO
    # ==========================================
    
    def setup_frames(self):
        # 1. Frame de ZZZ
        self.frame_zzz = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.build_game_screen(self.frame_zzz, "zzz", "Zenless Zone Zero", "#D97706", "Nv. 60", "Prydwen (Agentes)", "Shiyu Defense & Deadly Assault")
        
        # 2. Frame de Genshin
        self.frame_genshin = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.build_game_screen(self.frame_genshin, "genshin", "Genshin Impact", "#059669", "Nv. 90", "KeqingMains (KQM)", "Abismo / Teatro")
        
        # 3. Frame de HSR
        self.frame_hsr = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.build_game_screen(self.frame_hsr, "hsr", "Honkai: Star Rail", "#7C3AED", "Nv. 80", "Prydwen (Personagens)", "MoC / PF / AS")
        
        # 4. Frame de Configurações
        self.frame_config = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.build_config_screen(self.frame_config)

    def select_frame(self, name: str):
        # Oculta todos os frames principais
        self.frame_zzz.pack_forget()
        self.frame_genshin.pack_forget()
        self.frame_hsr.pack_forget()
        self.frame_config.pack_forget()
        
        # Reseta cores de fundo dos botões da sidebar para transparente
        self.btn_zzz.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_genshin.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_hsr.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_config.configure(fg_color="transparent", text_color="#D4D4D8")
        
        # Destaca o botão ativo com a cor do tema de cada aba
        if name == "zzz":
            self.btn_zzz.configure(fg_color="#D97706", text_color="#FFFFFF")
            self.frame_zzz.pack(fill="both", expand=True, padx=5, pady=5)
        elif name == "genshin":
            self.btn_genshin.configure(fg_color="#059669", text_color="#FFFFFF")
            self.frame_genshin.pack(fill="both", expand=True, padx=5, pady=5)
        elif name == "hsr":
            self.btn_hsr.configure(fg_color="#7C3AED", text_color="#FFFFFF")
            self.frame_hsr.pack(fill="both", expand=True, padx=5, pady=5)
        elif name == "config":
            self.btn_config.configure(fg_color="#4B5563", text_color="#FFFFFF")
            self.frame_config.pack(fill="both", expand=True, padx=5, pady=5)

    # ==========================================
    # DESIGN SYSTEM: LAYOUT DE ABAS DE JOGOS
    # ==========================================
    
    def build_game_screen(self, container, game_id: str, title: str, theme_color: str, max_lvl: str, guides_src: str, endgame_src: str):
        # 1. Header Banner estilizado com Pillow Degradê
        banner_img = self.create_game_banner(
            banner_path=f"assets/{game_id}_banner.png",
            theme_color_hex=theme_color,
            title=title,
            subtitle=f"Gerenciador de RAG e Extrações de Meta-Guias para {title}"
        )
        header_banner = ctk.CTkLabel(container, image=banner_img, text="", corner_radius=12)
        header_banner.pack(fill="x", padx=10, pady=(10, 15))
        # Card 1: Dados do Roster (HoYoLAB)
        card_roster = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_roster.pack(fill="x", padx=10, pady=10)
        
        roster_title = ctk.CTkLabel(
            card_roster,
            text="👤 Dados de Personagens & Roster",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        roster_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        roster_cb = ctk.CTkCheckBox(
            card_roster,
            text=f"Extrair Roster, Eidolons/Constelações e Builds (Nível Máximo: {max_lvl})",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=theme_color,
            hover_color=theme_color
        )
        roster_cb.pack(padx=40, pady=(5, 20), anchor="w")
        roster_cb.select()
        
        # Card 2: Guias e Endgame (Scraping)
        card_scraping = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_scraping.pack(fill="x", padx=10, pady=10)
        
        scraping_title = ctk.CTkLabel(
            card_scraping,
            text="📚 Guias & Metagame (Web Scraping)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        scraping_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        guides_cb = ctk.CTkCheckBox(
            card_scraping,
            text=f"Guias Individuais de Construção de Build ({guides_src})",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=theme_color,
            hover_color=theme_color
        )
        guides_cb.pack(padx=40, pady=6, anchor="w")
        
        meta_cb = ctk.CTkCheckBox(
            card_scraping,
            text=f"Tier Lists e Estatísticas de Endgame ({endgame_src})",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=theme_color,
            hover_color=theme_color
        )
        meta_cb.pack(padx=40, pady=(6, 20), anchor="w")

        setattr(self, f"{game_id}_roster_cb", roster_cb)
        setattr(self, f"{game_id}_guides_cb", guides_cb)
        setattr(self, f"{game_id}_meta_cb", meta_cb)
        
        # Card 3: Ações de Execução
        card_actions = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_actions.pack(fill="x", padx=10, pady=10)
        
        actions_inner = ctk.CTkFrame(card_actions, fg_color="transparent")
        actions_inner.pack(padx=20, pady=15, fill="x")
        actions_inner.grid_columnconfigure((0, 1, 2), weight=1)
        
        sel_all = ctk.CTkButton(
            actions_inner,
            text="Marcar Tudo",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=35,
            command=lambda: self.select_all_tasks(game_id, True)
        )
        sel_all.grid(row=0, column=0, padx=5, sticky="ew")
        
        desel_all = ctk.CTkButton(
            actions_inner,
            text="Desmarcar Tudo",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=35,
            command=lambda: self.select_all_tasks(game_id, False)
        )
        desel_all.grid(row=0, column=1, padx=5, sticky="ew")
        
        run_btn = ctk.CTkButton(
            actions_inner,
            text=f"🚀 Executar Tarefas {game_id.upper()}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=theme_color,
            hover_color=theme_color,  # CustomTkinter escurece automaticamente ou usamos o mesmo
            height=38,
            command=lambda: self.start_game_task_thread(game_id)
        )
        run_btn.grid(row=0, column=2, padx=5, sticky="ew")
        setattr(self, f"{game_id}_run_btn", run_btn)

    def select_all_tasks(self, game_id: str, state: bool):
        roster = getattr(self, f"{game_id}_roster_cb")
        guides = getattr(self, f"{game_id}_guides_cb")
        meta = getattr(self, f"{game_id}_meta_cb")
        if state:
            roster.select()
            guides.select()
            meta.select()
        else:
            roster.deselect()
            guides.deselect()
            meta.deselect()

    # ==========================================
    # DESIGN SYSTEM: LAYOUT DA TELA CONFIG
    # ==========================================
    
    def build_config_screen(self, container):
        # Cabeçalho da Configuração com Pillow Degradê
        banner_img = self.create_game_banner(
            banner_path="assets/config_banner.png",
            theme_color_hex="#3F3F46",
            title="Configurações Globais",
            subtitle="Autenticação HoYoLAB e gerenciamento de sincronizações no Google NotebookLM"
        )
        header_banner = ctk.CTkLabel(container, image=banner_img, text="", corner_radius=12)
        header_banner.pack(fill="x", padx=10, pady=(10, 15))
        
        # --- CARD 1: CREDENCIAIS HOYOLAB ---
        card_creds = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_creds.pack(fill="x", padx=10, pady=10)
        
        card_creds_title = ctk.CTkLabel(
            card_creds,
            text="🔑 Credenciais da Conta HoYoLAB",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        card_creds_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        desc_creds = ctk.CTkLabel(
            card_creds,
            text="Para extrair as informações do seu perfil, insira os cookies da sua conta abaixo ou clique em Login Automático.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#A1A1AA"
        )
        desc_creds.pack(padx=20, pady=2, anchor="w")
        
        # Campo de Cookie
        self.cookie_entry = ctk.CTkEntry(
            card_creds,
            placeholder_text="Cole o cabeçalho Cookie do seu navegador (ltuid_v2=...; ltoken_v2=...)",
            height=35,
            corner_radius=8
        )
        self.cookie_entry.pack(padx=20, pady=12, fill="x")
        
        # Frame de botões e indicador
        creds_action_frame = ctk.CTkFrame(card_creds, fg_color="transparent")
        creds_action_frame.pack(padx=20, pady=(0, 20), fill="x")
        
        self.login_btn = ctk.CTkButton(
            creds_action_frame,
            text="🌐 Autenticação por Login Automático",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=35,
            command=self.start_login_thread
        )
        self.login_btn.pack(side="left", padx=(0, 10))
        
        self.save_cookie_btn = ctk.CTkButton(
            creds_action_frame,
            text="💾 Salvar Cookie Manual",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=35,
            command=self.salvar_cookie_manual
        )
        self.save_cookie_btn.pack(side="left")
        
        self.auth_indicator = ctk.CTkLabel(
            creds_action_frame,
            text="🔒 Não Autenticado",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#EF4444"
        )
        self.auth_indicator.pack(side="right", padx=10)
        
        # --- CARD 2: CADERNOS NOTEBOOKLM ---
        card_notebooks = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_notebooks.pack(fill="x", padx=10, pady=10)
        
        card_notebooks_title = ctk.CTkLabel(
            card_notebooks,
            text="🔗 URLs dos Cadernos do Google NotebookLM",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        card_notebooks_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        desc_notebooks = ctk.CTkLabel(
            card_notebooks,
            text="Insira os links de compartilhamento específicos do NotebookLM correspondentes a cada jogo.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#A1A1AA"
        )
        desc_notebooks.pack(padx=20, pady=2, anchor="w")
        
        # Grid para os 3 campos
        grid_notebooks = ctk.CTkFrame(card_notebooks, fg_color="transparent")
        grid_notebooks.pack(padx=20, pady=12, fill="x")
        grid_notebooks.grid_columnconfigure(1, weight=1)
        
        # ZZZ
        zzz_lbl = ctk.CTkLabel(grid_notebooks, text="🟢 URL Notebook ZZZ:   ", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        zzz_lbl.grid(row=0, column=0, pady=6, sticky="w")
        self.notebook_url_zzz = ctk.CTkEntry(grid_notebooks, placeholder_text="Cole o link do caderno de Zenless Zone Zero...", height=32, corner_radius=6)
        self.notebook_url_zzz.grid(row=0, column=1, pady=6, sticky="ew")
        
        # Genshin
        genshin_lbl = ctk.CTkLabel(grid_notebooks, text="🟡 URL Notebook Genshin: ", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        genshin_lbl.grid(row=1, column=0, pady=6, sticky="w")
        self.notebook_url_genshin = ctk.CTkEntry(grid_notebooks, placeholder_text="Cole o link do caderno de Genshin Impact...", height=32, corner_radius=6)
        self.notebook_url_genshin.grid(row=1, column=1, pady=6, sticky="ew")
        
        # HSR
        hsr_lbl = ctk.CTkLabel(grid_notebooks, text="🟣 URL Notebook HSR:     ", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        hsr_lbl.grid(row=2, column=0, pady=6, sticky="w")
        self.notebook_url_hsr = ctk.CTkEntry(grid_notebooks, placeholder_text="Cole o link do caderno de Honkai: Star Rail...", height=32, corner_radius=6)
        self.notebook_url_hsr.grid(row=2, column=1, pady=6, sticky="ew")
        
        self.save_links_btn = ctk.CTkButton(
            card_notebooks,
            text="💾 Salvar Configurações de Links",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=32,
            command=self.salvar_notebooks_config
        )
        self.save_links_btn.pack(padx=20, pady=(0, 20), anchor="w")
        
        # --- CARD 3: AÇÕES DE SINCRONIZAÇÃO ---
        card_sync = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_sync.pack(fill="x", padx=10, pady=10)
        
        card_sync_title = ctk.CTkLabel(
            card_sync,
            text="🚀 Sincronização em Massa (Upload Google)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        card_sync_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        desc_sync = ctk.CTkLabel(
            card_sync,
            text="Selecione quais pastas locais consolidar e enviar automaticamente aos respectivos cadernos do NotebookLM.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#A1A1AA"
        )
        desc_sync.pack(padx=20, pady=2, anchor="w")
        
        # Checkboxes Horizontais
        cbs_frame = ctk.CTkFrame(card_sync, fg_color="transparent")
        cbs_frame.pack(padx=20, pady=12, fill="x")
        cbs_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.sync_zzz_cb = ctk.CTkCheckBox(cbs_frame, text="Zenless Zone Zero (ZZZ)", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#8B5CF6", hover_color="#7C3AED")
        self.sync_zzz_cb.grid(row=0, column=0, padx=5, sticky="w")
        self.sync_zzz_cb.select()
        
        self.sync_genshin_cb = ctk.CTkCheckBox(cbs_frame, text="Genshin Impact (GI)", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#8B5CF6", hover_color="#7C3AED")
        self.sync_genshin_cb.grid(row=0, column=1, padx=5, sticky="w")
        
        self.sync_hsr_cb = ctk.CTkCheckBox(cbs_frame, text="Honkai: Star Rail (HSR)", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#8B5CF6", hover_color="#7C3AED")
        self.sync_hsr_cb.grid(row=0, column=2, padx=5, sticky="w")
        
        # Botão Upload
        self.sync_btn = ctk.CTkButton(
            card_sync,
            text="📤 EXECUTAR SINCRONIZAÇÃO NOTEBOOKLM",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            height=40,
            corner_radius=8
        )
        self.sync_btn.pack(padx=20, pady=(5, 20), fill="x")
        self.sync_btn.configure(command=self.start_sync_thread)

    # LOGICA DE CONFIGURAÇÕES DE CARREGAR/SALVAR
    # ==========================================
    
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
                    self.auth_indicator.configure(text="✅ Autenticado", text_color="#10B981")
                    self.sidebar_auth_badge.configure(text="🔓 Conectado", text_color="#10B981")
                    self.log("Credenciais carregadas com sucesso de cookies.json.", "SUCCESS")
                    
                    uid = cookies.get("ltuid_v2") or cookies.get("ltuid")
                    token = cookies.get("ltoken_v2") or cookies.get("ltoken")
                    self.cookie_entry.delete(0, "end")
                    self.cookie_entry.insert(0, f"ltuid={uid}; ltoken={token}")
            except Exception as e:
                self.log(f"Erro ao carregar cookies: {e}", "ERROR")
                
    def carregar_configuracao(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Carrega URLs
                url_zzz = config.get("notebook_zzz", "")
                if url_zzz:
                    self.notebook_url_zzz.insert(0, url_zzz)
                    
                url_genshin = config.get("notebook_genshin", "")
                if url_genshin:
                    self.notebook_url_genshin.insert(0, url_genshin)
                    
                url_hsr = config.get("notebook_hsr", "")
                if url_hsr:
                    self.notebook_url_hsr.insert(0, url_hsr)
                    
                # Carrega checkboxes
                if config.get("sync_zzz", True):
                    self.sync_zzz_cb.select()
                else:
                    self.sync_zzz_cb.deselect()
                    
                if config.get("sync_genshin", False):
                    self.sync_genshin_cb.select()
                else:
                    self.sync_genshin_cb.deselect()
                    
                if config.get("sync_hsr", False):
                    self.sync_hsr_cb.select()
                else:
                    self.sync_hsr_cb.deselect()
            except Exception as e:
                self.log(f"Erro ao carregar configuracoes: {e}", "WARN")

    def salvar_notebooks_config(self):
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
            config["notebook_zzz"] = self.notebook_url_zzz.get().strip()
            config["notebook_genshin"] = self.notebook_url_genshin.get().strip()
            config["notebook_hsr"] = self.notebook_url_hsr.get().strip()
            config["sync_zzz"] = bool(self.sync_zzz_cb.get())
            config["sync_genshin"] = bool(self.sync_genshin_cb.get())
            config["sync_hsr"] = bool(self.sync_hsr_cb.get())
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            self.log("Links e seleções de cadernos salvos com sucesso!", "SUCCESS")
        except Exception as e:
            self.log(f"Erro ao salvar configuracao: {e}", "ERROR")

    def parse_cookie_string(self, cookie_str: str) -> dict:
        cookies = {}
        cookie_str = cookie_str.strip()
        try:
            return json.loads(cookie_str)
        except Exception:
            pass
            
        parts = cookie_str.split(';')
        for part in parts:
            if '=' in part:
                k, v = part.strip().split('=', 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def salvar_cookie_manual(self):
        raw_cookie = self.cookie_entry.get().strip()
        if not raw_cookie:
            self.log("O campo de cookie está vazio.", "ERROR")
            return
            
        cookies = self.parse_cookie_string(raw_cookie)
        has_v2 = "ltuid_v2" in cookies and "ltoken_v2" in cookies
        has_v1 = "ltuid" in cookies and "ltoken" in cookies
        
        if not (has_v2 or has_v1):
            self.log("Cookie inserido não possui as chaves necessárias (ltuid/ltoken).", "ERROR")
            self.auth_indicator.configure(text="❌ Autenticação Inválida", text_color="#EF4444")
            self.sidebar_auth_badge.configure(text="❌ Erro Conexão", text_color="#EF4444")
            return
            
        self.cookies = cookies
        try:
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=4)
            self.auth_indicator.configure(text="✅ Autenticado", text_color="#10B981")
            self.sidebar_auth_badge.configure(text="🔓 Conectado", text_color="#10B981")
            self.log("Cookies manuais salvos em cookies.json e carregados com sucesso.", "SUCCESS")
        except Exception as e:
            self.log(f"Falha ao salvar cookies: {e}", "ERROR")

    def log(self, message: str, level: str = "INFO"):
        """Adiciona uma mensagem formatada ao console inferior."""
        colors = {
            "INFO": "🔹",
            "WARN": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }
        prefix = colors.get(level, "🔹")
        full_msg = f"{prefix} [{level}] {message}\n"
        
        self.console.configure(state="normal")
        self.console.insert("end", full_msg)
        self.console.see("end")
        self.console.configure(state="disabled")
        self.status_label.configure(text=message)

    # ==========================================
    # THREAD DE LOGIN AUTOMÁTICO
    # ==========================================
    
    def start_login_thread(self):
        self.log("Abrindo navegador... Faça login manualmente na janela do HoYoLAB.", "INFO")
        self.login_btn.configure(state="disabled")
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
        self.progress_bar.set(0)
        self.login_btn.configure(state="normal")
        
        self.cookies = cookies_captured
        self.auth_indicator.configure(text="✅ Autenticado", text_color="#10B981")
        self.sidebar_auth_badge.configure(text="🔓 Conectado", text_color="#10B981")
        self.log("Cookies capturados automaticamente do navegador com sucesso!", "SUCCESS")
        
        # Preenche o campo visual
        uid = cookies_captured.get("ltuid_v2") or cookies_captured.get("ltuid")
        token = cookies_captured.get("ltoken_v2") or cookies_captured.get("ltoken")
        self.cookie_entry.delete(0, "end")
        self.cookie_entry.insert(0, f"ltuid={uid}; ltoken={token}")
        
        try:
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies_captured, f, indent=4)
        except Exception as e:
            self.log(f"Erro ao salvar cookies: {e}", "ERROR")
        
    def login_failed(self, error_message: str):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.login_btn.configure(state="normal")
        self.auth_indicator.configure(text="🔒 Falha na Autenticação", text_color="#EF4444")
        self.sidebar_auth_badge.configure(text="🔒 Não Autenticado", text_color="#EF4444")
        self.log(f"Falha de Login: {error_message}", "ERROR")

    # ==========================================
    # THREAD DE EXECUÇÃO DE JOGOS
    # ==========================================
    
    def start_game_task_thread(self, game_id: str):
        roster_cb = getattr(self, f"{game_id}_roster_cb")
        guides_cb = getattr(self, f"{game_id}_guides_cb")
        meta_cb = getattr(self, f"{game_id}_meta_cb")
        
        # Verifica se alguma opção foi selecionada
        if not (roster_cb.get() or guides_cb.get() or meta_cb.get()):
            self.log(f"Nenhuma opção de tarefa selecionada para {game_id.upper()}.", "WARN")
            return
            
        # Desabilita o botão para evitar cliques duplicados
        run_btn = getattr(self, f"{game_id}_run_btn")
        run_btn.configure(state="disabled")
        
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        thread = threading.Thread(
            target=self.run_game_tasks,
            args=(game_id, roster_cb.get(), guides_cb.get(), meta_cb.get()),
            daemon=True
        )
        thread.start()
        
    def run_game_tasks(self, game_id: str, run_roster: bool, run_guides: bool, run_meta: bool):
        self.log(f"Iniciando tarefas selecionadas para {game_id.upper()}...", "INFO")
        
        # --- 1. EXTRAÇÃO DE ROSTER ---
        if run_roster:
            if not self.cookies:
                self.log("HoYoLAB Cookies não localizados. Faça login ou insira manualmente na aba Configurações.", "ERROR")
                self.after(0, self.game_task_completed, game_id, False, "Cookies ausentes.")
                return
                
            self.log(f"Conectando a HoYoLAB para extração do roster de {game_id.upper()}...", "INFO")
            try:
                extractor = MultiGameExtractor(self.cookies)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                filename = loop.run_until_complete(extractor.extrair_jogo(game_id))
                loop.close()
                self.log(f"Roster extraído e salvo com sucesso em: {filename}", "SUCCESS")
            except Exception as roster_err:
                traceback.print_exc()
                self.log(f"Falha ao extrair Roster de {game_id.upper()}: {roster_err}", "ERROR")

        # --- 2. EXTRAÇÃO DE GUIDES ---
        if run_guides:
            self.log(f"Iniciando raspagem de guias para {game_id.upper()}...", "INFO")
            if game_id == "hsr":
                try:
                    self.log("Obtendo lista de personagens HSR...", "INFO")
                    scraper = PrydwenScraper()
                    chars = scraper.get_character_list()
                    self.log(f"Encontrados {len(chars)} personagens. Baixando guias...", "INFO")
                    for idx, c in enumerate(chars, 1):
                        self.log(f"({idx}/{len(chars)}) Raspando guia de {c['name']}...", "INFO")
                        try:
                            data = scraper.scrape_character_guide(c["name"], c["url"])
                            scraper.save_to_markdown(c["name"], data)
                        except Exception as child_err:
                            self.log(f"Erro no guia de {c['name']}: {child_err}", "WARN")
                    self.log("Guias de HSR baixados com sucesso!", "SUCCESS")
                except Exception as scraper_err:
                    traceback.print_exc()
                    self.log(f"Erro ao obter guias HSR: {scraper_err}", "ERROR")
                    
            elif game_id == "zzz":
                try:
                    self.log("Obtendo lista de agentes ZZZ...", "INFO")
                    scraper = PrydwenZZZScraper()
                    agents = scraper.get_agent_list()
                    self.log(f"Encontrados {len(agents)} agentes. Baixando guias...", "INFO")
                    for idx, a in enumerate(agents, 1):
                        self.log(f"({idx}/{len(agents)}) Raspando guia de {a['name']}...", "INFO")
                        try:
                            data = scraper.scrape_agent_guide(a["name"], a["url"])
                            scraper.save_to_markdown(a["name"], data)
                        except Exception as child_err:
                            self.log(f"Erro no guia de {a['name']}: {child_err}", "WARN")
                    self.log("Guias de ZZZ baixados com sucesso!", "SUCCESS")
                except Exception as scraper_err:
                    traceback.print_exc()
                    self.log(f"Erro ao obter guias ZZZ: {scraper_err}", "ERROR")
                    
            elif game_id == "genshin":
                self.log("O raspador KeqingMains (KQM) para Genshin Impact ainda não está ativo.", "WARN")

        # --- 3. EXTRAÇÃO DE META E ENDGAME ---
        if run_meta:
            self.log(f"Iniciando extração do meta de {game_id.upper()}...", "INFO")
            if game_id == "hsr":
                try:
                    self.log("Raspando Tier Lists HSR do Prydwen...", "INFO")
                    scraper_m = PrydwenMetaScraper()
                    data = scraper_m.scrape_tier_list()
                    filepath_tier = scraper_m.save_meta_markdown(data, "hsr/meta_e_tierlists_atual.md")
                    
                    self.log("Raspando estatísticas de endgame HSR...", "INFO")
                    reports = scraper_m.scrape_endgame_reports()
                    filepath_endgame = scraper_m.save_endgame_markdown(reports, "hsr/meta_endgame_report.md")
                    
                    # Consolidado
                    consolidated_path = "hsr/meta_endgame_hsr.md"
                    with open(consolidated_path, "w", encoding="utf-8") as out_f:
                        if os.path.exists(filepath_tier):
                            with open(filepath_tier, "r", encoding="utf-8") as f1:
                                out_f.write(f1.read())
                                out_f.write("\n\n---\n\n")
                        if os.path.exists(filepath_endgame):
                            with open(filepath_endgame, "r", encoding="utf-8") as f2:
                                out_f.write(f2.read())
                    self.log(f"Meta de HSR consolidado com sucesso em: {consolidated_path}", "SUCCESS")
                except Exception as meta_err:
                    traceback.print_exc()
                    self.log(f"Falha ao extrair meta HSR: {meta_err}", "ERROR")
            elif game_id == "zzz":
                try:
                    self.log("Extraindo meta, tier list e relatórios de endgame do ZZZ...", "INFO")
                    scraper = PrydwenZZZScraper()
                    filepath = scraper.save_meta_to_markdown()
                    self.log(f"Meta de ZZZ salvo e consolidado com sucesso em: {filepath}", "SUCCESS")
                except Exception as meta_err:
                    traceback.print_exc()
                    self.log(f"Falha ao extrair meta ZZZ: {meta_err}", "ERROR")
            elif game_id == "genshin":
                self.log("Relatório de endgame (Abismo/Teatro) do Genshin ainda não está ativo.", "WARN")
                
        self.after(0, self.game_task_completed, game_id, True, "Tarefas concluídas.")
        
    def game_task_completed(self, game_id: str, success: bool, msg: str):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        
        run_btn = getattr(self, f"{game_id}_run_btn")
        run_btn.configure(state="normal")
        
        if success:
            self.log(f"Todas as tarefas de {game_id.upper()} foram finalizadas com sucesso!", "SUCCESS")
        else:
            self.log(f"Tarefas de {game_id.upper()} falharam: {msg}", "ERROR")

    # ==========================================
    # THREAD DE SINCRONIZAÇÃO NOTEBOOKLM
    # ==========================================
    
    def start_sync_thread(self):
        # Primeiro, salva as configurações de links e seleções atuais
        self.salvar_notebooks_config()
        
        # Carrega links dos campos
        url_zzz = self.notebook_url_zzz.get().strip()
        url_genshin = self.notebook_url_genshin.get().strip()
        url_hsr = self.notebook_url_hsr.get().strip()
        
        # Verifica se pelo menos um jogo marcado possui URL
        marked_games = []
        if self.sync_zzz_cb.get():
            marked_games.append(("zzz", url_zzz))
        if self.sync_genshin_cb.get():
            marked_games.append(("genshin", url_genshin))
        if self.sync_hsr_cb.get():
            marked_games.append(("hsr", url_hsr))
            
        if not marked_games:
            self.log("Nenhum jogo selecionado para sincronização ou sem cadernos marcados.", "WARN")
            return
            
        # Verifica se as URLs dos marcados estão vazias
        for g_id, url in marked_games:
            if not url:
                self.log(f"A URL do notebook para {g_id.upper()} não foi preenchida na aba de Configurações.", "ERROR")
                return
                
        self.sync_btn.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        self.log("Iniciando fila de upload para os cadernos selecionados no NotebookLM...", "INFO")
        
        thread = threading.Thread(target=self.sync_task, daemon=True)
        thread.start()
        
    def sync_task(self):
        try:
            from notebooklm_uploader import bundle_guides
            
            game_uploads = {}
            
            # --- 1. ZENLESS ZONE ZERO ---
            if self.sync_zzz_cb.get():
                files = []
                if os.path.exists("zzz/roster_zzz.md"):
                    files.append("zzz/roster_zzz.md")
                if os.path.exists("zzz/meta_endgame_zzz.md"):
                    files.append("zzz/meta_endgame_zzz.md")
                if os.path.exists("zzz/guias") and os.path.isdir("zzz/guias"):
                    md_files = [f for f in os.listdir("zzz/guias") if f.endswith(".md")]
                    if md_files:
                        self.log("Consolidando guias individuais de ZZZ...", "INFO")
                        bundle_path = bundle_guides("zzz/guias", "zzz/todos_os_guias_zzz.md", "Zenless Zone Zero")
                        if bundle_path and os.path.exists(bundle_path):
                            files.append("zzz/todos_os_guias_zzz.md")
                game_uploads["zzz"] = {
                    "url": self.notebook_url_zzz.get().strip(),
                    "files": files
                }
                
            # --- 2. GENSHIN IMPACT ---
            if self.sync_genshin_cb.get():
                files = []
                if os.path.exists("genshin/roster_genshin.md"):
                    files.append("genshin/roster_genshin.md")
                if os.path.exists("genshin/meta_kqm_genshin.md"):
                    files.append("genshin/meta_kqm_genshin.md")
                if os.path.exists("genshin/guias") and os.path.isdir("genshin/guias"):
                    md_files = [f for f in os.listdir("genshin/guias") if f.endswith(".md")]
                    if md_files:
                        self.log("Consolidando guias individuais de Genshin...", "INFO")
                        bundle_path = bundle_guides("genshin/guias", "genshin/todos_os_guias_genshin.md", "Genshin Impact")
                        if bundle_path and os.path.exists(bundle_path):
                            files.append("genshin/todos_os_guias_genshin.md")
                game_uploads["genshin"] = {
                    "url": self.notebook_url_genshin.get().strip(),
                    "files": files
                }
                
            # --- 3. HONKAI: STAR RAIL ---
            if self.sync_hsr_cb.get():
                files = []
                if os.path.exists("hsr/roster_hsr.md"):
                    files.append("hsr/roster_hsr.md")
                if os.path.exists("hsr/meta_endgame_hsr.md"):
                    files.append("hsr/meta_endgame_hsr.md")
                if os.path.exists("hsr/guias") and os.path.isdir("hsr/guias"):
                    md_files = [f for f in os.listdir("hsr/guias") if f.endswith(".md")]
                    if md_files:
                        self.log("Consolidando guias individuais de HSR...", "INFO")
                        bundle_path = bundle_guides("hsr/guias", "hsr/todos_os_guias_hsr.md", "Honkai Star Rail")
                        if bundle_path and os.path.exists(bundle_path):
                            files.append("hsr/todos_os_guias_hsr.md")
                game_uploads["hsr"] = {
                    "url": self.notebook_url_hsr.get().strip(),
                    "files": files
                }
                
            if not game_uploads:
                raise Exception("Nenhum caderno foi selecionado com arquivos válidos para sincronização.")
                
            from notebooklm_uploader import NotebookLMUploader
            uploader = NotebookLMUploader()
            
            uploader.upload_multiple_games(game_uploads)
            
            self.after(0, self.sync_completed, True, "Sincronização de todos os cadernos concluída com sucesso!")
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.sync_completed, False, str(e))
            
    def sync_completed(self, success: bool, message: str):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.sync_btn.configure(state="normal")
        
        if success:
            self.log(message, "SUCCESS")
        else:
            self.log(f"Erro de Sincronização: {message}", "ERROR")

if __name__ == "__main__":
    app = App()
    app.mainloop()
