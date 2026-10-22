# Vídeos de avatar (HeyGen + ElevenLabs) — POC

Esta pasta guarda os vídeos estáticos usados como abertura da Vivia em 4 dos
7 momentos do dia (acordar, café da manhã, meio da tarde, antes de dormir),
para as duas personas fictícias de teste (João e Viviane). Decisão de
arquitetura completa em `claude/avatar_heygen_poc.md` no projeto Claude.

Os arquivos `.mp4` **não ficam neste repositório automaticamente** — são
criados manualmente no app do HeyGen (a partir de uma frase fixa + a voz
gerada no ElevenLabs) e precisam ser adicionados aqui por fora, um a um.
O código (`src/vivia/avatar/videos.py`) só aponta para os nomes de arquivo
abaixo; se um arquivo não existir aqui, a Vivia simplesmente cai de volta
no comportamento normal (texto + áudio), sem quebrar nada.

## Estrutura esperada