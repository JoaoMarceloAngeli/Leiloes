"""Roda todos os coletores e gera os dados do mapa.

Uso:  python scripts/atualizar.py

Se um coletor falhar (site fora do ar, mudança no layout), os outros continuam
e o CSV anterior daquela fonte é mantido.
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
COLETORES = sorted(p for p in (SCRIPTS / "coletores").glob("*.py")
                   if p.stem != "modelo_coletor" and not p.stem.startswith("_"))

falhas = []
for c in COLETORES:
    r = subprocess.run([sys.executable, str(c)])
    if r.returncode != 0:
        falhas.append(c.stem)

# Preço do boi gordo (Conab); se falhar, fica o arquivo anterior
if subprocess.run([sys.executable, str(SCRIPTS / "precos_conab.py")]).returncode:
    falhas.append("precos_conab")
subprocess.run([sys.executable, str(SCRIPTS / "gerar_dados.py")], check=True)
if falhas:
    print("ATENÇÃO, coletores com erro:", ", ".join(falhas))
    sys.exit(1)
