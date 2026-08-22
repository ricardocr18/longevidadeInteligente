# Vivia — POC

Tutora de saúde conversacional para pessoas de 60+ anos, dentro de um programa de longevidade inteligente. Conversa por voz ou texto em sete momentos do dia (acordar, café da manhã, meio da manhã, almoço, meio da tarde, jantar, antes de dormir), com memória entre dias e personalização por perfil biográfico.

---

## Stack

- **Python 3.12** + **uv** (gerenciador de ambiente e dependências)
- **LangGraph** — orquestração dos 7 momentos do dia
- **OpenAI** — LLM de conversação (`gpt-5.6-luna`) e transcrição de voz (`gpt-4o-transcribe`)
- **ElevenLabs** — síntese de voz (`eleven_multilingual_v2`)
- **FastAPI** — servidor web e API
- **SQLite** — memória de curto prazo (mensagens do dia) e episódica (resumos diários)
- **Railway** — hospedagem (Dockerfile próprio, volume persistente para o banco)

## Estrutura do projeto

```
vivia-poc/
├── data/
│   ├── personas/          # joao.json, viviane.json — perfil biográfico vivo (SÓ ficcionais)
│   └── prompts/
│       ├── system_prompt.md      # comportamento global da Vivia
│       ├── summary_prompt.md     # instrução de geração do resumo diário
│       └── moments/              # um .md por momento do dia
├── scripts/
│   └── seed_db.py          # criação manual das tabelas (uso local opcional)
├── src/vivia/
│   ├── config.py            # variáveis de ambiente (pydantic-settings)
│   ├── main.py               # ponto de entrada do terminal (modo teste)
│   ├── graph/                # LangGraph: state, nodes, router, builder
│   ├── memory/                # db, repository, summarizer
│   ├── personas/               # loader.py — carrega e formata o perfil
│   ├── voice/                    # stt.py, tts.py
│   └── web/                       # app.py (FastAPI) + static/ (frontend)
├── Dockerfile
├── railway.json
├── pyproject.toml
└── .env.example
```

## Rodando localmente

```powershell
# Instalar dependências
uv sync

# Copiar e preencher as variáveis de ambiente
cp .env.example .env
# editar .env com suas chaves reais

# Rodar a interface web
uv run uvicorn vivia.web.app:app --reload --port 8000
```

Abra `http://localhost:8000`. Em `APP_ENV=development` (padrão local), o terminal oferece a opção de escolher manualmente o momento do dia para acelerar testes — em produção isso é sempre automático, baseado no horário real (fuso do Brasil, fixo independente de onde o servidor rodar).

Também é possível rodar por terminal, sem interface web nem voz:

```powershell
uv run vivia
```

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI (LLM + transcrição) |
| `OPENAI_MODEL` | Modelo de conversação (`gpt-5.6-luna`) |
| `STT_MODEL` | Modelo de transcrição (`gpt-4o-transcribe`) |
| `ELEVENLABS_API_KEY` | Chave da ElevenLabs |
| `ELEVENLABS_VOICE_ID` | ID da voz usada pela Vivia |
| `ELEVENLABS_MODEL` | Modelo de TTS (`eleven_multilingual_v2`) |
| `APP_ENV` | `development` (testes manuais) ou `production` (automático) |
| `DATABASE_URL` | Caminho do banco SQLite (local: `vivia.db`; Railway: `/data/vivia.db`, dentro do volume persistente) |
| `PORT` | Porta do servidor (Railway injeta automaticamente) |


## Personas da POC

Duas personas fictícias para validação: **João** (65, hipertenso, ansiedade, aposentado, trabalha meio período) e **Viviane** (80, hipertensa, diabética, depressão, mora sozinha com apoio de diarista). Perfis completos em `data/personas/`.

**Importante:** essas duas continuam versionadas no Git de propósito — são dados de teste. Personas reais (previstas para o MVP com WhatsApp) nunca devem seguir esse padrão — o perfil delas deve morar no banco, nunca em arquivo commitado.

## O que está fora do escopo desta POC

- Integração real com WhatsApp (planejada para o MVP)
- Agendador de check-ins pró-ativos (a Vivia hoje só responde, não inicia contato sozinha — decisão consciente para esta fase)
- Múltiplas personas além de João e Viviane
- Busca semântica em histórico de longo prazo (pgvector) — hoje a memória usa uma janela de resumos dos últimos 7 dias
- Dashboard/Command Center para equipe de saúde
- Notificação real para o "gestor do programa" — hoje é só um campo registrado no banco

## Fases de desenvolvimento

| Fase | Entrega |
|---|---|
| 1 | Setup do projeto, ambiente `uv`, banco SQLite |
| 2 | LangGraph com os 7 momentos, personas, conversa por texto |
| 3 | Voz (STT/TTS) e interface web |
| 4 | Memória entre dias (resumo diário automático) |
| 5 | Deploy, testes finais, documentação |
| 6 | Prompts mais ricos, critério de desescalada no Protocolo de Dia Difícil, layout fixo no frontend |