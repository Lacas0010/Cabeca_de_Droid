from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union


class RelicPieceModel(BaseModel):
    slot: str = Field(description="Slot ou posição da peça no conjunto")
    name: Optional[str] = Field(default="Relíquia", description="Nome da relíquia ou set ao qual pertence")
    main_stat: str = Field(description="Atributo principal da peça com seu valor")
    sub_stats: Union[str, List[Any]] = Field(default="", description="Lista ou string delimitada de substatus da peça")
    icon: Optional[str] = Field(default="", description="URL do ícone da peça")


class SimulatedStatDiff(BaseModel):
    stat_name: str = Field(description="Nome do atributo que sofreu variação na simulação")
    old_val: float = Field(description="Valor numérico anterior antes da troca da peça")
    new_val: float = Field(description="Novo valor numérico projetado após a substituição")
    diff: float = Field(description="Diferença matemática absoluta (new_val - old_val)")
    formatted_diff: str = Field(description="Diferença formatada para exibição com sinal (+/-)")


class SimulateSwapRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    char_name: str = Field(description="Nome do personagem que terá a peça substituída")
    target_slot: str = Field(description="Identificador do slot onde a peça candidata será testada")
    replacement_relic: RelicPieceModel = Field(description="Nova peça candidata para o teste de sandbox")
    current_relics: Optional[List[RelicPieceModel]] = Field(
        default=None, description="Lista opcional de peças atuais equipadas"
    )
    current_stats: Optional[Dict[str, Any]] = Field(
        default=None, description="Dicionário com os atributos de combate atuais"
    )


class SimulateSwapResponse(BaseModel):
    character_name: str = Field(description="Nome do personagem analisado")
    game_id: str = Field(description="Identificador do jogo")
    target_slot: str = Field(description="Slot testado")
    old_piece_score: float = Field(description="Pontuação de 0 a 100 da peça atual")
    old_piece_grade: str = Field(description="Nota alfabética da peça atual (ex: 'S', 'A', 'B')")
    new_piece_score: float = Field(description="Pontuação de 0 a 100 da nova peça")
    new_piece_grade: str = Field(description="Nota alfabética da nova peça")
    old_build_score: float = Field(description="Pontuação geral média da build antes da troca")
    old_build_grade: str = Field(description="Classificação da build antes da troca")
    new_build_score: float = Field(description="Nova pontuação geral média da build após a troca")
    new_build_grade: str = Field(description="Nova classificação da build após a troca")
    score_diff: float = Field(description="Variação líquida na pontuação da build")
    grade_changed: bool = Field(description="Verdadeiro se a classificação alfabética subiu ou desceu")
    is_upgrade: bool = Field(description="Verdadeiro se a troca representa uma melhoria objetiva")
    stat_diffs: List[SimulatedStatDiff] = Field(
        default=[], description="Lista de deltas para todos os atributos afetados"
    )
    breakpoint_feedback: List[str] = Field(
        default=[], description="Alertas sobre breakpoints e speed tuning atingidos ou perdidos"
    )
    verdict_summary: str = Field(description="Veredito executivo em linguagem natural explicando se a troca compensa")
