from pydantic import BaseModel, Field
from typing import Optional


class RedeemCodeRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz') para resgate")
    code: Optional[str] = Field(
        default=None, description="Código promocional a ser resgatado; se omitido, ativa varredura automática"
    )
