import os
import json
import asyncio
import threading
import traceback
import time
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps
from auth import capturar_cookies_hoyolab
from extractor import MultiGameExtractor
from scraper_prydwen import PrydwenScraper
from scraper_zzz import PrydwenZZZScraper
from scraper_meta import PrydwenMetaScraper

def bundle_guides(src_dir: str, dest_file: str, game_title: str) -> str:
    """
    Consolida múltiplos arquivos Markdown em um único arquivo de saída.
    """
    if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
        return None
    md_files = [f for f in os.listdir(src_dir) if f.endswith(".md")]
    if not md_files:
        return None
        
    lines = []
    lines.append(f"# Compilado Completo de Guias - {game_title}")
    lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    for f_name in sorted(md_files):
        f_path = os.path.join(src_dir, f_name)
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                lines.append(content)
                lines.append("\n\n---\n\n")
        except Exception as e:
            print(f"Erro ao ler {f_path} na consolidação: {e}")
            
    os.makedirs(os.path.dirname(dest_file) or ".", exist_ok=True)
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return dest_file

# Configurações de Aparência do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração da janela principal
        self.title("HoYo AI Assistant (Groq RAG Local)")
        self.geometry("1050x700")
        self.resizable(True, True)
        self.center_window(1050, 700)
        
        # Estado do app
        self.cookies = {}
        self.cookie_file = "cookies.json"
        self.config_file = "config.json"
        self.chat_history = []
        
        # Inicializa o assistente Groq RAG
        from groq_rag import GroqRAG
        self.groq_rag = GroqRAG()
        
        # --- ESTRUTURA DO LAYOUT ---
        # 1. Sidebar à esquerda (largura ~240px)
        self.setup_sidebar()
        
        # 2. Terminal/Console na Base (altura ~130px)
        self.setup_bottom_terminal()
        
        # 3. Área Principal Dinâmica (Resto do espaço à direita)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#121214")
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Inicializa Frames correspondentes aos botões de navegação
        self.setup_frames()
        
        # Seleciona ZZZ por padrão
        self.select_frame("zzz")
        
        # Carrega dados salvos
        self.carregar_cookies_salvos()
        self.carregar_configuracao()
        self.log("HoYo AI Assistant inicializado com sucesso. Pronto.", "SUCCESS")
        
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
            text="🤖 HoYo Assistant",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#F4F4F5"
        )
        app_logo.pack(padx=20, pady=(25, 5), anchor="w")
        
        app_sub = ctk.CTkLabel(
            self.sidebar,
            text="AI Groq RAG Hub v3.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#71717A"
        )
        app_sub.pack(padx=20, pady=(0, 25), anchor="w")
        # Tenta carregar ícones
        icon_zzz = self.load_sidebar_icon("assets/zzz_icon.png")
        icon_genshin = self.load_sidebar_icon("assets/genshin_icon.png")
        icon_hsr = self.load_sidebar_icon("assets/hsr_icon.png")
        icon_chat = self.load_sidebar_icon("assets/chat_icon.png")
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
        
        # Botão do Chat IA RAG
        self.btn_chat = ctk.CTkButton(
            self.sidebar,
            text=" Chat IA Meta" if icon_chat else "🤖 Chat IA Meta",
            image=icon_chat,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("chat")
        )
        self.btn_chat.pack(padx=15, pady=4, fill="x")
        
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

        # 5. Frame do Chat IA Assistant
        self.frame_chat = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.setup_chat_frame(self.frame_chat)

    def select_frame(self, name: str):
        # Oculta todos os frames principais
        self.frame_zzz.pack_forget()
        self.frame_genshin.pack_forget()
        self.frame_hsr.pack_forget()
        self.frame_config.pack_forget()
        self.frame_chat.pack_forget()
        
        # Reseta cores de fundo dos botões da sidebar para transparente
        self.btn_zzz.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_genshin.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_hsr.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_config.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_chat.configure(fg_color="transparent", text_color="#D4D4D8")
        
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
        elif name == "chat":
            self.btn_chat.configure(fg_color="#2563EB", text_color="#FFFFFF")
            self.frame_chat.pack(fill="both", expand=True, padx=5, pady=5)

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
    def build_config_screen(self, container):
        # Cabeçalho da Configuração com Pillow Degradê
        banner_img = self.create_game_banner(
            banner_path="assets/config_banner.png",
            theme_color_hex="#3F3F46",
            title="Configurações Globais",
            subtitle="Autenticação HoYoLAB e configuração de chaves do assistente RAG local"
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
        
        
        # --- CARD 2: API KEY DA GROQ ---
        card_groq = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_groq.pack(fill="x", padx=10, pady=10)
        
        card_groq_title = ctk.CTkLabel(
            card_groq,
            text="🔑 Groq API Key",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#E4E4E7"
        )
        card_groq_title.pack(padx=20, pady=(15, 5), anchor="w")
        
        desc_groq = ctk.CTkLabel(
            card_groq,
            text="Insira sua chave de API da Groq para habilitar o Assistente IA de Chat RAG local.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#A1A1AA"
        )
        desc_groq.pack(padx=20, pady=2, anchor="w")
        
        self.groq_key_entry = ctk.CTkEntry(
            card_groq,
            placeholder_text="Cole sua GROQ_API_KEY aqui...",
            height=35,
            corner_radius=8,
            show="*"
        )
        self.groq_key_entry.pack(padx=20, pady=12, fill="x")
        
        groq_action_frame = ctk.CTkFrame(card_groq, fg_color="transparent")
        groq_action_frame.pack(padx=20, pady=(0, 20), fill="x")
        
        self.save_groq_key_btn = ctk.CTkButton(
            groq_action_frame,
            text="💾 Salvar Chave API",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=35,
            command=self.salvar_groq_config
        )
        self.save_groq_key_btn.pack(side="left", padx=(0, 10))
        
        self.toggle_groq_visibility_btn = ctk.CTkButton(
            groq_action_frame,
            text="👁️ Mostrar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2E2E35",
            hover_color="#3F3F46",
            height=35,
            command=self.toggle_groq_key_visibility
        )
        self.toggle_groq_visibility_btn.pack(side="left", padx=(0, 10))
        
        self.test_groq_btn = ctk.CTkButton(
            groq_action_frame,
            text="⚡ Testar Conexão",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=35,
            command=self.start_test_groq_thread
        )
        self.test_groq_btn.pack(side="left")
        
        self.groq_status_lbl = ctk.CTkLabel(
            groq_action_frame,
            text="🔌 Status: Não testado",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#A1A1AA"
        )
        self.groq_status_lbl.pack(side="right", padx=10)

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
                
                key = config.get("groq_api_key") or config.get("gemini_api_key", "")
                if key:
                    self.groq_key_entry.delete(0, "end")
                    self.groq_key_entry.insert(0, key)
                    threading.Thread(target=self.run_silent_groq_test, args=(key,), daemon=True).start()
            except Exception as e:
                self.log(f"Erro ao carregar configuracoes: {e}", "WARN")

    def run_silent_groq_test(self, key):
        from groq_rag import GroqRAG
        tester = GroqRAG(api_key=key)
        success, _ = tester.test_connection()
        if success:
            self.after(0, lambda: self.groq_status_lbl.configure(text="✅ Status: Conectado", text_color="#10B981"))
        else:
            self.after(0, lambda: self.groq_status_lbl.configure(text="❌ Status: Erro / Desconectado", text_color="#EF4444"))

    def salvar_groq_config(self):
        key = self.groq_key_entry.get().strip()
        if not key:
            self.log("API Key da Groq está vazia.", "WARN")
            return
            
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            config["groq_api_key"] = key
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
                
            self.log("API Key da Groq salva em config.json!", "SUCCESS")
            
            from groq_rag import GroqRAG
            self.groq_rag = GroqRAG(api_key=key)
        except Exception as e:
            self.log(f"Erro ao salvar API Key da Groq: {e}", "ERROR")

    def toggle_groq_key_visibility(self):
        current_show = self.groq_key_entry.cget("show")
        if current_show == "*":
            self.groq_key_entry.configure(show="")
            self.toggle_groq_visibility_btn.configure(text="🙈 Ocultar")
        else:
            self.groq_key_entry.configure(show="*")
            self.toggle_groq_visibility_btn.configure(text="👁️ Mostrar")

    def start_test_groq_thread(self):
        key = self.groq_key_entry.get().strip()
        if not key:
            self.log("Por favor, insira uma API Key da Groq para testar.", "WARN")
            return
            
        self.test_groq_btn.configure(state="disabled")
        self.groq_status_lbl.configure(text="🔌 Status: Conectando...", text_color="#3B82F6")
        self.log("Testando conexão com a Groq...", "INFO")
        
        thread = threading.Thread(target=self.run_test_groq_connection, args=(key,))
        thread.daemon = True
        thread.start()

    def run_test_groq_connection(self, key):
        from groq_rag import GroqRAG
        tester = GroqRAG(api_key=key)
        success, msg = tester.test_connection()
        self.after(0, self.on_test_groq_completed, success, msg)

    def on_test_groq_completed(self, success, msg):
        self.test_groq_btn.configure(state="normal")
        if success:
            self.groq_status_lbl.configure(text="✅ Status: Conectado", text_color="#10B981")
            self.log(msg, "SUCCESS")
            self.salvar_groq_config()
        else:
            self.groq_status_lbl.configure(text="❌ Status: Erro", text_color="#EF4444")
            self.log(msg, "ERROR")


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
                    
                    self.log("Consolidando guias individuais de HSR...", "INFO")
                    bundle_guides("hsr/guias", "hsr/todos_os_guias_hsr.md", "Honkai: Star Rail")
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
                    
                    self.log("Consolidando guias individuais de ZZZ...", "INFO")
                    bundle_guides("zzz/guias", "zzz/todos_os_guias_zzz.md", "Zenless Zone Zero")
                except Exception as scraper_err:
                    traceback.print_exc()
                    self.log(f"Erro ao obter guias ZZZ: {scraper_err}", "ERROR")
                    
            elif game_id == "genshin":
                try:
                    # Puxa a lista de personagens do roster
                    extracted_characters = []
                    roster_path = "genshin/roster_genshin.md"
                    if os.path.exists(roster_path):
                        try:
                            with open(roster_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    if line.startswith("|") and not line.startswith("| Personagem") and not line.startswith("| :---"):
                                        parts = [p.strip() for p in line.split("|")]
                                        if len(parts) > 2:
                                            cname = parts[1].replace("**", "").strip()
                                            if cname and cname not in extracted_characters:
                                                extracted_characters.append(cname)
                        except Exception as e:
                            self.log(f"Erro ao carregar roster de Genshin: {e}", "WARN")
                    
                    if not extracted_characters:
                        self.log("Roster de Genshin não encontrado. Usando lista padrão de personagens populares.", "INFO")
                        extracted_characters = ["Keqing", "Hu Tao", "Raiden Shogun", "Furina", "Nahida", "Bennett", "Zhongli", "Kaedehara Kazuha", "Yelan", "Xingqiu"]
                        
                    self.log(f"Iniciando raspagem de guias KQM para {len(extracted_characters)} personagens de Genshin...", "INFO")
                    from scraper_kqm import KQMScraper
                    
                    kqm = KQMScraper(output_dir="genshin/guias")
                    kqm.scrape_all_guides(character_list=extracted_characters, logger_cb=self.log)
                    self.log("Guias do KQM extraídos e salvos em: genshin/guias/", "SUCCESS")
                    
                    self.log("Consolidando guias individuais de Genshin...", "INFO")
                    bundle_guides("genshin/guias", "genshin/todos_os_guias_genshin.md", "Genshin Impact")
                except Exception as scraper_err:
                    traceback.print_exc()
                    self.log(f"Erro ao extrair guias do KQM: {scraper_err}", "ERROR")


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
                try:
                    self.log("Iniciando extração do meta e endgame de GENSHIN do Game8...", "INFO")
                    from scraper_genshin_meta import GenshinMetaScraper
                    
                    meta_scraper = GenshinMetaScraper(output_path="genshin/meta_kqm_genshin.md")
                    meta_scraper.run_full_scrape(logger_cb=self.log)
                    self.log("Relatório de Endgame e Tier List salvos em: genshin/meta_kqm_genshin.md", "SUCCESS")
                except Exception as meta_err:
                    traceback.print_exc()
                    self.log(f"Erro ao extrair metagame do Genshin: {meta_err}", "ERROR")

                
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
    # GERENCIAMENTO DO CHAT ASSISTENTE IA RAG
    # ==========================================
    
    def setup_chat_frame(self, container):
        # Banner Superior
        banner_img = self.create_game_banner(
            banner_path="assets/config_banner.png",
            theme_color_hex="#1D4ED8",
            title="HoYo AI Assistant",
            subtitle="Assistente IA integrado com RAG local em tempo real (Groq / Llama 3.3)"
        )
        header_banner = ctk.CTkLabel(container, image=banner_img, text="", corner_radius=12)
        header_banner.pack(fill="x", padx=10, pady=(10, 10))
        
        # Filtro de Jogo Ativo / Contexto
        filter_frame = ctk.CTkFrame(container, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        filter_lbl = ctk.CTkLabel(
            filter_frame,
            text="Contexto do Assistente RAG:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#E4E4E7"
        )
        filter_lbl.pack(side="left", padx=(5, 10))
        
        self.chat_game_selector = ctk.CTkSegmentedButton(
            filter_frame,
            values=["Todos", "ZZZ", "Genshin", "HSR"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            selected_color="#2563EB",
            selected_hover_color="#1D4ED8"
        )
        self.chat_game_selector.pack(side="left", fill="x", expand=True)
        self.chat_game_selector.set("Todos")
        
        # Scrollable Frame para o Histórico de Mensagens
        self.chat_scroll = ctk.CTkScrollableFrame(container, fg_color="#141416", corner_radius=12, border_width=1, border_color="#2D2D35")
        self.chat_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Adiciona mensagem de boas-vindas inicial
        self.append_welcome_message()
        
        # Base: Campo de Entrada de Texto e Enviar
        self.chat_input_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.chat_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.chat_entry = ctk.CTkEntry(
            self.chat_input_frame,
            placeholder_text="Pergunte sobre builds do meta, seu roster, equipes recomendadas...",
            height=40,
            corner_radius=8
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda event: self.send_chat_message())
        
        self.chat_send_btn = ctk.CTkButton(
            self.chat_input_frame,
            text="🚀 Enviar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            width=80,
            height=40,
            corner_radius=8,
            command=self.send_chat_message
        )
        self.chat_send_btn.pack(side="left", padx=(0, 10))
        
        self.chat_clear_btn = ctk.CTkButton(
            self.chat_input_frame,
            text="🧹 Limpar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            width=80,
            height=40,
            corner_radius=8,
            command=self.clear_chat_history
        )
        self.chat_clear_btn.pack(side="left")

    def append_welcome_message(self):
        welcome = (
            "Olá! Eu sou o HoYo AI Assistant, seu conselheiro do metagame.\n\n"
            "Posso analisar seus personagens extraídos e relacioná-los com as informações das builds do Prydwen, KeqingMains e Game8 para recomendar composições e builds ótimas.\n\n"
            "Como posso te ajudar hoje?"
        )
        self.add_message_bubble("assistant", welcome)

    def add_message_bubble(self, sender: str, text: str):
        bubble_container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_container.pack(fill="x", padx=5, pady=6)
        
        is_user = (sender.lower() == "user")
        
        align_side = "right" if is_user else "left"
        fg_color = "#1D4ED8" if is_user else "#27272A"
        prefix = "🧑 Você:" if is_user else "🤖 Assistente Groq:"
        
        # Calcula tamanho vertical adequado para o CTkTextbox com base no conteúdo
        lines_count = max(len(text.split('\n')), 1)
        tb_height = min(max(lines_count * 20 + 20, 50), 380)
        
        sender_lbl = ctk.CTkLabel(
            bubble_container,
            text=prefix,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#A1A1AA"
        )
        sender_lbl.pack(anchor="ne" if is_user else "nw", padx=8, pady=(0, 2))
        
        tb = ctk.CTkTextbox(
            bubble_container,
            fg_color=fg_color,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=tb_height,
            corner_radius=10,
            border_width=0,
            wrap="word"
        )
        tb.pack(anchor="ne" if is_user else "nw", fill="x", padx=5, expand=True)
        tb.insert("1.0", text)
        tb.configure(state="disabled")
        
        # Autoscroll suave
        self.after(60, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def send_chat_message(self):
        query = self.chat_entry.get().strip()
        if not query:
            return
            
        self.chat_entry.delete(0, "end")
        self.add_message_bubble("user", query)
        self.chat_history.append({"role": "user", "text": query})
        
        # Estado carregando
        self.chat_entry.configure(state="disabled")
        self.chat_send_btn.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.status_label.configure(text="Groq pensando... ⌛", text_color="#3B82F6")
        
        # Identifica filtro de jogo selecionado
        game_sel = self.chat_game_selector.get().lower()
        game_id = "todos"
        if "zzz" in game_sel:
            game_id = "zzz"
        elif "genshin" in game_sel:
            game_id = "genshin"
        elif "hsr" in game_sel:
            game_id = "hsr"
            
        thread = threading.Thread(target=self.process_chat_api_call, args=(query, game_id), daemon=True)
        thread.start()

    def process_chat_api_call(self, query: str, game_id: str):
        try:
            if not self.groq_rag.client:
                # Recarrega se não inicializado
                from groq_rag import GroqRAG
                self.groq_rag = GroqRAG()
                
            history_input = self.chat_history[:-1] # exclui a query recém-adicionada
            contexto = self.groq_rag.load_game_context(game_id, query)
            response = self.groq_rag.ask_assistant(query, contexto, history_input)
            self.after(0, self.on_chat_response_received, response)
        except Exception as e:
            traceback.print_exc()
            self.after(0, self.on_chat_response_received, f"Erro ao chamar assistente: {e}")

    def on_chat_response_received(self, response: str):
        self.add_message_bubble("model", response)
        self.chat_history.append({"role": "model", "text": response})
        
        # Desliga carregamento
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.chat_entry.configure(state="normal")
        self.chat_send_btn.configure(state="normal")
        self.chat_entry.focus()
        self.status_label.configure(text="Pronto.", text_color="#A1A1AA")

    def clear_chat_history(self):
        self.chat_history = []
        for child in self.chat_scroll.winfo_children():
            child.destroy()
        self.append_welcome_message()
        self.log("Histórico de conversa limpo.", "INFO")

if __name__ == "__main__":
    app = App()
    app.mainloop()
