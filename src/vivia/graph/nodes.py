from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from vivia.config import settings
from vivia.graph.state import ViviaState

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _build_system_prompt(state: ViviaState, moment_name: str, moment_prompt: str) -> str:
    base = _load_prompt("system_prompt.md")
    return (
        base.format(
            user_id=state["user_id"],
            session_date=state["session_date"],
            current_moment=moment_name,  # nome explícito do nó, nunca o do estado
            persona_profile=state["persona_profile"],
            recent_summaries=state["recent_summaries"] or "Primeiro dia de uso.",
            medication_taken="Sim" if state["medication_taken"] else "Não registrado",
            water_glasses=state["water_glasses"],
            mood_score=state["mood_score"] if state["mood_score"] >= 0 else "Não registrado",
            steps_count=state["steps_count"] if state["steps_count"] >= 0 else "Não registrado",
        )
        + "\n\n"
        + moment_prompt
    )


def _get_llm() -> ChatOpenAI:
    """
    Cria o cliente do LLM.

    IMPORTANTE — sem 'temperature' fixa de propósito: modelos de raciocínio
    da OpenAI (o1, o3, o4-mini, e toda a linha gpt-5.x, incluindo
    gpt-5.6-*) rejeitam qualquer valor de temperature diferente do padrão
    (1) com erro 400. Deixar o parâmetro de fora torna o código compatível
    com QUALQUER modelo configurado no .env, de raciocínio ou não, atual
    ou futuro — sem precisar tratar caso a caso.

    max_retries / timeout: retry automático com backoff em erros
    transitórios (500, timeout, conexão) antes de desistir.
    """
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        max_retries=4,
        timeout=30,
    )


def _call_llm(state: ViviaState, moment_name: str) -> ViviaState:
    llm = _get_llm()
    moment_prompt = _load_prompt(f"moments/{moment_name}.md")
    system = _build_system_prompt(state, moment_name, moment_prompt)

    try:
        response = llm.invoke(
            [SystemMessage(content=system)] + state["messages"]
        )
    except Exception as exc:
        # Erro persistente mesmo após os retries automáticos do langchain.
        # Repassamos com uma mensagem mais clara para quem estiver rodando
        # a POC (main.py trata isso com uma mensagem amigável).
        raise RuntimeError(
            f"Falha ao falar com a OpenAI após múltiplas tentativas "
            f"no momento '{moment_name}'. Detalhe original: {exc}"
        ) from exc

    return {"messages": [response], "current_moment": moment_name}


# Um nó por momento do dia
def node_acordar(state: ViviaState) -> ViviaState:
    return _call_llm(state, "acordar")

def node_cafe_manha(state: ViviaState) -> ViviaState:
    return _call_llm(state, "cafe_manha")

def node_meio_manha(state: ViviaState) -> ViviaState:
    return _call_llm(state, "meio_manha")

def node_almoco(state: ViviaState) -> ViviaState:
    return _call_llm(state, "almoco")

def node_meio_tarde(state: ViviaState) -> ViviaState:
    return _call_llm(state, "meio_tarde")

def node_jantar(state: ViviaState) -> ViviaState:
    return _call_llm(state, "jantar")

def node_antes_dormir(state: ViviaState) -> ViviaState:
    return _call_llm(state, "antes_dormir")