# Mapa de Leilões de Gado

Mapa interativo (estilo Google Maps) com os leilões de gado do Brasil: filtros por estado,
tipo, modalidade e período, busca, e "leilões perto de mim".

## Como usar

1. Edite `data/leiloes.csv`. Ele abre no Excel; salve como CSV UTF-8.
   - `data` no formato `AAAA-MM-DD`, `uf` com a sigla (MG, MS…), `cidade` com o nome oficial do município.
2. Gere os dados do mapa:
   ```
   python scripts/gerar_dados.py
   ```
   O script converte cada cidade em coordenadas, ignora leilões que já passaram e
   remove duplicados. Ele também avisa quais cidades não encontrou.
3. Abra `site/index.html` no navegador.

## Estrutura

| Caminho | O que é |
|---|---|
| `data/leiloes.csv` | Leilões cadastrados à mão |
| `data/coletados/*.csv` | Leilões coletados automaticamente, um arquivo por fonte |
| `data/municipios.csv`, `data/estados.csv` | Coordenadas dos 5.570 municípios ([kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros), base IBGE) |
| `scripts/gerar_dados.py` | Junta tudo e gera `site/leiloes.js` |
| `scripts/coletores/modelo_coletor.py` | Modelo para criar um coletor por fonte |
| `site/` | O mapa (Leaflet + OpenStreetMap, gratuito) |

## Próximos passos

- Criar coletores para as agendas das principais leiloeiras e portais.
- Agendar a coleta diária.
- Publicar o site (GitHub Pages, Netlify ou similar).

## Atualizar com os coletores

```
python scripts/atualizar.py
```
Roda todos os coletores de `scripts/coletores/` e depois o `gerar_dados.py`.

O `gerar_dados.py` junta o mesmo leilão quando ele vem de mais de uma fonte: mesmo dia, mesmo
estado e nome parecido. A fonte mais completa fica como base e as outras só preenchem campos
vazios. A ordem está em `PRIORIDADE`.

Leilões virtuais aparecem no mapa com pino azul, na cidade do estúdio de transmissão.
Os de local físico aparecem com pino verde.

A lista de fontes e o andamento estão em [docs/FONTES.md](docs/FONTES.md).
