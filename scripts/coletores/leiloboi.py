"""Coletor: Leiloboi Leilões Rurais (Campo Grande/MS).

Fonte: página pública de agenda -> https://leiloboi.com/leiloes
O site não publica robots.txt (sem restrições). 1 requisição por execução.
Descoberta pelo diretório de casas de leilão do Compre Rural.

Uso:  python scripts/coletores/leiloboi.py
Saída: data/coletados/leiloboi.csv
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import (MESES, NAO_GADO, UFS, baixar, capitalizar, gravar_csv,  # noqa: E402
                    inferir_data, limpar, tipo_do_leilao)

FONTE = "leiloboi"
BASE = "https://leiloboi.com"
URL = f"{BASE}/leiloes"


def coletar() -> list[dict]:
    pagina = baixar(URL).decode("utf-8", errors="replace")
    leiloes = []
    for href, card in re.findall(r'<a href="(/leiloes/[^"]+)">\s*<table class="leilao(.*?)</table>',
                                 pagina, re.S):
        data = re.search(r'class="data-leilao">\s*<strong>(\d+)</strong>\s*(\w+)', card)
        titulo = re.search(r"<h5>(.*?)</h5>", card, re.S)
        local = re.search(r'class="local[^"]*">(.*?)</small>', card, re.S)
        if not (data and titulo and local):
            continue
        titulo = capitalizar(limpar(titulo.group(1)))
        if NAO_GADO.search(titulo):
            continue
        hora = re.search(r"fa-clock[^>]*></i>\s*(\d{1,2}:\d{2})", card)
        categoria = re.search(r'class="badge bg-danger">(.*?)</span>', card)
        categoria = limpar(categoria.group(1)) if categoria else ""
        # "FAZENDA NOVO HORIZONTE - CURVA DO LEQUE - CORUMBÁ/MS" ("CAMPO GRADE" é erro do site)
        local = limpar(local.group(1)).upper().replace("CAMPO GRADE", "CAMPO GRANDE")

        # A cidade é o último trecho "CIDADE/UF". Sem isso, usa a sede (Campo Grande/MS).
        # Textos como "SEDE LEILOBOI EM CAMPO GRANDE" são resolvidos no gerar_dados.py.
        cm = re.search(r"([^-/]+?)\s*/\s*([A-Z]{2})\b", local)
        cidade, uf = (cm.group(1).strip(), cm.group(2)) if cm and cm.group(2) in UFS else ("Campo Grande", "MS")
        virtual = "VIRTUAL" in local.upper() or "virtual" in titulo.lower() or "SEDE LEILOBOI" in local.upper()

        mes = MESES.get(data.group(2).lower()[:3])
        if not mes:
            continue
        leiloes.append({
            "nome": titulo,
            "data": inferir_data(int(data.group(1)), mes),
            "hora": hora.group(1) if hora else "",
            "cidade": capitalizar(cidade),
            "uf": uf,
            "local": capitalizar(local),
            "leiloeira": "Leiloboi",
            "tipo": tipo_do_leilao(categoria, titulo),
            "modalidade": "Virtual" if virtual else "Presencial",
            "raca": "",
            "link": BASE + href,
        })
    return leiloes


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
