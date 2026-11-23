"""Adiciona um recinto de leilão (local fixo onde há leilões frequentes) a partir de um link do Google Maps.

Uso:
  python scripts/adicionar_recinto.py "https://maps.app.goo.gl/yXKs8EtZEYUYeAgj6"
  python scripts/adicionar_recinto.py "<link>" --dias "Toda sexta, 20h" --telefone "(62) 9..." --obs "Gado de corte"

O link curto (maps.app.goo.gl) é aberto só para ler o endereço de destino; nenhuma página
do Google é baixada. Do destino saem o nome e as coordenadas; a cidade é o município mais
próximo (base IBGE em data/municipios.csv). Grava em data/recintos.csv.
Depois rode  python scripts/gerar_dados.py  para atualizar o mapa.
"""
import argparse
import csv
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
ARQUIVO = DADOS / "recintos.csv"
CAMPOS = ["nome", "cidade", "uf", "lat", "lng", "dias", "telefone", "site", "maps", "obs", "fonte"]


class SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def destino(link: str) -> str:
    """Endereço completo do link (segue só os redirecionamentos, sem baixar páginas)."""
    abridor = urllib.request.build_opener(SemRedirecionar)
    for _ in range(5):
        if "/maps/place/" in link or "/maps/@" in link:
            return link
        try:
            abridor.open(urllib.request.Request(link, method="HEAD"), timeout=20)
            return link
        except urllib.error.HTTPError as e:
            novo = e.headers.get("Location")
            if not novo or e.code not in (301, 302, 303, 307, 308):
                raise
            link = urllib.parse.urljoin(link, novo)
    return link


def ler_link(link: str) -> tuple[str, float, float]:
    url = urllib.parse.unquote_plus(destino(link))
    nome = re.search(r"/maps/place/([^/@]+)", url)
    coord = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url) or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if not (nome and coord):
        sys.exit(f"Não consegui ler nome e coordenadas deste link:\n  {url}")
    return nome.group(1).strip(), float(coord.group(1)), float(coord.group(2))


def municipio_mais_proximo(lat: float, lng: float) -> tuple[str, str]:
    with open(DADOS / "estados.csv", encoding="utf-8-sig") as f:
        uf_por_codigo = {r["codigo_uf"]: r["uf"] for r in csv.DictReader(f)}
    melhor, menor = None, float("inf")
    with open(DADOS / "municipios.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            la, ln = float(r["latitude"]), float(r["longitude"])
            d = (la - lat) ** 2 + ((ln - lng) * math.cos(math.radians(lat))) ** 2
            if d < menor:
                melhor, menor = (r["nome"], uf_por_codigo[r["codigo_uf"]]), d
    return melhor


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("link")
    p.add_argument("--nome", help="corrige o nome que vem do Google Maps")
    p.add_argument("--dias", default="", help='dias/horários dos leilões, ex.: "Toda sexta, 20h"')
    p.add_argument("--telefone", default="")
    p.add_argument("--site", default="", help="site ou Instagram")
    p.add_argument("--obs", default="")
    a = p.parse_args()

    nome, lat, lng = ler_link(a.link)
    nome = a.nome or nome
    cidade, uf = municipio_mais_proximo(lat, lng)

    linhas = []
    if ARQUIVO.exists():
        with open(ARQUIVO, encoding="utf-8-sig") as f:
            linhas = list(csv.DictReader(f))
    if any(l["nome"].lower() == nome.lower() and l["cidade"] == cidade and l["uf"] == uf for l in linhas):
        print(f"Já cadastrado: {nome} ({cidade}/{uf})")
        return 0

    linhas.append({"nome": nome, "cidade": cidade, "uf": uf, "lat": f"{lat:.6f}", "lng": f"{lng:.6f}",
                   "dias": a.dias, "telefone": a.telefone, "site": a.site, "maps": a.link,
                   "obs": a.obs, "fonte": "google_maps (link enviado)"})
    with open(ARQUIVO, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)
    print(f"Recinto adicionado: {nome} - {cidade}/{uf} ({lat:.5f}, {lng:.5f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
