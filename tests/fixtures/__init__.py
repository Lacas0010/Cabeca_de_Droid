import os
import json
from typing import Dict, Any

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))


def load_fixture(fixture_filename: str) -> Dict[str, Any]:
    """
    Carrega e retorna o conteúdo de uma fixture JSON sanitizada.

    Exemplo:
        from tests.fixtures import load_fixture
        roster_data = load_fixture("hoyolab_hsr_roster.json")
    """
    target_path = os.path.join(FIXTURES_DIR, fixture_filename)
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Fixture não encontrada: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_fixture", "FIXTURES_DIR"]
