"""Funções compartilhadas pelos coletores."""
import csv
import html
import json
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
UA = "MapaLeiloes/0.1 (coletor de agenda de leiloes de gado)"
CAMPOS = ["nome", "data", "hora", "cidade", "uf", "local", "leiloeira",
          "tipo", "modalidade", "raca", "link", "fonte"]
UFS = set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split())

# Leilões que não são de gado bovino
NAO_GADO = re.compile(
    r"s[eê]men|embri[oõaã]|cavalo|equin|quarto de milha|crioulo|mangalarga|appaloosa|"
    r"p[oô]nei|ovin|caprin|m[aá]quin|implemento|\bhorse|\bbarrel|\bla[cç]o\b", re.I)

# Cidades que, nessas fontes, são o estúdio de transmissão e não o local da fazenda
ESTUDIOS = {("londrina", "PR"), ("sao paulo", "SP")}
AVISO_ESTUDIO = "Estúdio de transmissão (local da fazenda não informado)"


def eh_estudio(cidade: str, uf: str) -> bool:
    import unicodedata
    c = unicodedata.normalize("NFKD", cidade).encode("ascii", "ignore").decode().lower().strip()
    return (c, uf.upper()) in ESTUDIOS

MINUSCULAS = {"de", "do", "da", "dos", "das", "e", "d"}


def baixar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def baixar_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r), r.headers


def limpar(texto: str) -> str:
    """Remove tags HTML, decodifica entidades e normaliza espaços."""
    t = html.unescape(re.sub(r"<[^>]+>", " ", texto or ""))
    return re.sub(r"\s+", " ", t.replace("​", "").replace(" ", " ")).strip()


def capitalizar(texto: str) -> str:
    """'SÃO JOSÉ DO RIO PRETO' -> 'São José do Rio Preto'."""
    palavras = texto.lower().split()
    return " ".join(p if (i and p in MINUSCULAS) else p.capitalize() for i, p in enumerate(palavras))


MESES = {m: i for i, m in enumerate(
    "jan fev mar abr mai jun jul ago set out nov dez".split(), start=1)}


def inferir_data(dia: int, mes: int, hoje: date | None = None) -> str:
    """Para agendas que mostram só dia/mês: escolhe o ano que deixa a data
    perto do futuro próximo (trata a virada de dezembro para janeiro)."""
    hoje = hoje or date.today()
    candidatos = []
    for ano in (hoje.year - 1, hoje.year, hoje.year + 1):
        try:
            candidatos.append(date(ano, mes, dia))
        except ValueError:
            pass
    return min(candidatos, key=lambda c: abs(c - hoje - timedelta(days=60))).isoformat()


def tipo_do_leilao(*textos: str) -> str:
    t = " ".join(textos).lower()
    if re.search(r"leite|leiteir|girolando|holand|jersey", t):
        return "Leite"
    if re.search(r"touro|reprodutor", t):
        return "Reprodutores"
    if re.search(r"matriz|matrizes|f[eê]mea|novilha", t):
        return "Matrizes"
    if re.search(r"bezerr|terneir|reposi|boi gordo|corte", t):
        return "Corte"
    if re.search(r"elite|gen[eé]tica|especial|sele[cç][aã]o|mega|\bpo\b", t):
        return "Elite"
    return "Geral"


def gravar_csv(fonte: str, leiloes: list[dict]) -> None:
    destino = RAIZ / "data" / "coletados" / f"{fonte}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for l in leiloes:
            w.writerow({c: l.get(c, "") for c in CAMPOS} | {"fonte": fonte})
    print(f"{fonte}: {len(leiloes)} leilões de gado gravados em {destino.relative_to(RAIZ)}")
