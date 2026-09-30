from pydantic import BaseModel
from typing import Optional

class ConfigSaveRequest(BaseModel):
    groq_api_key: Optional[str] = None
    cookies_raw: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None
    auto_sync_time: Optional[str] = None
    auto_sync_roster: Optional[bool] = None
    auto_sync_guides: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    discord_webhook_url: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    notify_on_checkin: Optional[bool] = None
    notify_on_energy_cap: Optional[bool] = None
    energy_cap_threshold_pct: Optional[int] = None
    notify_on_endgame: Optional[bool] = None
    notify_on_codes: Optional[bool] = None

class NotificationTestRequest(BaseModel):
    discord_webhook_url: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
