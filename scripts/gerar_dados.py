"""Gera site/leiloes.js a partir de data/leiloes.csv (e dos coletores em data/coletados/*.csv).

Cada leilão recebe latitude/longitude do município (base IBGE em data/municipios.csv).
Uso:  python scripts/gerar_dados.py
"""
import csv
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
SAIDA = RAIZ / "site" / "leiloes.js"

CAMPOS = ["nome", "data", "hora", "cidade", "uf", "local", "leiloeira",
          "tipo", "modalidade", "raca", "link", "fonte"]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().replace("-", " ").replace("'", " ").split())


def carregar_municipios() -> dict:
    with open(DADOS / "estados.csv", encoding="utf-8-sig") as f:
        uf_por_codigo = {r["codigo_uf"]: r["uf"] for r in csv.DictReader(f)}
    municipios = {}
    with open(DADOS / "municipios.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            uf = uf_por_codigo[r["codigo_uf"]]
            municipios[(normalizar(r["nome"]), uf)] = (float(r["latitude"]), float(r["longitude"]), r["nome"])
    return municipios


def localizar(municipios: dict, cidade: str, uf: str):
    """Acha o município. Se o texto tiver algo antes do nome
    ('Parque de Exposições de Dourados', 'Sede Leiloboi em Campo Grande'),
    tenta as partes finais do texto, da mais longa para a mais curta."""
    palavras = normalizar(cidade).split()
    for i in range(len(palavras)):
        achado = municipios.get((" ".join(palavras[i:]), uf))
        if achado:
            return achado
    return None


# Ordem de prioridade quando o mesmo leilão vem de várias fontes: a primeira
# fica como base e as seguintes só preenchem campos vazios.
# Sites das próprias leiloeiras vêm primeiro: trazem o local exato do leilão.
PRIORIDADE = ["central_leiloes", "leiloboi", "ln_leiloes", "acnb_nelore",
              "canal_do_boi", "programa_leiloes", "canal_do_criador"]

PALAVRAS_IGNORADAS = {"leilao", "virtual", "de", "do", "da", "dos", "das", "e", "o", "a",
                      "&", "-", "no", "na", "em", "com"}


def tokens(nome: str) -> set:
    palavras = re.findall(r"[a-z0-9]+", normalizar(nome))
    return {p for p in palavras
            if p not in PALAVRAS_IGNORADAS and not re.fullmatch(r"\d+(o|a|ª|º)?|20\d\d", p)}


# Palavras comuns a muitos leilões: não servem para dizer que dois nomes são o mesmo leilão
GENERICAS = {"nelore", "gir", "girolando", "angus", "brangus", "senepol", "guzera", "sindi",
             "pintado", "po", "leiteiro", "corte", "elite", "touros", "touro", "matrizes",
             "femeas", "bezerros", "novilhas", "reprodutores", "fazenda", "genetica", "especial",
             "mega", "etapa", "convidados", "amigos", "selecao", "programa", "leiloes", "fest"}


def minutos(hora: str) -> int | None:
    m = re.match(r"(\d{1,2}):(\d{2})", hora or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def mesmo_leilao(a: dict, b: dict) -> bool:
    """Mesmo dia, mesmo estado e nomes parecidos. Exemplos que devem casar:
    '6º Leilão Virtual Nelore Gran Filé 2026' x 'Leilão Virtual Nelore Gran Filé 2026'
    'Leilão Nelore Eliza' x 'Leilão Eliza'."""
    if a["data"] != b["data"] or a["uf"] != b["uf"]:
        return False
    ta, tb = tokens(a["nome"]), tokens(b["nome"])
    if not ta or not tb:
        return False
    if len(ta & tb) / len(ta | tb) >= 0.6:
        return True
    da, db = ta - GENERICAS, tb - GENERICAS   # palavras que identificam o leilão
    if not da or not db:
        return False
    if da <= db or db <= da:
        return True
    # Compartilham um nome próprio e começam quase no mesmo horário
    # (as fontes às vezes divergem em até 1 hora)
    ma, mb = minutos(a["hora"]), minutos(b["hora"])
    return bool(da & db) and ma is not None and mb is not None and abs(ma - mb) <= 60


def ler_leiloes() -> list:
    coletados = sorted((DADOS / "coletados").glob("*.csv"),
                       key=lambda p: PRIORIDADE.index(p.stem) if p.stem in PRIORIDADE else 99)
    arquivos = [DADOS / "leiloes.csv", *coletados]
    leiloes = []
    for arq in arquivos:
        if not arq.exists():
            continue
        with open(arq, encoding="utf-8-sig") as f:
            for linha in csv.DictReader(f):
                leiloes.append({c: (linha.get(c) or "").strip() for c in CAMPOS})
    return leiloes


def ler_recintos() -> list:
    """Locais fixos com leilões frequentes (data/recintos.csv, via scripts/adicionar_recinto.py)."""
    arq = DADOS / "recintos.csv"
    if not arq.exists():
        return []
    with open(arq, encoding="utf-8-sig") as f:
        recintos = []
        for r in csv.DictReader(f):
            try:
                r["lat"], r["lng"] = float(r["lat"]), float(r["lng"])
            except (TypeError, ValueError):
                continue
            recintos.append({k: v.strip() if isinstance(v, str) else v for k, v in r.items()})
    return sorted(recintos, key=lambda r: (r["uf"], r["cidade"], r["nome"]))


def main() -> int:
    municipios = carregar_municipios()
    hoje = date.today().isoformat()
    saida, sem_local, duplicados = [], [], 0

    for l in ler_leiloes():
        if not l["nome"] or not l["data"]:
            continue
        if l["data"] < hoje:  # ignora leilões que já passaram
            continue
        l["uf"] = l["uf"].upper()

        igual = next((s for s in saida if mesmo_leilao(s, l)), None)
        if igual:  # mesmo leilão vindo de outra fonte: só completa o que falta
            duplicados += 1
            for campo, valor in l.items():
                if valor and not igual.get(campo):
                    igual[campo] = valor
            fontes = [f for f in igual["fonte"].split(", ") if f]
            if l["fonte"] and l["fonte"] not in fontes:
                igual["fonte"] = ", ".join(fontes + [l["fonte"]])
            continue

        achado = localizar(municipios, l["cidade"], l["uf"])
        if not achado:
            sem_local.append(f'{l["nome"]} ({l["cidade"]}/{l["uf"]})')
            continue
        l["lat"], l["lng"], l["cidade"] = achado
        saida.append(l)

    saida.sort(key=lambda x: (x["data"], x["hora"]))
    recintos = ler_recintos()
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(
        "// Arquivo gerado por scripts/gerar_dados.py - não edite à mão\n"
        f"window.LEILOES_ATUALIZADO = {json.dumps(hoje)};\n"
        f"window.LEILOES = {json.dumps(saida, ensure_ascii=False, indent=1)};\n"
        f"window.RECINTOS = {json.dumps(recintos, ensure_ascii=False, indent=1)};\n",
        encoding="utf-8",
    )
    print(f"{len(saida)} leilões gravados em {SAIDA.relative_to(RAIZ)} "
          f"({duplicados} duplicados entre fontes foram unidos), {len(recintos)} recintos")
    if sem_local:
        print("Cidade não encontrada (confira nome/UF):", *sem_local, sep="\n  - ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
