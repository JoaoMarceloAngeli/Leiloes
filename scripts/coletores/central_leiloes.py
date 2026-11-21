"""Coletor: Central Leilões (Araçatuba/SP).

Fonte: página pública de agenda -> https://www.centralleiloes.com.br/agenda-de-leiloes.php
O site não publica robots.txt (sem restrições). 1 requisição por execução.
Muitos leilões também aparecem no Canal do Boi, mas aqui vem o local exato
(ex.: "Fazenda Vale das Palmeiras | Cedral/SP"), por isso esta fonte tem prioridade.

Uso:  python scripts/coletores/central_leiloes.py
Saída: data/coletados/central_leiloes.csv
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import (MESES, NAO_GADO, UFS, baixar, capitalizar, gravar_csv,  # noqa: E402
                    inferir_data, limpar, tipo_do_leilao)

FONTE = "central_leiloes"
BASE = "https://www.centralleiloes.com.br"
URL = f"{BASE}/agenda-de-leiloes.php"

# "FAZENDA VALE DAS PALMEIRAS | CEDRAL/SP"  ou  "PALÁCIO DO TIRACHAPÉU - SALVADOR | BA"
LOCAL_RE = re.compile(r"^(?:(.*?)\s*[|-]\s*)?([^|/-]+?)\s*[/|]\s*([A-Z]{2})$")


def coletar() -> list[dict]:
    pagina = baixar(URL).decode("utf-8", errors="replace")
    leiloes = []
    for bloco in pagina.split('class="thumb-wrapper')[1:]:
        data = re.search(r'class="post-date">\s*(\d+)\s*<span>(\w+)</span>', bloco)
        titulo = re.search(r'class="entry-title"><a href="([^"]+)"[^>]*>(.*?)</a>', bloco, re.S)
        if not (data and titulo):
            continue
        nome = capitalizar(limpar(titulo.group(2)))
        if NAO_GADO.search(nome):
            continue
        hora = re.search(r"fa-clock-o\"></i>\s*(\d{1,2}:\d{2})", bloco)
        canal = re.search(r"fa-play-circle-o\"></i>(.*?)</li>", bloco, re.S)
        local = re.search(r"fa-map-marker\"></i>(.*?)</li>", bloco, re.S)
        local = limpar(local.group(1)) if local else ""
        categorias = ", ".join(limpar(c) for c in re.findall(r"id_categoria=\d+\">(.*?)</a>", bloco))

        lm = LOCAL_RE.match(local)
        if not lm or lm.group(3) not in UFS:
            # "VIRTUAL" ou "ESPAÇO GOURMET DO CANAL DO BOI": sem cidade; esses já vêm do Canal do Boi
            continue
        mes = MESES.get(data.group(2).lower()[:3])
        if not mes:
            continue

        racas = sorted(set(re.findall(r"\b(Nelore|Brangus|Angus|Senepol|Gir|Girolando|Guzerá|"
                                      r"Tabapuã|Brahman|Braford|Sindi)\b", categorias, re.I)))
        leiloes.append({
            "nome": nome,
            "data": inferir_data(int(data.group(1)), mes),
            "hora": hora.group(1) if hora else "",
            "cidade": capitalizar(lm.group(2)),
            "uf": lm.group(3),
            "local": capitalizar(lm.group(1) or ""),
            "leiloeira": "Central Leilões",
            "tipo": tipo_do_leilao(categorias, nome),
            "modalidade": ("Virtual" if "virtual" in nome.lower()
                           else "Presencial + TV" if canal and limpar(canal.group(1)) else "Presencial"),
            "raca": " / ".join(r.capitalize() for r in racas),
            "link": f"{BASE}/{titulo.group(1)}",
        })
    return leiloes


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
