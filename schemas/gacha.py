from pydantic import BaseModel, Field
from typing import Optional


class GachaRequest(BaseModel):
    game_id: Optional[str] = Field(default="genshin", description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    banner_type: Optional[str] = Field(default="character", description="Tipo de banner ('character' ou 'weapon')")
    current_pity: Optional[int] = Field(default=0, description="Contagem atual de pity do jogador no banner")
    is_guaranteed: Optional[bool] = Field(
        default=False, description="Indica se o próximo item de 5 estrelas é o garantido (sem 50/50 ou 75/25)"
    )
    pulls_available: Optional[int] = Field(
        default=0, description="Quantidade de tiros/destinos disponíveis para simulação"
    )
    target_copies: Optional[int] = Field(default=1, description="Número de cópias desejadas do item alvo")
    current_copies: Optional[int] = Field(default=0, description="Número de cópias já possuídas")
    current_rank: Optional[int] = Field(
        default=None,
        description="Rank/constelação/eidolon/refinamento inicial (-1 para não obtido, 0 para C0/E0/M0/R1)",
    )
    target_rank: Optional[int] = Field(
        default=None, description="Rank final almejado (0 a 6 para char, 0 a 4 para arma)"
    )
    char_name: Optional[str] = Field(default=None, description="Nome do personagem ou arma alvo no banner promocional")


class GachaForecastRequest(BaseModel):
    game_id: Optional[str] = Field(default="genshin", description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    banner_type: Optional[str] = Field(default="character", description="Tipo de banner ('character' ou 'weapon')")
    character_name: Optional[str] = Field(default="", description="Nome do personagem ou arma alvo do planejamento")
    current_pulls: Optional[int] = Field(
        default=0, description="Tiros ou equivalente em gemas/jades/polychromes já guardados"
    )
    current_pity: Optional[int] = Field(default=0, description="Pity acumulado no banner relevante")
    is_guaranteed: Optional[bool] = Field(default=False, description="Garantido no 50/50 ou 75/25 ativo")
    target_rank: Optional[int] = Field(default=0, description="Constelação, eidolon ou refinamento alvo (0 para C0/R1)")
    current_rank: Optional[int] = Field(default=-1, description="Rank atual (-1 se não possui o item)")
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
    target_date: Optional[str] = Field(
        default=None, description="Data/hora alvo da atualização quando o banner chega (ISO 8601)"
    )
    created_at: Optional[str] = Field(default=None, description="Data/hora exata em que a meta foi criada (ISO 8601)")
    banner_phase: Optional[int] = Field(
        default=1, description="Fase do banner planejado: 1 (23:30 para os 3 jogos) ou 2 (20h Genshin, 14h HSR/ZZZ)"
    )


class GachaGoalItem(BaseModel):
    id: int = Field(description="ID único da meta salva")
    game_id: str = Field(description="Identificador do jogo")
    character_name: str = Field(description="Nome do personagem ou arma alvo")
    character_icon: Optional[str] = Field(default=None, description="URL segura do ícone do item alvo")
    target_rank_str: str = Field(description="Rank/Constelação/Eidolon almejado")
    current_pulls: int = Field(description="Tiros iniciais no momento da criação")
    current_pity: int = Field(description="Pity inicial no momento da criação")
    is_guaranteed: bool = Field(description="Status do garantido no momento da criação")
    target_days: int = Field(description="Prazo total em dias planejado")
    has_daily_pass: bool = Field(description="Se possui passe diário ativo")
    success_rate: float = Field(description="Probabilidade calculada de sucesso (%)")
    projected_pulls: int = Field(description="Total de tiros projetados até o banner")
    notes: Optional[str] = Field(default="", description="Notas da meta")
    created_at: str = Field(description="Data/hora ISO em que a meta foi criada")
    target_date: str = Field(description="Data/hora ISO da chegada da atualização/banner")
    banner_phase: Optional[int] = Field(default=1, description="Fase do banner (1 ou 2)")
    banner_time: Optional[str] = Field(
        default="23:30", description="Horário oficial do banner (ex: '23:30', '20:00', '14:00')"
    )
    days_elapsed: int = Field(default=0, description="Dias decorridos desde a criação")
    days_remaining: int = Field(default=0, description="Dias restantes até o banner")
    seconds_elapsed: int = Field(default=0, description="Segundos decorridos desde a criação")
    seconds_remaining: int = Field(default=0, description="Segundos restantes até o banner")
    time_progress_pct: float = Field(default=0.0, description="Percentual de progresso temporal (0 a 100%)")
    is_arrived: bool = Field(default=False, description="Indica se o dia da atualização/banner já chegou")
    accumulated_pulls_now: int = Field(default=0, description="Estimativa de tiros acumulados até o momento atual")


class GachaGoalsListResponse(BaseModel):
    game_id: str = Field(description="Filtro de jogo consultado")
    goals: list[GachaGoalItem] = Field(default_factory=list, description="Lista de metas salvas com tempo em andamento")


class CharacterMiniInfo(BaseModel):
    name: str = Field(description="Nome do personagem")
    icon: str = Field(description="URL da foto/ícone do personagem")
    rarity: int = Field(default=5, description="Raridade (5 para 5★/Rank S, 4 para 4★/Rank A)")
    element: Optional[str] = Field(default=None, description="Elemento do personagem")


class BannerDetail(BaseModel):
    character_name: str = Field(description="Nome do personagem ou arma em destaque no banner")
    banner_title: Optional[str] = Field(default=None, description="Título do evento/banner in-game")
    banner_image: str = Field(description="URL da imagem oficial de arte do banner in-game")
    character_info: Optional[CharacterMiniInfo] = Field(default=None, description="Foto e informações do 5★ do banner")
    featured_4stars: list[str] = Field(
        default_factory=list, description="Lista de personagens/armas 4★ com taxa aumentada"
    )
    featured_4stars_info: list[CharacterMiniInfo] = Field(
        default_factory=list, description="Fotos e dados dos 4★ com taxa aumentada"
    )
    is_primary: bool = Field(default=False, description="Se é o banner principal de estreia da fase")
    banner_type: Optional[str] = Field(default="character", description="Tipo de banner ('character' ou 'weapon')")


class GameBannersData(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr', 'zzz')")
    patch_info: Optional[str] = Field(default="", description="Versão e fase ativa do patch")
    banners: list[BannerDetail] = Field(default_factory=list, description="Lista de banners de personagens ativos")
    weapon_banners: list[BannerDetail] = Field(default_factory=list, description="Lista de banners de armas ativos")
    last_updated: Optional[str] = Field(default=None, description="Data da última sincronização do manifesto")


class GachaSimulatorDefaultsResponse(BaseModel):
    game_id: str = Field(description="Identificador do jogo")
    banner_type: str = Field(default="character", description="Tipo de banner consultado ('character' ou 'weapon')")
    current_pity: int = Field(default=0, description="Pity atual do jogador no banner consultado")
    is_guaranteed: bool = Field(default=False, description="Status do garantido")
    character_pity: Optional[int] = Field(default=0, description="Pity do banner de personagens")
    character_guaranteed: Optional[bool] = Field(default=False, description="Garantido no banner de personagens")
    weapon_pity: Optional[int] = Field(default=0, description="Pity do banner de armas")
    weapon_guaranteed: Optional[bool] = Field(default=False, description="Garantido no banner de armas")
    active_banner_character: Optional[str] = Field(default=None, description="Nome do item 5★ do banner ativo padrão")
    active_banner_title: Optional[str] = Field(default=None, description="Título oficial do banner in-game ativo")
    active_banner_image: Optional[str] = Field(default=None, description="URL proxy da arte do banner ativo")
    active_character_info: Optional[CharacterMiniInfo] = Field(
        default=None, description="Foto e informações do 5★ ativo"
    )
    featured_4stars: list[str] = Field(default_factory=list, description="Lista de nomes dos 4★ em destaque")
    featured_4stars_info: list[CharacterMiniInfo] = Field(
        default_factory=list, description="Fotos e dados dos 4★ com taxa aumentada"
    )
    patch_info: Optional[str] = Field(default="", description="Informações da fase e versão atual do patch")
    available_banners: list[BannerDetail] = Field(default_factory=list, description="Banners ativos disponíveis")
    available_weapon_banners: list[BannerDetail] = Field(
        default_factory=list, description="Banners de armas ativos disponíveis"
    )


class StrategyAskAIRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    custom_question: Optional[str] = Field(
        default=None, description="Pergunta específica do usuário sobre sinergias e economia de tiros"
    )
