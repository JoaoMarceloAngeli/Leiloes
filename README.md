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
3. Abra o site por um servidor local (a chave do Google só funciona assim, não com duplo clique):
   ```
   python -m http.server 8000 -d site
   ```
   e acesse http://localhost:8000

## Google Maps (configuração única)

O mapa usa a Maps JavaScript API e os recintos usam a Places API (New). São duas chaves:

| Chave | Onde fica | Restrição no Google Cloud |
|---|---|---|
| **do site** | `site/config.js` (copie de `config.exemplo.js`) | Sites: `http://localhost:8000/*` e o endereço público. APIs: Maps JavaScript API e Places API (New) |
| **do servidor** | `.env` na raiz: `GOOGLE_PLACES_CHAVE=...` | APIs: só Places API (New) |

`site/config.js` e `.env` ficam fora do git.

**Termos do Google seguidos aqui:** dos recintos achados pelo Google, só o `place_id` é guardado de forma
permanente; a localização fica guardada por no máximo 30 dias (renovada por `atualizar.py`);
nome e endereço são buscados pelo site na hora do clique. Os dados do Google só aparecem sobre o mapa do Google.

**Varredura de recintos de um estado:**
```
python scripts/places_varredura.py varrer GO --simular   # mostra quantas chamadas serão feitas
python scripts/places_varredura.py varrer GO              # busca (limite padrão: 400 chamadas)
# revise data/temp/candidatos_GO.csv no Excel: "s" na coluna aprovar
python scripts/places_varredura.py importar GO
python scripts/places_varredura.py atualizar
python scripts/gerar_dados.py
```

## Estrutura

| Caminho | O que é |
|---|---|
| `data/leiloes.csv` | Leilões cadastrados à mão |
| `data/coletados/*.csv` | Leilões coletados automaticamente, um arquivo por fonte |
| `data/municipios.csv`, `data/estados.csv` | Coordenadas dos 5.570 municípios ([kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros), base IBGE) |
| `scripts/gerar_dados.py` | Junta tudo e gera `site/leiloes.js` |
| `scripts/coletores/modelo_coletor.py` | Modelo para criar um coletor por fonte |
| `site/` | O mapa (Leaflet + OpenStreetMap, gratuito) |

## Recintos de leilão (quadrados laranja)

Muitos leilões presenciais do interior, como os semanais em Goiás, acontecem sempre no mesmo recinto
e não aparecem em nenhum site. Esses locais ficam no mapa como **recintos**, sem data:

```
python scripts/adicionar_recinto.py "https://maps.app.goo.gl/..." --dias "Toda sexta, 20h" --telefone "(62) ..."
python scripts/gerar_dados.py
```

No Google Maps, abra o local, toque em **Compartilhar** e copie o link. O script lê nome e coordenadas
do link, acha o município mais próximo e grava em `data/recintos.csv`, que também pode ser editado à mão.

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
