import json
from typing import AsyncGenerator


async def generate_account_roast_stream(game_id: str) -> AsyncGenerator[str, None]:
    """Transmite mensagem informando que o módulo de IA está temporariamente desativado."""
    yield (
        "data: "
        + json.dumps(
            {"error": "O módulo de IA está temporariamente desativado nesta versão."},
            ensure_ascii=False,
        )
        + "\n\n"
    )
