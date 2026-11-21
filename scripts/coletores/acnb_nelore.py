"""Coletor: ACNB (Associação dos Criadores de Nelore do Brasil): agenda de leilões oficializados.

Fonte: página pública -> https://www.nelore.org.br/agenda-de-leiloes/
Traz local e cidade reais (ex.: "Sítio Arara Azul, Domingos Martins/ES").

Só a página 1 (os 10 próximos leilões) é coletada: as páginas seguintes vêm
de /wp-admin/admin-ajax.php, que o robots.txt do site bloqueia. Como o coletor
roda com frequência, os leilões mais distantes entram conforme se aproximam.
O site é lento (cerca de 20 s por página).

Uso:  python scripts/coletores/acnb_nelore.py
Saída: data/coletados/acnb_nelore.csv
"""
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import UA, UFS, NAO_GADO, capitalizar, gravar_csv, limpar, tipo_do_leilao  # noqa: E402

FONTE = "acnb_nelore"
URL = "https://www.nelore.org.br/agenda-de-leiloes/"

ESTADOS = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA", "CEARA": "CE",
    "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA",
    "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG", "PARA": "PA",
    "PARAIBA": "PB", "PARANA": "PR", "PERNAMBUCO": "PE", "PERNANBUCO": "PE", "PIAUI": "PI",
    "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS",
    "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP",
    "SERGIPE": "SE", "TOCANTINS": "TO",
}


def sem_acento(t: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper().strip()


def baixar_pagina() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


def ler_itens(pagina: str) -> list[dict]:
    itens = []
    blocos = re.split(r'<div class="griddy lista"', pagina)[1:]
    for b in blocos:
        def campo(rotulo):
            m = re.search(rf"<label>{rotulo}:\s*<span>(.*?)</span>", b, re.S)
            return limpar(m.group(1)) if m else ""

        idm = re.search(r"openLeilaoModal\((\d+)\)", b)
        titulo = re.search(r'<h3 class="cursor-pointer"[^>]*>(.*?)</h3>', b, re.S)
        if not (idm and titulo):
            continue
        itens.append({
            "id": idm.group(1), "nome": limpar(titulo.group(1)), "data": campo("Data"),
            "hora": campo("Hor&aacute;rio") or campo("Horário"), "local": campo("Local"),
            "cidade": campo("Cidade"), "promotor": campo(r"Promotor\(es\)"),
        })
    return itens


def converter(i: dict) -> dict | None:
    dm = re.match(r"(\d{2})/(\d{2})/(\d{4})", i["data"])          # "28/11/2026 à 28/11/2026"
    cm = re.match(r"(.+?)\s*-\s*(.+)$", i["cidade"])              # "UNAÍ - MINAS GERAIS"
    if not (dm and cm) or NAO_GADO.search(i["nome"]):
        return None
    uf = ESTADOS.get(sem_acento(cm.group(2)))
    if uf not in UFS:
        return None
    virtual = "VIRTUAL" in i["local"].upper() or "virtual" in i["nome"].lower()
    return {
        "nome": capitalizar(i["nome"]),
        "data": f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}",
        "hora": i["hora"][:5],
        "cidade": capitalizar(cm.group(1)),
        "uf": uf,
        "local": "" if virtual else capitalizar(i["local"]),
        "leiloeira": capitalizar(i["promotor"]),   # promotor (criador); a ACNB não informa a leiloeira
        "tipo": tipo_do_leilao(i["nome"]),
        "modalidade": "Virtual" if virtual else "Presencial",
        "raca": "Nelore",
        "link": URL,
    }


def coletar() -> list[dict]:
    return [l for l in map(converter, ler_itens(baixar_pagina())) if l]


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
