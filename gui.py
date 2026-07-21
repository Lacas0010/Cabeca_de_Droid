import os
import re
import json
import asyncio
import threading
import traceback
import time
import datetime
import sys
import webbrowser
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
        self.loaded_images_cache = {}
        
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
        self.after(100, self.start_avatar_prefetch)
        self.log("HoYo AI Assistant inicializado com sucesso. Pronto.", "SUCCESS")
        
    def center_window(self, width: int, height: int):
        """Centraliza a janela na tela do usuário."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def resource_path(self, relative_path: str):
        """ Retorna o caminho absoluto do recurso, compatível com PyInstaller --onefile """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def load_sidebar_icon(self, icon_path: str):
        """Carrega e redimensiona um ícone de sidebar, retornando um CTkImage ou None."""
        full_path = self.resource_path(icon_path)
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path).convert("RGBA")
                return ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
            except Exception as e:
                self.log(f"Erro ao carregar ícone {full_path}: {e}", "WARN")
        return None

    def hex_to_rgb(self, hex_str: str) -> tuple:
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def create_game_banner(self, banner_path: str, theme_color_hex: str, title: str, subtitle: str, width: int = 750, height: int = 125) -> ctk.CTkImage:
        """
        Preenche 100% do banner com a arte do jogo e adiciona um degradê
        escuro no canto esquerdo para garantir leitura do texto.
        """
        full_path = self.resource_path(banner_path)
        try:
            # 1. Carrega e ajusta a imagem para preencher 100% do container (Crop estilo Cover)
            if os.path.exists(full_path):
                img = Image.open(full_path).convert("RGBA")
                
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
                self.log(f"Asset de banner não encontrado: {full_path}. Usando cor sólida.", "INFO")
                final_banner = Image.new("RGBA", (width, height), theme_color_hex)

        except Exception as e:
            self.log(f"Erro ao carregar banner {full_path}: {e}", "WARN")
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
        icon_help = self.load_sidebar_icon("assets/help_icon.png")
        
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
        
        self.btn_help = ctk.CTkButton(
            self.sidebar,
            text=" Como Usar" if icon_help else "❓ Como Usar",
            image=icon_help,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color="#D4D4D8",
            hover_color="#2E2E35",
            anchor="w",
            command=lambda: self.select_frame("how_to")
        )
        self.btn_help.pack(padx=15, pady=4, fill="x")
        
        # Botão Global de Sincronizar Todos os Jogos em 1-Clique
        self.btn_sync_all = ctk.CTkButton(
            self.sidebar,
            text="🚀 Sincronizar Tudo",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            text_color="#FFFFFF",
            command=self.run_sync_all_games
        )
        self.btn_sync_all.pack(padx=15, pady=(12, 4), fill="x")
        
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
        from status_logger import StatusLoggerFrame
        self.terminal_container = ctk.CTkFrame(self, fg_color="transparent")
        self.terminal_container.pack(side="bottom", fill="x", expand=False)
        
        self.loggers = {}
        logger_titles = {
            "zzz": "Status - Zenless Zone Zero",
            "genshin": "Status - Genshin Impact",
            "hsr": "Status - Honkai: Star Rail",
            "global": "Status do Sistema"
        }
        
        for key, title in logger_titles.items():
            st_frame = StatusLoggerFrame(self.terminal_container, title=title, corner_radius=0, border_width=0)
            self.loggers[key] = st_frame
            
        self.active_logger_key = None
        self.switch_status_logger("global")

    def switch_status_logger(self, key: str):
        target_key = key if key in self.loggers else "global"
        if self.active_logger_key == target_key:
            return
            
        for k, logger_frame in self.loggers.items():
            logger_frame.pack_forget()
            
        self.loggers[target_key].pack(side="bottom", fill="x", expand=False)
        self.active_logger_key = target_key
        self.progress_bar = self.loggers[target_key].progress_bar

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
        
        # 6. Frame de Como Usar
        self.frame_how_to = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.build_how_to_screen(self.frame_how_to)

    def select_frame(self, name: str):
        # Alterna o logger de status do rodapé para o jogo/aba correspondente
        self.switch_status_logger(name)

        # Oculta todos os frames principais
        self.frame_zzz.pack_forget()
        self.frame_genshin.pack_forget()
        self.frame_hsr.pack_forget()
        self.frame_config.pack_forget()
        self.frame_chat.pack_forget()
        self.frame_how_to.pack_forget()
        
        # Reseta cores de fundo dos botões da sidebar para transparente
        self.btn_zzz.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_genshin.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_hsr.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_config.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_chat.configure(fg_color="transparent", text_color="#D4D4D8")
        self.btn_help.configure(fg_color="transparent", text_color="#D4D4D8")
        
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
        elif name == "how_to":
            self.btn_help.configure(fg_color="#10B981", text_color="#FFFFFF")
            self.frame_how_to.pack(fill="both", expand=True, padx=5, pady=5)

    def open_game_folder(self, game_id: str):
        """Abre o diretório local do jogo no Windows Explorer."""
        folder_path = os.path.abspath(game_id)
        os.makedirs(folder_path, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            else:
                import subprocess
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder_path])
        except Exception as e:
            self.log(f"Erro ao abrir pasta {folder_path}: {e}", "WARN", game_id=game_id)

    def parse_roster_summary(self, game_id: str) -> dict:
        """Lê o arquivo roster_{game_id}.md se existir e extrai estatísticas resumidas."""
        filepath = f"{game_id}/roster_{game_id}.md"
        if not os.path.exists(filepath):
            return None
            
        summary = {
            "exists": True,
            "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%d/%m %H:%M"),
            "uid": "N/A",
            "level": "N/A",
            "total_chars": 0,
            "5star_count": 0
        }
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # UID: pega tanto "(UID: 600156277)" quanto "**UID:** 1000135767"
            m_uid = re.search(r'UID[^\d]*(\d+)', content)
            if m_uid:
                summary["uid"] = m_uid.group(1)
                
            # Nível: pega **Nível de Desbravamento:** 70 ou **Nível de Intermediário:** 59
            m_lvl = re.search(r'\*\*Nível[^*:]*:\*\*\s*(\d+)', content)
            if m_lvl:
                summary["level"] = f"Nv. {m_lvl.group(1)}"
            else:
                summary["level"] = "Ativo"
                
            lines = content.splitlines()
            char_lines = [l for l in lines if l.startswith("|") and not l.startswith("| Personagem") and not l.startswith("| Agente") and not l.startswith("| :---")]
            summary["total_chars"] = len(char_lines)
            
            # 5 estrelas: verifica ⭐⭐⭐⭐⭐, S (⭐⭐⭐⭐⭐), 5★ ou 5 Estrelas
            five_stars = [l for l in char_lines if "⭐⭐⭐⭐⭐" in l or "S (" in l or "5★" in l or "5 Estrelas" in l]
            summary["5star_count"] = len(five_stars)
        except Exception:
            pass
            
        return summary

    def run_sync_all_games(self):
        """Dispara as tarefas de todos os jogos simultaneamente em background."""
        self.show_toast("🚀 Sincronização Global Iniciada", "Atualizando ZZZ, Genshin e HSR em segundo plano...")
        for g_id in ["zzz", "genshin", "hsr"]:
            self.start_game_task_thread(g_id)
            
    def start_avatar_prefetch(self):
        """Baixa todos os avatares dos personagens em background em paralelo para a Galeria Visual carregar instantaneamente."""
        def _bg_prefetch():
            import concurrent.futures
            for game_id in ["zzz", "genshin", "hsr"]:
                chars = self.parse_roster_characters(game_id)
                def _download_one(c):
                    c_name = c.get("name", "")
                    if not c_name: return
                    url = c.get("icon", "") or self.get_fallback_avatar_url(game_id, c_name)
                    if not url: return
                    safe_fn = re.sub(r'[^a-zA-Z0-9]', '_', c_name.lower()) + ".png"
                    cache_path = f"assets/avatars/{game_id}/{safe_fn}"
                    if not os.path.exists(cache_path) or os.path.getsize(cache_path) < 500:
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                            res = requests.get(url, headers=headers, timeout=6)
                            if res.status_code == 200 and len(res.content) > 500:
                                with open(cache_path, "wb") as f:
                                    f.write(res.content)
                        except Exception:
                            pass
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(_download_one, chars[:50])
            try:
                self.after(0, lambda: self.update_dashboard_ui(self.current_game))
            except Exception:
                pass
        threading.Thread(target=_bg_prefetch, daemon=True).start()

    def load_remote_image(self, url: str, cache_path: str, size: tuple = (40, 40), target_label=None) -> ctk.CTkImage:
        """Carrega imagem do cache local se existir; se não, baixa em background sem travar a UI."""
        cache_key = f"{cache_path}_{size[0]}x{size[1]}"
        if cache_key in self.loaded_images_cache:
            return self.loaded_images_cache[cache_key]
            
        if os.path.exists(cache_path) and os.path.getsize(cache_path) >= 500:
            try:
                img = Image.open(cache_path).convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                self.loaded_images_cache[cache_key] = ctk_img
                return ctk_img
            except Exception:
                pass
                
        if url and target_label:
            def _async_download():
                try:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    res = requests.get(url, headers=headers, timeout=8)
                    if res.status_code == 200 and len(res.content) > 500:
                        with open(cache_path, "wb") as f:
                            f.write(res.content)
                        img = Image.open(cache_path).convert("RGBA")
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                        self.loaded_images_cache[cache_key] = ctk_img
                        
                        def _update():
                            if target_label.winfo_exists():
                                target_label.configure(image=ctk_img, text="")
                                target_label._img_ref = ctk_img
                        self.after(0, _update)
                except Exception:
                    pass
            threading.Thread(target=_async_download, daemon=True).start()
            
        return None

    def parse_roster_characters(self, game_id: str) -> list:
        """Extrai lista de personagens a partir do JSON ou diretamente do roster_{game_id}.md."""
        json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    if data:
                        return data
            except Exception:
                pass
                
        md_path = f"{game_id}/roster_{game_id}.md"
        if not os.path.exists(md_path):
            return []
            
        chars = []
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            for l in lines:
                if not l.startswith("|") or l.startswith("| Personagem") or l.startswith("| Agente") or l.startswith("| :---"):
                    continue
                parts = [p.strip() for p in l.split("|")[1:-1]]
                if len(parts) >= 4:
                    name = parts[0]
                    lvl_raw = parts[1].replace("Nv.", "").strip()
                    rarity_str = parts[2]
                    rank_str = parts[3]
                    
                    rarity = 5 if ("⭐⭐⭐⭐⭐" in rarity_str or "S (" in rarity_str or "5" in rarity_str) else 4
                    
                    element = "Físico"
                    if len(parts) >= 6:
                        element = parts[5]
                    elif len(parts) == 5:
                        element = parts[4]
                        
                    chars.append({
                        "name": name,
                        "level": lvl_raw,
                        "rarity": rarity,
                        "rank_str": rank_str,
                        "element": element,
                        "icon": ""
                    })
        except Exception as e:
            print(f"Aviso ao parsear personagens do md: {e}")
            
        return chars

    def get_character_build_detail(self, game_id: str, char_name: str) -> str:
        """Lê roster_{game_id}.md e extrai o bloco de detalhes da build do personagem especificado."""
        filepath = f"{game_id}/roster_{game_id}.md"
        if not os.path.exists(filepath):
            return "Nenhum relatório de Roster extraído ainda."
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            pattern = rf'(\*\*(?:Personagem|Agente):\*\*\s*{re.escape(char_name)}.*?)(?=\n\*\*(?:Personagem|Agente):\*\*|\n## |\Z)'
            match = re.search(pattern, content, re.DOTALL | re.I)
            if match:
                return match.group(1).strip()
        except Exception as e:
            print(f"Erro ao buscar detalhes da build de {char_name}: {e}")
            
        return f"Build detalhada de {char_name} não encontrada no relatório.\n\n(Dica: Personagens no nível máximo possuem relatórios completos com armas/cones, conjuntos de artefatos/relíquias e substatus no arquivo roster_{game_id}.md)."

    def parse_character_build_data(self, game_id: str, char_name: str) -> dict:
        """Lê roster_{game_id}.md e estrutura todos os dados da build em um dicionário limpo."""
        raw_text = self.get_character_build_detail(game_id, char_name)
        
        data = {
            "name": char_name,
            "raw": raw_text,
            "weapon": "Não informado / Nível < máx.",
            "sets": [],
            "stats": {},
            "pieces": []
        }
        
        if "não encontrada" in raw_text.lower():
            return data
            
        m_w = re.search(r'-\s*\*\*(?:Cone de Luz|Arma|W-Engine):\*\*\s*(.*)', raw_text)
        if m_w:
            data["weapon"] = m_w.group(1).strip()
            
        m_s = re.search(r'-\s*\*\*(?:Relíquias|Artefatos|Discos):\*\*\s*(.*)', raw_text)
        if m_s:
            sets_raw = m_s.group(1).strip()
            data["sets"] = [s.strip() for s in sets_raw.split('+')]
            
        m_st = re.search(r'-\s*\*\*Status Finais:\*\*\s*(.*)', raw_text)
        if m_st:
            stats_raw = m_st.group(1).strip()
            for pair in stats_raw.split(','):
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    data["stats"][k.strip()] = v.strip()
                    
        m_pieces = re.findall(r'•\s*\[(.*?)\]\s*(.*?)\n\s*-\s*Principal:\s*(.*?)\n\s*-\s*Substatus:\s*(.*?)(?=\n\s*•|\Z|\n\n|\n---)', raw_text, re.DOTALL)
        for slot, p_name, main_s, sub_s in m_pieces:
            data["pieces"].append({
                "slot": slot.strip(),
                "name": p_name.strip(),
                "main": main_s.strip(),
                "sub": sub_s.strip()
            })
            
        return data

    def get_fallback_avatar_url(self, game_id: str, char_name: str) -> str:
        """Retorna uma URL de CDN pública para avatares caso a extração inicial não tenha imagem."""
        safe_n = char_name.strip()
        if game_id == "hsr":
            safe_mapped = {
                "Desbravador(a)": "8001", "Himeko": "1003", "Himeko - Nova": "1003",
                "Seele": "1102", "Bronya": "1101", "Kafka": "1005", "Blade": "1205",
                "Jingliu": "1212", "Acheron": "1308", "Firefly": "1310", "Ruan Mei": "1303",
                "Robin": "1309", "Sparkle": "1306", "Luocha": "1203", "Aventurine": "1304",
                "Fu Xuan": "1208", "Silver Wolf": "1006", "Loba Prateada": "1006",
                "Tingyun": "1202", "Pela": "1105", "Evanescia": "1308", "Yao Guang": "1204",
                "Cyrene": "1306", "Sparxie": "1306", "Castorice": "1308", "Cipher": "1006",
                "A Herta": "1013", "A Dália": "1303", "Rappa": "1317"
            }
            char_id = safe_mapped.get(safe_n, "8001")
            return f"https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/avatar/{char_id}.png"
        elif game_id == "genshin":
            clean_name = safe_n.replace(" ", "")
            return f"https://enka.network/ui/UI_AvatarIcon_{clean_name}.png"
        elif game_id == "zzz":
            clean_name = safe_n.replace(" ", "")
            return f"https://raw.githubusercontent.com/Mar-7th/ZenlessZoneZeroRes/main/icon/agent/{clean_name}.png"
        return ""

    def inspect_character_build(self, game_id: str, char_info: dict):
        """Exibe o painel retrátil de Build Detalhada diretamente DENTRO da página principal (Zero popups!)."""
        char_name = char_info.get("name", "Personagem")
        build_data = self.parse_character_build_data(game_id, char_name)
        
        container = getattr(self, f"{game_id}_build_inspector_frame", None)
        if not container:
            return
            
        for widget in container.winfo_children():
            widget.destroy()
            
        container.pack(fill="x", padx=12, pady=(0, 12))
        
        # Header do Painel de Build
        hdr = ctk.CTkFrame(container, fg_color="#18181B", corner_radius=10, border_width=1, border_color="#3B82F6")
        hdr.pack(fill="x", padx=4, pady=(4, 6))
        
        # Esquerda: Avatar + Nome + Nível + Elemento
        left_box = ctk.CTkFrame(hdr, fg_color="transparent")
        left_box.pack(side="left", padx=12, pady=8)
        
        c_icon_url = char_info.get("icon", "") or self.get_fallback_avatar_url(game_id, char_name)
        safe_fn = re.sub(r'[^a-zA-Z0-9]', '_', char_name.lower()) + ".png"
        c_path = f"assets/avatars/{game_id}/{safe_fn}"
        
        lbl_hdr_avatar = ctk.CTkLabel(left_box, text="👤", font=ctk.CTkFont(size=22))
        lbl_hdr_avatar.pack(side="left", padx=(0, 10))
        
        ctk_img = self.load_remote_image(c_icon_url, c_path, size=(44, 44), target_label=lbl_hdr_avatar)
        if ctk_img:
            lbl_hdr_avatar.configure(image=ctk_img, text="")
            lbl_hdr_avatar._img_ref = ctk_img
            
        name_box = ctk.CTkFrame(left_box, fg_color="transparent")
        name_box.pack(side="left")
        
        ctk.CTkLabel(name_box, text=f"⚔️ Build Detalhada: {char_name}", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        sub_info = f"{char_info.get('rank_str', '')} • Elemento: {char_info.get('element', 'Desconhecido')} • Nível {char_info.get('level', '')}"
        ctk.CTkLabel(name_box, text=sub_info, font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#A1A1AA").pack(anchor="w")
        
        # Direita: Botão Fechar Painel
        btn_close = ctk.CTkButton(
            hdr,
            text="❌ Fechar Detalhes",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#3F3F46",
            hover_color="#52525B",
            height=28,
            width=110,
            command=lambda: container.pack_forget()
        )
        btn_close.pack(side="right", padx=12, pady=8)
        
        # Corpo Principal: Grid com Equipamento, Relíquias e Status Finais
        body = ctk.CTkFrame(container, fg_color="#09090B", corner_radius=10)
        body.pack(fill="x", padx=4, pady=(0, 4))
        
        # Linha 1: Arma + Conjuntos de Relíquias
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(8, 4))
        row1.grid_columnconfigure((0, 1), weight=1)
        
        # Card Arma
        w_card = ctk.CTkFrame(row1, fg_color="#18181B", corner_radius=8, border_width=1, border_color="#27272A")
        w_card.grid(row=0, column=0, padx=4, sticky="ew")
        
        w_info = char_info.get("weapon", {})
        w_icon_url = w_info.get("icon", "")
        w_box = ctk.CTkFrame(w_card, fg_color="transparent")
        w_box.pack(fill="x", padx=8, pady=6)
        
        if w_icon_url:
            w_fn = re.sub(r'[^a-zA-Z0-9]', '_', build_data['weapon'].lower()) + ".png"
            w_path = f"assets/weapons/{game_id}/{w_fn}"
            lbl_w = ctk.CTkLabel(w_box, text="")
            lbl_w.pack(side="left", padx=(0, 8))
            w_img = self.load_remote_image(w_icon_url, w_path, size=(36, 36), target_label=lbl_w)
            if w_img:
                lbl_w.configure(image=w_img)
                lbl_w._img_ref = w_img
                
        w_txt_box = ctk.CTkFrame(w_box, fg_color="transparent")
        w_txt_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(w_txt_box, text="🗡️ EQUIPAMENTO / ARMA", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(anchor="w")
        ctk.CTkLabel(w_txt_box, text=build_data["weapon"], font=ctk.CTkFont(size=11, weight="bold"), text_color="#3B82F6", wraplength=240).pack(anchor="w")
        
        # Card Conjuntos
        s_card = ctk.CTkFrame(row1, fg_color="#18181B", corner_radius=8, border_width=1, border_color="#27272A")
        s_card.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(s_card, text="🔮 CONJUNTOS DE ARTEFATOS / RELÍQUIAS", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(padx=10, pady=(6, 2), anchor="w")
        sets_text = " + ".join(build_data["sets"]) if build_data["sets"] else "Nenhum conjunto ativado"
        ctk.CTkLabel(s_card, text=sets_text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981", wraplength=260).pack(padx=10, pady=(0, 8), anchor="w")
        
        # Linha 2: Pílulas de Status Finais
        if build_data["stats"]:
            st_card = ctk.CTkFrame(body, fg_color="#18181B", corner_radius=8, border_width=1, border_color="#27272A")
            st_card.pack(fill="x", padx=12, pady=4)
            
            ctk.CTkLabel(st_card, text="📊 STATUS FINAIS CONSOLIDADOS", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(padx=10, pady=(6, 2), anchor="w")
            
            pills_box = ctk.CTkFrame(st_card, fg_color="transparent")
            pills_box.pack(fill="x", padx=6, pady=(0, 6))
            
            for k, v in build_data["stats"].items():
                pill = ctk.CTkFrame(pills_box, fg_color="#27272A", corner_radius=6)
                pill.pack(side="left", padx=2, pady=2)
                ctk.CTkLabel(pill, text=f"{k}: ", font=ctk.CTkFont(size=9), text_color="#A1A1AA").pack(side="left", padx=(6, 0), pady=2)
                ctk.CTkLabel(pill, text=f"{v}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B").pack(side="left", padx=(0, 6), pady=2)
                
        # Linha 3: Cards de Peças Individuais (Substatus)
        if build_data["pieces"]:
            pc_box = ctk.CTkFrame(body, fg_color="transparent")
            pc_box.pack(fill="x", padx=10, pady=(4, 8))
            
            ctk.CTkLabel(pc_box, text="📜 DETALHAMENTO DE PEÇAS E SUBSTATUS", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(padx=4, pady=(2, 4), anchor="w")
            
            pc_scroll = ctk.CTkScrollableFrame(pc_box, orientation="horizontal", height=80, fg_color="transparent")
            pc_scroll.pack(fill="x")
            
            for piece in build_data["pieces"]:
                p_frame = ctk.CTkFrame(pc_scroll, fg_color="#18181B", corner_radius=8, width=170, height=75, border_width=1, border_color="#27272A")
                p_frame.pack(side="left", padx=3, pady=2)
                p_frame.pack_propagate(False)
                
                ctk.CTkLabel(p_frame, text=f"[{piece['slot']}] {piece['name'][:18]}", font=ctk.CTkFont(size=9, weight="bold"), text_color="#8B5CF6").pack(padx=6, pady=(4, 0), anchor="w")
                ctk.CTkLabel(p_frame, text=f"Principal: {piece['main']}", font=ctk.CTkFont(size=9, weight="bold"), text_color="#10B981").pack(padx=6, pady=0, anchor="w")
                ctk.CTkLabel(p_frame, text=f"Subs: {piece['sub']}", font=ctk.CTkFont(size=8), text_color="#D4D4D8", wraplength=160).pack(padx=6, pady=(0, 4), anchor="w")

    def update_dashboard_ui(self, game_id: str):
        card = getattr(self, f"{game_id}_dashboard_card", None)
        if not card:
            return
            
        for widget in card.winfo_children():
            widget.destroy()
            
        info = self.parse_roster_summary(game_id)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=16, pady=12, fill="x")
        
        if info:
            inner.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            # Col 0: UID
            f0 = ctk.CTkFrame(inner, fg_color="#27272A", corner_radius=8)
            f0.grid(row=0, column=0, padx=4, sticky="ew")
            ctk.CTkLabel(f0, text="UID DA CONTA", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(pady=(6, 0))
            ctk.CTkLabel(f0, text=info["uid"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#3B82F6").pack(pady=(0, 6))
            
            # Col 1: Nível
            f1 = ctk.CTkFrame(inner, fg_color="#27272A", corner_radius=8)
            f1.grid(row=0, column=1, padx=4, sticky="ew")
            ctk.CTkLabel(f1, text="NÍVEL DE JOGO", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(pady=(6, 0))
            ctk.CTkLabel(f1, text=info["level"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#10B981").pack(pady=(0, 6))
            
            # Col 2: Total de Personagens
            f2 = ctk.CTkFrame(inner, fg_color="#27272A", corner_radius=8)
            f2.grid(row=0, column=2, padx=4, sticky="ew")
            ctk.CTkLabel(f2, text="ROSTER OBTIDO", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(pady=(6, 0))
            ctk.CTkLabel(f2, text=f"{info['total_chars']} Chars ({info['5star_count']} 5★)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F59E0B").pack(pady=(0, 6))
            
            # Col 3: Última Sincronização
            f3 = ctk.CTkFrame(inner, fg_color="#27272A", corner_radius=8)
            f3.grid(row=0, column=3, padx=4, sticky="ew")
            ctk.CTkLabel(f3, text="ÚLTIMA SINCRONIZAÇÃO", font=ctk.CTkFont(size=9, weight="bold"), text_color="#A1A1AA").pack(pady=(6, 0))
            ctk.CTkLabel(f3, text=f"🟢 {info['mtime']}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#8B5CF6").pack(pady=(0, 6))
            
            # Col 4: Botão de Abrir Pasta no Explorer
            btn_folder = ctk.CTkButton(
                inner,
                text="📁 Pasta (.md)",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#3F3F46",
                hover_color="#52525B",
                height=38,
                command=lambda g=game_id: self.open_game_folder(g)
            )
            btn_folder.grid(row=0, column=4, padx=4, sticky="ew")
            
            # Renderiza a Galeria Visual de Personagens (com fallback pro MD)
            char_data = self.parse_roster_characters(game_id)
            if char_data:
                try:
                    gallery_box = ctk.CTkFrame(card, fg_color="#141416", corner_radius=10)
                    gallery_box.pack(fill="x", padx=12, pady=(0, 12))
                    
                    lbl_gal = ctk.CTkLabel(
                        gallery_box,
                        text="🎴 Galeria Visual de Personagens Extraídos (Clique para ver a Build completa)",
                        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                        text_color="#E4E4E7"
                    )
                    lbl_gal.pack(padx=12, pady=(8, 4), anchor="w")
                    
                    scroll_gal = ctk.CTkScrollableFrame(
                        gallery_box,
                        orientation="horizontal",
                        height=90,
                        fg_color="transparent"
                    )
                    scroll_gal.pack(fill="x", padx=6, pady=(0, 8))
                    
                    elem_colors = {
                        "Fogo": "#5F1D1D", "Pyro": "#5F1D1D", "Fire": "#5F1D1D",
                        "Gelo": "#1D3A5F", "Cryo": "#1D3A5F", "Ice": "#1D3A5F",
                        "Vento": "#1D5F3A", "Anemo": "#1D5F3A", "Wind": "#1D5F3A",
                        "Raio": "#4D1D5F", "Electro": "#4D1D5F", "Lightning": "#4D1D5F",
                        "Quântico": "#2E1D5F", "Quantum": "#2E1D5F",
                        "Imaginário": "#5F4D1D", "Geo": "#5F4D1D", "Imaginary": "#5F4D1D",
                        "Dendro": "#1D5F2E", "Hydro": "#085F75", "Físico": "#374151", "Physical": "#374151"
                    }
                    
                    for char in char_data[:40]: # Exibe os 40 principais
                        bg_c = elem_colors.get(char.get("element", ""), "#27272A")
                        
                        c_card = ctk.CTkFrame(scroll_gal, fg_color=bg_c, corner_radius=8, width=105, height=85)
                        c_card.pack(side="left", padx=4, pady=2)
                        c_card.pack_propagate(False)
                        
                        # Torna o card inteiro clicável para abrir a build no painel da própria página
                        c_card.bind("<Button-1>", lambda e, g=game_id, c=char: self.inspect_character_build(g, c))
                        
                        c_name = char["name"]
                        if len(c_name) > 11:
                            c_name = c_name[:10] + "…"
                            
                        lbl_n = ctk.CTkLabel(c_card, text=c_name, font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF")
                        lbl_n.pack(pady=(4, 0))
                        lbl_n.bind("<Button-1>", lambda e, g=game_id, c=char: self.inspect_character_build(g, c))
                        
                        c_icon_url = char.get("icon", "") or self.get_fallback_avatar_url(game_id, char['name'])
                        safe_fn = re.sub(r'[^a-zA-Z0-9]', '_', char['name'].lower()) + ".png"
                        c_path = f"assets/avatars/{game_id}/{safe_fn}"
                        
                        lbl_i = ctk.CTkLabel(c_card, text="👤", font=ctk.CTkFont(size=18))
                        lbl_i.pack(pady=1)
                        lbl_i.bind("<Button-1>", lambda e, g=game_id, c=char: self.inspect_character_build(g, c))
                        
                        ctk_img = self.load_remote_image(c_icon_url, c_path, size=(36, 36), target_label=lbl_i)
                        if ctk_img:
                            lbl_i.configure(image=ctk_img, text="")
                            lbl_i._img_ref = ctk_img
                            
                        r_lvl = f"{char.get('rank_str', '')} • Nv.{char.get('level', '')}"
                        lbl_r = ctk.CTkLabel(c_card, text=r_lvl, font=ctk.CTkFont(size=9), text_color="#F4F4F5")
                        lbl_r.pack(pady=(0, 4))
                        lbl_r.bind("<Button-1>", lambda e, g=game_id, c=char: self.inspect_character_build(g, c))
                        
                    # Frame container para a inspeção de build embutida na página (retrátil)
                    inspector_frame = ctk.CTkFrame(card, fg_color="transparent")
                    setattr(self, f"{game_id}_build_inspector_frame", inspector_frame)
                except Exception as gal_err:
                    print(f"Aviso ao renderizar galeria visual: {gal_err}")
            
        else:
            inner.grid_columnconfigure(0, weight=3)
            inner.grid_columnconfigure(1, weight=1)
            
            lbl_empty = ctk.CTkLabel(
                inner,
                text="⚪ Nenhum dado extraído localmente para este jogo ainda. Marque as opções abaixo e execute!",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#A1A1AA",
                anchor="w"
            )
            lbl_empty.grid(row=0, column=0, padx=5, sticky="w")
            
            btn_folder = ctk.CTkButton(
                inner,
                text="📁 Abrir Pasta no Explorer",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#27272A",
                hover_color="#3F3F46",
                height=32,
                command=lambda g=game_id: self.open_game_folder(g)
            )
            btn_folder.grid(row=0, column=1, padx=5, sticky="e")

    def show_toast(self, title: str, message: str, level: str = "SUCCESS"):
        """Exibe uma notificação flutuante suave (Toast) temporária na UI."""
        def _create_toast():
            toast = ctk.CTkFrame(
                self,
                fg_color="#065F46" if level == "SUCCESS" else "#7F1D1D",
                corner_radius=10,
                border_width=1,
                border_color="#10B981" if level == "SUCCESS" else "#EF4444"
            )
            
            lbl_title = ctk.CTkLabel(
                toast,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#FFFFFF"
            )
            lbl_title.pack(padx=16, pady=(10, 2), anchor="w")
            
            lbl_msg = ctk.CTkLabel(
                toast,
                text=message,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#F4F4F5"
            )
            lbl_msg.pack(padx=16, pady=(0, 10), anchor="w")
            
            toast.place(relx=0.97, rely=0.04, anchor="ne")
            self.after(4000, lambda: toast.destroy() if toast.winfo_exists() else None)
            
        if threading.current_thread() is threading.main_thread():
            _create_toast()
        else:
            self.after(0, _create_toast)

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
        header_banner.pack(fill="x", padx=10, pady=(10, 12))
        
        # Dashboard Resumo da Conta & Acesso Rápido
        dashboard_card = ctk.CTkFrame(container, corner_radius=12, fg_color="#18181B", border_width=1, border_color="#27272A")
        dashboard_card.pack(fill="x", padx=10, pady=(0, 10))
        setattr(self, f"{game_id}_dashboard_card", dashboard_card)
        self.update_dashboard_ui(game_id)
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
            text=f"Extrair Roster, Eidolons/Constelações, Builds e Recordes de Endgames (Nível Máximo: {max_lvl})",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=theme_color,
            hover_color=theme_color
        )
        roster_cb.pack(padx=40, pady=(5, 20), anchor="w")
        roster_cb.select()
        
        # Card 2: Guias e Endgame (Coleta de Dados)
        card_scraping = ctk.CTkFrame(container, corner_radius=12, fg_color="#1C1C22", border_width=1, border_color="#2D2D35")
        card_scraping.pack(fill="x", padx=10, pady=10)
        
        scraping_title = ctk.CTkLabel(
            card_scraping,
            text="📚 Guias & Metagame (Sincronização Online)",
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

    def build_how_to_screen(self, container):
        title_lbl = ctk.CTkLabel(
            container,
            text="📖 Como usar o HoYo AI Assistant",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#F4F4F5"
        )
        title_lbl.pack(padx=20, pady=(20, 10), anchor="w")

        # Texto explicativo geral
        intro_text = (
            "Este aplicativo foi criado para ajudar você a analisar suas contas da HoYoverse utilizando Inteligência Artificial.\n"
            "Ele puxa automaticamente todos os seus dados públicos (Roster, Builds e Endgames) da HoYoLAB e cruza com dados de Metagame."
        )
        intro_lbl = ctk.CTkLabel(container, text=intro_text, font=ctk.CTkFont(family="Segoe UI", size=14), text_color="#D4D4D8", justify="left")
        intro_lbl.pack(padx=20, pady=(0, 20), anchor="w")

        # Passo a Passo (Configurações)
        step1_title = ctk.CTkLabel(container, text="1. Faça o Login na HoYoLAB", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#10B981")
        step1_title.pack(padx=20, pady=(10, 5), anchor="w")
        step1_text = (
            "Vá até a aba de '⚙️ Configurações' no menu esquerdo e clique em 'Login Automático (Navegador)'.\n"
            "O app vai abrir o site da HoYoLAB, onde você deve logar na sua conta. Após o login, ele irá extrair os cookies \n"
            "necessários (ltuid e ltoken) e salvá-los localmente para poder acessar seu histórico das contas."
        )
        step1_lbl = ctk.CTkLabel(container, text=step1_text, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#A1A1AA", justify="left")
        step1_lbl.pack(padx=20, pady=(0, 15), anchor="w")

        # Passo a Passo (Extração)
        step2_title = ctk.CTkLabel(container, text="2. Selecione o Jogo e Extraia os Dados", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#3B82F6")
        step2_title.pack(padx=20, pady=(10, 5), anchor="w")
        step2_text = (
            "Nas abas 'Zenless Zone Zero', 'Genshin Impact' ou 'Honkai: Star Rail', você encontra as opções de extração.\n"
            "- A opção 'Roster' vai buscar todos os seus personagens, níveis, constelações/eidolons, além de extrair todos os seus \n"
            "recordes recentes dos modos Endgame (MoC, Abismo, Shiyu).\n"
            "- A opção de Guias/Meta faz web-scraping automático de sites de tier list (como Prydwen e KeqingMains) para montar o RAG."
        )
        step2_lbl = ctk.CTkLabel(container, text=step2_text, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#A1A1AA", justify="left")
        step2_lbl.pack(padx=20, pady=(0, 15), anchor="w")

        # Passo a Passo (Chat IA)
        step3_title = ctk.CTkLabel(container, text="3. Converse com a Inteligência Artificial", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#8B5CF6")
        step3_title.pack(padx=20, pady=(10, 5), anchor="w")
        step3_text = (
            "Na aba '🤖 Chat IA Meta' você pode conversar diretamente com uma LLM treinada que já conhece sua conta.\n"
            "Para isso funcionar, você precisará gerar uma API Key gratuita na Groq e colar na aba de '⚙️ Configurações'."
        )
        step3_lbl = ctk.CTkLabel(container, text=step3_text, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#A1A1AA", justify="left")
        step3_lbl.pack(padx=20, pady=(0, 15), anchor="w")

        # Opção Gemini Notebook (Externo)
        gemini_card = ctk.CTkFrame(container, corner_radius=10, fg_color="#27272A")
        gemini_card.pack(fill="x", padx=20, pady=20)
        
        gemini_title = ctk.CTkLabel(gemini_card, text="Alternativa: Usando o NotebookLM (Opcional)", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color="#E4E4E7")
        gemini_title.pack(padx=15, pady=(15, 5), anchor="w")
        gemini_text = (
            "Se você não quiser usar a API da Groq, o Chat IA do programa é totalmente opcional! Você pode simplesmente gerar os\n"
            "arquivos '.md' (ex: roster_hsr.md) nas pastas dos jogos geradas no seu PC e fazer o upload manual deles para o NotebookLM do Google.\n"
            "O Gemini também fará o papel de Coach de Endgame lindamente usando os arquivos markdown gerados por esse app."
        )
        gemini_lbl = ctk.CTkLabel(gemini_card, text=gemini_text, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#A1A1AA", justify="left")
        gemini_lbl.pack(padx=15, pady=(0, 10), anchor="w")

        def open_notebooklm():
            import webbrowser
            webbrowser.open("https://notebooklm.google.com/")

        btn_notebook = ctk.CTkButton(
            gemini_card,
            text="Abrir Google NotebookLM",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#3F3F46", hover_color="#52525B",
            command=open_notebooklm
        )
        btn_notebook.pack(padx=15, pady=(0, 15), anchor="w")

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

    def log(self, message: str, level: str = "INFO", progresso: float = None, game_id: str = None):
        """Adiciona uma mensagem formatada ao componente de status e logs."""
        target_key = game_id if (game_id and game_id in self.loggers) else (self.active_logger_key or "global")
        logger = self.loggers.get(target_key, self.loggers["global"])
        
        if level == "ERROR":
            logger.exibir_erro(mensagem_usuario=message, erro_tecnico=message)
        else:
            prefixos = {
                "INFO": "ℹ️ ",
                "WARN": "⚠️ ",
                "SUCCESS": "✨ "
            }
            emoji_prefix = prefixos.get(level, "🔹 ")
            logger.atualizar_status(f"{emoji_prefix}{message}", progresso=progresso)
            logger.log_tecnico(f"[{level}] {message}")

    # ==========================================
    # THREAD DE LOGIN AUTOMÁTICO
    # ==========================================
    
    def start_login_thread(self):
        self.log("Abrindo navegador... Faça login manualmente na janela do HoYoLAB.", "INFO", game_id="global")
        self.login_btn.configure(state="disabled")
        logger = self.loggers.get("global")
        logger.progress_bar.configure(mode="indeterminate")
        logger.progress_bar.start()
        
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
        logger = self.loggers.get("global")
        logger.progress_bar.stop()
        logger.progress_bar.set(0)
        self.login_btn.configure(state="normal")
        
        self.cookies = cookies_captured
        self.auth_indicator.configure(text="✅ Autenticado", text_color="#10B981")
        self.sidebar_auth_badge.configure(text="🔓 Conectado", text_color="#10B981")
        self.log("Cookies capturados automaticamente do navegador com sucesso!", "SUCCESS", game_id="global")
        
        # Preenche o campo visual
        uid = cookies_captured.get("ltuid_v2") or cookies_captured.get("ltuid")
        token = cookies_captured.get("ltoken_v2") or cookies_captured.get("ltoken")
        self.cookie_entry.delete(0, "end")
        self.cookie_entry.insert(0, f"ltuid={uid}; ltoken={token}")
        
        try:
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies_captured, f, indent=4)
        except Exception as e:
            self.log(f"Erro ao salvar cookies: {e}", "ERROR", game_id="global")
        
    def login_failed(self, error_message: str):
        logger = self.loggers.get("global")
        logger.progress_bar.stop()
        logger.progress_bar.set(0)
        self.login_btn.configure(state="normal")
        self.auth_indicator.configure(text="🔒 Falha na Autenticação", text_color="#EF4444")
        self.sidebar_auth_badge.configure(text="🔒 Não Autenticado", text_color="#EF4444")
        self.log(f"Falha de Login: {error_message}", "ERROR", game_id="global")

    # ==========================================
    # THREAD DE EXECUÇÃO DE JOGOS
    # ==========================================
    
    def start_game_task_thread(self, game_id: str):
        roster_cb = getattr(self, f"{game_id}_roster_cb")
        guides_cb = getattr(self, f"{game_id}_guides_cb")
        meta_cb = getattr(self, f"{game_id}_meta_cb")
        
        # Verifica se alguma opção foi selecionada
        if not (roster_cb.get() or guides_cb.get() or meta_cb.get()):
            self.log(f"Nenhuma opção de tarefa selecionada para {game_id.upper()}.", "WARN", game_id=game_id)
            return
            
        # Desabilita o botão para evitar cliques duplicados
        run_btn = getattr(self, f"{game_id}_run_btn")
        run_btn.configure(state="disabled")
        
        logger = self.loggers.get(game_id, self.loggers["global"])
        logger.progress_bar.configure(mode="determinate")
        logger.atualizar_status("⏳ Preparando tarefas...", progresso=0.0)
        
        thread = threading.Thread(
            target=self.run_game_tasks,
            args=(game_id, roster_cb.get(), guides_cb.get(), meta_cb.get()),
            daemon=True
        )
        thread.start()
        
    def run_game_tasks(self, game_id: str, run_roster: bool, run_guides: bool, run_meta: bool):
        def log_game(msg, level="INFO", progresso=None):
            self.log(msg, level=level, progresso=progresso, game_id=game_id)

        log_game(f"Iniciando tarefas selecionadas para {game_id.upper()}...", "INFO", progresso=0.02)
        
        # --- 1. EXTRAÇÃO DE ROSTER ---
        if run_roster:
            if not self.cookies:
                log_game("HoYoLAB Cookies não localizados. Faça login ou insira manualmente na aba Configurações.", "ERROR")
                self.after(0, self.game_task_completed, game_id, False, "Cookies ausentes.")
                return
                
            log_game(f"Conectando a HoYoLAB para extração do roster de {game_id.upper()}...", "INFO", progresso=0.05)
            try:
                extractor = MultiGameExtractor(self.cookies)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                filename = loop.run_until_complete(extractor.extrair_jogo(game_id))
                loop.close()
                log_game(f"Roster extraído e salvo com sucesso em: {filename}", "SUCCESS", progresso=0.25)
            except Exception as roster_err:
                traceback.print_exc()
                log_game(f"Falha ao extrair Roster de {game_id.upper()}: {roster_err}", "ERROR")

        # --- 2. EXTRAÇÃO DE GUIDES ---
        if run_guides:
            log_game(f"Iniciando busca de guias para {game_id.upper()}...", "INFO", progresso=0.28)
            if game_id == "hsr":
                try:
                    log_game("Obtendo lista de personagens HSR...", "INFO", progresso=0.30)
                    scraper = PrydwenScraper()
                    chars = scraper.get_character_list()
                    log_game(f"Encontrados {len(chars)} personagens. Baixando guias...", "INFO", progresso=0.32)
                    total_chars = len(chars)
                    for idx, c in enumerate(chars, 1):
                        p_val = 0.32 + 0.50 * (idx / total_chars if total_chars > 0 else 1.0)
                        log_game(f"({idx}/{total_chars}) Coletando guia de {c['name']}...", "INFO", progresso=p_val)
                        try:
                            data = scraper.scrape_character_guide(c["name"], c["url"])
                            scraper.save_to_markdown(c["name"], data)
                        except Exception as child_err:
                            log_game(f"Erro no guia de {c['name']}: {child_err}", "WARN", progresso=p_val)
                    log_game("Guias de HSR baixados com sucesso!", "SUCCESS", progresso=0.82)
                    
                    log_game("Consolidando guias individuais de HSR...", "INFO", progresso=0.84)
                    bundle_guides("hsr/guias", "hsr/todos_os_guias_hsr.md", "Honkai: Star Rail")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(f"Erro ao obter guias HSR: {scraper_err}", "ERROR")
                    
            elif game_id == "zzz":
                try:
                    log_game("Obtendo lista de agentes ZZZ...", "INFO", progresso=0.30)
                    scraper = PrydwenZZZScraper()
                    agents = scraper.get_agent_list()
                    log_game(f"Encontrados {len(agents)} agentes. Baixando guias...", "INFO", progresso=0.32)
                    total_agents = len(agents)
                    for idx, a in enumerate(agents, 1):
                        p_val = 0.32 + 0.50 * (idx / total_agents if total_agents > 0 else 1.0)
                        log_game(f"({idx}/{total_agents}) Coletando guia de {a['name']}...", "INFO", progresso=p_val)
                        try:
                            data = scraper.scrape_agent_guide(a["name"], a["url"])
                            scraper.save_to_markdown(a["name"], data)
                        except Exception as child_err:
                            log_game(f"Erro no guia de {a['name']}: {child_err}", "WARN", progresso=p_val)
                    log_game("Guias de ZZZ baixados com sucesso!", "SUCCESS", progresso=0.82)
                    
                    log_game("Consolidando guias individuais de ZZZ...", "INFO", progresso=0.84)
                    bundle_guides("zzz/guias", "zzz/todos_os_guias_zzz.md", "Zenless Zone Zero")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(f"Erro ao obter guias ZZZ: {scraper_err}", "ERROR")
                    
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
                            log_game(f"Erro ao carregar roster de Genshin: {e}", "WARN")
                    
                    if not extracted_characters:
                        log_game("Roster de Genshin não encontrado. Usando lista padrão de personagens populares.", "INFO", progresso=0.30)
                        extracted_characters = ["Keqing", "Hu Tao", "Raiden Shogun", "Furina", "Nahida", "Bennett", "Zhongli", "Kaedehara Kazuha", "Yelan", "Xingqiu"]
                        
                    log_game(f"Iniciando busca de guias KQM para {len(extracted_characters)} personagens de Genshin...", "INFO", progresso=0.32)
                    from scraper_kqm import KQMScraper
                    
                    kqm = KQMScraper(output_dir="genshin/guias")
                    kqm.scrape_all_guides(character_list=extracted_characters, logger_cb=log_game)
                    log_game("Guias do KQM obtidos e salvos em: genshin/guias/", "SUCCESS", progresso=0.82)
                    
                    log_game("Consolidando guias individuais de Genshin...", "INFO", progresso=0.84)
                    bundle_guides("genshin/guias", "genshin/todos_os_guias_genshin.md", "Genshin Impact")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(f"Erro ao obter guias do KQM: {scraper_err}", "ERROR")


        # --- 3. EXTRAÇÃO DE META E ENDGAME ---
        if run_meta:
            log_game(f"Iniciando sincronização do meta de {game_id.upper()}...", "INFO", progresso=0.86)
            if game_id == "hsr":
                try:
                    log_game("Coletando Tier Lists HSR do Prydwen...", "INFO", progresso=0.88)
                    scraper_m = PrydwenMetaScraper()
                    data = scraper_m.scrape_tier_list()
                    filepath_tier = scraper_m.save_meta_markdown(data, "hsr/meta_e_tierlists_atual.md")
                    
                    log_game("Coletando estatísticas de endgame HSR...", "INFO", progresso=0.92)
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
                    log_game(f"Meta de HSR consolidado com sucesso em: {consolidated_path}", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(f"Falha ao obter meta HSR: {meta_err}", "ERROR")
            elif game_id == "zzz":
                try:
                    log_game("Coletando meta, tier list e relatórios de endgame do ZZZ...", "INFO", progresso=0.90)
                    scraper = PrydwenZZZScraper()
                    filepath = scraper.save_meta_to_markdown()
                    log_game(f"Meta de ZZZ salvo e consolidado com sucesso em: {filepath}", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(f"Falha ao obter meta ZZZ: {meta_err}", "ERROR")
            elif game_id == "genshin":
                try:
                    log_game("Iniciando busca de meta e endgame de GENSHIN do Game8...", "INFO", progresso=0.90)
                    from scraper_genshin_meta import GenshinMetaScraper
                    
                    meta_scraper = GenshinMetaScraper(output_path="genshin/meta_kqm_genshin.md")
                    meta_scraper.run_full_scrape(logger_cb=log_game)
                    log_game("Relatório de Endgame e Tier List salvos em: genshin/meta_kqm_genshin.md", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(f"Erro ao obter metagame do Genshin: {meta_err}", "ERROR")

                
        self.after(0, self.game_task_completed, game_id, True, "Tarefas concluídas.")
        
    def game_task_completed(self, game_id: str, success: bool, msg: str):
        run_btn = getattr(self, f"{game_id}_run_btn")
        run_btn.configure(state="normal")
        
        if success:
            self.log(f"Todas as tarefas de {game_id.upper()} foram finalizadas com sucesso!", "SUCCESS", progresso=1.0, game_id=game_id)
            self.show_toast(f"✨ {game_id.upper()} Concluído", f"Todas as tarefas de {game_id.upper()} foram finalizadas!")
            self.update_dashboard_ui(game_id)
        else:
            self.log(f"Tarefas de {game_id.upper()} falharam: {msg}", "ERROR", game_id=game_id)
            self.show_toast(f"❌ {game_id.upper()} Falhou", f"Erro: {msg}", level="ERROR")

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
        
        # Banner de Validação da API Key se não estiver salva
        if not (self.groq_rag and self.groq_rag.api_key):
            warn_card = ctk.CTkFrame(container, corner_radius=10, fg_color="#371B1B", border_width=1, border_color="#7F1D1D")
            warn_card.pack(fill="x", padx=10, pady=(0, 10))
            
            lbl = ctk.CTkLabel(
                warn_card,
                text="🔑 Nenhuma API Key da Groq configurada. O assistente IA precisa de uma chave gratuita para responder.",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color="#FCA5A5"
            )
            lbl.pack(side="left", padx=15, pady=10)
            
            btn_cfg = ctk.CTkButton(
                warn_card,
                text="🔑 Obter Chave Gratuita Groq",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                fg_color="#DC2626",
                hover_color="#B91C1C",
                height=28,
                command=lambda: webbrowser.open("https://console.groq.com/keys")
            )
            btn_cfg.pack(side="right", padx=15, pady=10)
        
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
        
        # Chips de Prompts Rápidos Sugeridos
        chips_frame = ctk.CTkFrame(container, fg_color="transparent")
        chips_frame.pack(fill="x", padx=10, pady=(0, 6))
        
        lbl_chips = ctk.CTkLabel(chips_frame, text="💡 Sugestões de Perguntas Rápida:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A1A1AA")
        lbl_chips.pack(anchor="w", padx=2, pady=(0, 4))
        
        chips_box = ctk.CTkFrame(chips_frame, fg_color="transparent")
        chips_box.pack(fill="x")
        
        prompts = [
            "🏆 Monte meu melhor time para o Endgame",
            "⚡ QUAIS PERSONAGENS PRECISAM DE ATRIBUTOS?",
            "⚔️ Melhores 2 times de maior DPS com meu Roster"
        ]
        
        for p in prompts:
            btn_p = ctk.CTkButton(
                chips_box,
                text=p,
                font=ctk.CTkFont(size=11),
                fg_color="#27272A",
                hover_color="#3F3F46",
                text_color="#E4E4E7",
                height=26,
                corner_radius=13,
                command=lambda text=p: self.insert_prompt_and_send(text)
            )
            btn_p.pack(side="left", padx=3, pady=2)
            
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

    def insert_prompt_and_send(self, prompt_text: str):
        """Insere o texto do prompt sugerido e dispara o envio automaticamente."""
        self.chat_entry.delete(0, "end")
        self.chat_entry.insert(0, prompt_text)
        self.send_chat_message()

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
        logger = self.loggers.get("global")
        logger.progress_bar.configure(mode="indeterminate")
        logger.progress_bar.start()
        logger.atualizar_status("Groq pensando... ⌛")
        
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
        logger = self.loggers.get("global")
        logger.progress_bar.stop()
        logger.progress_bar.set(0)
        logger.atualizar_status("Pronto.")
        self.chat_entry.configure(state="normal")
        self.chat_send_btn.configure(state="normal")
        self.chat_entry.focus()

    def clear_chat_history(self):
        self.chat_history = []
        for child in self.chat_scroll.winfo_children():
            child.destroy()
        self.append_welcome_message()
        self.log("Histórico de conversa limpo.", "INFO")

if __name__ == "__main__":
    app = App()
    app.mainloop()
