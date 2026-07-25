from datetime import date

from langchain_core.messages import HumanMessage
from vivia.graph.builder import build_graph
from vivia.graph.router import get_current_moment
from vivia.personas.loader import load_persona, persona_to_prompt
from vivia.memory.repository import (
    get_recent_summaries,
    format_summaries_for_prompt,
    save_message,
)


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

    current_moment = get_current_moment()
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

    print(f"\nMomento atual: {current_moment}")
    print(f"Persona: {persona['nome']}")
    print("─" * 40)
    print("(digite 'sair' para encerrar)\n")

    # Primeiro turno — Vivia inicia
    result = graph.invoke(state)
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

        save_message(user_id, current_moment, "user", user_input, session_date)
        state["messages"].append(HumanMessage(content=user_input))

        result = graph.invoke(state)
        vivia_msg = result["messages"][-1].content
        print(f"\nVivia: {vivia_msg}\n")
        save_message(
            user_id, result["current_moment"], "assistant", vivia_msg, session_date
        )
        state = result


if __name__ == "__main__":
    run()