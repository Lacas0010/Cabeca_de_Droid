"""
Módulo de Scrapers do Cabeça de Droid.
Responsável por extrair guias de personagens, tier lists e metagame de fontes públicas como Prydwen.
"""
from scrapers.scraper_prydwen import PrydwenScraper
from scrapers.scraper_zzz import PrydwenZZZScraper
from scrapers.scraper_genshin import PrydwenGenshinScraper
from scrapers.scraper_meta import PrydwenMetaScraper

__all__ = [
    "PrydwenScraper",
    "PrydwenZZZScraper",
    "PrydwenGenshinScraper",
    "PrydwenMetaScraper",
]
