from routers.security import router as security_router
from routers.config import router as config_router
from routers.sync import router as sync_router
from routers.roster import router as roster_router
from routers.endgame import router as endgame_router
from routers.gacha import router as gacha_router
from routers.farming import router as farming_router
from routers.relics import router as relics_router
from routers.strategy import router as strategy_router
from routers.codes import router as codes_router
from routers.history import router as history_router
from routers.checkin import router as checkin_router
from routers.chat import router as chat_router
from routers.static_data import router as static_data_router
from routers.system import router as system_router

all_routers = [
    security_router,
    config_router,
    sync_router,
    roster_router,
    endgame_router,
    gacha_router,
    farming_router,
    relics_router,
    strategy_router,
    codes_router,
    history_router,
    checkin_router,
    chat_router,
    static_data_router,
    system_router,
]

__all__ = ["all_routers"]
