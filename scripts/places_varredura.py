"""Varredura de recintos de leilão de gado num estado, pela Places API (New) do Google.

Etapas:
  1) python scripts/places_varredura.py varrer GO --maximo 400
     Faz uma busca "leilão de gado" em cada município do estado (mais algumas buscas gerais)
     e grava os candidatos em data/temp/candidatos_GO.csv. Para antes de passar de --maximo
     chamadas (cada chamada é cobrada; confira os preços no Google Cloud).
     Use --simular para só contar quantas chamadas seriam feitas, sem chamar a API.

  2) Abra data/temp/candidatos_GO.csv no Excel e marque "s" na coluna aprovar dos que são
     recintos de gado de verdade. Preencha dias, telefone e obs se souber.

  3) python scripts/places_varredura.py importar GO
     Leva os aprovados para data/recintos.csv guardando só place_id + os nossos campos,
     e apaga o arquivo de candidatos (nome e endereço do Google não podem ficar guardados).

  4) python scripts/places_varredura.py atualizar      (uma vez por mês, já roda no atualizar.py)
     Guarda a localização de cada recinto com a data. Os termos deixam guardar lat/lng por até
     30 dias; assim o site não precisa consultar o Google a cada visita. Coordenadas com mais de
     30 dias são descartadas pelo gerar_dados.py e o site volta a buscar na hora.
"""
import argparse
import csv
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_places import RAIZ, buscar_texto, carregar_chave, localizacao  # noqa: E402

DADOS = RAIZ / "data"
TEMP = DADOS / "temp"
RECINTOS = DADOS / "recintos.csv"
CAMPOS_RECINTO = ["place_id", "nome", "cidade", "uf", "lat", "lng", "dias", "telefone", "site",
                  "maps", "obs", "fonte", "coord_data"]
CAMPOS_GOOGLE = ["places.id", "places.displayName", "places.formattedAddress", "places.types",
                 "nextPageToken"]
NOMES_UF = {"GO": "Goiás", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "TO": "Tocantins",
            "PA": "Pará", "MG": "Minas Gerais", "BA": "Bahia", "RO": "Rondônia", "MA": "Maranhão"}
BUSCAS_GERAIS = ["recinto de leilão de gado", "leilões rurais", "leilão de bovinos", "parque de leilões"]

BOM = re.compile(r"leil|recinto|tatersal|pecu[aá]ria|remate", re.I)
RUIM = re.compile(r"im[oó]v|ve[ií]cul|detran|judici|carro|moto|banco|caixa econ|sucata", re.I)


def normalizar(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def municipios(uf: str) -> list[tuple[str, float, float]]:
    with open(DADOS / "estados.csv", encoding="utf-8-sig") as f:
        codigo = next(r["codigo_uf"] for r in csv.DictReader(f) if r["uf"] == uf)
    with open(DADOS / "municipios.csv", encoding="utf-8-sig") as f:
        return [(r["nome"], float(r["latitude"]), float(r["longitude"]))
                for r in csv.DictReader(f) if r["codigo_uf"] == codigo]


def varrer(uf: str, maximo: int, simular: bool) -> int:
    lista = municipios(uf)
    estado = NOMES_UF.get(uf, uf)
    buscas = [(f"{b} em {estado}", None, "") for b in BUSCAS_GERAIS]
    buscas += [(f"leilão de gado em {nome}, {uf}", (lat, lng), nome) for nome, lat, lng in lista]
    print(f"{len(lista)} municípios em {uf}; {len(buscas)} buscas na primeira página "
          f"(as buscas gerais podem ir até 3 páginas). Limite: {maximo} chamadas.")
    if simular:
        return 0
    chave = carregar_chave()
    if not chave:
        sys.exit("Falta GOOGLE_PLACES_CHAVE no arquivo .env (veja o README).")

    achados, chamadas = {}, 0
    for texto, centro, municipio in buscas:
        token, paginas = "", 0
        while chamadas < maximo:
            resp = buscar_texto(chave, texto, CAMPOS_GOOGLE, centro=centro, token=token)
            chamadas += 1
            paginas += 1
            for p in resp.get("places", []):
                nome = p.get("displayName", {}).get("text", "")
                endereco = p.get("formattedAddress", "")
                if p["id"] in achados or not re.search(rf"\b{uf}\b|{estado}", endereco):
                    continue
                provavel = "sim" if BOM.search(nome) and not RUIM.search(nome + " " + endereco) else ""
                achados[p["id"]] = {"aprovar": "", "provavel": provavel, "nome_google": nome,
                                    "endereco_google": endereco, "tipos": ",".join(p.get("types", [])),
                                    "busca": municipio or texto, "place_id": p["id"],
                                    "dias": "", "telefone": "", "site": "", "obs": ""}
            token = resp.get("nextPageToken", "")
            if not token or centro or paginas >= 3:   # por município, só a 1ª página
                break
        if chamadas >= maximo:
            print(f"Parei no limite de {maximo} chamadas (busca atual: {texto}).")
            break
        if chamadas % 25 == 0:
            print(f"  {chamadas} chamadas, {len(achados)} candidatos…")

    TEMP.mkdir(parents=True, exist_ok=True)
    saida = TEMP / f"candidatos_{uf}.csv"
    linhas = sorted(achados.values(), key=lambda a: (a["provavel"] != "sim", a["busca"], a["nome_google"]))
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig: abre certo no Excel
        w = csv.DictWriter(f, fieldnames=list(linhas[0]) if linhas else ["aprovar"], delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    print(f"{chamadas} chamadas feitas. {len(achados)} candidatos "
          f"({sum(a['provavel'] == 'sim' for a in linhas)} prováveis) em {saida.relative_to(RAIZ)}")
    return 0


def cidade_da_busca(busca: str, endereco: str, uf: str) -> str:
    """Município do recinto: tenta achar no endereço do Google um município do estado."""
    nomes = {normalizar(n): n for n, _, _ in municipios(uf)}
    for parte in re.split(r"[,-]", endereco):
        n = nomes.get(normalizar(parte.strip()))
        if n:
            return n
    return busca if normalizar(busca) in nomes else ""


def importar(uf: str) -> int:
    arq = TEMP / f"candidatos_{uf}.csv"
    if not arq.exists():
        sys.exit(f"Não achei {arq.relative_to(RAIZ)}. Rode primeiro: varrer {uf}")
    with open(arq, encoding="utf-8-sig") as f:
        aprovados = [r for r in csv.DictReader(f, delimiter=";") if r["aprovar"].strip().lower() in ("s", "sim", "x")]

    atuais = []
    if RECINTOS.exists():
        with open(RECINTOS, encoding="utf-8-sig") as f:
            atuais = list(csv.DictReader(f))
    ids = {r.get("place_id") for r in atuais}
    novos = 0
    for r in aprovados:
        if r["place_id"] in ids:
            continue
        atuais.append({"place_id": r["place_id"], "nome": "",
                       "cidade": cidade_da_busca(r["busca"], r["endereco_google"], uf), "uf": uf,
                       "lat": "", "lng": "", "dias": r["dias"], "telefone": r["telefone"], "site": r["site"],
                       "maps": f"https://www.google.com/maps/place/?q=place_id:{r['place_id']}",
                       "obs": r["obs"], "fonte": "google_places"})
        novos += 1
    with open(RECINTOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_RECINTO, extrasaction="ignore")
        w.writeheader()
        w.writerows(atuais)
    arq.unlink()
    print(f"{novos} recintos novos em {RECINTOS.relative_to(RAIZ)}; arquivo de candidatos apagado.")
    return 0


def atualizar() -> int:
    chave = carregar_chave()
    if not chave or not RECINTOS.exists():
        print("Sem chave no .env ou sem recintos: nada a atualizar.")
        return 0
    with open(RECINTOS, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    hoje, feitos = date.today(), 0
    for l in linhas:
        if not l.get("place_id"):
            continue
        data = l.get("coord_data") or ""
        if data and (hoje - date.fromisoformat(data)).days < 25:   # ainda vale; renova com folga
            continue
        loc = localizacao(chave, l["place_id"])
        if loc:
            l["lat"], l["lng"], l["coord_data"] = f"{loc[0]:.6f}", f"{loc[1]:.6f}", hoje.isoformat()
            feitos += 1
    with open(RECINTOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_RECINTO, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    print(f"Localização atualizada de {feitos} recinto(s).")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="acao", required=True)
    v = sub.add_parser("varrer")
    v.add_argument("uf")
    v.add_argument("--maximo", type=int, default=400, help="limite de chamadas à API (padrão 400)")
    v.add_argument("--simular", action="store_true", help="só mostra quantas chamadas seriam feitas")
    i = sub.add_parser("importar")
    i.add_argument("uf")
    sub.add_parser("atualizar")
    a = p.parse_args()
    if a.acao == "atualizar":
        return atualizar()
    uf = a.uf.upper()
    return varrer(uf, a.maximo, a.simular) if a.acao == "varrer" else importar(uf)


if __name__ == "__main__":
    sys.exit(main())
