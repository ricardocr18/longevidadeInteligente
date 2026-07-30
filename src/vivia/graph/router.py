from datetime import datetime, date
from zoneinfo import ZoneInfo

# Fixo em horário do Brasil, independente de onde o servidor estiver
# rodando (o Railway, por exemplo, roda os containers em UTC por padrão).
# Sem isso, a detecção automática de momento do dia ficaria errada em
# produção — e como não existe mais escolha manual no frontend, esse
# erro passaria despercebido até alguém notar a Vivia "fora de hora".
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")

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


def now_in_brazil() -> datetime:
    """Horário atual, sempre no fuso de São Paulo."""
    return datetime.now(BRAZIL_TZ)


def today_in_brazil() -> date:
    """Data atual (o 'dia' civil), sempre no fuso de São Paulo.

    Importante perto da meia-noite: usar isso em vez de date.today()
    evita que o servidor (rodando em UTC) ache que já é o dia seguinte
    quando no Brasil ainda são, por exemplo, 21h."""
    return now_in_brazil().date()


def get_current_moment() -> str:
    """Retorna o momento do dia baseado no horário atual do Brasil."""
    hour = now_in_brazil().hour
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