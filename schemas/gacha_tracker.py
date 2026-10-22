from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union


class GachaPullItem(BaseModel):
    id: str = Field(description="Identificador único universal da puxada/tiro extraído da API da HoYoverse")
    time: str = Field(description="Data e hora da puxada em formato string 'YYYY-MM-DD HH:MM:SS'")
    name: str = Field(description="Nome do personagem ou cone/arma/w-engine obtido")
    item_type: str = Field(default="character", description="Tipo do item ('character' ou 'weapon')")
    rarity: int = Field(default=3, description="Raridade estelar do item (3, 4 ou 5)")
    gacha_type: str = Field(default="301", description="Código numérico do tipo de banner na API")
    banner_category: str = Field(
        default="character", description="Categoria agregada do banner ('character', 'weapon' ou 'standard')"
    )
    pity: int = Field(default=1, description="Contador de pity calculado no momento em que o item veio")
    is_win_5050: Optional[bool] = Field(default=None, description="Indica se venceu o 50/50 em pulls 5 estrelas")


class FiveStarRecord(BaseModel):
    name: str = Field(description="Nome do item 5 estrelas obtido")
    rarity: int = Field(default=5, description="Raridade do item (sempre 5)")
    time: str = Field(description="Data e hora do registro")
    pity: int = Field(description="Contagem de pity em que o item 5 estrelas foi dropado")
    is_win_5050: bool = Field(description="Verdadeiro se o item 5 estrelas foi ganho no 50/50")
    is_rate_up: bool = Field(description="Verdadeiro se era o item de destaque (rate-up) do banner")
    banner_category: str = Field(description="Categoria do banner onde ocorreu a obtenção")


class BannerTrackerStats(BaseModel):
    banner_category: str = Field(description="Categoria do banner analisado ('character', 'weapon', 'standard')")
    display_name: str = Field(description="Nome legível para exibição visual do banner")
    current_pity: int = Field(default=0, description="Pity acumulado desde o último item 5 estrelas")
    is_guaranteed: bool = Field(default=False, description="Indica se o próximo 5 estrelas deste banner é garantido")
    total_pulls: int = Field(default=0, description="Total histórico de puxadas registradas no banner")
    five_stars_count: int = Field(default=0, description="Total de itens 5 estrelas obtidos")
    four_stars_count: int = Field(default=0, description="Total de itens 4 estrelas obtidos")
    three_stars_count: int = Field(default=0, description="Total de itens 3 estrelas obtidos")
    avg_five_star_pity: float = Field(default=0.0, description="Média histórica de pity por item 5 estrelas")
    win_5050_rate: float = Field(default=100.0, description="Taxa percentual de vitórias no 50/50")
    recent_five_stars: List[FiveStarRecord] = Field(
        default=[], description="Lista dos últimos itens 5 estrelas obtidos"
    )
    next_soft_pity_in: int = Field(default=0, description="Pulls restantes até atingir a margem de soft pity")
    pulls_to_hard_pity: int = Field(default=90, description="Pulls restantes até o hard pity absoluto (garantia)")


class GachaTrackerOverviewResponse(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    uid: str = Field(description="UID da conta cujos dados de gacha foram calculados")
    character_banner: BannerTrackerStats = Field(
        description="Estatísticas consolidadas do banner promocional de personagens"
    )
    weapon_banner: BannerTrackerStats = Field(
        description="Estatísticas consolidadas do banner de armas / cones de luz / w-engines"
    )
    standard_banner: BannerTrackerStats = Field(description="Estatísticas consolidadas do banner permanente/mochilão")
    total_pulls_all_banners: int = Field(default=0, description="Soma total de tiros em todos os banners monitorados")
    total_five_stars_all_banners: int = Field(default=0, description="Soma total de 5 estrelas obtidos na conta")
    overall_luck_rating: str = Field(
        default="Normal",
        description="Classificação executiva de sorte da conta ('Lendária', 'Sortuda', 'Normal', 'Azarada')",
    )


class ImportGachaRequest(BaseModel):
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Dump de dados crus ou formato padronizado UIGF/SRGF"
    )
    pulls_list: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Lista pré-formatada de registros de pulls"
    )
    uid: Optional[str] = Field(default=None, description="UID associado às puxadas importadas")


class ImportGachaResponse(BaseModel):
    success: bool = Field(description="Indica se o processo de importação foi concluído")
    game_id: str = Field(description="Identificador do jogo processado")
    uid: str = Field(description="UID para o qual os tiros foram registrados")
    total_imported: int = Field(description="Número de novas puxadas inseridas no banco local")
    total_duplicates: int = Field(description="Puxadas ignoradas por já existirem no histórico")
    message: str = Field(description="Mensagem resumida do status da importação")
