import base64
from datetime import date
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage, AIMessage

from vivia.config import settings
from vivia.graph.builder import build_graph
from vivia.graph.router import MOMENTS, get_current_moment
from vivia.personas.loader import load_persona, persona_to_prompt
from vivia.memory.repository import (
    get_recent_summaries,
    format_summaries_for_prompt,
    get_today_messages,
    delete_today_messages,
    save_message,
)
from vivia.memory.summarizer import ensure_summaries_up_to_date
from vivia.voice.stt import transcribe_audio
from vivia.voice.tts import synthesize_speech

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Vivia POC")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MOMENT_LABELS = {
    "acordar": "Ao acordar",
    "cafe_manha": "Café da manhã",
    "meio_manha": "Meio da manhã",
    "almoco": "Almoço",
    "meio_tarde": "Meio da tarde",
    "jantar": "Jantar",
    "antes_dormir": "Antes de dormir",
}

PERSONAS = [
    {"id": "joao", "nome": "João"},
    {"id": "viviane", "nome": "Viviane"},
]

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _is_test_mode() -> bool:
    return settings.app_env != "production"


def _rebuild_messages(rows: list[dict]) -> list:
    msgs = []
    for r in rows:
        if r["role"] == "user":
            msgs.append(HumanMessage(content=r["content"]))
        else:
            msgs.append(AIMessage(content=r["content"]))
    return msgs


def _process_turn(user_id: str, user_text: str | None, moment_override: str | None) -> dict:
    session_date = date.today().isoformat()

    # Checagem de virada de dia: se algum dia anterior ficou sem resumo,
    # gera agora, antes de continuar. Barato quando não há pendência.
    ensure_summaries_up_to_date(user_id, before_date=session_date)

    persona = load_persona(user_id)
    persona_text = persona_to_prompt(persona)
    summaries_text = format_summaries_for_prompt(get_recent_summaries(user_id))

    messages = _rebuild_messages(get_today_messages(user_id, session_date))

    # Em produção, o momento SEMPRE vem do relógio real. A escolha manual
    # só existe fora de produção, e nem é mais exposta no frontend — só
    # continua disponível aqui por segurança/depuração futura.
    if moment_override and _is_test_mode() and moment_override in MOMENT_LABELS:
        current_moment = moment_override
    else:
        current_moment = get_current_moment()

    if user_text:
        messages.append(HumanMessage(content=user_text))

    state = {
        "user_id": user_id,
        "session_date": session_date,
        "current_moment": current_moment,
        "messages": messages,
        "persona_profile": persona_text,
        "recent_summaries": summaries_text,
        "medication_taken": False,
        "water_glasses": 0,
        "mood_score": -1,
        "steps_count": -1,
    }

    result = _get_graph().invoke(state)
    vivia_text = result["messages"][-1].content

    if user_text:
        save_message(user_id, current_moment, "user", user_text, session_date)
    save_message(user_id, current_moment, "assistant", vivia_text, session_date)

    return {"text": vivia_text, "moment": current_moment}


@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/config")
def get_config():
    return {"personas": PERSONAS}


@app.post("/api/reset")
async def reset_conversation(user_id: str = Form(...)):
    """
    Apaga o histórico de hoje de uma persona. Não exposto no frontend —
    só existe fora de produção, como ferramenta de depuração manual.
    """
    if not _is_test_mode():
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    session_date = date.today().isoformat()
    deleted = delete_today_messages(user_id, session_date)
    return {"deleted": deleted, "session_date": session_date}


@app.post("/api/start")
async def start_session(
    user_id: str = Form(...),
    moment: str | None = Form(None),
):
    result = _process_turn(user_id, None, moment)
    audio_b64 = base64.b64encode(synthesize_speech(result["text"])).decode("utf-8")
    return {**result, "audio_base64": audio_b64}


@app.post("/api/message")
async def send_text_message(
    user_id: str = Form(...),
    text: str = Form(...),
    moment: str | None = Form(None),
):
    result = _process_turn(user_id, text, moment)
    audio_b64 = base64.b64encode(synthesize_speech(result["text"])).decode("utf-8")
    return {**result, "audio_base64": audio_b64}


@app.post("/api/voice-message")
async def send_voice_message(
    user_id: str = Form(...),
    moment: str | None = Form(None),
    audio: UploadFile = File(...),
):
    audio_bytes = await audio.read()
    transcript = transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")

    result = _process_turn(user_id, transcript, moment)
    audio_b64 = base64.b64encode(synthesize_speech(result["text"])).decode("utf-8")
    return {**result, "transcript": transcript, "audio_base64": audio_b64}