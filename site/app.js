(function () {
  const $ = (id) => document.getElementById(id);

  // ---------- Utilidades ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const semAcento = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const paraData = (iso) => new Date(iso + "T00:00:00");
  const fmtData = (iso) => paraData(iso).toLocaleDateString("pt-BR",
    { weekday: "short", day: "2-digit", month: "short" });
  const fmtDataLonga = (iso) => paraData(iso).toLocaleDateString("pt-BR",
    { weekday: "long", day: "2-digit", month: "long" });
  const linkSeguro = (u) => /^https?:\/\//i.test(u || "") ? u : "";
  const ehVirtual = (l) => l.modalidade === "Virtual";
  const ENDERECO_SITE = location.protocol.startsWith("http") ? location.origin + location.pathname : "";

  function distanciaKm(a, b) {
    const r = Math.PI / 180, R = 6371;
    const dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
    const h = Math.sin(dLat / 2) ** 2 +
      Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  // ---------- Dados: leilões (com data) e recintos (locais fixos, sem data) ----------
  const itens = [
    ...(window.LEILOES || []).map((l, i) => ({ ...l, id: "l" + i, recinto: false,
      chave: ["L", l.nome, l.data, l.cidade, l.uf].join("|") })),
    ...(window.RECINTOS || []).filter((r) => r.lat != null && r.lng != null)
      .map((r, i) => ({ ...r, id: "r" + i, recinto: true,
        chave: ["R", r.nome, r.cidade, r.uf].join("|") })),
  ];
  const porId = new Map(itens.map((it) => [it.id, it]));
  // Locais que já têm leilões com data (dia fixo) não precisam do quadrado: os pinos já mostram o lugar
  const locaisComData = new Set(itens.filter((it) => it.previsto).map((it) => [it.leiloeira, it.cidade, it.uf].join("|")));
  const temData = (r) => locaisComData.has([r.nome, r.cidade, r.uf].join("|"));

  // Raças: a fonte escreve de vários jeitos ("Nelore PO - Senepol", "Angus - Brangus - Ultrablack")
  const RACAS = ["Nelore", "Nelore Pintado", "Angus", "Brangus", "Ultrablack", "Senepol", "Brahman", "Braford",
    "Hereford", "Tabapuã", "Guzerá", "Sindi", "Gir", "Gir Leiteiro", "Girolando", "Holandês", "Jersey", "Caracu"];
  const textoRaca = (it) => semAcento(" " + [it.raca, it.nome].join(" ") + " ");
  const temRaca = (it, raca) => new RegExp("[^a-z]" + semAcento(raca) + "[^a-z]").test(textoRaca(it));

  // ---------- Preço do boi gordo (Conab) ----------
  const PRECOS = (window.PRECOS && window.PRECOS.por_uf) || {};
  const real = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const variacao = (v) => v == null ? "" : `${v > 0 ? "▲" : v < 0 ? "▼" : "="} ${Math.abs(v).toLocaleString("pt-BR")}%`;
  const linhaPreco = (uf) => PRECOS[uf]
    ? `Boi gordo em ${uf}: ${real(PRECOS[uf].arroba)}/@ (Conab, ${PRECOS[uf].semana})` : "";

  // ---------- Favoritos (guardados só neste navegador) ----------
  const CHAVE_FAV = "mapa-leiloes:favoritos";
  let favoritos = new Set();
  try { favoritos = new Set(JSON.parse(localStorage.getItem(CHAVE_FAV) || "[]")); } catch (e) { /* sem armazenamento */ }
  const ehFavorito = (it) => favoritos.has(it.chave);
  function alternarFavorito(it) {
    ehFavorito(it) ? favoritos.delete(it.chave) : favoritos.add(it.chave);
    try { localStorage.setItem(CHAVE_FAV, JSON.stringify([...favoritos])); } catch (e) { /* segue só nesta visita */ }
  }
  const botaoFav = (it) => `<button type="button" class="fav${ehFavorito(it) ? " ativo" : ""}" data-id="${it.id}"
    title="${ehFavorito(it) ? "Remover dos favoritos" : "Favoritar"}" aria-pressed="${ehFavorito(it)}">${ehFavorito(it) ? "★" : "☆"}</button>`;

  // ---------- Compartilhar, rota e agenda ----------
  function textoCompartilhar(it) {
    const linhas = it.recinto
      ? [`*${it.nome}*`, `Local de leilão em ${it.cidade}/${it.uf}`, it.dias || ""]
      : [`*${it.nome}*`, `📅 ${fmtDataLonga(it.data)}${it.hora ? " às " + it.hora : ""}${it.previsto ? " (data prevista)" : ""}`,
        `📍 ${it.cidade}/${it.uf}${it.local && !ehVirtual(it) ? " · " + it.local : ""}`,
        it.modalidade ? `${it.modalidade}${it.raca ? " · " + it.raca : ""}` : ""];
    const link = linkSeguro(it.link) || linkSeguro(it.maps);
    if (link) linhas.push(link);
    if (ENDERECO_SITE) linhas.push(`Mapa de leilões: ${ENDERECO_SITE}?busca=${encodeURIComponent(it.nome)}`);
    return linhas.filter(Boolean).join("\n");
  }

  function botoesAcao(it) {
    const zap = `https://wa.me/?text=${encodeURIComponent(textoCompartilhar(it))}`;
    const rota = `https://www.google.com/maps/dir/?api=1&destination=${it.lat},${it.lng}`;
    const waze = `https://waze.com/ul?ll=${it.lat},${it.lng}&navigate=yes`;
    const fisico = it.recinto || !ehVirtual(it);   // leilão virtual: o ponto é o estúdio, não faz sentido ir
    return `<div class="acoes">
      <a class="acao acao-zap" href="${esc(zap)}" target="_blank" rel="noopener">WhatsApp</a>
      ${fisico ? `<a class="acao" href="${esc(rota)}" target="_blank" rel="noopener">Como chegar</a>
                  <a class="acao" href="${esc(waze)}" target="_blank" rel="noopener">Waze</a>` : ""}
      ${it.recinto ? "" : `<button type="button" class="acao" data-lembrar="${it.id}">Lembrar</button>`}
    </div>`;
  }

  // Arquivo de agenda (.ics): o celular abre no calendário. Sem horário vira evento de dia inteiro.
  function baixarAgenda(it) {
    const dia = it.data.replace(/-/g, "");
    const fimDia = new Date(paraData(it.data).getTime() + 864e5).toISOString().slice(0, 10).replace(/-/g, "");
    const quando = it.hora
      ? [`DTSTART:${dia}T${it.hora.replace(":", "")}00`, `DURATION:PT3H`]
      : [`DTSTART;VALUE=DATE:${dia}`, `DTEND;VALUE=DATE:${fimDia}`];
    const linha = (t) => String(t).replace(/[\\,;]/g, (c) => "\\" + c).replace(/\n/g, "\\n");
    const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Mapa de Leiloes//PT-BR", "BEGIN:VEVENT",
      `UID:${it.chave.replace(/[^\w]/g, "")}@mapa-leiloes`,
      `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
      ...quando,
      `SUMMARY:${linha(it.nome)}`,
      `LOCATION:${linha(`${it.local ? it.local + ", " : ""}${it.cidade}/${it.uf}`)}`,
      `DESCRIPTION:${linha(textoCompartilhar(it))}`,
      "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", `DESCRIPTION:${linha("Amanhã: " + it.nome)}`, "END:VALARM",
      "END:VEVENT", "END:VCALENDAR"].join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
    a.download = `leilao-${it.data}.ics`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  // ---------- Mapa ----------
  const mapa = L.map("mapa", { zoomControl: true }).setView([-14.5, -52], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);
  const grupo = L.markerClusterGroup({ showCoverageOnHover: false });
  const camadaRecintos = L.layerGroup();
  mapa.addLayer(grupo);
  mapa.addLayer(camadaRecintos);
  const marcadores = new Map();
  let minhaPosicao = null, meuPonto = null;
  const celular = window.matchMedia("(max-width: 760px)");
  const listaVisivel = () => !celular.matches || document.body.classList.contains("lista-aberta");
  // Balão sempre inteiro na tela (no celular, deixa espaço para o botão "Lista")
  const opcoesBalao = () => ({
    maxWidth: celular.matches ? 270 : 320,
    autoPanPaddingTopLeft: [16, 16],
    autoPanPaddingBottomRight: [16, celular.matches ? 80 : 16],
  });

  function popupLeilao(l) {
    const link = linkSeguro(l.link);
    return `<div class="popup">
      <div class="popup-topo"><h3>${esc(l.nome)}</h3>${botaoFav(l)}</div>
      <p><b>${esc(fmtData(l.data))}</b>${l.hora ? " às " + esc(l.hora) : ""}</p>
      <p>${esc(l.cidade)}/${esc(l.uf)}${l.local ? " · " + esc(l.local) : ""}</p>
      ${l.previsto
        ? `<p class="aviso-previsto">Leilão semanal: data prevista pelo dia fixo do recinto.
           ${l.hora ? "" : "Horário não informado. "}Confirme com o recinto antes de ir.</p>`
        : (l.leiloeira ? `<p>Leiloeira: ${esc(l.leiloeira)}</p>` : "")}
      <p>${[l.tipo, l.raca, l.modalidade].filter(Boolean).map(esc).join(" · ")}</p>
      ${link && !l.previsto ? `<p><a href="${esc(link)}" target="_blank" rel="noopener">Ver catálogo / transmissão →</a></p>` : ""}
      ${PRECOS[l.uf] && !ehVirtual(l) ? `<p class="preco-card">💰 ${esc(linhaPreco(l.uf))}</p>` : ""}
      ${botoesAcao(l)}
    </div>`;
  }

  function popupRecinto(r) {
    const site = linkSeguro(r.site);
    return `<div class="popup">
      <div class="popup-topo"><h3>${esc(r.nome)}</h3>${botaoFav(r)}</div>
      <p>Local de leilão · ${esc(r.cidade)}/${esc(r.uf)}</p>
      <p>${r.dias ? "<b>" + esc(r.dias) + "</b>" : "Dias dos leilões não informados: confirme com o local."}</p>
      ${r.telefone ? `<p>Telefone: ${esc(r.telefone)}</p>` : ""}
      ${r.obs ? `<p>${esc(r.obs)}</p>` : ""}
      ${site ? `<p><a href="${esc(site)}" target="_blank" rel="noopener">Site / Instagram →</a></p>` : ""}
      ${botoesAcao(r)}
    </div>`;
  }

  const icone = (classe, tam, ancora) => L.divIcon({
    className: "", html: `<span class="${classe}"></span>`,
    iconSize: [tam, tam], iconAnchor: ancora, popupAnchor: [0, -ancora[1] + 2],
  });
  const ICONES = {
    fisico: icone("pino", 22, [11, 22]),
    virtual: icone("pino pino-virtual", 22, [11, 22]),
    recinto: icone("recinto", 16, [8, 8]),
  };

  itens.forEach((it) => {
    const m = L.marker([it.lat, it.lng], {
      title: it.nome,
      icon: it.recinto ? ICONES.recinto : ehVirtual(it) ? ICONES.virtual : ICONES.fisico,
      zIndexOffset: it.recinto ? -100 : 0,
    }).bindPopup(() => it.recinto ? popupRecinto(it) : popupLeilao(it), opcoesBalao());   // gerado ao abrir: estrela sempre atual
    m.on("click", () => {
      if (celular.matches) {
        // Celular: tocar no pino só mostra o card; a lista não abre nem rola
        if (document.body.classList.contains("lista-aberta")) {
          document.body.classList.remove("lista-aberta");
          $("alternar").textContent = "☰ Lista";
        }
        marcarNaLista(it.id);
      } else {
        destacar(it.id, false);
      }
    });
    marcadores.set(it.id, m);
  });

  // ---------- Filtros ----------
  function preencher(select, valores) {
    [...new Set(valores.filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"))
      .forEach((v) => select.add(new Option(v, v)));
  }
  const soLeiloes = itens.filter((it) => !it.recinto);
  preencher($("f-uf"), itens.map((it) => it.uf));
  preencher($("f-tipo"), soLeiloes.map((l) => l.tipo));
  preencher($("f-modalidade"), soLeiloes.map((l) => l.modalidade));
  RACAS.filter((r) => soLeiloes.some((l) => temRaca(l, r)))
    .forEach((r) => $("f-raca").add(new Option(r, r)));

  let diaEscolhido = "";   // calendário: mostra só um dia
  function filtrados(ignorarDia) {
    const termo = semAcento($("busca").value.trim());
    const uf = $("f-uf").value, tipo = $("f-tipo").value, mod = $("f-modalidade").value, raca = $("f-raca").value;
    const dias = Number($("f-periodo").value);
    const raio = Number($("f-distancia").value);
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const limite = dias ? new Date(hoje.getTime() + dias * 864e5) : null;
    const semVirtuais = $("sem-virtuais").checked;
    const comRecintos = $("com-recintos").checked;
    const soFavoritos = $("so-favoritos").checked;

    let lista = itens.filter((it) => {
      if (soFavoritos && !ehFavorito(it)) return false;
      if (uf && it.uf !== uf) return false;
      if (raio && minhaPosicao && distanciaKm(minhaPosicao, it) > raio) return false;
      if (termo && !semAcento([it.nome, it.cidade, it.uf, it.leiloeira, it.raca, it.local, it.obs]
        .join(" ")).includes(termo)) return false;
      if (diaEscolhido && !ignorarDia && (it.recinto || it.data !== diaEscolhido)) return false;
      if (it.recinto) return comRecintos && !tipo && !mod && !raca && !temData(it);   // local sem data, tipo, raça
      return (!semVirtuais || !ehVirtual(it)) &&
        (!tipo || it.tipo === tipo) &&
        (!mod || it.modalidade === mod) &&
        (!raca || temRaca(it, raca)) &&
        (!limite || paraData(it.data) <= limite);
    });
    if (minhaPosicao) {
      lista = lista.map((it) => ({ ...it, km: distanciaKm(minhaPosicao, it) }))
        .sort((a, b) => a.km - b.km);
    } else {
      lista.sort((a, b) => (a.recinto - b.recinto) ||
        (a.recinto ? a.nome.localeCompare(b.nome, "pt-BR") : 0));   // leilões por data, recintos no fim
    }
    return lista;
  }

  function itemLista(it) {
    const li = document.createElement("li");
    li.dataset.id = it.id;
    if (it.recinto) {
      li.className = "item-recinto";
      li.innerHTML = `${botaoFav(it)}
        <div class="item-data">Local de leilão${it.dias ? " · " + esc(it.dias) : ""}</div>
        <div class="item-nome">${esc(it.nome)}</div>
        <div class="item-info">${esc(it.cidade)}/${esc(it.uf)}${it.km != null ? ` · ${Math.round(it.km)} km` : ""}</div>
        <span class="etiqueta etiqueta-recinto">Sem data</span>`;
    } else {
      li.innerHTML = `${botaoFav(it)}
        <div class="item-data">${esc(fmtData(it.data))}${it.hora ? " · " + esc(it.hora) : ""}</div>
        <div class="item-nome">${esc(it.nome)}</div>
        <div class="item-info">${esc(it.cidade)}/${esc(it.uf)}${it.km != null ? ` · ${Math.round(it.km)} km` : ""}
          ${it.leiloeira ? " · " + esc(it.leiloeira) : ""}</div>
        ${[it.tipo, it.raca, it.modalidade].filter(Boolean).map((t) => `<span class="etiqueta">${esc(t)}</span>`).join("")}
        ${it.previsto ? '<span class="etiqueta etiqueta-recinto">Semanal · data prevista</span>' : ""}`;
    }
    li.addEventListener("click", () => destacar(it.id, true));
    return li;
  }

  function render(enquadrar) {
    const lista = filtrados();
    grupo.clearLayers();
    camadaRecintos.clearLayers();
    grupo.addLayers(lista.filter((it) => !it.recinto).map((it) => marcadores.get(it.id)));
    lista.filter((it) => it.recinto).forEach((it) => camadaRecintos.addLayer(marcadores.get(it.id)));

    const ul = $("lista");
    ul.innerHTML = lista.length ? "" : `<li class="vazio">${$("so-favoritos").checked
      ? "Nenhum favorito com esses filtros. Toque na ☆ de um leilão ou recinto para favoritar."
      : "Nada encontrado com esses filtros."}</li>`;
    lista.forEach((it) => ul.appendChild(itemLista(it)));

    const nL = lista.filter((it) => !it.recinto).length, nR = lista.length - nL;
    const cidades = new Set(lista.map((it) => it.cidade + it.uf)).size;
    desenharCalendario();
    atualizarPrecos();
    $("dia-escolhido").hidden = !diaEscolhido;
    if (diaEscolhido) $("dia-escolhido").querySelector("span").textContent = "Só " + fmtDataLonga(diaEscolhido);
    const raio = Number($("f-distancia").value);
    $("resumo").textContent = `${nL} leilão(ões)${nR ? ` e ${nR} local(is) sem data` : ""} em ${cidades} cidade(s)` +
      (minhaPosicao ? (raio ? ` · até ${raio} km de você` : " · mais próximos primeiro") : "");

    // Ao buscar, trocar de estado ou de distância, leva o mapa até o que foi encontrado
    if (enquadrar && lista.length) {
      const pontos = lista.map((it) => [it.lat, it.lng]);
      if (minhaPosicao && raio) pontos.push([minhaPosicao.lat, minhaPosicao.lng]);
      mapa.fitBounds(L.latLngBounds(pontos), { padding: [40, 40], maxZoom: 11 });
    }
  }

  // Rola só a lista (nunca a página), e só se ela estiver visível
  function rolarAte(li) {
    if (!listaVisivel()) return;
    const caixa = $("painel");
    const c = caixa.getBoundingClientRect(), r = li.getBoundingClientRect();
    const topo = caixa.querySelector("header").offsetHeight;
    if (r.top < c.top + topo) caixa.scrollTop -= c.top + topo - r.top + 8;
    else if (r.bottom > c.bottom) caixa.scrollTop += r.bottom - c.bottom + 8;
  }

  function irPara(id) {
    const m = marcadores.get(id);
    mapa.closePopup();
    if (porId.get(id).recinto) {
      mapa.setView(m.getLatLng(), Math.max(mapa.getZoom(), 12), { animate: false });
      m.openPopup();
    } else {
      grupo.zoomToShowLayer(m, () => m.openPopup());
    }
  }

  // Marca o item na lista sem rolar nada
  function marcarNaLista(id) {
    document.querySelectorAll("#lista li.ativo").forEach((el) => el.classList.remove("ativo"));
    const li = document.querySelector(`#lista li[data-id="${id}"]`);
    if (li) li.classList.add("ativo");
    return li;
  }

  function destacar(id, voar) {
    const li = marcarNaLista(id);
    if (li && !voar) rolarAte(li);
    if (!voar) return;
    if (celular.matches && document.body.classList.contains("lista-aberta")) {
      // No celular: fecha a gaveta primeiro e só depois leva o mapa ao leilão
      document.body.classList.remove("lista-aberta");
      $("alternar").textContent = "☰ Lista";
      setTimeout(() => { mapa.invalidateSize(); irPara(id); }, 280);
    } else {
      irPara(id);
    }
  }

  // Estrela e "Lembrar" (na lista ou no balão do mapa)
  document.addEventListener("click", (e) => {
    const lembrar = e.target.closest("[data-lembrar]");
    if (lembrar) {
      e.preventDefault();
      const it = porId.get(lembrar.dataset.lembrar);
      if (it) baixarAgenda(it);
      return;
    }
    const botao = e.target.closest(".fav");
    if (!botao) return;
    e.stopPropagation();
    const it = porId.get(botao.dataset.id);
    if (!it) return;
    alternarFavorito(it);
    const ativo = ehFavorito(it);
    document.querySelectorAll(`.fav[data-id="${it.id}"]`).forEach((b) => {
      b.classList.toggle("ativo", ativo);
      b.textContent = ativo ? "★" : "☆";
      b.title = ativo ? "Remover dos favoritos" : "Favoritar";
      b.setAttribute("aria-pressed", ativo);
    });
    if ($("so-favoritos").checked && !ativo) render(false);
  }, true);

  // ---------- Minha localização ----------
  function localizar(depois) {
    if (minhaPosicao) return depois();
    if (!navigator.geolocation) return alert("Seu navegador não permite localização.");
    $("perto").textContent = "Localizando…";
    navigator.geolocation.getCurrentPosition((p) => {
      minhaPosicao = { lat: p.coords.latitude, lng: p.coords.longitude };
      meuPonto = L.circleMarker([minhaPosicao.lat, minhaPosicao.lng], { radius: 8, color: "#1f6feb", fillOpacity: .9 })
        .addTo(mapa).bindPopup("Você está aqui");
      $("perto").textContent = "📍 Ordenado por distância";
      depois();
    }, () => {
      $("perto").textContent = "📍 Leilões perto de mim";
      $("f-distancia").value = "";
      alert("Não foi possível obter sua localização. Confira se o site tem permissão de localização.");
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 });
  }

  $("perto").addEventListener("click", () => localizar(() => {
    mapa.setView([minhaPosicao.lat, minhaPosicao.lng], 7);
    render(false);
  }));
  $("f-distancia").addEventListener("input", () => {
    if (!$("f-distancia").value) return render(false);
    localizar(() => render(true));
  });

  let espera;
  $("busca").addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(() => render(true), 350);
  });
  $("f-uf").addEventListener("input", () => render(true));
  $("so-favoritos").addEventListener("input", () => render($("so-favoritos").checked));
  ["f-tipo", "f-modalidade", "f-periodo", "f-raca", "sem-virtuais", "com-recintos"].forEach((id) =>
    $(id).addEventListener("input", () => render(false)));

  $("alternar").addEventListener("click", () => {
    mapa.closePopup();
    document.body.classList.toggle("lista-aberta");
    $("alternar").textContent = document.body.classList.contains("lista-aberta") ? "🗺 Mapa" : "☰ Lista";
  });

  $("rodape").textContent = window.LEILOES_ATUALIZADO
    ? `Dados atualizados em ${paraData(window.LEILOES_ATUALIZADO).toLocaleDateString("pt-BR")}`
    : "Rode scripts/gerar_dados.py para gerar os dados.";

  // ---------- Quadro de preços ----------
  function atualizarPrecos() {
    const ufs = Object.keys(PRECOS);
    if (!ufs.length) { $("precos").hidden = true; return; }
    const uf = $("f-uf").value;
    $("precos").hidden = false;
    $("precos-titulo").textContent = PRECOS[uf]
      ? `💰 Boi gordo ${uf}: ${real(PRECOS[uf].arroba)}/@ ${variacao(PRECOS[uf].variacao_4sem)}`
      : "💰 Preço da arroba do boi gordo";
    $("precos-tabela").innerHTML = ufs.sort().map((u) => `<tr class="${u === uf ? "ativo" : ""}">
        <td>${esc(u)}</td><td>${esc(real(PRECOS[u].arroba))}</td>
        <td class="${PRECOS[u].variacao_4sem > 0 ? "sobe" : PRECOS[u].variacao_4sem < 0 ? "desce" : ""}">${esc(variacao(PRECOS[u].variacao_4sem))}</td>
        <td>${esc(PRECOS[u].semana.replace(/\/\d{4}$/, ""))}</td></tr>`).join("");
  }

  // ---------- Calendário ----------
  const mesVisto = new Date(); mesVisto.setDate(1); mesVisto.setHours(0, 0, 0, 0);
  const isoDia = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  function desenharCalendario() {
    if ($("calendario").hidden) return;
    const porDia = {};
    filtrados(true).forEach((it) => { if (!it.recinto) porDia[it.data] = (porDia[it.data] || 0) + 1; });
    const hoje = isoDia(new Date());
    const ano = mesVisto.getFullYear(), mes = mesVisto.getMonth();
    const nomeMes = mesVisto.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
    $("cal-mes").textContent = nomeMes.charAt(0).toUpperCase() + nomeMes.slice(1);
    let html = ["D", "S", "T", "Q", "Q", "S", "S"].map((d) => `<span class="cal-cab">${d}</span>`).join("");
    html += "<span></span>".repeat(new Date(ano, mes, 1).getDay());
    for (let d = 1; d <= new Date(ano, mes + 1, 0).getDate(); d++) {
      const iso = isoDia(new Date(ano, mes, d)), n = porDia[iso] || 0;
      const classes = ["cal-dia", iso < hoje ? "passado" : "", iso === hoje ? "hoje" : "",
        n ? "tem" : "", iso === diaEscolhido ? "escolhido" : ""].filter(Boolean).join(" ");
      html += `<button type="button" class="${classes}" data-dia="${iso}" ${n ? "" : "disabled"}
        title="${n ? n + " leilão(ões)" : "Sem leilões"}">${d}${n ? `<small>${n}</small>` : ""}</button>`;
    }
    $("cal-grade").innerHTML = html;
  }
  $("ver-calendario").addEventListener("click", () => {
    $("calendario").hidden = !$("calendario").hidden;
    $("ver-calendario").classList.toggle("ativo", !$("calendario").hidden);
    if ($("calendario").hidden) diaEscolhido = "";
    render(false);
  });
  $("cal-ant").addEventListener("click", () => { mesVisto.setMonth(mesVisto.getMonth() - 1); desenharCalendario(); });
  $("cal-prox").addEventListener("click", () => { mesVisto.setMonth(mesVisto.getMonth() + 1); desenharCalendario(); });
  $("cal-grade").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dia]");
    if (!b || b.disabled) return;
    diaEscolhido = diaEscolhido === b.dataset.dia ? "" : b.dataset.dia;
    render(Boolean(diaEscolhido));
  });
  $("dia-escolhido").querySelector("button").addEventListener("click", () => { diaEscolhido = ""; render(false); });

  // ---------- Resumo da semana (para mandar no WhatsApp) ----------
  function textoResumo() {
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const fim = new Date(hoje.getTime() + 7 * 864e5);
    const lista = filtrados(true).filter((it) => !it.recinto && paraData(it.data) < fim)
      .sort((a, b) => (a.data + a.hora).localeCompare(b.data + b.hora));
    const uf = $("f-uf").value;
    const titulo = `🐂 *Leilões de gado${uf ? " em " + uf : ""}*\n${hoje.toLocaleDateString("pt-BR")} a ${
      new Date(fim.getTime() - 864e5).toLocaleDateString("pt-BR")}`;
    if (!lista.length) return titulo + "\n\nNenhum leilão nos próximos 7 dias com esses filtros.";
    const MAX = 40;
    let dia = "";
    const linhas = [titulo];
    lista.slice(0, MAX).forEach((it) => {
      if (it.data !== dia) { dia = it.data; linhas.push("", `*${fmtDataLonga(it.data)}*`); }
      linhas.push(`• ${it.hora ? it.hora + " " : ""}${it.nome} – ${it.cidade}/${it.uf}${ehVirtual(it) ? " (virtual)" : ""}${it.previsto ? " (previsto)" : ""}`);
    });
    if (lista.length > MAX) linhas.push("", `…e mais ${lista.length - MAX}. Escolha um estado para ver todos.`);
    if (PRECOS[uf]) linhas.push("", `💰 ${linhaPreco(uf)}`);
    if (ENDERECO_SITE) linhas.push("", `Mapa completo: ${ENDERECO_SITE}`);
    return linhas.join("\n");
  }
  const dialogo = $("dialogo-resumo");
  $("resumo-semana").addEventListener("click", () => {
    $("resumo-texto").value = textoResumo();
    if (dialogo.showModal) dialogo.showModal(); else dialogo.setAttribute("open", "");
  });
  $("resumo-zap").addEventListener("click", () =>
    window.open(`https://wa.me/?text=${encodeURIComponent($("resumo-texto").value)}`, "_blank", "noopener"));
  $("resumo-copiar").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("resumo-texto").value); }
    catch (e) { $("resumo-texto").select(); document.execCommand("copy"); }
    $("resumo-copiar").textContent = "Copiado ✓";
    setTimeout(() => { $("resumo-copiar").textContent = "Copiar texto"; }, 2000);
  });
  $("resumo-fechar").addEventListener("click", () => {
    if (dialogo.close) dialogo.close(); else dialogo.removeAttribute("open");
  });

  // Link compartilhado (…?busca=Nome do leilão): já abre filtrado
  const buscaInicial = new URLSearchParams(location.search).get("busca");
  if (buscaInicial) $("busca").value = buscaInicial;
  render(Boolean(buscaInicial));

  // ---------- Instalar como app (PWA) ----------
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("sw.js").catch(() => { /* segue sem modo app */ });
  }
  let pedidoInstalar = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    pedidoInstalar = e;
    $("instalar").hidden = false;
  });
  $("instalar").addEventListener("click", async () => {
    if (!pedidoInstalar) return;
    pedidoInstalar.prompt();
    await pedidoInstalar.userChoice;
    pedidoInstalar = null;
    $("instalar").hidden = true;
  });
  window.addEventListener("appinstalled", () => { $("instalar").hidden = true; });
  // iPhone não tem o aviso de instalar: mostra a dica uma vez
  const ehIphone = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.navigator.standalone;
  if (ehIphone) {
    let visto = false;
    try { visto = localStorage.getItem("mapa-leiloes:dica-ios") === "1"; } catch (e) { /* ignora */ }
    if (!visto) {
      $("dica-ios").hidden = false;
      $("dica-ios").querySelector("button").addEventListener("click", () => {
        $("dica-ios").hidden = true;
        try { localStorage.setItem("mapa-leiloes:dica-ios", "1"); } catch (e) { /* ignora */ }
      });
    }
  }
})();
