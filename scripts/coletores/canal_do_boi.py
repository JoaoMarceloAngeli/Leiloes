"""Coletor: Canal do Boi e AgroCanal (SBA - Sistema Brasileiro do Agronegócio).

Fonte: página pública "Agenda de Leilões" -> https://sba1.com/leiloes
(canaldoboi.com.br redireciona para sba1.com). O robots.txt do site não tem
nenhuma restrição. 1 requisição por execução. Os links de lotes apontam para a Arrobaplay.

Uso:  python scripts/coletores/canal_do_boi.py
Saída: data/coletados/canal_do_boi.csv
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import (NAO_GADO, UFS, baixar, capitalizar, gravar_csv,  # noqa: E402
                    inferir_data, limpar, tipo_do_leilao)

FONTE = "canal_do_boi"
URL = "https://sba1.com/leiloes"

RACAS = ["Nelore", "Angus", "Brangus", "Braford", "Hereford", "Senepol", "Brahman", "Guzerá",
         "Tabapuã", "Gir", "Girolando", "Holandês", "Jersey", "Sindi", "Caracu", "Bonsmara",
         "Wagyu", "Ultrablack", "Montana", "Charolês", "Simental"]


def raca_por_titulo(titulo: str) -> str:
    return " / ".join(r for r in RACAS if re.search(rf"\b{r}\b", titulo, re.I))


def coletar() -> list[dict]:
    pagina = baixar(URL).decode("utf-8", errors="replace")
    leiloes = []
    for card in re.findall(r'<a class="leilao-agenda[^"]*"(.*?)</a>', pagina, re.S):
        link = re.search(r"href='([^']+)'", card)
        titulo = re.search(r"<h5>(.*?)</h5>", card, re.S)
        detalhes = re.search(r'class="detalhes">(.*?)</div>', card, re.S)
        if not (titulo and detalhes):
            continue
        titulo = capitalizar(limpar(titulo.group(1)))
        if NAO_GADO.search(titulo):
            continue

        # "21/11 - 13:00<br />SÃO JOSÉ DO RIO PRETO/SP"  ou  "VIRTUAL - ARAÇATUBA/SP"
        partes = [limpar(p) for p in re.split(r"<br\s*/?>", detalhes.group(1))]
        dm = re.match(r"(\d{2})/(\d{2})\s*-\s*(\d{2}:\d{2})", partes[0])
        if not dm or len(partes) < 2:
            continue
        lugar, _, cidade_uf = partes[1].rpartition(" - ")
        cm = re.match(r"(.+)/(\w{2})$", cidade_uf.strip())
        if not cm or cm.group(2).upper() not in UFS:
            continue
        virtual = "VIRTUAL" in partes[1].upper() or "virtual" in titulo.lower()

        canais = ", ".join(limpar(c) for c in re.findall(r'badge-leilao-canal">(.*?)<img', card, re.S))
        leiloeira = re.search(r"<img src='[^']*leiloeiras[^']*' title='([^']*)'", card)
        leiloes.append({
            "nome": titulo,
            "data": inferir_data(int(dm.group(1)), int(dm.group(2))),
            "hora": dm.group(3),
            "cidade": capitalizar(cm.group(1)),
            "uf": cm.group(2).upper(),
            "local": (capitalizar(lugar) if lugar and lugar.upper() != "VIRTUAL"
                      else f"Transmissão: {canais}"),
            "leiloeira": limpar(leiloeira.group(1)) if leiloeira else "",
            "tipo": tipo_do_leilao(titulo),
            "modalidade": "Virtual" if virtual else "Presencial + TV",
            "raca": raca_por_titulo(titulo),
            "link": link.group(1) if link else URL,
        })
    return leiloes


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
