from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class ViviaState(TypedDict):
    # Identidade da sessão
    user_id: str                          # "joao" | "viviane"
    session_date: str                     # "2026-07-23"
    current_moment: str                   # momento ativo do dia

    # Conversa em andamento
    messages: Annotated[list[BaseMessage], add_messages]

    # Contexto carregado no início do dia
    persona_profile: str                  # JSON do perfil serializado
    recent_summaries: str                 # resumos dos últimos 7 dias

    # Checklist do dia (atualizado a cada momento)
    medication_taken: bool
    water_glasses: int
    mood_score: int                       # 0-10, -1 = não registrado
    steps_count: int                      # -1 = não registrado