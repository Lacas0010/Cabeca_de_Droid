from pydantic import BaseModel
from typing import Optional

class SyncRequest(BaseModel):
    run_roster: bool = True
    run_guides: bool = True
    run_meta: bool = True

class StaticDataSyncRequest(BaseModel):
    game_id: Optional[str] = None
