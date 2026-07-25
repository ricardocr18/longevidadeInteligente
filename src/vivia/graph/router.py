from datetime import datetime


MOMENTS = [
    "acordar",
    "cafe_manha",
    "meio_manha",
    "almoco",
    "meio_tarde",
    "jantar",
    "antes_dormir",
]

MOMENT_SCHEDULE = {
    "acordar":       (5,  8),
    "cafe_manha":    (8,  10),
    "meio_manha":    (10, 12),
    "almoco":        (12, 14),
    "meio_tarde":    (14, 18),
    "jantar":        (18, 21),
    "antes_dormir":  (21, 24),
}


def get_current_moment() -> str:
    """Retorna o momento do dia baseado no horário atual."""
    hour = datetime.now().hour
    for moment, (start, end) in MOMENT_SCHEDULE.items():
        if start <= hour < end:
            return moment
    return "antes_dormir"  # fallback para madrugada


def get_next_moment(current: str) -> str:
    """Retorna o próximo momento na sequência."""
    idx = MOMENTS.index(current)
    if idx < len(MOMENTS) - 1:
        return MOMENTS[idx + 1]
    return "__end__"