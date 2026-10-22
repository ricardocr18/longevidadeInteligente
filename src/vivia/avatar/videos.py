"""
Vídeos estáticos de avatar (HeyGen + ElevenLabs) — POC.

Em 4 dos 7 momentos do dia (acordar, cafe_manha, meio_tarde, antes_dormir),
a abertura da conversa pode ser entregue como um vídeo pré-gravado do avatar
da Vivia (gerado manualmente no HeyGen, com voz do ElevenLabs) em vez de
texto + áudio sintetizado. Os outros 3 momentos (meio_manha, almoco, jantar)
NUNCA têm vídeo — seguem exatamente como hoje.

Decisão de arquitetura (registrada em claude/avatar_heygen_poc.md no projeto):
- O vídeo substitui SÓ a primeira mensagem do momento (a abertura). Depois
  que a pessoa responde, a conversa volta a ser texto/áudio normal.
- Os arquivos .mp4 NÃO fazem parte deste commit — são grandes, criados
  manualmente fora do código (app do HeyGen) e precisam ser adicionados por
  fora em data/avatares/<persona>/. Ver o README.md daquela pasta.
- É uma POC: a lista abaixo é fixa, feita só para as personas fictícias de
  teste (joao/viviane). Um user_id real (WhatsApp/MVP) nunca bate em nenhuma
  entrada deste mapa, então a ausência de vídeo é sempre o comportamento
  padrão — não precisa de nenhuma flag extra pra "desligar" isso em produção.
"""
from dataclasses import dataclass
from pathlib import Path

AVATARES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "avatares"


@dataclass(frozen=True)
class AvatarVideo:
    # Caminho relativo a data/avatares/ (o mesmo nome de arquivo que o
    # Ricardo já usou ao exportar do HeyGen).
    filename: str
    # Frase exata falada no vídeo — é isso que vai pro histórico/resumo
    # diário no lugar do texto que o LLM geraria, para o que a Vivia "disse"
    # bater com o que a pessoa de fato viu/ouviu no vídeo.
    text: str


# (user_id, moment) -> vídeo. Só estas 8 combinações existem; qualquer outro
# par (inclusive qualquer user_id que não seja "joao"/"viviane") não tem
# vídeo e segue o fluxo normal de texto + TTS.
AVATAR_VIDEOS: dict[tuple[str, str], AvatarVideo] = {
    ("joao", "acordar"): AvatarVideo(
        "joao/01_joao_acordar.mp4",
        "Bom dia, Sr João! Que bom falar com você de novo. Como foi a noite?",
    ),
    ("joao", "cafe_manha"): AvatarVideo(
        "joao/02_joao_cafe.mp4",
        "E o café da manhã, Sr João, já foi? O que teve hoje?",
    ),
    ("joao", "meio_tarde"): AvatarVideo(
        "joao/05_joao_tarde.mp4",
        "Boa tarde, Sr João! O que tem em mente para ocupar o seu tempo agora?",
    ),
    ("joao", "antes_dormir"): AvatarVideo(
        "joao/07_joao_noite.mp4",
        "Boa noite, Sr João. Durma bem.",
    ),
    ("viviane", "acordar"): AvatarVideo(
        "viviane/03_viviane_acordar.mp4",
        "Bom dia, Sra Viviane. Como você está hoje?",
    ),
    ("viviane", "cafe_manha"): AvatarVideo(
        "viviane/04_viviane_cafe.mp4",
        "Sra Viviane, e o café da manhã, já tomou? Me conta o que teve.",
    ),
    ("viviane", "meio_tarde"): AvatarVideo(
        "viviane/06_viviane_tarde.mp4",
        "Boa tarde, Sra Viviane. Como está sendo a sua tarde?",
    ),
    ("viviane", "antes_dormir"): AvatarVideo(
        "viviane/08_viviane_noite.mp4",
        "Boa noite, Sra Viviane. Durma bem.",
    ),
}


def get_avatar_video(user_id: str, moment: str) -> AvatarVideo | None:
    """
    Retorna o vídeo de abertura fixo para (user_id, moment), se existir —
    independente de o arquivo .mp4 já estar presente em disco ou não (quem
    chama decide o que fazer se o mapa aponta pra um arquivo ausente; ver
    web/app.py).
    """
    return AVATAR_VIDEOS.get((user_id, moment))


def avatar_video_exists_on_disk(video: AvatarVideo) -> bool:
    """Confere se o .mp4 já foi colocado em data/avatares/ (ver README lá)."""
    return (AVATARES_DIR / video.filename).is_file()