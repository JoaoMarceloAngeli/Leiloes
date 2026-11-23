// Mapa de Leilões de Gado, sobre o Google Maps (Maps JavaScript API).
// A chave e o Map ID vêm de config.js (veja config.exemplo.js).
(function () {
  const $ = (id) => document.getElementById(id);
  const cfg = window.CONFIG_MAPA || {};

  if (!cfg.chave || cfg.chave.startsWith("COLE_AQUI")) {
    $("mapa").innerHTML = `<div class="aviso-mapa">
      <h2>Falta a chave do Google Maps</h2>
      <p>Copie <code>site/config.exemplo.js</code> para <code>site/config.js</code>, preencha a chave
      e o Map ID e abra o site por <code>http://localhost:8000</code> (veja o README).</p></div>`;
    $("resumo").textContent = "Mapa não carregado: falta configurar a chave.";
    return;
  }

  // Carrega a Maps JavaScript API e chama iniciar() quando estiver pronta.
  window.__iniciarMapa = iniciar;
  const s = document.createElement("script");
  s.src = "https://maps.googleapis.com/maps/api/js?" + new URLSearchParams({
    key: cfg.chave, v: "weekly", loading: "async", language: "pt-BR", region: "BR",
    libraries: "marker,places", callback: "__iniciarMapa",
  });
  s.async = true;
  s.onerror = () => { $("resumo").textContent = "Não foi possível carregar o Google Maps."; };
  document.head.appendChild(s);

  // ---------- Utilidades ----------
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const semAcento = (v) => String(v).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
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

  function elemento(classe) {
    const el = document.createElement("span");
    el.className = classe;
    return el;
  }

  function popupLeilao(l) {
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

  // Recinto: os dados do Google (nome, endereço) só são buscados quando a pessoa clica.
  function popupRecinto(r, g) {
    const nome = (g && g.displayName) || r.nome || "Recinto de leilão";
    const maps = linkSeguro((g && g.googleMapsURI) || r.maps), site = linkSeguro(r.site);
    return `<div class="popup">
      <h3>${esc(nome)}</h3>
      <p>Recinto de leilão · ${esc(r.cidade)}/${esc(r.uf)}</p>
      ${g && g.formattedAddress ? `<p>${esc(g.formattedAddress)}</p>` : ""}
      <p>${r.dias ? "<b>" + esc(r.dias) + "</b>" : "Dias dos leilões não informados: confirme com o recinto."}</p>
      ${r.telefone ? `<p>Telefone: ${esc(r.telefone)}</p>` : ""}
      ${r.obs ? `<p>${esc(r.obs)}</p>` : ""}
      ${site ? `<p><a href="${esc(site)}" target="_blank" rel="noopener">Site / Instagram →</a></p>` : ""}
      ${maps ? `<p><a href="${esc(maps)}" target="_blank" rel="noopener">Abrir no Google Maps →</a></p>` : ""}
    </div>`;
  }

  async function iniciar() {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    const { Place } = await google.maps.importLibrary("places");

    const leiloes = (window.LEILOES || []).map((l, i) => ({ ...l, id: i }));
    const mapa = new google.maps.Map($("mapa"), {
      center: { lat: -14.5, lng: -52 }, zoom: 4, mapId: cfg.mapId || "DEMO_MAP_ID",
      mapTypeControl: true, streetViewControl: false, fullscreenControl: false,
      gestureHandling: "greedy",
    });
    const janela = new google.maps.InfoWindow();
    const marcadores = new Map();
    let minhaPosicao = null, meuMarcador = null;

    leiloes.forEach((l) => {
      const m = new AdvancedMarkerElement({
        position: { lat: l.lat, lng: l.lng }, title: l.nome,
        content: elemento("pino" + (ehVirtual(l) ? " pino-virtual" : "")),
      });
      m.addListener("click", () => { abrir(l, m); destacar(l.id, false); });
      marcadores.set(l.id, m);
    });
    const grupo = new markerClusterer.MarkerClusterer({ map: mapa, markers: [] });

    function abrir(l, m) {
      janela.setContent(popupLeilao(l));
      janela.open({ map: mapa, anchor: m });
    }

    // ---------- Recintos ----------
    const recintos = [];
    await Promise.all((window.RECINTOS || []).map(async (r) => {
      let posicao = r.lat != null && r.lng != null ? { lat: r.lat, lng: r.lng } : null;
      let lugar = null;
      if (r.place_id) {
        lugar = new Place({ id: r.place_id });
        // Normalmente a localização já vem guardada (até 30 dias, renovada pelo atualizar.py).
        // Só consulta o Google na abertura se ela venceu; nome e endereço só no clique.
        if (!posicao) {
          try {
            await lugar.fetchFields({ fields: ["location"] });
            posicao = lugar.location;
          } catch (e) { console.warn("Recinto não carregado:", r.place_id, e); }
        }
      }
      if (!posicao) return;
      const m = new AdvancedMarkerElement({
        position: posicao, title: r.nome || "Recinto de leilão",
        content: elemento("recinto"), zIndex: -1,
      });
      let detalhes = null;
      m.addListener("click", async () => {
        janela.setContent(popupRecinto(r, detalhes));
        janela.open({ map: mapa, anchor: m });
        if (lugar && !detalhes) {
          try {
            await lugar.fetchFields({ fields: ["displayName", "formattedAddress", "googleMapsURI"] });
            detalhes = lugar;
            janela.setContent(popupRecinto(r, detalhes));
          } catch (e) { console.warn(e); }
        }
      });
      recintos.push(m);
    }));
    const mostrarRecintos = () => recintos.forEach((m) => { m.map = $("com-recintos").checked ? mapa : null; });
    $("com-recintos").addEventListener("input", mostrarRecintos);
    mostrarRecintos();

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
      grupo.clearMarkers();
      grupo.addMarkers(lista.map((l) => marcadores.get(l.id)));

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
        const m = marcadores.get(id), l = leiloes[id];
        mapa.panTo(m.position);
        mapa.setZoom(Math.max(mapa.getZoom(), 12));
        // Espera o agrupamento se desfazer para o pino estar visível
        google.maps.event.addListenerOnce(mapa, "idle", () => abrir(l, m));
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
        if (meuMarcador) meuMarcador.map = null;
        meuMarcador = new AdvancedMarkerElement({
          map: mapa, position: minhaPosicao, title: "Você está aqui", content: elemento("voce"),
        });
        mapa.setCenter(minhaPosicao);
        mapa.setZoom(7);
        $("perto").textContent = "📍 Ordenado por distância";
        render();
      }, () => {
        $("perto").textContent = "📍 Leilões perto de mim";
        alert("Não foi possível obter sua localização.");
      });
    });

    $("rodape").textContent = window.LEILOES_ATUALIZADO
      ? `Dados atualizados em ${paraData(window.LEILOES_ATUALIZADO).toLocaleDateString("pt-BR")}`
      : "Rode scripts/gerar_dados.py para gerar os dados.";

    render();
  }

  $("alternar").addEventListener("click", () => document.body.classList.toggle("lista-aberta"));
})();
