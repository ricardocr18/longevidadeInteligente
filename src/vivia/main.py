from datetime import date

from langchain_core.messages import HumanMessage
from vivia.config import settings
from vivia.graph.builder import build_graph
from vivia.graph.router import MOMENTS, get_current_moment
from vivia.personas.loader import load_persona, persona_to_prompt
from vivia.memory.repository import (
    get_recent_summaries,
    format_summaries_for_prompt,
    save_message,
)

MOMENT_LABELS = {
    "acordar": "Ao acordar",
    "cafe_manha": "Café da manhã",
    "meio_manha": "Meio da manhã",
    "almoco": "Almoço",
    "meio_tarde": "Meio da tarde",
    "jantar": "Jantar",
    "antes_dormir": "Antes de dormir",
}


def _is_test_mode() -> bool:
    """
    A seleção manual de momento só existe fora de produção. Em produção
    (APP_ENV=production, configurado no deploy real), o momento é SEMPRE
    calculado por router.get_current_moment() — nunca escolhido à mão.
    """
    return settings.app_env != "production"


def _invoke_with_feedback(graph, state):
    """Chama o grafo e traduz falhas de API em mensagem amigável."""
    try:
        return graph.invoke(state)
    except RuntimeError as exc:
        print(
            "\n⚠ A Vivia não conseguiu responder agora — a OpenAI está "
            "instável ou fora do ar no momento.\n"
            f"Detalhe técnico: {exc}\n"
            "Tente novamente em alguns instantes.\n"
        )
        return None


def _prompt_manual_moment(current: str) -> str:
    """[SOMENTE POC/TESTE] Menu para escolher o momento do dia na mão."""
    print("\nEscolha o momento do dia para testar:")
    for i, m in enumerate(MOMENTS, start=1):
        marcador = "  (atual)" if m == current else ""
        print(f"  {i}. {MOMENT_LABELS[m]}{marcador}")

    while True:
        escolha = input("Número do momento: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(MOMENTS):
            return MOMENTS[int(escolha) - 1]
        print("Opção inválida — digite um número entre 1 e 7.")


def _choose_initial_moment() -> str:
    """
    Fora de produção, pergunta se quer detecção automática (o comportamento
    real) ou escolha manual (só para acelerar testes). Em produção, pula
    direto para a detecção automática, sem perguntar nada.
    """
    if not _is_test_mode():
        return get_current_moment()

    modo = input(
        "Detectar o momento pelo horário real ou escolher manualmente "
        "para teste? (auto/manual) [auto]: "
    ).strip().lower()

    if modo == "manual":
        return _prompt_manual_moment(current="")
    return get_current_moment()


def run() -> None:
    print("\n══════════════════════════════════════")
    print("          V I V I A  —  POC           ")
    print("══════════════════════════════════════")

    user_id = input("Persona (joao / viviane): ").strip().lower()
    if user_id not in ("joao", "viviane"):
        print("Persona não reconhecida.")
        return

    persona = load_persona(user_id)
    persona_text = persona_to_prompt(persona)

    summaries = get_recent_summaries(user_id)
    summaries_text = format_summaries_for_prompt(summaries)

    current_moment = _choose_initial_moment()
    session_date = date.today().isoformat()

    graph = build_graph()

    state = {
        "user_id": user_id,
        "session_date": session_date,
        "current_moment": current_moment,
        "messages": [],
        "persona_profile": persona_text,
        "recent_summaries": summaries_text,
        "medication_taken": False,
        "water_glasses": 0,
        "mood_score": -1,
        "steps_count": -1,
    }

    print(f"\nMomento atual: {MOMENT_LABELS[current_moment]}")
    print(f"Persona: {persona['nome']}")
    print("─" * 40)
    if _is_test_mode():
        print(
            "(digite 'sair' para encerrar | 'momento' para trocar o "
            "momento do dia — disponível só neste modo de teste)\n"
        )
    else:
        print("(digite 'sair' para encerrar)\n")

    # Primeiro turno — Vivia inicia
    result = _invoke_with_feedback(graph, state)
    if result is None:
        return
    vivia_msg = result["messages"][-1].content
    print(f"Vivia: {vivia_msg}\n")
    save_message(user_id, current_moment, "assistant", vivia_msg, session_date)
    state = result

    # Loop de conversa
    while True:
        user_input = input("Você: ").strip()

        if user_input.lower() == "sair":
            print("\nVivia: Até mais! Cuide-se bem. 💚\n")
            break

        if user_input.lower() == "momento" and _is_test_mode():
            novo_momento = _prompt_manual_moment(current=state["current_moment"])
            state["current_moment"] = novo_momento
            print(
                f"\n[POC] Momento alterado manualmente para: "
                f"{MOMENT_LABELS[novo_momento]}\n"
            )

            # Vivia inicia o novo momento proativamente, mantendo o
            # histórico da conversa do dia (mesma lógica do primeiro turno).
            result = _invoke_with_feedback(graph, state)
            if result is None:
                continue
            vivia_msg = result["messages"][-1].content
            print(f"Vivia: {vivia_msg}\n")
            save_message(
                user_id, result["current_moment"], "assistant", vivia_msg, session_date
            )
            state = result
            continue

        save_message(user_id, state["current_moment"], "user", user_input, session_date)
        state["messages"].append(HumanMessage(content=user_input))

        result = _invoke_with_feedback(graph, state)
        if result is None:
            state["messages"].pop()
            continue

        vivia_msg = result["messages"][-1].content
        print(f"\nVivia: {vivia_msg}\n")
        save_message(
            user_id, result["current_moment"], "assistant", vivia_msg, session_date
        )
        state = result


if __name__ == "__main__":
    run()