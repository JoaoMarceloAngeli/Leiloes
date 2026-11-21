"""MODELO de coletor: copie este arquivo para cada fonte (ex.: coletor_leiloeira_x.py).

Cada coletor lê a agenda pública de UMA fonte e grava data/coletados/<fonte>.csv
com as mesmas colunas de data/leiloes.csv. Depois rode scripts/gerar_dados.py.

Antes de coletar um site, confira os termos de uso e o robots.txt dele.
Se puder, peça autorização à leiloeira: muitas gostam da divulgação.

Dependências:  pip install requests beautifulsoup4
"""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CAMPOS = ["nome", "data", "hora", "cidade", "uf", "local", "leiloeira",
          "tipo", "modalidade", "raca", "link", "fonte"]

FONTE = "modelo"                      # nome curto da fonte, vira o nome do CSV
URL_AGENDA = "https://exemplo.com.br/agenda"  # página com a agenda de leilões


def coletar() -> list[dict]:
    """Baixa a página e devolve uma lista de dicionários com as colunas de CAMPOS.

    Exemplo (adapte os seletores CSS ao HTML real da fonte):

        import requests
        from bs4 import BeautifulSoup
        html = requests.get(URL_AGENDA, timeout=30,
                            headers={"User-Agent": "MapaLeiloes/1.0"}).text
        sopa = BeautifulSoup(html, "html.parser")
        for card in sopa.select(".leilao"):
            yield {
                "nome": card.select_one(".titulo").get_text(strip=True),
                "data": "2026-12-01",          # sempre no formato AAAA-MM-DD
                "hora": "20:00",
                "cidade": "Uberaba", "uf": "MG",
                "link": card.select_one("a")["href"],
                "fonte": FONTE,
            }
    """
    return []


def main():
    leiloes = list(coletar())
    destino = RAIZ / "data" / "coletados" / f"{FONTE}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for l in leiloes:
            w.writerow({c: l.get(c, "") for c in CAMPOS})
    print(f"{len(leiloes)} leilões de '{FONTE}' gravados em {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
