"""Pacote modular com cálculos especializados de domínio (Gacha Monte Carlo, Breakpoints, Radar Meta e Estratégia de Conta)."""

from calculators.gacha_math import simulate_gacha_probabilities, calculate_gacha_forecast
from calculators.stat_breakpoints import calculate_stat_breakpoints
from calculators.account_strategy import _norm_str, analyze_account_gaps, recommend_relic_crafting
from calculators.benchmark_radar import (
    VALID_BENCHMARK_STATS,
    build_radar_benchmark_payload,
    canonicalize_benchmark_key,
    deduplicate_endgame_stats,
    is_generic_hsr_placeholder,
    is_generic_placeholder_benchmark,
    parse_benchmark_spec,
    parse_stat_number,
    standardize_main_stat_display,
)

__all__ = [
    "simulate_gacha_probabilities",
    "calculate_gacha_forecast",
    "calculate_stat_breakpoints",
    "_norm_str",
    "analyze_account_gaps",
    "recommend_relic_crafting",
    "VALID_BENCHMARK_STATS",
    "build_radar_benchmark_payload",
    "canonicalize_benchmark_key",
    "deduplicate_endgame_stats",
    "is_generic_hsr_placeholder",
    "parse_benchmark_spec",
    "parse_stat_number",
    "standardize_main_stat_display",
]
