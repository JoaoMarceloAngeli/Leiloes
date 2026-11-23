(function () {
  const $ = (id) => document.getElementById(id);

  // ---------- Utilidades ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const semAcento = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const paraData = (iso) => new Date(iso + "T00:00:00");
  const fmtData = (iso) => paraData(iso).toLocaleDateString("pt-BR",
    { weekday: "short", day: "2-digit", month: "short" });
  const linkSeguro = (u) => /^https?:\/\//i.test(u || "") ? u : "";
  const ehVirtual = (l) => l.modalidade === "Virtual";

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
  let minhaPosicao = null;

  function popupLeilao(l) {
    const link = linkSeguro(l.link);
    return `<div class="popup">
      <div class="popup-topo"><h3>${esc(l.nome)}</h3>${botaoFav(l)}</div>
      <p><b>${esc(fmtData(l.data))}</b>${l.hora ? " às " + esc(l.hora) : ""}</p>
      <p>${esc(l.cidade)}/${esc(l.uf)}${l.local ? " · " + esc(l.local) : ""}</p>
      ${l.leiloeira ? `<p>Leiloeira: ${esc(l.leiloeira)}</p>` : ""}
      <p>${[l.tipo, l.raca, l.modalidade].filter(Boolean).map(esc).join(" · ")}</p>
      ${link ? `<p><a href="${esc(link)}" target="_blank" rel="noopener">Ver catálogo / transmissão →</a></p>` : ""}
    </div>`;
  }

  function popupRecinto(r) {
    const maps = linkSeguro(r.maps), site = linkSeguro(r.site);
    return `<div class="popup">
      <div class="popup-topo"><h3>${esc(r.nome)}</h3>${botaoFav(r)}</div>
      <p>Recinto de leilão · ${esc(r.cidade)}/${esc(r.uf)}</p>
      <p>${r.dias ? "<b>" + esc(r.dias) + "</b>" : "Dias dos leilões não informados: confirme com o recinto."}</p>
      ${r.telefone ? `<p>Telefone: ${esc(r.telefone)}</p>` : ""}
      ${r.obs ? `<p>${esc(r.obs)}</p>` : ""}
      ${site ? `<p><a href="${esc(site)}" target="_blank" rel="noopener">Site / Instagram →</a></p>` : ""}
      ${maps ? `<p><a href="${esc(maps)}" target="_blank" rel="noopener">Abrir no Google Maps →</a></p>` : ""}
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
    }).bindPopup(() => it.recinto ? popupRecinto(it) : popupLeilao(it));   // gerado ao abrir: estrela sempre atual
    m.on("click", () => destacar(it.id, false));
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

  function filtrados() {
    const termo = semAcento($("busca").value.trim());
    const uf = $("f-uf").value, tipo = $("f-tipo").value, mod = $("f-modalidade").value;
    const dias = Number($("f-periodo").value);
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const limite = dias ? new Date(hoje.getTime() + dias * 864e5) : null;
    const semVirtuais = $("sem-virtuais").checked;
    const comRecintos = $("com-recintos").checked;
    const soFavoritos = $("so-favoritos").checked;

    let lista = itens.filter((it) => {
      if (soFavoritos && !ehFavorito(it)) return false;
      if (uf && it.uf !== uf) return false;
      if (termo && !semAcento([it.nome, it.cidade, it.uf, it.leiloeira, it.raca, it.local, it.obs]
        .join(" ")).includes(termo)) return false;
      if (it.recinto) return comRecintos && !tipo && !mod;   // recinto não tem data, tipo nem modalidade
      return (!semVirtuais || !ehVirtual(it)) &&
        (!tipo || it.tipo === tipo) &&
        (!mod || it.modalidade === mod) &&
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
        <div class="item-data">Recinto${it.dias ? " · " + esc(it.dias) : ""}</div>
        <div class="item-nome">${esc(it.nome)}</div>
        <div class="item-info">${esc(it.cidade)}/${esc(it.uf)}${it.km != null ? ` · ${Math.round(it.km)} km` : ""}</div>
        <span class="etiqueta etiqueta-recinto">Recinto de leilão</span>`;
    } else {
      li.innerHTML = `${botaoFav(it)}
        <div class="item-data">${esc(fmtData(it.data))}${it.hora ? " · " + esc(it.hora) : ""}</div>
        <div class="item-nome">${esc(it.nome)}</div>
        <div class="item-info">${esc(it.cidade)}/${esc(it.uf)}${it.km != null ? ` · ${Math.round(it.km)} km` : ""}
          ${it.leiloeira ? " · " + esc(it.leiloeira) : ""}</div>
        ${[it.tipo, it.raca, it.modalidade].filter(Boolean).map((t) => `<span class="etiqueta">${esc(t)}</span>`).join("")}`;
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
    $("resumo").textContent = `${nL} leilão(ões)${nR ? ` e ${nR} recinto(s)` : ""} em ${cidades} cidade(s)` +
      (minhaPosicao ? " · mais próximos primeiro" : "");

    // Ao buscar ou trocar de estado, leva o mapa até o que foi encontrado
    if (enquadrar && lista.length) {
      mapa.fitBounds(L.latLngBounds(lista.map((it) => [it.lat, it.lng])), { padding: [40, 40], maxZoom: 11 });
    }
  }

  function destacar(id, voar) {
    document.querySelectorAll("#lista li.ativo").forEach((el) => el.classList.remove("ativo"));
    const li = document.querySelector(`#lista li[data-id="${id}"]`);
    if (li) { li.classList.add("ativo"); if (!voar) li.scrollIntoView({ block: "nearest" }); }
    if (voar) {
      const m = marcadores.get(id);
      if (porId.get(id).recinto) {
        mapa.setView(m.getLatLng(), Math.max(mapa.getZoom(), 12));
        m.openPopup();
      } else {
        grupo.zoomToShowLayer(m, () => m.openPopup());
      }
      document.body.classList.remove("lista-aberta");
    }
  }

  // Estrela (na lista ou no balão do mapa)
  document.addEventListener("click", (e) => {
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

  let espera;
  $("busca").addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(() => render(true), 350);
  });
  $("f-uf").addEventListener("input", () => render(true));
  $("so-favoritos").addEventListener("input", () => render($("so-favoritos").checked));
  ["f-tipo", "f-modalidade", "f-periodo", "sem-virtuais", "com-recintos"].forEach((id) =>
    $(id).addEventListener("input", () => render(false)));

  $("perto").addEventListener("click", () => {
    if (!navigator.geolocation) return alert("Seu navegador não permite localização.");
    $("perto").textContent = "Localizando…";
    navigator.geolocation.getCurrentPosition((p) => {
      minhaPosicao = { lat: p.coords.latitude, lng: p.coords.longitude };
      L.circleMarker([minhaPosicao.lat, minhaPosicao.lng], { radius: 8, color: "#1f6feb", fillOpacity: .9 })
        .addTo(mapa).bindPopup("Você está aqui");
      mapa.setView([minhaPosicao.lat, minhaPosicao.lng], 7);
      $("perto").textContent = "📍 Ordenado por distância";
      render(false);
    }, () => {
      $("perto").textContent = "📍 Leilões perto de mim";
      alert("Não foi possível obter sua localização.");
    });
  });

  $("alternar").addEventListener("click", () => document.body.classList.toggle("lista-aberta"));

  $("rodape").textContent = window.LEILOES_ATUALIZADO
    ? `Dados atualizados em ${paraData(window.LEILOES_ATUALIZADO).toLocaleDateString("pt-BR")}`
    : "Rode scripts/gerar_dados.py para gerar os dados.";

  render(false);
})();
