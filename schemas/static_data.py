"""Contratos Pydantic v2 para endpoints de dados estáticos e avaliação de atributos."""

from typing import Dict
from pydantic import RootModel


class EvaluateStatsRequest(RootModel[Dict[str, str]]):
    """Payload JSON chave-valor de atributos finais do personagem para avaliação contra benchmarks."""

    root: Dict[str, str]
