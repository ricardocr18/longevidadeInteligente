# Python 3.12 — versão estável, com imagem oficial garantida no Docker Hub.
# Ignoramos de propósito o .python-version local (3.14, herdado do seu
# Windows) porque o pyproject.toml já exige só requires-python = ">=3.12",
# e usar exatamente 3.12 aqui evita qualquer dependência de o ambiente de
# build conseguir baixar uma versão de Python mais nova.
FROM python:3.12-slim

# Compilador C como precaução — algumas dependências Python (ex: pydantic-core)
# podem precisar compilar código nativo se não houver wheel pré-compilada
# para essa combinação exata de plataforma/arquitetura. Mais barato instalar
# isso de propósito do que descobrir faltando no meio de outro build falhado.
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia o binário oficial do uv direto da imagem da Astral — mais rápido e
# confiável do que instalar via pip (que foi o que nos deu a versão antiga
# 0.4.30 no Nixpacks). Isso sempre traz a versão mais atual do uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copia primeiro só os arquivos de dependência, para aproveitar cache de
# camada do Docker: só reinstala tudo se pyproject.toml/uv.lock mudarem,
# não a cada alteração de código.
COPY pyproject.toml uv.lock ./

# Força Python 3.12 explicitamente, ignorando qualquer .python-version.
ENV UV_PYTHON=3.12

RUN uv sync --frozen --no-dev --no-install-project

# Agora copia o resto do código do projeto.
COPY . .

# Sincroniza de novo — instala o próprio pacote vivia por cima das
# dependências que já estavam em cache da camada anterior.
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Forma "shell" (sem colchetes) de propósito: permite expansão da variável
# $PORT em tempo de execução, já que o Railway injeta essa porta
# dinamicamente a cada deploy — a forma "exec" (com colchetes) não faria
# essa substituição.
CMD uv run uvicorn vivia.web.app:app --host 0.0.0.0 --port ${PORT:-8000}