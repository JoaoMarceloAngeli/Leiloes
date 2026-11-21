"""Coletor: Canal do Criador (Canal Rural / Lance Rural / Programa Leilões).

Fonte: API pública do WordPress do site, tipo de conteúdo "leilao".
  https://canaldocriador.com.br/wp-json/wp/v2/leilao
O robots.txt do site libera a coleta (Disallow vazio). Poucas requisições por execução.

Uso:  python scripts/coletores/canal_do_criador.py
Saída: data/coletados/canal_do_criador.csv
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import (AVISO_ESTUDIO, NAO_GADO, UFS, baixar_json, eh_estudio,  # noqa: E402
                    gravar_csv, limpar, tipo_do_leilao)

FONTE = "canal_do_criador"
API = "https://canaldocriador.com.br/wp-json/wp/v2/leilao"

# Itens da agenda que são programas de TV, não leilões
NAO_LEILAO_RACA = {"programa", "programa diário", "programa diario"}
NAO_LEILAO_TITULO = re.compile(r"^(lance na tv|programa\b)", re.I)


def baixar_tudo() -> list[dict]:
    itens, pagina = [], 1
    while True:
        dados, cab = baixar_json(f"{API}?per_page=100&page={pagina}&_fields=id,title,link,acf,meta")
        itens += dados
        if pagina >= int(cab.get("X-WP-TotalPages", "1")):
            return itens
        pagina += 1
        time.sleep(1)


def converter(item: dict) -> dict | None:
    acf, meta = item.get("acf") or {}, item.get("meta") or {}
    titulo = limpar(item["title"]["rendered"])
    raca = (acf.get("raca") or "").strip()

    if raca.lower() in NAO_LEILAO_RACA or NAO_LEILAO_TITULO.search(titulo):
        return None
    if NAO_GADO.search(f"{raca} {titulo}"):
        return None

    m = re.match(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})", meta.get("data_hora_de_abertura") or "")
    if not m:
        return None

    lm = re.match(r"(.+?)\s*\((\w{2})\)\s*$", (acf.get("local") or "").strip())   # "Boa vista (RR)"
    cidade, uf = (lm.group(1).strip(), lm.group(2).upper()) if lm else ("", "")
    if uf and uf not in UFS:   # leilão fora do Brasil (ex.: Santa Cruz (BO))
        return None

    estudio = eh_estudio(cidade, uf)   # Londrina / São Paulo = estúdios de transmissão
    virtual = bool(re.search(r"virtual|online", titulo, re.I)) or estudio
    programa = (acf.get("programa") or "").strip()
    return {
        "nome": titulo,
        "data": m.group(1),
        "hora": m.group(2),
        "cidade": cidade,
        "uf": uf,
        # Em leilão virtual, a cidade costuma ser a do estúdio de transmissão
        "local": AVISO_ESTUDIO if estudio else (f"Transmissão: {programa}" if programa else ""),
        "leiloeira": (acf.get("leiloeira") or "").strip(),
        "tipo": tipo_do_leilao(raca, titulo),
        "modalidade": "Virtual" if virtual else "Transmitido na TV",
        "raca": "" if raca.lower() in {"gado de corte", "gado geral", "diversos"} else raca,
        "link": item.get("link", ""),
    }


if __name__ == "__main__":
    gravar_csv(FONTE, [l for l in map(converter, baixar_tudo()) if l])
