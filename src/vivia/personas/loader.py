import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "personas"


def load_persona(user_id: str) -> dict:
    """Carrega o perfil JSON de uma persona pelo user_id."""
    path = DATA_DIR / f"{user_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Persona '{user_id}' não encontrada em {DATA_DIR}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _format_familia(profile: dict) -> str:
    lines = []
    conjuge = profile.get("conjuge")
    if conjuge and conjuge.get("nome"):
        lines.append(f"Cônjuge: {conjuge['nome']}")

    filhos = profile.get("filhos", [])
    if filhos:
        partes = [f"{f['nome']} ({f['situacao']})" for f in filhos]
        lines.append("Filhos: " + "; ".join(partes))

    netos = profile.get("netos", [])
    if netos:
        partes = [f"{n['nome']} — {n['observacao']}" for n in netos]
        lines.append("Netos: " + "; ".join(partes))

    return "\n".join(lines)


def persona_to_prompt(profile: dict) -> str:
    """
    Serializa o perfil biográfico vivo (estrutura aninhada) em texto
    estruturado para injeção no system prompt.
    """
    p = profile
    bio = p.get("biografia", {})
    saude = p.get("saude", {})
    social = p.get("contexto_social", {})
    prefs = p.get("preferencias", {})

    lines = [
        f"Nome: {p['nome']} ({p.get('tratamento', p['nome'])})",
        f"Idade: {p.get('idade', 'não informada')} anos",
        f"Estado civil: {p.get('estado_civil', 'não informado')}",
        "",
        "── Família ──",
        _format_familia(p),
        "",
        "── Biografia ──",
        f"Profissão: {bio.get('profissao', 'não informada')}",
        f"Instrução: {bio.get('instrucao', 'não informada')} "
        f"(nível: {bio.get('escolaridade_nivel', 'não informado')} — "
        f"use isso para calibrar a linguagem, conforme regra 1 do prompt)",
    ]

    marcos = bio.get("marcos_de_vida", [])
    if marcos:
        lines.append("Marcos de vida:")
        for m in marcos:
            lines.append(f"  - {m}")

    lines += [
        "",
        "── Saúde ──",
        f"Comorbidades: {', '.join(saude.get('comorbidades', []))}",
        f"Medicamentos: {'; '.join(saude.get('medicamentos', []))}",
        f"Atividade física: {saude.get('atividade_fisica', 'não informada')}",
        f"Alimentação: {saude.get('alimentacao', 'não informada')}",
    ]

    alertas = saude.get("alertas", [])
    if alertas:
        lines.append("Alertas de atenção especial:")
        for a in alertas:
            lines.append(f"  ⚠ {a}")

    lines += [
        "",
        "── Contexto social ──",
        f"Arranjo domiciliar: {social.get('arranjo_domiciliar', 'não informado')}",
        f"Rede social: {social.get('rede_social', 'não informada')}",
        f"Religião/espiritualidade: {social.get('religiao', 'não informada')} "
        f"(regra 4: só mencionar se a pessoa trouxer o tema)",
        f"Nível socioeconômico e rotina: {social.get('nivel_socioeconomico_rotina', 'não informado')}",
        "",
        "── Preferências ──",
        f"Entretenimento: {', '.join(prefs.get('entretenimento', []))}",
        f"Instrumento musical: {prefs.get('instrumento_musical', 'não informado')}",
        f"Letramento digital: {prefs.get('letramento_digital', 'não informado')}",
        "",
        "── Plano de cuidado ──",
    ]
    for item in p.get("plano_cuidado", []):
        lines.append(f"  - {item}")

    return "\n".join(lines)