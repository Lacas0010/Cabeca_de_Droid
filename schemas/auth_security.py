from pydantic import BaseModel
from typing import Optional

class ManualCookieRequest(BaseModel):
    cookie_string: str

class PinSetRequest(BaseModel):
    pin: str

class PinVerifyRequest(BaseModel):
    pin: str

class PinDisableRequest(BaseModel):
    current_pin: Optional[str] = None

class LanToggleRequest(BaseModel):
    enabled: Optional[bool] = None
    allow_lan: Optional[bool] = None
