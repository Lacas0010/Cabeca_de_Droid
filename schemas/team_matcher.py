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


class EndgameResetScheduleItem(BaseModel):
    """Horário de reset da temporada ativa de um modo endgame."""

    id: str = Field(..., description="Identificador do modo (moc, pure_fiction, spiral_abyss, shiyu_defense, etc.)")
    name: str = Field(..., description="Nome localizado do modo")
    badge: str = Field("", description="Sigla curta do modo")
    icon: Optional[str] = Field(None, description="URL local do ícone oficial do modo endgame")
    begin_at: Optional[str] = Field(None, description="Início da temporada atual em ISO-8601 UTC")
    reset_at: Optional[str] = Field(None, description="Data/hora exata do próximo reset em ISO-8601 UTC")
    source: str = Field("hoyolab", description="Origem do horário ('hoyolab' ou 'estimated')")


class EndgameResponse(BaseModel):
    """Resposta estruturada do endpoint /api/endgame/{game_id}."""

    status: str = Field("success", description="Status da resposta")
    game_id: str = Field(..., description="Jogo consultado (hsr, genshin, zzz)")
    has_data: bool = Field(False, description="Indica se há registros de times/andares sincronizados")
    updated_at: str = Field("", description="Timestamp da última atualização no banco")
    uid: str = Field("", description="UID da conta consultada")
    modes: List[dict] = Field(default_factory=list, description="Modos de endgame com times e pontuações")
    reset_schedules: List[EndgameResetScheduleItem] = Field(
        default_factory=list, description="Cronograma de reset de todos os modos endgame do jogo"
    )


class ServerCycleResetInfo(BaseModel):
    """Horários de reset Diário (04:00) e Semanal (Segunda 04:00) no fuso do servidor."""

    daily_reset_at: str = Field(..., description="Próximo reset diário às 04:00 (servidor) em ISO-8601 UTC")
    weekly_reset_at: str = Field(..., description="Próximo reset semanal na segunda às 04:00 (servidor) em ISO-8601 UTC")
    server_tz_label: str = Field("UTC-5", description="Rótulo do fuso do servidor utilizado no cálculo")


class EndgameResetRadarItem(BaseModel):
    """Card compacto de um modo endgame no Radar Unificado de Resets da Home."""

    game_id: str = Field(..., description="Identificador do jogo ('hsr', 'genshin', 'zzz')")
    game_label: str = Field(..., description="Sigla curta do jogo ('HSR', 'Genshin', 'ZZZ')")
    id: str = Field(..., description="Identificador do modo endgame")
    name: str = Field(..., description="Nome localizado do modo")
    badge: str = Field("", description="Sigla curta do modo")
    icon: Optional[str] = Field(None, description="URL local do ícone oficial do modo endgame")
    begin_at: Optional[str] = Field(None, description="Início da temporada atual em ISO-8601 UTC")
    reset_at: Optional[str] = Field(None, description="Próximo reset em ISO-8601 UTC")
    source: str = Field("hoyolab", description="Origem do horário ('hoyolab' ou 'estimated')")
    status: str = Field("pending", description="Estado de conclusão: 'completed', 'in_progress' ou 'pending'")
    stars: Optional[int] = Field(None, description="Estrelas/medalhas conquistadas na temporada")
    max_stars: Optional[int] = Field(None, description="Máximo de estrelas/medalhas do modo")
    metric_value: Optional[str] = Field(None, description="Classificação ou métrica principal (ex: 'S', '12/12')")
    has_record: bool = Field(False, description="Indica se há registro coletado para este modo")
    seconds_remaining: Optional[int] = Field(None, description="Segundos restantes até o reset")
    is_urgent_pending: bool = Field(False, description="True quando pendente/em progresso e próximo do reset (<= 72h)")


class BannerResetRadarItem(BaseModel):
    """Grupo de banners ativos com mesma data/hora de virada no Radar Unificado da Home."""

    game_id: str = Field(..., description="Identificador do jogo ('genshin', 'hsr', 'zzz')")
    game_label: str = Field(..., description="Sigla curta do jogo ('Genshin', 'HSR', 'ZZZ')")
    title: str = Field(..., description="Nomes dos personagens 5★ deste grupo de banner")
    primary_character: str = Field(..., description="Personagem 5★ principal para preenchimento no Simulador")
    characters: List[dict] = Field(default_factory=list, description="Lista de personagens 5★ (name, icon)")
    patch_label: str = Field("", description="Rótulo de patch e fase (ex: 'Patch 7.2 Phase 1')")
    duration_type: str = Field("phase_1", description="Tipo de duração ('phase_1', 'phase_2', 'full_patch', 'collab')")
    phase: Optional[int] = Field(None, description="Fase numérica (1 ou 2) quando aplicável")
    banner_time: str = Field("23:30", description="Horário de virada configurado (HH:MM)")
    end_date: Optional[str] = Field(None, description="Data de término (YYYY-MM-DD)")
    end_at: Optional[str] = Field(None, description="Timestamp exato de virada em ISO-8601 UTC")
    seconds_remaining: Optional[int] = Field(None, description="Segundos restantes até a virada do banner")
    is_ending_soon: bool = Field(False, description="True quando faltam <= 48h para o término do banner")


class EndgameResetRadarResponse(BaseModel):
    """Resposta agregada do Radar Unificado de Resets (7 modos endgame + Banners Ativos + Diário/Semanal)."""

    status: str = Field("success", description="Status da resposta")
    generated_at: str = Field(..., description="Timestamp UTC de geração")
    server_resets: ServerCycleResetInfo = Field(..., description="Timers de reset diário e semanal do servidor")
    summary: dict = Field(default_factory=dict, description="Contadores resumidos de conclusão e pendências")
    items: List[EndgameResetRadarItem] = Field(
        default_factory=list, description="Os 7 modos endgame ordenados por urgência"
    )
    banners: List[BannerResetRadarItem] = Field(
        default_factory=list, description="Banners ativos com data de virada ordenados por urgência"
    )
