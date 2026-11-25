"""
Módulo de Scrapers do Cabeça de Droid.
Responsável por extrair guias de personagens, tier lists e metagame de fontes públicas como Prydwen.
"""

from scrapers.scraper_prydwen import PrydwenScraper
from scrapers.scraper_zzz import PrydwenZZZScraper
from scrapers.scraper_genshin import PrydwenGenshinScraper
from scrapers.scraper_meta import PrydwenMetaScraper
from scrapers.endgame_icons_scraper import sync_endgame_icons
from scrapers.role_icons_scraper import sync_role_icons
from scrapers.resource_icons_scraper import sync_resource_icons
from scrapers.equipment_effects_scraper import sync_equipment_effects

__all__ = [
    "PrydwenScraper",
    "PrydwenZZZScraper",
    "PrydwenGenshinScraper",
    "PrydwenMetaScraper",
    "sync_endgame_icons",
    "sync_role_icons",
    "sync_resource_icons",
    "sync_equipment_effects",
]
