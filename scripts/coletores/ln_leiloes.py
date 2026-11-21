"""Coletor: LN Leilões Rurais (Aquidauana/MS).

Fonte: página pública de leilões -> https://www.lnleiloes.com.br/leiloes
robots.txt: "Disallow:" vazio (sem restrições). 1 requisição por execução.
Faz leilão virtual semanal de gado de corte. Não informa local da fazenda:
usa a sede (Aquidauana/MS) e marca como virtual.

Uso:  python scripts/coletores/ln_leiloes.py
Saída: data/coletados/ln_leiloes.csv
"""
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import MESES, NAO_GADO, baixar, capitalizar, gravar_csv, limpar, tipo_do_leilao  # noqa: E402

FONTE = "ln_leiloes"
BASE = "https://www.lnleiloes.com.br"
URL = f"{BASE}/leiloes"


def coletar() -> list[dict]:
    pagina = baixar(URL).decode("utf-8", errors="replace")
    leiloes = []
    for href, card in re.findall(r'<a href="(/leilao-detalhes/\d+)"[^>]*>(.*?)</a>', pagina, re.S):
        # "25 NOV. 2026 · 16:00"
        dm = re.search(r"(\d{1,2})\s+([A-Z]{3})\.?\s+(\d{4})\s*(?:<!--.*?-->)?\s*·\s*(\d{1,2}:\d{2})", card, re.S)
        titulo = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not (dm and titulo):
            continue
        nome = capitalizar(limpar(titulo.group(1)))
        mes = MESES.get(dm.group(2).lower())
        if not mes or NAO_GADO.search(nome):
            continue
        leiloes.append({
            "nome": nome,
            "data": date(int(dm.group(3)), mes, int(dm.group(1))).isoformat(),
            "hora": dm.group(4),
            "cidade": "Aquidauana",
            "uf": "MS",
            "local": "Sede LN Leilões (leilão virtual)",
            "leiloeira": "LN Leilões",
            "tipo": tipo_do_leilao(nome),
            "modalidade": "Virtual" if "virtual" in nome.lower() else "Presencial",
            "raca": "",
            "link": BASE + href,
        })
    return leiloes


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
