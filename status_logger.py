import os
import sys
import time
import datetime
import threading
import traceback
import customtkinter as ctk

class StatusLoggerFrame(ctk.CTkFrame):
    """
    Componente modular de Status e Feedback Visual com Logs Retráteis.
    
    Recursos:
    - Indicador de status amigável em linguagem natural com emojis.
    - Barra de progresso percentual elegante.
    - Painel retrátil (sanfonado) para logs técnicos (Dev Mode / Debug).
    - Execução segura para chamadas assíncronas/multi-thread (thread-safe).
    """
    def __init__(self, master, title: str = "Status da Operação", **kwargs):
        kwargs.setdefault("fg_color", "#18181B")
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#27272A")
        super().__init__(master, **kwargs)
        
        self._is_expanded = False
        self._build_ui(title)
        
    def _build_ui(self, title: str):
        # ==========================================
        # 1. ÁREA SUPERIOR (FEEDBACK DO USUÁRIO FINAL)
        # ==========================================
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=16, pady=14)
        
        # Rótulo de Cabeçalho Discreto
        self.lbl_header = ctk.CTkLabel(
            self.top_frame,
            text=title.upper(),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#71717A"
        )
        self.lbl_header.pack(anchor="w", pady=(0, 4))
        
        # Status Principal (Mensagem Amigável)
        self.lbl_status = ctk.CTkLabel(
            self.top_frame,
            text="⏳ Aguardando início...",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#F4F4F5",
            anchor="w",
            justify="left"
        )
        self.lbl_status.pack(anchor="w", fill="x", pady=(0, 10))
        
        # Container da Barra de Progresso + Porcentagem
        self.progress_container = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.progress_container.pack(fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_container,
            height=8,
            corner_radius=4,
            progress_color="#3B82F6", # Azul moderno
            fg_color="#27272A"
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.progress_bar.set(0.0)
        
        self.lbl_percentage = ctk.CTkLabel(
            self.progress_container,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#A1A1AA",
            width=40
        )
        self.lbl_percentage.pack(side="right")
        
        # Divisor Discreto
        self.divider = ctk.CTkFrame(self, height=1, fg_color="#27272A")
        self.divider.pack(fill="x", padx=16, pady=(8, 0))
        
        # ==========================================
        # 2. ÁREA INFERIOR (BOTÃO & LOGS TÉCNICOS DEV)
        # ==========================================
        self.btn_toggle = ctk.CTkButton(
            self,
            text="🛠️ Ver detalhes técnicos",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
            text_color="#A1A1AA",
            hover_color="#27272A",
            anchor="w",
            height=32,
            command=self.toggle_logs
        )
        self.btn_toggle.pack(fill="x", padx=10, pady=4)
        
        # Textbox de Logs Técnicos (Inicia OCULTO)
        self.textbox_logs = ctk.CTkTextbox(
            self,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#09090B",
            text_color="#10B981", # Verde estilo terminal
            corner_radius=8,
            border_width=1,
            border_color="#27272A",
            state="disabled"
        )

    # ==========================================
    # LÓGICA REPETÍVEL & THREAD-SAFETY
    # ==========================================
    def toggle_logs(self):
        """Expande ou recolhe o painel de logs técnicos."""
        self._is_expanded = not self._is_expanded
        if self._is_expanded:
            self.textbox_logs.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            self.btn_toggle.configure(text="🔽 Ocultar detalhes técnicos", text_color="#3B82F6")
        else:
            self.textbox_logs.pack_forget()
            self.btn_toggle.configure(text="🛠️ Ver detalhes técnicos", text_color="#A1A1AA")

    def _safe_dispatch(self, func, *args, **kwargs):
        """Garante que a UI só seja atualizada na Main Thread do Tkinter."""
        if threading.current_thread() is threading.main_thread():
            func(*args, **kwargs)
        else:
            self.after(0, lambda: func(*args, **kwargs))

    # ==========================================
    # MÉTODOS PÚBLICOS SOLICITADOS
    # ==========================================
    def atualizar_status(self, mensagem: str, progresso: float = None):
        """
        Atualiza a mensagem amigável e o percentual da barra de progresso (0.0 a 1.0).
        """
        def _update():
            self.lbl_status.configure(text=mensagem, text_color="#F4F4F5")
            
            if progresso is not None:
                clamped_progress = max(0.0, min(1.0, float(progresso)))
                self.progress_bar.set(clamped_progress)
                self.lbl_percentage.configure(text=f"{int(clamped_progress * 100)}%", text_color="#A1A1AA")
                self.progress_bar.configure(progress_color="#3B82F6")
                
        self._safe_dispatch(_update)

    def log_tecnico(self, mensagem_raw: str):
        """
        Insere uma linha com carimbo de data/hora no console técnico oculto.
        """
        def _log():
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {mensagem_raw}\n"
            
            self.textbox_logs.configure(state="normal")
            self.textbox_logs.insert("end", log_entry)
            self.textbox_logs.see("end")
            self.textbox_logs.configure(state="disabled")
            
        self._safe_dispatch(_log)

    def exibir_erro(self, mensagem_usuario: str, erro_tecnico: str = None):
        """
        Exibe uma mensagem limpa de erro em vermelho para o usuário 
        e grava os detalhes brutos/traceback dentro do painel oculto.
        """
        def _show_error():
            self.lbl_status.configure(text=f"❌ {mensagem_usuario}", text_color="#EF4444")
            self.progress_bar.configure(progress_color="#EF4444")
            self.lbl_percentage.configure(text="Erro", text_color="#EF4444")
            
        self._safe_dispatch(_show_error)
        
        if erro_tecnico:
            self.log_tecnico(f"[ERRO CRÍTICO / TRACEBACK]\n{erro_tecnico}")

    def reset(self, mensagem_inicial: str = "⏳ Aguardando início..."):
        """Reseta os componentes para o estado inicial."""
        def _reset():
            self.lbl_status.configure(text=mensagem_inicial, text_color="#F4F4F5")
            self.progress_bar.set(0.0)
            self.progress_bar.configure(progress_color="#3B82F6")
            self.lbl_percentage.configure(text="0%", text_color="#A1A1AA")
            
        self._safe_dispatch(_reset)
