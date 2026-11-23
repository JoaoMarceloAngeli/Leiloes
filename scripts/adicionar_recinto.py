"""Adiciona um recinto de leilão (local fixo onde há leilões frequentes) a partir de um link do Google Maps.

Uso:
  python scripts/adicionar_recinto.py "https://maps.app.goo.gl/yXKs8EtZEYUYeAgj6"
  python scripts/adicionar_recinto.py "<link>" --dias "Toda sexta, 20h" --telefone "(62) 9..." --obs "Gado de corte"

O link curto (maps.app.goo.gl) é aberto só para ler o endereço de destino; nenhuma página
do Google é baixada. Do destino saem o nome e as coordenadas; a cidade é o município mais
próximo (base IBGE em data/municipios.csv). Grava em data/recintos.csv.

Com a chave GOOGLE_PLACES_CHAVE no .env, o script troca nome e coordenadas pelo place_id
(única informação do Google que os termos deixam guardar) e o mapa busca o resto ao abrir.
Sem chave, guarda as coordenadas provisoriamente. Para converter os que ficaram assim:
  python scripts/adicionar_recinto.py --converter

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_places import buscar_texto, carregar_chave  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
ARQUIVO = DADOS / "recintos.csv"
CAMPOS = ["place_id", "nome", "cidade", "uf", "lat", "lng", "dias", "telefone", "site", "maps", "obs", "fonte", "coord_data"]


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


def achar_place_id(chave: str, nome: str, lat: float, lng: float) -> str:
    """Busca o local pelo nome perto das coordenadas, pedindo só o id (campo mais barato)."""
    resp = buscar_texto(chave, nome, ["places.id"], centro=(lat, lng), raio_m=500)
    lugares = resp.get("places", [])
    return lugares[0]["id"] if lugares else ""


def ler_recintos() -> list[dict]:
    if not ARQUIVO.exists():
        return []
    with open(ARQUIVO, encoding="utf-8-sig") as f:
        return [{c: r.get(c, "") or "" for c in CAMPOS} for r in csv.DictReader(f)]


def gravar(linhas: list[dict]) -> None:
    with open(ARQUIVO, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)


def para_place_id(linha: dict, chave: str) -> bool:
    """Troca nome/coordenadas vindos do Google pelo place_id. Devolve True se converteu."""
    pid = achar_place_id(chave, linha["nome"], float(linha["lat"]), float(linha["lng"]))
    if not pid:
        return False
    linha.update(place_id=pid, nome="", lat="", lng="",
                 maps=f"https://www.google.com/maps/place/?q=place_id:{pid}")
    return True


def converter() -> int:
    chave = carregar_chave()
    if not chave:
        sys.exit("Falta GOOGLE_PLACES_CHAVE no arquivo .env.")
    linhas = ler_recintos()
    for l in linhas:
        if l["fonte"].startswith("google_maps") and not l["place_id"]:
            antes = l["nome"]
            print(("Convertido: " if para_place_id(l, chave) else "Não achei no Google: ") + antes)
    gravar(linhas)
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:] == ["--converter"]:
        return converter()
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

    linhas = ler_recintos()
    if any(l["nome"].lower() == nome.lower() and l["uf"] == uf for l in linhas):
        print(f"Já cadastrado: {nome} ({cidade}/{uf})")
        return 0
    nova = {"place_id": "", "nome": nome, "cidade": cidade, "uf": uf, "lat": f"{lat:.6f}", "lng": f"{lng:.6f}",
            "dias": a.dias, "telefone": a.telefone, "site": a.site, "maps": a.link,
            "obs": a.obs, "fonte": "google_maps (link enviado)"}
    chave = carregar_chave()
    if chave and para_place_id(nova, chave):
        if any(l["place_id"] == nova["place_id"] for l in linhas):
            print(f"Já cadastrado: {nome} ({cidade}/{uf})")
            return 0
        print(f"Recinto adicionado pelo place_id: {nome} - {cidade}/{uf}")
    else:
        print(f"Recinto adicionado (coordenadas provisórias, sem chave): {nome} - {cidade}/{uf}")
    linhas.append(nova)
    gravar(linhas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
