from pydantic import BaseModel, Field
from typing import Optional


class ConfigSaveRequest(BaseModel):
    groq_api_key: Optional[str] = Field(
        default=None, description="Chave de API do serviço Groq para RAG e geração de texto"
    )
    cookies_raw: Optional[str] = Field(
        default=None, description="String crua de cookies do HoYoLAB extraída do navegador"
    )
    auto_sync_enabled: Optional[bool] = Field(
        default=None, description="Habilitar sincronização automática diária em segundo plano"
    )
    auto_sync_time: Optional[str] = Field(
        default=None, description="Horário diário programado para sincronização (HH:MM)"
    )
    auto_sync_roster: Optional[bool] = Field(
        default=None, description="Sincronizar roster de personagens durante o ciclo automático"
    )
    auto_sync_guides: Optional[bool] = Field(
        default=None, description="Sincronizar guias e metadados durante o ciclo automático"
    )
    notifications_enabled: Optional[bool] = Field(
        default=None, description="Chave mestre para envio de notificações externas"
    )
    discord_webhook_url: Optional[str] = Field(default=None, description="URL do webhook do canal Discord para alertas")
    telegram_bot_token: Optional[str] = Field(
        default=None, description="Token do bot do Telegram para envio de mensagens"
    )
    telegram_chat_id: Optional[str] = Field(default=None, description="Identificador do chat ou grupo no Telegram")
    notify_on_checkin: Optional[bool] = Field(
        default=None, description="Enviar notificação ao concluir o check-in diário"
    )
    notify_on_energy_cap: Optional[bool] = Field(
        default=None, description="Enviar alerta quando a resina/energia atingir o limite estipulado"
    )
    energy_cap_threshold_pct: Optional[int] = Field(
        default=None, description="Percentual da capacidade máxima para disparar alerta de energia (ex: 90%)"
    )
    notify_on_endgame: Optional[bool] = Field(
        default=None, description="Notificar lembretes de reinicialização de ciclos de endgame"
    )
    notify_on_codes: Optional[bool] = Field(
        default=None, description="Notificar quando novos códigos promocionais forem resgatados"
    )
    quiet_hours_enabled: Optional[bool] = Field(
        default=None, description="Ativar período de silêncio para não enviar notificações noturnas"
    )
    quiet_hours_start: Optional[str] = Field(default=None, description="Horário de início do modo silencioso (HH:MM)")
    quiet_hours_end: Optional[str] = Field(default=None, description="Horário de término do modo silencioso (HH:MM)")
    notify_windows_toast: Optional[bool] = Field(
        default=None, description="Exibir notificações nativas do Windows Toast na área de trabalho"
    )


class NotificationTestRequest(BaseModel):
    discord_webhook_url: Optional[str] = Field(default=None, description="URL do webhook Discord a ser testado")
    telegram_bot_token: Optional[str] = Field(default=None, description="Token do bot Telegram a ser testado")
    telegram_chat_id: Optional[str] = Field(default=None, description="Chat ID de destino para a mensagem de teste")
    test_windows: Optional[bool] = Field(
        default=True, description="Disparar notificação nativa de teste no sistema operacional"
    )
