from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class BreakpointRequest(BaseModel):
    game_id: Optional[str] = Field(default="hsr", description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    char_name: str = Field(description="Nome do personagem a ser avaliado contra breakpoints de meta")
    stats: Dict[str, Any] = Field(description="Dicionário com os status finais do personagem")


class BreakpointItem(BaseModel):
    stat: str = Field(description="Nome do atributo avaliado (ex: 'Velocidade', 'Taxa CRIT', 'Recarga')")
    current: str = Field(description="Valor atual formatado do status no personagem")
    status: str = Field(description="Situação do breakpoint (ex: 'Alcançado', 'Próximo', 'Insuficiente')")
    next_goal: str = Field(description="Próxima meta recomendada pelo meta")
    is_reached: bool = Field(default=False, description="Verdadeiro se o requisito do breakpoint foi cumprido")
    tier_progress: Optional[float] = Field(default=None, description="Progresso percentual de 0 a 100 até a meta")
    action_value: Optional[float] = Field(default=None, description="Valor de ação (Action Value) resultante no ciclo")
    category: Optional[str] = Field(
        default="general", description="Categoria do breakpoint ('speed_tuning', 'crit_balance', 'energy')"
    )
    speed_tuning_tip: Optional[str] = Field(
        default=None, description="Dica prática para ajuste fino de turnos e ordem de ação"
    )


class BreakpointResponse(BaseModel):
    char_name: str = Field(description="Nome do personagem analisado")
    game_id: str = Field(description="Identificador do jogo")
    speed_action_value: Optional[float] = Field(default=None, description="Action Value inicial de velocidade")
    cycles_summary: Optional[str] = Field(
        default=None, description="Resumo da quantidade de ações nos primeiros ciclos de combate"
    )
    breakpoints: List[BreakpointItem] = Field(
        default=[], description="Lista com todos os breakpoints avaliados para o personagem"
    )
