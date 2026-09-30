from pydantic import BaseModel
from typing import Optional

class GachaRequest(BaseModel):
    game_id: Optional[str] = "genshin"
    current_pity: Optional[int] = 0
    is_guaranteed: Optional[bool] = False
    pulls_available: Optional[int] = 0
    target_copies: Optional[int] = 1
    current_copies: Optional[int] = 0
    current_rank: Optional[int] = None
    target_rank: Optional[int] = None
    char_name: Optional[str] = None

class GachaForecastRequest(BaseModel):
    game_id: Optional[str] = "genshin"
    character_name: Optional[str] = ""
    current_pulls: Optional[int] = 0
    current_pity: Optional[int] = 0
    is_guaranteed: Optional[bool] = False
    target_rank: Optional[int] = 0
    current_rank: Optional[int] = -1
    target_days: Optional[int] = 21
    has_daily_pass: Optional[bool] = False
    has_battle_pass: Optional[bool] = False
    include_shop_resets: Optional[bool] = True
    include_events_estimate: Optional[bool] = True
    include_endgame_resets: Optional[bool] = True

class GachaGoalSaveRequest(BaseModel):
    game_id: str
    character_name: str
    target_rank_str: str
    current_pulls: int
    current_pity: int
    is_guaranteed: bool
    target_days: int
    has_daily_pass: bool
    success_rate: float
    projected_pulls: int
    notes: Optional[str] = ""

class StrategyAskAIRequest(BaseModel):
    game_id: str
    custom_question: Optional[str] = None
