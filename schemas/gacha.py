from pydantic import BaseModel, Field
from typing import Optional


class GachaRequest(BaseModel):
    game_id: Optional[str] = Field(default="genshin", description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    current_pity: Optional[int] = Field(default=0, description="Contagem atual de pity do jogador no banner")
    is_guaranteed: Optional[bool] = Field(
        default=False, description="Indica se o próximo item de 5 estrelas é o garantido (sem 50/50)"
    )
    pulls_available: Optional[int] = Field(
        default=0, description="Quantidade de tiros/destinos disponíveis para simulação"
    )
    target_copies: Optional[int] = Field(default=1, description="Número de cópias desejadas do item alvo")
    current_copies: Optional[int] = Field(default=0, description="Número de cópias já possuídas")
    current_rank: Optional[int] = Field(
        default=None, description="Rank/constelação/eidolon inicial (-1 para não obtido, 0 para C0/E0/M0)"
    )
    target_rank: Optional[int] = Field(default=None, description="Rank/constelação/eidolon final almejado (0 a 6)")
    char_name: Optional[str] = Field(default=None, description="Nome do personagem alvo no banner promocional")


class GachaForecastRequest(BaseModel):
    game_id: Optional[str] = Field(default="genshin", description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    character_name: Optional[str] = Field(default="", description="Nome do personagem alvo do planejamento")
    current_pulls: Optional[int] = Field(
        default=0, description="Tiros ou equivalente em gemas/jades/polychromes já guardados"
    )
    current_pity: Optional[int] = Field(default=0, description="Pity acumulado no banner relevante")
    is_guaranteed: Optional[bool] = Field(default=False, description="Garantido no 50/50 ativo")
    target_rank: Optional[int] = Field(default=0, description="Constelação ou eidolon alvo (0 para C0)")
    current_rank: Optional[int] = Field(default=-1, description="Constelação atual (-1 se não possui o personagem)")
    target_days: Optional[int] = Field(default=21, description="Dias restantes até o encerramento do banner planejado")
    has_daily_pass: Optional[bool] = Field(
        default=False, description="Usuário possui passe diário ativo (Bênção / Expresso / Interlaço)"
    )
    has_battle_pass: Optional[bool] = Field(default=False, description="Usuário adquire o passe de batalha da versão")
    include_shop_resets: Optional[bool] = Field(
        default=True, description="Considerar os 5 tiros mensais da loja de poeira estelar"
    )
    include_events_estimate: Optional[bool] = Field(
        default=True, description="Incluir estimativa conservadora de gemas de eventos da versão"
    )
    include_endgame_resets: Optional[bool] = Field(
        default=True, description="Incluir gemas obtidas em resets das modalidades de endgame"
    )


class GachaGoalSaveRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    character_name: str = Field(description="Nome do personagem alvo a ser salvo na meta")
    target_rank_str: str = Field(description="Texto descritivo do rank almejado (ex: 'C0', 'E2', 'M6')")
    current_pulls: int = Field(description="Quantidade de tiros no momento do salvamento")
    current_pity: int = Field(description="Pity atual no momento do salvamento")
    is_guaranteed: bool = Field(description="Se o garantido estava ativo")
    target_days: int = Field(description="Janela de dias definida para a meta")
    has_daily_pass: bool = Field(description="Se o usuário possuía passe diário na simulação")
    success_rate: float = Field(description="Probabilidade matemática calculada de sucesso (%)")
    projected_pulls: int = Field(description="Total projetado de tiros acumulados no término do prazo")
    notes: Optional[str] = Field(default="", description="Anotações estratégicas adicionais sobre o plano")


class StrategyAskAIRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    custom_question: Optional[str] = Field(
        default=None, description="Pergunta específica do usuário sobre sinergias e economia de tiros"
    )
