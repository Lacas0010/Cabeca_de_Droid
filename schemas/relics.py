from pydantic import BaseModel, Field
from typing import List, Optional


class TrashRelicItem(BaseModel):
    name: str = Field(description="Nome do artefato, relíquia ou disco analisado")
    slot: str = Field(description="Slot ou posição da peça equipada")
    main_stat: str = Field(description="Atributo principal presente na peça")
    substats: List[str] = Field(default=[], description="Lista com as linhas de atributos secundários")
    reason: str = Field(description="Diagnóstico detalhado do motivo da peça ser considerada lixo ou ineficiente")
    recommendation: str = Field(description="Recomendação de descarte, síntese ou reciclagem em EXP")
    character_name: Optional[str] = Field(
        default=None, description="Nome do personagem em que a peça está equipada, se houver"
    )
    icon: Optional[str] = Field(default=None, description="URL do ícone oficial da peça")


class CoringaRelicItem(BaseModel):
    name: str = Field(description="Nome da relíquia ou artefato de alto potencial")
    slot: str = Field(description="Slot da peça")
    main_stat: str = Field(description="Atributo principal")
    substats: List[str] = Field(default=[], description="Lista de substats de alto valor")
    crit_value: Optional[float] = Field(default=None, description="Valor de CRIT calculado (2x Taxa + Dano)")
    coringa_tier: str = Field(description="Classificação coringa ('SS+', 'S', 'A')")
    reason: str = Field(description="Explicação da utilidade universal da peça para múltiplos personagens")
    character_name: Optional[str] = Field(default=None, description="Personagem portador atual")
    icon: Optional[str] = Field(default=None, description="URL do ícone da peça")


class TrashRelicsResponse(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    total_analyzed: int = Field(description="Quantidade total de peças de equipamento avaliadas")
    good_relics_count: int = Field(description="Contagem de peças com notas adequadas para o meta")
    trash_count: int = Field(description="Contagem total de peças categorizadas como lixo/descarte")
    trash_relics: List[TrashRelicItem] = Field(default=[], description="Lista de peças recomendadas para reciclagem")
    coringa_count: int = Field(default=0, description="Contagem de peças com atributos coringa excepcionais")
    coringa_relics: List[CoringaRelicItem] = Field(default=[], description="Lista de peças coringa preservadas")
