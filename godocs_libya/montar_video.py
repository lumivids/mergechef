"""Monta o vídeo final a partir de uma pasta com clipes/imagens numerados e o áudio da narração.

Uso (Windows):
    python montar_video.py "C:\\Users\\ferra\\Downloads\\libia"

Regras:
- Cada cena é identificada pelo número no nome do arquivo (img 001, img_002, 003.mp4...).
- Se houver vídeo e imagem com o mesmo número, usa o vídeo.
- Cada cena dura SEGUNDOS_POR_CENA. Vídeos mais curtos são desacelerados e mais longos são cortados;
  imagens paradas ganham um zoom lento.
- A última cena se estende até o fim do áudio.
- O áudio é o arquivo .mp3/.wav/.m4a/.aac da pasta (se houver vários, são unidos em ordem alfabética).
Requer o ffmpeg instalado e no PATH.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SEGUNDOS_POR_CENA = 7.0
LARGURA, ALTURA, FPS = 1920, 1080, 30

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}

ENQUADRAR = (f"scale={LARGURA}:{ALTURA}:force_original_aspect_ratio=increase,"
             f"crop={LARGURA}:{ALTURA},setsar=1")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duracao(arquivo):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(arquivo)],
        check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


def numero_da_cena(arquivo):
    m = re.search(r"(\d+)", arquivo.stem)
    return int(m.group(1)) if m else None


def coletar(pasta):
    cenas, audios = {}, []
    for f in sorted(pasta.iterdir()):
        ext = f.suffix.lower()
        if ext in AUDIO_EXT:
            audios.append(f)
            continue
        if ext not in VIDEO_EXT | IMAGE_EXT:
            continue
        n = numero_da_cena(f)
        if n is None:
            continue
        atual = cenas.get(n)
        if atual is None or (ext in VIDEO_EXT and atual.suffix.lower() not in VIDEO_EXT):
            cenas[n] = f
    return cenas, audios


def clipe_de_video(origem, alvo, destino):
    fator = alvo / duracao(origem)
    filtro = f"setpts=PTS*{max(fator, 1.0):.5f},{ENQUADRAR},fps={FPS}"
    run(["ffmpeg", "-y", "-i", str(origem), "-an", "-vf", filtro, "-t", f"{alvo:.3f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(destino)])


def clipe_de_imagem(origem, alvo, destino):
    quadros = int(round(alvo * FPS))
    zoom = (f"scale={LARGURA * 2}:{ALTURA * 2}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA * 2}:{ALTURA * 2},"
            f"zoompan=z='1+0.08*on/{quadros}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={quadros}:s={LARGURA}x{ALTURA}:fps={FPS},setsar=1")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(origem), "-vf", zoom, "-frames:v", str(quadros),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(destino)])


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python montar_video.py "C:\\caminho\\da\\pasta"')
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg não encontrado. Instale (https://ffmpeg.org) e coloque no PATH.")

    pasta = Path(sys.argv[1])
    cenas, audios = coletar(pasta)
    if not cenas:
        sys.exit("Nenhuma imagem ou vídeo numerado encontrado na pasta.")
    if not audios:
        sys.exit("Nenhum arquivo de áudio encontrado na pasta.")

    numeros = sorted(cenas)
    faltando = sorted(set(range(numeros[0], numeros[-1] + 1)) - set(numeros))
    if faltando:
        print(f"Atenção: cenas faltando: {', '.join(f'{n:03d}' for n in faltando)}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        if len(audios) == 1:
            audio = audios[0]
        else:
            lista = tmp / "audios.txt"
            lista.write_text("".join(f"file '{a.resolve().as_posix()}'\n" for a in audios), encoding="utf-8")
            audio = tmp / "audio.wav"
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), str(audio)])
        total_audio = duracao(audio)

        clipes = []
        for i, n in enumerate(numeros):
            ultimo = i == len(numeros) - 1
            alvo = max(total_audio - SEGUNDOS_POR_CENA * i, 1.0) if ultimo else SEGUNDOS_POR_CENA
            origem = cenas[n]
            destino = tmp / f"cena_{n:03d}.mp4"
            print(f"[{i + 1}/{len(numeros)}] img {n:03d} <- {origem.name} ({alvo:.1f}s)")
            if origem.suffix.lower() in VIDEO_EXT:
                clipe_de_video(origem, alvo, destino)
            else:
                clipe_de_imagem(origem, alvo, destino)
            clipes.append(destino)

        lista = tmp / "clipes.txt"
        lista.write_text("".join(f"file '{c.as_posix()}'\n" for c in clipes), encoding="utf-8")
        saida = pasta / "video_final_libya.mp4"
        print("Juntando cenas e áudio...")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(audio),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-shortest", str(saida)])

    print(f"Pronto: {saida}")


if __name__ == "__main__":
    main()
