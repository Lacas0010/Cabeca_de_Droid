from pydantic import BaseModel, Field


class BrowserClientSignal(BaseModel):
    """Identificador efêmero da aba/janela do navegador conectada localmente."""

    client_id: str = Field(..., min_length=1, max_length=128)
