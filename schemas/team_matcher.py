from typing import List, Optional
from pydantic import BaseModel, Field


class TeamMemberSubstitute(BaseModel):
    """Substituto funcional disponível no próprio roster do jogador."""

    name: str = Field(..., description="Nome do personagem substituto")
    role: str = Field(..., description="Função/papel tático do substituto")
    element: Optional[str] = Field("", description="Elemento do substituto")
    level: Optional[int] = Field(1, description="Nível atual no roster do jogador")
    rarity: Optional[int] = Field(4, description="Raridade (4★ ou 5★)")
    rank_str: Optional[str] = Field("C0", description="Constelação, Eidolon ou Cinema Mental")
    icon: Optional[str] = Field("", description="Ícone do personagem")
    synergy_reason: Optional[str] = Field("", description="Justificativa funcional da substituição")


class TeamMemberMatch(BaseModel):
    """Membro individual de uma equipe com status de posse e substitutos."""

    name: str = Field(..., description="Nome do personagem recomendado")
    role: str = Field(..., description="Papel na equipe (DPS, Buffer, Debuffer, Sustento, Stunner, etc.)")
    element: Optional[str] = Field("", description="Elemento do personagem")
    is_owned: bool = Field(..., description="Indica se o jogador possui o personagem na conta")
    level: Optional[int] = Field(None, description="Nível no roster do jogador, se possuído")
    rarity: Optional[int] = Field(None, description="Raridade do personagem")
    rank_str: Optional[str] = Field(None, description="Constelação, Eidolon ou Cinema Mental do jogador")
    icon: Optional[str] = Field(None, description="Ícone do personagem")
    substitutes: List[TeamMemberSubstitute] = Field(
        default_factory=list, description="Substitutos viáveis do roster do jogador se não possuído"
    )


class MatchedTeamItem(BaseModel):
    """Composição de equipe cruzada com o roster real do jogador."""

    team_id: str = Field(..., description="Identificador único da composição")
    team_name: str = Field(..., description="Nome de referência ou arquétipo da equipe")
    game_id: str = Field(..., description="Identificador do jogo (hsr, genshin, zzz)")
    mode: str = Field(..., description="Modo de jogo de referência (MoC, PF, AS, Abismo, Shiyu Defense)")
    tier_or_rank: Optional[str] = Field("", description="Classificação no meta (Rank 1, Tier S, etc.)")
    avg_performance: Optional[str] = Field("", description="Média de ciclos, rodadas ou pontuação do meta")
    usage_rate: Optional[str] = Field("", description="Taxa de uso global no endgame")
    match_percentage: float = Field(..., description="Percentual direto de personagens possuídos (0 a 100%)")
    owned_count: int = Field(..., description="Quantidade de membros possuídos")
    total_count: int = Field(..., description="Quantidade total de membros da equipe (4 ou 3)")
    is_ready: bool = Field(..., description="True se a equipe tem 100% de posse ou substitutos para todos os faltantes")
    readiness_score: float = Field(0.0, description="Nível de preparo e build dos membros possuídos (0 a 100)")
    members: List[TeamMemberMatch] = Field(..., description="Membros recomendados com status de posse")
    synergy_notes: Optional[str] = Field("", description="Notas táticas de sinergia da equipe")
    recommended_buffs_bosses: Optional[str] = Field("", description="Chefes enfrentados ou bônus de fase recomendados")


class EndgameTeamMatchResponse(BaseModel):
    """Resposta estruturada da compatibilidade de equipes de endgame com o roster."""

    status: str = Field("success", description="Status da resposta")
    game_id: str = Field(..., description="Jogo consultado")
    uid: Optional[str] = Field(None, description="UID da conta consultada")
    mode_filter: Optional[str] = Field(None, description="Filtro de modo aplicado")
    total_teams: int = Field(0, description="Total de equipes avaliadas")
    ready_teams_count: int = Field(0, description="Total de equipes 100% completas")
    teams: List[MatchedTeamItem] = Field(
        default_factory=list, description="Lista de equipes ordenadas por compatibilidade"
    )
    available_modes: List[str] = Field(
        default_factory=list, description="Lista de modos de endgame disponíveis para filtro"
    )
