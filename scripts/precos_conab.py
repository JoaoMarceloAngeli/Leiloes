"""Preço do boi gordo por estado: dados abertos da Conab (preço recebido pelo produtor, semanal).

Fonte: https://portaldeinformacoes.conab.gov.br/downloads/arquivos/PrecosSemanalUF.txt
(arquivo de dados abertos, ~17 MB, separado por ";", em latin-1). Só o boi gordo é aproveitado:
a Conab não publica bezerro, garrote nem vaca. Valor em R$/kg; o site mostra R$/@ (x 15).

Uso:  python scripts/precos_conab.py
Saída: data/precos_boi.json  (se o download falhar, o arquivo anterior é mantido)
"""
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "data" / "precos_boi.json"
URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/PrecosSemanalUF.txt"
UA = "MapaLeiloes/0.1 (coletor de agenda de leiloes de gado)"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        texto = r.read().decode("latin-1")

    series = defaultdict(list)   # uf -> [(ano, mes, semana, "dd-mm-aaaa - dd-mm-aaaa", R$/kg)]
    for linha in texto.splitlines()[1:]:
        c = [x.strip() for x in linha.split(";")]
        if len(c) < 11 or c[0] != "BOI" or c[1] != "GORDO":
            continue
        try:
            series[c[3]].append((int(c[5]), int(c[6]), int(c[8]), c[7], float(c[10].replace(",", "."))))
        except ValueError:
            continue
    if not series:
        print("precos_conab: boi gordo não encontrado no arquivo; mantendo o anterior")
        return 1

    por_uf = {}
    for uf, v in sorted(series.items()):
        v.sort()
        ultimo = v[-1]
        antes = v[-5] if len(v) >= 5 else None   # 4 semanas antes
        ini, fim = [p.strip() for p in ultimo[3].split(" - ")]
        por_uf[uf] = {
            "arroba": round(ultimo[4] * 15, 2),
            "kg": ultimo[4],
            "semana": f"{ini[:5].replace('-', '/')} a {fim[:5].replace('-', '/')}/{fim[6:]}",
            "variacao_4sem": round((ultimo[4] / antes[4] - 1) * 100, 1) if antes else None,
        }
    SAIDA.write_text(json.dumps({"fonte": "Conab - preço recebido pelo produtor (boi gordo)",
                                 "baixado_em": date.today().isoformat(), "por_uf": por_uf},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"precos_conab: boi gordo de {len(por_uf)} estados gravado em {SAIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # sem internet ou site fora do ar: mantém o arquivo anterior
        print(f"precos_conab: erro ({e}); mantendo o arquivo anterior")
        sys.exit(1)
