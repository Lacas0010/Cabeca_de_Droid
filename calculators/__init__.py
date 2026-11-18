"""Pacote modular com cálculos especializados de domínio (Gacha Monte Carlo, Breakpoints e Estratégia de Conta)."""

from calculators.gacha_math import simulate_gacha_probabilities, calculate_gacha_forecast
from calculators.stat_breakpoints import calculate_stat_breakpoints
from calculators.account_strategy import _norm_str, analyze_account_gaps, recommend_relic_crafting

__all__ = [
    "simulate_gacha_probabilities",
    "calculate_gacha_forecast",
    "calculate_stat_breakpoints",
    "_norm_str",
    "analyze_account_gaps",
    "recommend_relic_crafting",
]
