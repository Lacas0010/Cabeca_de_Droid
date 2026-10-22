from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class AccountItem(BaseModel):
    uid: str = Field(description="Identificador único (UID) do jogador na conta HoYoverse")
    game_id: str = Field(description="Código identificador do jogo ('genshin', 'hsr' ou 'zzz')")
    nickname: str = Field(description="Nome de exibição (apelido) do jogador no jogo")
    level: int = Field(default=1, description="Nível de pioneiro, rank de aventura ou nível de interlaço")
    active_days: int = Field(default=0, description="Dias ativos acumulados no jogo")
    updated_at: str = Field(default="", description="Data e hora da última sincronização da conta em formato ISO")
    is_active: bool = Field(default=False, description="Indica se esta conta é a conta atualmente ativa para o jogo")
    char_count: int = Field(default=0, description="Quantidade total de personagens obtidos")
    five_stars_count: int = Field(default=0, description="Quantidade total de personagens 5 estrelas obtidos")


class SwitchAccountRequest(BaseModel):
    game_id: str = Field(description="Identificador do jogo ('genshin', 'hsr' ou 'zzz') para troca de conta")
    uid: str = Field(description="UID da conta que deve se tornar ativa")


class AccountsListResponse(BaseModel):
    accounts: List[AccountItem] = Field(default=[], description="Lista de todas as contas vinculadas detectadas")
    active_accounts: Dict[str, str] = Field(default={}, description="Mapa com o UID ativo atualmente por jogo")
