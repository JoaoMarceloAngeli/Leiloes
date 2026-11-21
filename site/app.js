(function () {
  const leiloes = (window.LEILOES || []).map((l, i) => ({ ...l, id: i }));
  const $ = (id) => document.getElementById(id);

  // ---------- Mapa ----------
  const mapa = L.map("mapa", { zoomControl: true }).setView([-14.5, -52], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);
  const grupo = L.markerClusterGroup({ showCoverageOnHover: false });
  mapa.addLayer(grupo);
  const marcadores = new Map();
  let minhaPosicao = null;

  // ---------- Utilidades ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const semAcento = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const paraData = (iso) => new Date(iso + "T00:00:00");
  const fmtData = (iso) => paraData(iso).toLocaleDateString("pt-BR",
    { weekday: "short", day: "2-digit", month: "short" });
  const linkSeguro = (u) => /^https?:\/\//i.test(u) ? u : "";

  function distanciaKm(a, b) {
    const r = Math.PI / 180, R = 6371;
    const dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
    const h = Math.sin(dLat / 2) ** 2 +
      Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function popupHtml(l) {
    const link = linkSeguro(l.link);
    return `<div class="popup">
      <h3>${esc(l.nome)}</h3>
      <p><b>${esc(fmtData(l.data))}</b>${l.hora ? " às " + esc(l.hora) : ""}</p>
      <p>${esc(l.cidade)}/${esc(l.uf)}${l.local ? " · " + esc(l.local) : ""}</p>
      ${l.leiloeira ? `<p>Leiloeira: ${esc(l.leiloeira)}</p>` : ""}
      <p>${[l.tipo, l.raca, l.modalidade].filter(Boolean).map(esc).join(" · ")}</p>
      ${link ? `<p><a href="${esc(link)}" target="_blank" rel="noopener">Ver catálogo / transmissão →</a></p>` : ""}
    </div>`;
  }

  // Leilões na mesma cidade ficam no mesmo ponto; o cluster os separa ao clicar.
  const ehVirtual = (l) => l.modalidade === "Virtual";
  const icone = (virtual) => L.divIcon({
    className: "",
    html: `<span class="pino ${virtual ? "pino-virtual" : ""}"></span>`,
    iconSize: [22, 22], iconAnchor: [11, 22], popupAnchor: [0, -20],
  });
  const ICONES = { fisico: icone(false), virtual: icone(true) };

  leiloes.forEach((l) => {
    const m = L.marker([l.lat, l.lng], {
      title: l.nome, icon: ehVirtual(l) ? ICONES.virtual : ICONES.fisico,
    }).bindPopup(popupHtml(l));
    m.on("click", () => destacar(l.id, false));
    marcadores.set(l.id, m);
  });

  // ---------- Filtros ----------
  function preencher(select, valores) {
    [...new Set(valores.filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"))
      .forEach((v) => select.add(new Option(v, v)));
  }
  preencher($("f-uf"), leiloes.map((l) => l.uf));
  preencher($("f-tipo"), leiloes.map((l) => l.tipo));
  preencher($("f-modalidade"), leiloes.map((l) => l.modalidade));

  function filtrados() {
    const termo = semAcento($("busca").value.trim());
    const uf = $("f-uf").value, tipo = $("f-tipo").value, mod = $("f-modalidade").value;
    const dias = Number($("f-periodo").value);
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const limite = dias ? new Date(hoje.getTime() + dias * 864e5) : null;

    const semVirtuais = $("sem-virtuais").checked;
    let lista = leiloes.filter((l) =>
      (!semVirtuais || !ehVirtual(l)) &&
      (!uf || l.uf === uf) &&
      (!tipo || l.tipo === tipo) &&
      (!mod || l.modalidade === mod) &&
      (!limite || paraData(l.data) <= limite) &&
      (!termo || semAcento([l.nome, l.cidade, l.uf, l.leiloeira, l.raca, l.local].join(" ")).includes(termo))
    );
    if (minhaPosicao) {
      lista = lista.map((l) => ({ ...l, km: distanciaKm(minhaPosicao, l) }))
        .sort((a, b) => a.km - b.km);
    }
    return lista;
  }

  function render() {
    const lista = filtrados();
    grupo.clearLayers();
    grupo.addLayers(lista.map((l) => marcadores.get(l.id)));

    const ul = $("lista");
    ul.innerHTML = lista.length ? "" :
      '<li class="vazio">Nenhum leilão encontrado com esses filtros.</li>';
    lista.forEach((l) => {
      const li = document.createElement("li");
      li.dataset.id = l.id;
      li.innerHTML = `
        <div class="item-data">${esc(fmtData(l.data))}${l.hora ? " · " + esc(l.hora) : ""}</div>
        <div class="item-nome">${esc(l.nome)}</div>
        <div class="item-info">${esc(l.cidade)}/${esc(l.uf)}${l.km != null ? ` · ${Math.round(l.km)} km` : ""}
          ${l.leiloeira ? " · " + esc(l.leiloeira) : ""}</div>
        ${[l.tipo, l.raca, l.modalidade].filter(Boolean).map((t) => `<span class="etiqueta">${esc(t)}</span>`).join("")}`;
      li.addEventListener("click", () => destacar(l.id, true));
      ul.appendChild(li);
    });

    const cidades = new Set(lista.map((l) => l.cidade + l.uf)).size;
    $("resumo").textContent =
      `${lista.length} leilão(ões) em ${cidades} cidade(s)` + (minhaPosicao ? " · mais próximos primeiro" : "");
  }

  function destacar(id, voar) {
    document.querySelectorAll("#lista li.ativo").forEach((el) => el.classList.remove("ativo"));
    const li = document.querySelector(`#lista li[data-id="${id}"]`);
    if (li) { li.classList.add("ativo"); if (!voar) li.scrollIntoView({ block: "nearest" }); }
    if (voar) {
      const m = marcadores.get(id);
      grupo.zoomToShowLayer(m, () => m.openPopup());
      document.body.classList.remove("lista-aberta");
    }
  }

  ["busca", "f-uf", "f-tipo", "f-modalidade", "f-periodo", "sem-virtuais"].forEach((id) =>
    $(id).addEventListener("input", render));

  $("perto").addEventListener("click", () => {
    if (!navigator.geolocation) return alert("Seu navegador não permite localização.");
    $("perto").textContent = "Localizando…";
    navigator.geolocation.getCurrentPosition((p) => {
      minhaPosicao = { lat: p.coords.latitude, lng: p.coords.longitude };
      L.circleMarker([minhaPosicao.lat, minhaPosicao.lng], { radius: 8, color: "#1f6feb", fillOpacity: .9 })
        .addTo(mapa).bindPopup("Você está aqui");
      mapa.setView([minhaPosicao.lat, minhaPosicao.lng], 7);
      $("perto").textContent = "📍 Ordenado por distância";
      render();
    }, () => {
      $("perto").textContent = "📍 Leilões perto de mim";
      alert("Não foi possível obter sua localização.");
    });
  });

  $("alternar").addEventListener("click", () => document.body.classList.toggle("lista-aberta"));

  $("rodape").textContent = window.LEILOES_ATUALIZADO
    ? `Dados atualizados em ${paraData(window.LEILOES_ATUALIZADO).toLocaleDateString("pt-BR")}`
    : "Rode scripts/gerar_dados.py para gerar os dados.";

  render();
})();
