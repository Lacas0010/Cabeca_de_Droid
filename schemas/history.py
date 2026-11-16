from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CreateSnapshotRequest(BaseModel):
    refresh_from_hoyolab: bool = Field(
        default=True,
        description="Se verdadeiro e houver cookies configurados, atualiza o roster na HoYoLAB antes de gravar o snapshot.",
    )


class CreateSnapshotResponse(BaseModel):
    success: bool
    game_id: str
    snapshot_id: Optional[int] = None
    refreshed_from_hoyolab: bool = False
    message: str


class GlobalSyncResponse(BaseModel):
    success: bool
    results: Dict[str, Any] = Field(default_factory=dict)
    message: str
