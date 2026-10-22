from pydantic import BaseModel, Field
from typing import Optional


class SyncRequest(BaseModel):
    run_roster: bool = Field(default=True, description="Executar sincronização do roster de personagens")
    run_guides: bool = Field(default=True, description="Executar download e consolidação dos guias e tier lists")
    run_meta: bool = Field(default=True, description="Executar consolidação de metadados e estatísticas de endgame")


class StaticDataSyncRequest(BaseModel):
    game_id: Optional[str] = Field(
        default=None, description="Identificador do jogo específico a sincronizar, ou None para todos"
    )
