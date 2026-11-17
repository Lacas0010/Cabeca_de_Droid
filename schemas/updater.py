from typing import Optional
from pydantic import BaseModel


class UpdaterCheckResponse(BaseModel):
    update_available: bool
    is_frozen: bool
    current_version: str
    latest_version: str
    release_notes: str = ""
    download_url: Optional[str] = None
    asset_size: int = 0
    release_url: Optional[str] = None
    error: Optional[str] = None


class UpdaterStartRequest(BaseModel):
    download_url: Optional[str] = None
    target_version: Optional[str] = None
    release_url: Optional[str] = None


class UpdaterStatusResponse(BaseModel):
    running: bool
    stage: str
    progress: float
    message: str
    is_frozen: bool
    target_version: Optional[str] = None
    release_url: Optional[str] = None
    error: Optional[str] = None
