"""Coletor: Programa Leilões (maior leiloeira rural do país).

Fonte: página pública de agenda -> https://programaleiloes.com/agenda
(cerca de 30 dias à frente). O robots.txt só bloqueia áreas internas
(/emails/, /files/, /modules/, /appportal/). 1 requisição por execução.

Uso:  python scripts/coletores/programa_leiloes.py
Saída: data/coletados/programa_leiloes.csv
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import (AVISO_ESTUDIO, MESES, NAO_GADO, UFS, baixar, eh_estudio,  # noqa: E402
                    gravar_csv, inferir_data, limpar, tipo_do_leilao)

FONTE = "programa_leiloes"
BASE = "https://programaleiloes.com"
URL = f"{BASE}/agenda"

# Nome do arquivo do logo do canal -> nome do canal
CANAIS = {
    "canal-do-criador": "Canal do Criador", "canal-rural": "Canal Rural",
    "lance-rural": "Lance Rural", "terra-viva": "Terraviva", "agro": "AgroCanal",
    "remate-web": "Remate Web", "retransmissao-remate-web": "Remate Web",
    "remate-web-plus": "Remate Web Plus", "transmissao-via-internet": "Internet",
    "agreste-leiloes": "Agreste Leilões",
}


def coletar() -> list[dict]:
    pagina = baixar(URL).decode("utf-8", errors="replace")
    area = pagina[pagina.find('class="leiloes-area"'):]
    leiloes = []
    for href, card in re.findall(r'<a href="(/agenda/leilao/[^"]+)"[^>]*>(.*?)</a>', area, re.S):
        def campo(classe):
            m = re.search(rf'class="{classe}">(.*?)</span>', card, re.S)
            return limpar(m.group(1)) if m else ""

        titulo = campo("titulo").rstrip(";")
        categoria = campo("categoria")
        if NAO_GADO.search(f"{categoria} {titulo}"):
            continue

        dia = re.search(r'class="dia">\s*(\d+)', card)
        mes = MESES.get(campo("mes").lower()[:3])
        hora = campo("hora-tempo")
        cm = re.match(r"(.+?)\s*-\s*([A-Z]{2})$", campo("cidade"))
        if not (dia and mes and cm) or cm.group(2) not in UFS:
            continue

        canal = re.search(r'/([a-z0-9-]+)\.png" alt="Transmiss', card)
        canal = CANAIS.get(canal.group(1), "") if canal else ""
        estudio = eh_estudio(cm.group(1), cm.group(2))   # Londrina = sede/estúdio da leiloeira
        virtual = "virtual" in titulo.lower() or estudio
        raca = "" if categoria.upper() in {"OUTROS", "GADO DE CORTE"} else categoria

        leiloes.append({
            "nome": titulo,
            "data": inferir_data(int(dia.group(1)), mes),
            "hora": hora,
            "cidade": cm.group(1).strip(),
            "uf": cm.group(2),
            "local": campo("local") or (AVISO_ESTUDIO if estudio
                                        else f"Transmissão: {canal}" if canal else ""),
            "leiloeira": "Programa Leilões",
            "tipo": tipo_do_leilao(categoria, titulo),
            "modalidade": "Virtual" if virtual else "Transmitido na TV",
            "raca": raca,
            "link": BASE + href,
        })
    return leiloes


if __name__ == "__main__":
    gravar_csv(FONTE, coletar())
