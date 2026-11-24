# Fontes de leilões: checklist

Marque `[x]` quando a fonte estiver conferida. Na coluna **Situação** use:
`a conferir` · `tem agenda` · `sem agenda` · `coletor pronto` · `descartada`.

Os links foram confirmados em pesquisa. Onde não há link, o site ainda precisa ser localizado.

Ordem sugerida: **1 → 2 → 3 → 4 → 5 → 6**. Os agregadores cobrem muitas leiloeiras de uma vez.

---

## 1. Agregadores e canais de transmissão (cobertura nacional)

| ✓ | Fonte | Link | Situação | Observação |
|---|---|---|---|---|
| [x] | **Canal do Criador** (agenda do Canal Rural, Lance Rural e Programa Leilões) | [canaldocriador.com.br/leiloes](https://canaldocriador.com.br/leiloes/) | **coletor pronto** | `scripts/coletores/canal_do_criador.py`. API WordPress `wp-json/wp/v2/leilao`, cerca de 48 itens. Em leilão virtual, a cidade costuma ser o estúdio (Londrina/São Paulo). Tem também a lista `wp-json/wp/v2/leiloeiras`, útil para descobrir fontes |
| [x] | Canal Rural: leilões | [canalrural.com.br/leilao](https://www.canalrural.com.br/leilao/) | sem agenda | Só notícias; a agenda está no Canal do Criador |
| [x] | Lance Rural (Canal Rural) | [canalrural.com.br/leilao/lance-rural](https://www.canalrural.com.br/leilao/lance-rural/) | sem agenda | Página de notícias; os leilões do Lance Rural já vêm pelo Canal do Criador |
| [x] | Agro Agenda (agenda de eventos usada pelo Canal Rural) | [agroagenda.agr.br](https://agroagenda.agr.br/) | descartada por ora | API pública `api.agroagenda.agr.br/v1/home/buscar`; 300 eventos, só 1 leilão. Rever no futuro |
| [x] | **Canal do Boi + AgroCanal** (SBA) | [sba1.com/leiloes](https://sba1.com/leiloes) | **coletor pronto** | `scripts/coletores/canal_do_boi.py`. canaldoboi.com.br redireciona para sba1.com. Cerca de 20 leilões com cidade/UF, local e leiloeira. Página HTML; a data vem sem ano (o coletor deduz) |
| [x] | Arrobaplay (plataforma de lotes do SBA) | [arrobaplay.com/leiloes](https://arrobaplay.com/leiloes) | descartada | Mesmos leilões do SBA |
| [x] | Terraviva (Band/Newco) | [canalterraviva.uol.com.br/leiloes](https://canalterraviva.uol.com.br/leiloes) | sem local | API `…/api/programs?tags=leiloes`; cerca de 11 leilões, **sem cidade**. 9 de 11 são da Estância Bahia: coletar direto da leiloeira |
| [ ] | C2Rural | — | a conferir | Transmite leilões virtuais |
| [x] | Remate Web / Remate Web Plus | [remateweb.com/agenda](https://www.remateweb.com/agenda) | descartada | Mesmo sistema e mesma cidade (Londrina) do Programa Leilões. A agenda própria tem só 1 leilão futuro, que já está no Programa Leilões: os leilões que ela transmite já entram pelo coletor do Programa Leilões |
| [ ] | Compre Rural: leilões de animais | [comprerural.com/…/leilao-de-animais](https://www.comprerural.com/categorias/esportes-e-eventos/leilao-de-animais/) | a conferir | Notícias e agenda de leilões |
| [x] | Compre Rural: **diretório de casas de leilão** | [comprerural.com/categorias/casas-de-leiloes](https://comprerural.com/categorias/casas-de-leiloes/) | conferido | 20 fichas (quase todas do MS), 17 com site. Resultado por leiloeira na tabela abaixo |

**Leiloeiras do diretório Compre Rural** (testado em 21/11/2026):

| ✓ | Leiloeira | Site | Situação |
|---|---|---|---|
| [x] | **Leiloboi** (Campo Grande/MS) | [leiloboi.com/leiloes](https://leiloboi.com/leiloes) | **coletor pronto**: `leiloboi.py`. Inclui leilões presenciais em fazenda (Corumbá) e parque (Dourados) |
| [x] | **Central Leilões** (Araçatuba/SP) | [centralleiloes.com.br](https://www.centralleiloes.com.br/agenda-de-leiloes.php) | **coletor pronto**: `central_leiloes.py`. Local exato da fazenda; tem prioridade sobre o Canal do Boi |
| [ ] | Correa da Costa (Campo Grande/MS) | [correadacosta.com.br](https://www.correadacosta.com.br) | **não coletar**: o robots.txt bloqueia robôs de IA, incluindo os da Anthropic. Pedir agenda direto (34 anos, mais de 5.900 leilões: grande no MS) |
| [ ] | Leilosul (Pres. Venceslau/SP e Bataguassu/MS) | [leilosul.com.br/agenda](https://www.leilosul.com.br/agenda) | a página "agenda" lista lotes para lance, sem datas: rever |
| [x] | **LN Leilões** (Aquidauana/MS) | [lnleiloes.com.br/leiloes](https://www.lnleiloes.com.br/leiloes) | **coletor pronto**: `ln_leiloes.py`. Leilão virtual semanal de corte (quartas, 16h); sem local da fazenda, usa a sede |
| [ ] | Pantanal Leilões (Rio Negro/MS) | [pantanalleiloes.com.br](https://pantanalleiloes.com.br/leiloes/agenda-de-leiloes) | agenda com só 1 leilão (05/12) e **sem local**. Rever depois; se continuar assim, cadastrar à mão |
| [ ] | Taquari Leilões (Campo Grande/MS) | [taquarileiloes.com.br](https://www.taquarileiloes.com.br/agenda) | /agenda e /agenda-virtual **vazias** em 21/11/2026. Rever em outra época |
| [x] | LeiloGrande (Campo Grande/MS) | — | descartada: o domínio mostra só uma página padrão do servidor (site desativado) |
| [x] | Bela Vista Leilões (SP) | — | descartada: leilões de bens em geral, não rural |
| [x] | Embral Leilões (SP) | [embral.com.br](https://www.embral.com.br) | descartada: leilões em geral, não rural |
| [ ] | Gramadão, Leilosin, Iturama | — | sem site na ficha; só telefone |
| [x] | MS Pecuária, Fazenda Leilões, CP Leilões, Triângulo, Comitiva, LeiloSat, Nhandeara | — | **site fora do ar** (domínio não existe mais) |
| [ ] | Portal DBO | [portaldbo.com.br](https://www.portaldbo.com.br/) | a conferir | Cobre leilões de reposição |
| [ ] | Agrolink | [agrolink.com.br](https://www.agrolink.com.br/) | a conferir | Notícias de leilões |

## 2. Grandes leiloeiras (atuação em vários estados)

| ✓ | Leiloeira | Link | Situação | Observação |
|---|---|---|---|---|
| [x] | **Programa Leilões** | [programaleiloes.com/agenda](https://programaleiloes.com/agenda) | **coletor pronto** | `scripts/coletores/programa_leiloes.py`. Cerca de 115 itens em 30 dias (cerca de 90 de gado). Londrina é a sede/estúdio: esses leilões entram como "Virtual". O local da fazenda só aparece no catálogo PDF |
| [ ] | Estância Bahia Leilões (EB) | [estanciabahia.com.br/Agenda](https://estanciabahia.com.br/Agenda) · [ebleiloes.com.br/Agenda](https://ebleiloes.com.br/Agenda) | **pendente: precisa de autorização** | Sites feitos no Base44: a agenda só carrega por JavaScript, vinda do banco de dados do app. Chamar esse banco direto foi bloqueado como acesso não autorizado. Caminhos: pedir à EB um feed/planilha da agenda, ou cadastrar à mão em `data/leiloes.csv`. Parte da agenda aparece no Terraviva, mas sem cidade |
| [ ] | eblonline.com.br | — | descartada | É outra empresa (Empresa Brasileira de Leilões), não a Estância Bahia |
| [ ] | Trajano Silva Remates | — | a conferir | RS (Uruguaiana); remates e Expointer |
| [ ] | Gramadão Leilões | — | a conferir | Leilões toda quarta, 20h (corte e leite) |

**Leiloeiras descobertas nos agregadores** (a conferir uma a uma; algumas podem ter agenda própria com mais leilões):

| ✓ | Leiloeira | Onde apareceu | Situação |
|---|---|---|---|
| [ ] | Central Leilões | Canal do Boi (Araçatuba/SP, São José do Rio Preto/SP, Campo Grande/MS) | a conferir |
| [ ] | MB Leilões | Canal do Boi (Cuiabá/MT, leilão virtual semanal) | a conferir |
| [ ] | Connect Leilões | Canal do Boi, Terraviva (Londrina/PR, Itaituba/PA) | a conferir |
| [ ] | Ricardo Nicolau Leilões | Canal do Boi (Sinop/MT) | a conferir |
| [ ] | Star World Leilões | Terraviva | a conferir |
| [ ] | Capitaliza | Canal do Criador | a conferir |
| [ ] | Leiloboi | Canal do Criador | a conferir |
| [ ] | Tellechea & Bastos Leilões | Canal do Criador (RS) | a conferir |
| [ ] | Parceria Leilões | Canal do Criador | a conferir |
| [ ] | Macedo Leilões | Canal do Criador | a conferir |
| [ ] | Fiel Leilões | Canal do Criador | a conferir |

## 3. Plataformas digitais e aplicativos

| ✓ | Plataforma | Situação | Observação |
|---|---|---|---|
| [ ] | Rematefy | a conferir | Gestão de leilões rurais (web/app): pode concentrar várias leiloeiras |
| [ ] | LeiloApp | a conferir | Lances pelo celular |
| [ ] | Central de Lances Digital (CLD) | a conferir | Lances, cotações e agenda |
| [ ] | Meu Boi (parceria Programa Leilões) | a conferir | Integra gestão de rebanho aos leilões |
| [ ] | Gado Certo / O Gado | descartada? | Marketplace sem data fixa: não é leilão com agenda |

## 4. Por região

Em cada estado, confira três coisas: a **federação da agricultura** (calendário de eventos), o **governo estadual**
(calendário oficial) e as **leiloeiras locais** (pelo diretório do Compre Rural e pela Junta Comercial, na seção 6).

> **Federações (conferido em 21/11/2026):** Famasul, Famato, FAEG, Faepa, FAET e FAERO não publicam agenda de leilões.
> Os leilões presenciais do interior (Norte e Centro-Oeste) são divulgados pelas próprias leiloeiras, quase sempre
> só no Instagram/WhatsApp. O caminho é pedir a agenda direto, ou cadastrar à mão em `data/leiloes.csv`.

### Sul
| ✓ | UF | Fonte | Link | Situação |
|---|---|---|---|---|
| [ ] | RS | Sindiler-RS (sindicato dos leiloeiros) + Farsul: guia da temporada de remates | [notícia do guia](https://www.canalrural.com.br/pecuaria/temporada-de-primavera-no-rs-tera-mais-leiloes-neste-ano/) | **sem versão online encontrada**. Cerca de 243 eventos por temporada (outono e primavera). Pedir o PDF ao Sindiler/Farsul na próxima temporada (outono 2027) |
| [ ] | RS | Trajano Silva Remates | — | a conferir |
| [ ] | RS | Outras leiloeiras gaúchas | — | a conferir |
| [ ] | SC | Secretaria da Agricultura: **calendário oficial de eventos 2026** | [PDF](https://www2.agricultura.sc.gov.br/arquivos/eventos/1025-calendario-oficial-de-eventos-agropecuarios-2026/file) | **bloqueado: o site pede login** (testado em 21/11/2026, também pelo navegador). Também existe o ID 1005 no mesmo site. Pedir o PDF à SAR-SC ou à Cidasc e salvar em `data/fontes_manuais/`. 456 eventos com animais, incluindo leilões ([notícia](https://opresenterural.com.br/calendario-agropecuario-destaca-forca-produtiva-e-diversidade-do-campo-catarinense-em-2026/)) |
| [ ] | SC | FAESC | — | a conferir |
| [ ] | PR | FAEP + leiloeiras paranaenses (leite em Castro e região) | — | a conferir |

### Centro-Oeste
| ✓ | UF | Fonte | Link | Situação |
|---|---|---|---|---|
| [x] | MS | Famasul | [eventos](https://portal.sistemafamasul.com.br/eventos) | **sem leilões**: a agenda traz só exposições e rodeios dos sindicatos rurais (2 eventos em 21/11/2026) |
| [ ] | MS | Triângulo Leilões Rurais (Camapuã, Figueirão, Alcinópolis, Cassilândia, Campo Grande) | [Compre Rural](https://comprerural.com/triangulo-leiloes-camapua-ms/) | a conferir |
| [ ] | MS | MS Pecuária (Campo Grande) | — | a conferir |
| [ ] | MS | LN Leilões (Aquidauana) | — | a conferir |
| [x] | MS | Leilosin (Paranaíba) | [Compre Rural](https://comprerural.com/categorias/casas-de-leiloes/) | **sem site nem agenda online** (conferido em 23/11/2026). Leilões no Parque de Exposição Daniel Martins Ferreira, em Paranaíba: candidato a recinto (mandar link do Google Maps) |
| [x] | MS | Panorama Leilões (Cone Sul) | — | **sem site com agenda** (23/11/2026). Só aparece em notícias de resultados (Portal DBO) |
| [x] | MS | Reata Leilões | — | **nada encontrado** (23/11/2026): sem site, agenda nem notícias |
| [x] | MS/SP? | Gramadão Leilões | [Compre Rural](https://comprerural.com/categorias/casas-de-leiloes/) | **sem site** (23/11/2026). O diretório diz "toda quarta, 20h, corte e leite", mas o telefone é DDD 17 (SP). Confirmar cidade antes de cadastrar como recinto |
| [x] | MT | Famato + Acrimat | [leiloeiros](https://sistemafamato.org.br/leiloeiros-rurais/) | **sem agenda de leilões**. A Famato publica só a lista de leiloeiros credenciados em MT (nome e telefone, útil para contato, mas são dados pessoais: não coletar) e o calendário interno de 2025. O site da Acrimat está fora do ar |
| [ ] | MT | Estância Bahia Leilões | — | a conferir |
| [x] | MT | Leilão Cuiabá Premium | — | **nada encontrado** (23/11/2026). Em Cuiabá, os leilões que aparecem são da Estância Bahia e os do Centro de Eventos do Sindicato Rural |
| [x] | GO | FAEG | [eventos](https://sistemafaeg.com.br/eventos) | **sem leilões**: só eventos institucionais (cursos, Campo Saúde, Demoday) |
| [ ] | GO | Leiloeiras goianas (ver lista da Juceg) | [Juceg: leiloeiros](https://goias.gov.br/juceg/leiloeiros/) | **nenhum leilão de GO nos agregadores** (21/11/2026). Os leilões goianos são semanais em recintos locais, sem agenda online. Agora entram como **recintos** em `data/recintos.csv` (por link do Google Maps: Mara Rosa, além de Jandaia e Firminópolis, que vieram do OpenStreetMap). Faltam dias, horários e telefone de cada um |
| [ ] | GO | Google Maps: recintos de leilão em todo o estado | — | coleta automática proibida pelos termos do Google. **Decisão (23/11/2026): sem API.** A Places API exige trocar o mapa para o Google e um pagamento antecipado de R$ 180. Recintos entram por links enviados um a um (`scripts/adicionar_recinto.py`) |
| [ ] | GO | **Agrodefesa: leilões autorizados + recintos cadastrados** | [texto do pedido](pedidos/agrodefesa_lai.md) | todo leilão em GO é comunicado à Agrodefesa 5 dias antes. Pedido pela Lei de Acesso à Informação **enviado em 23/11/2026, protocolo 2026.1123.133352-18** (Ouvidoria/e-SIC Goiás, portal Expresso). Resposta em 24/11/2026: só indicou o [Dados Abertos Goiás](https://dadosabertos.go.gov.br/dataset/eventos-agropecuarios), mas os arquivos de "Eventos Agropecuários" (2020-2025) são de comerciantes de mudas, sem nenhum evento. **Recurso até 04/12/2026** (texto no pedido) |
| [ ] | DF | Leiloeiras do DF/entorno | — | a conferir |

### Sudeste
| ✓ | UF | Fonte | Link | Situação |
|---|---|---|---|---|
| [ ] | MG | FAEMG | — | a conferir |
| [x] | MG | Uberaba: ExpoZebu e leilões no Parque Fernando Costa | [ExpoZebu 2026](https://www.canalrural.com.br/pecuaria/91a-expozebu-e-aberta-em-uberaba-com-expectativa-de-r-200-milhoes-em-negocios/) | as agendas (ExpoZebu: 40 leilões; ExpoGenética: 32) são publicadas pela **ABCZ, que bloqueia robôs**. Os leilões que passam na TV já entram pelo Canal do Boi/Programa Leilões. **Império Leilões** (Uberaba, recinto para 7 mil animais, [nota](https://diariodocomercio.com.br/agronegocio/curtas-agronegocio-15-12-2/)): sem site encontrado, candidato a recinto (23/11/2026) |
| [ ] | MG | Leiloeiras mineiras (ver lista da Jucemg) | [Jucemg: leiloeiros](https://jucemg.mg.gov.br/pagina/140/leiloeiros-ordem-alfabetica) | a conferir |
| [x] | SP | FAESP + leiloeiras paulistas (Barretos, Araçatuba, Presidente Prudente) | — | Araçatuba: a principal é a **Central Leilões, já coletada**. Barretos e Presidente Prudente: nenhuma leiloeira com agenda online encontrada (23/11/2026) |
| [ ] | RJ | FAERJ | — | a conferir |
| [ ] | ES | FAES | — | a conferir |

### Norte
| ✓ | UF | Fonte | Link | Situação |
|---|---|---|---|---|
| [ ] | PA | **Faepa: calendário de eventos agropecuários** | [notícia de 2026](https://cnabrasil.org.br/noticias/liderancas-do-agronegocio-paraense-definem-calendario-de-eventos-e-confirmam-expopara-para-2026) | **não publicado online**. O calendário de 2026 foi definido em março, mas não há arquivo público, e a Faepa não tem site próprio (notícias ficam no portal da CNA). ⭐ Pedir direto à Faepa: em 2023 eram 102 leilões |
| [ ] | PA | Leiloeiras paraenses (Redenção, Marabá, Xinguara, Paragominas) | — | a conferir |
| [ ] | TO | FAET + leiloeiras tocantinenses (Araguaína, Gurupi, Paraíso: Estrela Dalva Leilões) | — | FAET: site sem conteúdo. Leiloeiras locais sem site encontrado (divulgam por Instagram/WhatsApp) |
| [ ] | RO | FAERO + leiloeiras de Rondônia (Ji-Paraná, Cacoal, Ariquemes) | — | FAERO: domínio não encontrado. Leiloeiras sem agenda online encontrada |
| [ ] | AC | FAEAC | — | a conferir |
| [ ] | AM | FAEA | — | a conferir |
| [ ] | RR / AP | Federações locais | — | a conferir |

### Nordeste
| ✓ | UF | Fonte | Link | Situação |
|---|---|---|---|---|
| [ ] | BA | FAEB + Bahia Farm Show + Fenagro | — | a conferir |
| [ ] | BA | Leiloeiras baianas (ver lista da Juceb) | [Juceb: leiloeiros](https://www.ba.gov.br/juceb/home/matriculas-e-carteira-profissional/leiloeiros) | a conferir |
| [ ] | MA | FAEMA + leiloeiras maranhenses (Açailândia, Imperatriz) | — | a conferir |
| [ ] | PE | FAEPE + leilões de Gravatá e Caruaru | [Folha PE (Gravatá)](https://www.folhape.com.br/economia/gravata-recebe-leilao-com-oferta-de-duas-mil-cabecas-de-gado-e/415029/) | a conferir |
| [ ] | PI / CE / RN / PB / AL / SE | Federações locais | — | a conferir |

## 5. Associações de raça (leilões de elite e genética)

| ✓ | Associação | Situação | Observação |
|---|---|---|---|
| [ ] | ABCZ (zebuínos: Nelore, Gir, Guzerá…) | **não coletar** | O robots.txt bloqueia o ClaudeBot. Tem agenda de eventos homologados e a "relação dos associados do Sindicato dos Leiloeiros Rurais": pedir direto |
| [x] | **ACNB (Nelore)** | **coletor pronto** | `acnb_nelore.py`. [Agenda de leilões oficializados](https://www.nelore.org.br/agenda-de-leiloes/) com local e cidade reais e o promotor. Só a página 1 (10 próximos): a paginação usa /wp-admin/, bloqueado no robots.txt. Site lento (cerca de 20 s) |
| [ ] | Associação Brasileira de Angus | **não coletar** | O robots.txt bloqueia todos os robôs (`Disallow: /`) |
| [ ] | Girolando | **não coletar** | O robots.txt bloqueia os robôs da Anthropic. Tem /eventos-ranking/leiloes e /eventos/leiloes-chancelados: pedir direto |
| [ ] | Associação Brasileira de Hereford e Braford | a conferir | Sul |
| [ ] | Girolando | a conferir | Leite |
| [ ] | ABCBRH (Holandês) | a conferir | Leite |
| [ ] | ABCGIL (Gir Leiteiro) | a conferir | Leite |
| [ ] | Senepol, Brahman, Tabapuã, Guzerá, Sindi | a conferir | Raças menores |

## 6. Descoberta de leiloeiras: listas oficiais de leiloeiros (Juntas Comerciais)

Não trazem agenda, mas listam **todos os leiloeiros registrados**. Use para achar leiloeiras rurais que faltam na lista.

| ✓ | UF | Link |
|---|---|---|
| [ ] | GO | [Juceg](https://goias.gov.br/juceg/leiloeiros/) |
| [ ] | MG | [Jucemg](https://jucemg.mg.gov.br/pagina/140/leiloeiros-ordem-alfabetica) |
| [ ] | BA | [Juceb](https://www.ba.gov.br/juceb/home/matriculas-e-carteira-profissional/leiloeiros) |
| [ ] | Demais UFs | Junta Comercial de cada estado (seção "Leiloeiros") |

---

### Como registrar o andamento
Quando conferir uma fonte, anote ao lado: se tem agenda online, em que formato (página HTML, PDF, app, Instagram)
e se dá para coletar automaticamente. Fontes só em PDF ou Instagram podem entrar à mão no `data/leiloes.csv`.
