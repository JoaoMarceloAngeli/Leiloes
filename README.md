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

## O que o site faz

- **Mapa e lista** com filtros por estado, tipo, modalidade, período, **raça** e **distância** (até 50/100/200/300 km).
- **Card do leilão:** favoritar (★), **WhatsApp** (texto pronto com link que abre o mapa filtrado),
  **Como chegar** (Google Maps), **Waze** e **Lembrar** (arquivo de agenda com aviso um dia antes).
- **Calendário** do mês com a quantidade de leilões por dia; um toque mostra só aquele dia.
- **Resumo da semana:** texto dos próximos 7 dias (com os filtros escolhidos) para mandar no WhatsApp.
- **Preço da arroba do boi gordo** por estado (Conab, dados abertos, semanal), no painel e no card.
- **Locais com dia fixo** (`dias` em `data/recintos.csv`) geram leilões previstos nas próximas 4 semanas.
- **Modo app:** dá para instalar no celular (ícone na tela inicial) e abre mesmo com sinal fraco.

## Publicação e atualização automática

O GitHub Actions ([.github/workflows/atualizar.yml](.github/workflows/atualizar.yml)) roda todos os coletores
**todo dia às 6h (Brasília)**, grava os dados novos no repositório e publica o site no **GitHub Pages**:
https://joaomarceloangeli.github.io/Leiloes/

- Para atualizar na hora: aba **Actions** > "Atualizar e publicar o mapa" > **Run workflow**.
- Mudanças em `site/`, `data/` ou `scripts/` enviadas com `git push` republicam o site sem coletar.
- Antes de editar no computador, rode `git pull` para trazer os dados que o robô gravou.

## Recintos de leilão (quadrados marrons)

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
