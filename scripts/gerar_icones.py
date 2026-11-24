"""Gera os ícones do app (site/icone-*.png) sem bibliotecas externas: pino branco em fundo verde claro.

Uso:  python scripts/gerar_icones.py
"""
import math
import struct
import zlib
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
VERDE = (140, 197, 132)
VERDE_ESCURO = (61, 122, 55)
BRANCO = (255, 255, 255)
MARROM = (169, 120, 75)


def png(caminho: Path, tam: int, pixels) -> None:
    linhas = b"".join(b"\x00" + bytes(c for px in pixels[y] for c in px) for y in range(tam))
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))
    caminho.write_bytes(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", tam, tam, 8, 6, 0, 0, 0))
                        + bloco(b"IDAT", zlib.compress(linhas, 9)) + bloco(b"IEND", b""))


def cor_em(x: float, y: float, arredondado: bool, escala: float):
    """x, y em 0..1. Devolve RGBA do ponto."""
    # fundo: quadrado de cantos arredondados (ou cheio, para o ícone "maskable" e o do iPhone)
    if arredondado:
        r = 0.22
        dx, dy = max(r - x, 0, x - (1 - r)), max(r - y, 0, y - (1 - r))
        if dx * dx + dy * dy > r * r:
            return (0, 0, 0, 0)
    # pino: círculo + ponta, centrado
    cx, cy, raio = 0.5, 0.5 - 0.10 * escala, 0.24 * escala
    ponta = cy + 0.40 * escala
    px, py = (x - cx), (y - cy)
    dentro_circulo = px * px + py * py <= raio * raio
    dentro_ponta = False
    if cy <= y <= ponta:
        meia = raio * (ponta - y) / (ponta - cy) * 1.02
        dentro_ponta = abs(px) <= meia and not (y < cy + raio * 0.6 and not dentro_circulo and abs(px) > raio * 0.9)
    if dentro_circulo or dentro_ponta:
        if px * px + py * py <= (raio * 0.45) ** 2:
            return MARROM + (255,)
        return BRANCO + (255,)
    # sombra suave do chão
    if abs(y - (ponta + 0.03 * escala)) < 0.018 * escala and abs(x - 0.5) < 0.16 * escala:
        return VERDE_ESCURO + (255,)
    return VERDE + (255,)


def icone(tam: int, arredondado: bool, escala: float) -> list:
    amostras = 4   # suavização das bordas
    pixels = []
    for j in range(tam):
        linha = []
        for i in range(tam):
            soma = [0, 0, 0, 0]
            for a in range(amostras):
                for b in range(amostras):
                    c = cor_em((i + (a + .5) / amostras) / tam, (j + (b + .5) / amostras) / tam, arredondado, escala)
                    for k in range(4):
                        soma[k] += c[k]
            n = amostras * amostras
            alfa = soma[3] / n
            cor = [round(soma[k] / n * (255 / alfa)) if alfa else 0 for k in range(3)] if alfa else [0, 0, 0]
            linha.append(tuple(min(255, v) for v in cor) + (round(alfa),))
        pixels.append(linha)
    return pixels


if __name__ == "__main__":
    for nome, tam, arred, escala in [("icone-192.png", 192, True, 1.0), ("icone-512.png", 512, True, 1.0),
                                     ("icone-512-maskable.png", 512, False, 0.75), ("icone-180.png", 180, False, 0.9)]:
        png(SITE / nome, tam, icone(tam, arred, escala))
        print("gerado", nome)
