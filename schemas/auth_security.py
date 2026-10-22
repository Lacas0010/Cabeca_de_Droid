from pydantic import BaseModel, Field
from typing import Optional


class ManualCookieRequest(BaseModel):
    cookie_string: str = Field(
        description="String contendo os cookies brutos da sessão HoYoLAB (ex: ltoken_v2, ltuid_v2)"
    )


class PinSetRequest(BaseModel):
    pin: str = Field(description="Novo código PIN numérico de 4 a 8 dígitos para segurança da interface")


class PinVerifyRequest(BaseModel):
    pin: str = Field(description="Código PIN a ser validado contra o hash armazenado no banco local")


class PinDisableRequest(BaseModel):
    current_pin: Optional[str] = Field(
        default=None, description="PIN atual para confirmação da desativação da proteção"
    )


class LanToggleRequest(BaseModel):
    enabled: Optional[bool] = Field(
        default=None, description="Habilitar ou desabilitar permissão de acesso via rede local"
    )
    allow_lan: Optional[bool] = Field(
        default=None, description="Alias retrocompatível para alteração de acesso em rede local"
    )
