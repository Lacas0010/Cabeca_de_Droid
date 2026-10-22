from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str = Field(description="Papel do emissor da mensagem ('user', 'assistant' ou 'system')")
    text: str = Field(description="Conteúdo textual da mensagem no chat")


class ChatRequest(BaseModel):
    message: str = Field(description="Pergunta ou comando enviado pelo usuário")
    game_id: str = Field(description="Contexto do jogo atual ('genshin', 'hsr' ou 'zzz')")
    history: List[ChatMessage] = Field(default=[], description="Histórico de mensagens recentes para contexto na LLM")


class TeamAnalyzeRequest(BaseModel):
    game_id: str = Field(description="Contexto do jogo ('genshin', 'hsr' ou 'zzz') para análise de composição")
    characters: List[str] = Field(description="Lista com os nomes dos personagens que compõem a equipe")


class ChatHistoryMessage(BaseModel):
    id: int = Field(description="Identificador sequencial único do registro no banco SQLite")
    game_id: str = Field(description="Identificador do jogo vinculado à conversa")
    role: str = Field(description="Papel do emissor ('user' ou 'assistant')")
    content: str = Field(description="Texto completo salvo da mensagem")
    created_at: str = Field(description="Carimbo de data e hora no padrão ISO")


class ChatHistoryResponse(BaseModel):
    game_id: str = Field(description="Identificador do jogo cujas mensagens foram carregadas")
    messages: List[ChatHistoryMessage] = Field(default=[], description="Lista histórica ordenada de mensagens salvas")
