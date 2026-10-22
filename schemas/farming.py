from pydantic import BaseModel, Field


class FarmOrderToggleRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz') da tarefa")
    task_id: str = Field(description="Chave única que identifica o card de farm/domínio")
    completed: bool = Field(default=True, description="Estado de conclusão da tarefa para a data de hoje")


class FarmOrderSendNotificationRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo cujo resumo de farm do dia deve ser despachado")


class MaterialsCalculateRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    char_name: str = Field(description="Nome do personagem selecionado para a projeção de materiais")
    current_level: int = Field(description="Nível atual do personagem")
    target_level: int = Field(description="Nível alvo desejado para a ascensão")
