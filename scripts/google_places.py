"""Acesso à Places API (New) do Google, usado por places_varredura.py e adicionar_recinto.py.

A chave do servidor fica no arquivo .env na raiz do projeto (fora do git):
    GOOGLE_PLACES_CHAVE=AIza...

Regras dos termos do Google Maps Platform que este projeto segue:
- só o place_id é guardado de forma permanente;
- nome e endereço vindos do Google só ficam em data/temp/ (revisão) e são apagados depois;
- os dados do Google só aparecem sobre o mapa do Google (site/app.js).
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
URL_BUSCA = "https://places.googleapis.com/v1/places:searchText"


def carregar_chave() -> str:
    chave = os.environ.get("GOOGLE_PLACES_CHAVE", "")
    env = RAIZ / ".env"
    if not chave and env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("GOOGLE_PLACES_CHAVE="):
                chave = linha.split("=", 1)[1].strip().strip('"')
    return chave


def buscar_texto(chave: str, texto: str, campos: list[str], centro=None, raio_m=30000,
                 token: str = "") -> dict:
    """Uma chamada de Text Search (New). Cada chamada é cobrada pelo campo mais caro pedido."""
    corpo = {"textQuery": texto, "languageCode": "pt-BR", "regionCode": "BR", "pageSize": 20}
    if centro:
        corpo["locationBias"] = {"circle": {"center": {"latitude": centro[0], "longitude": centro[1]},
                                            "radius": float(raio_m)}}
    if token:
        corpo["pageToken"] = token
    req = urllib.request.Request(
        URL_BUSCA, data=json.dumps(corpo).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": chave,
                 "X-Goog-FieldMask": ",".join(campos)})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"Places API respondeu {e.code}: {detalhe}") from None


def localizacao(chave: str, place_id: str) -> tuple[float, float] | None:
    """Place Details pedindo só a localização. Os termos deixam guardar lat/lng por até 30 dias."""
    req = urllib.request.Request(
        f"https://places.googleapis.com/v1/places/{place_id}",
        headers={"X-Goog-Api-Key": chave, "X-Goog-FieldMask": "location"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            loc = json.load(r).get("location")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Places API respondeu {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None
    return (loc["latitude"], loc["longitude"]) if loc else None
