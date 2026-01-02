const socket = io();
socket.emit("get_sells_history", socket.id);
// data_r = null;

document.addEventListener("DOMContentLoaded", () => {

  let calc_total = (data) => {
    total = 0;

    data.forEach((item) => {
      total += Number(item.total_venda);
    });

    total  = total.toFixed(2).replace(".", ",");
    return total;

  }

  socket.emit("get_sells_history", socket.id);

  const container = document.getElementById("item_container");
  const sub_div = document.getElementById("sub_h2");
  const data_div = document.getElementById("data_now");
  const total_seels_ = document.getElementById("total_sells");

  let sellData = [];

  // Helper: gera o HTML do item (mantive sua função)
  const item_div_render = (item) => {
    let {
      id,
      total_venda,
      quantidade_itens,
      itens_venda,
      tipo_pagamento,
      data_venda,
      hora_venda,
      quem_vendeu,
    } = item;

    return `
      <div class="w-full max-w-5xl mx-auto bg-gradient-to-r from-slate-900 to-slate-800 
          rounded-xl p-5 flex flex-col md:flex-row md:items-center 
          justify-between gap-4 shadow-lg">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
            <span class="text-white font-bold">#</span>
          </div>
          <div>
            <p class="text-white font-semibold text-sm">
              Compra <span class="text-indigo-400">#${id}</span>
            </p>
            <p class="text-slate-300 text-[18px]">
              Vendedor: <span class="text-white">${quem_vendeu}</span>
            </p>
            <p class="text-slate-400 text-[16px]">
              Data: ${data_venda} • ${hora_venda}
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-6 text-sm">
          <div>
            <p class="text-slate-400 text-xs">Itens</p>
            <p class="text-white font-semibold">${quantidade_itens}</p>
          </div>

          <div>
            <p class="text-slate-400 text-xs">Total</p>
            <p class="text-white font-semibold">
              R$ ${Number(total_venda).toFixed(2).replace(".", ",")}
            </p>
          </div>

          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-green-500"></span>
            <span class="text-green-400 font-medium">
              ${tipo_pagamento.toUpperCase()}
            </span>
          </div>
        </div>

        <div>
          <button 
            data-id="${id}"
            class="ver-detalhes px-4 py-2 rounded-full border border-slate-500 text-white text-sm hover:bg-slate-700 transition">
            Ver detalhes
          </button>
        </div>
      </div>
    `;
  };

  // IntersectionObserver — OBSERVE: container precisa ter altura e overflow
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const target = entry.target;
        if (entry.isIntersecting && !target.dataset.rendered) {
          const index = Number(target.dataset.index);
          const item = sellData[index];

          if (!item) return; // sanity check

          // Injeta HTML e marca como renderizado
          target.innerHTML = item_div_render(item);
          target.dataset.rendered = "true";

          // anima
          target.classList.add("rendered");

          // não precisa mais observar este alvo
          observer.unobserve(target);
        }
      });
    },
    {
      root: container, // observa dentro do scroll do container
      rootMargin: "200px", // renderiza um pouco antes de aparecer
      threshold: 0.5,
    }
  );

  
  
  // Recebe dados do servidor
  socket.on("recive_seels_h", (data) => {

    if (!Array.isArray(data)) {
      console.error("recive_seels_h expected array, got:", data);
      return;
    }

    sellData = data;

    container.innerHTML = "";

    // cria placeholders com espaço e index
    data.forEach((item, index) => {

      const placeholder = document.createElement("div");
      placeholder.className = "sell-slot";
      placeholder.dataset.index = index;
      // min-height definido via CSS, garantia extra:
      // placeholder.style.minHeight = "120px";
      container.appendChild(placeholder);
      observer.observe(placeholder);
    });

    console.info("placeholders created:", data.length);
    console.log(data);
    console.log(calc_total(data))
    total_seels_.textContent = calc_total(data)
    
  });

  
  // Delegação de evento: botão "Ver detalhes"
  container.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".ver-detalhes");
    if (!btn) return;
    const id = btn.dataset.id;
    // lógica ao clicar (ex.: abrir modal, emitir socket, etc.)
    console.log("Ver detalhes click id=", id);
    // Exemplo: emitir evento para servidor
    // socket.emit("request_sell_details", id);
  });

  // --- Data display (mantive seu bloco) ---
  let optionsBR = {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };

  let dateNow = new Date();
  const data_obj = dateNow.toLocaleString("pt-BR", optionsBR);
  const f_date = data_obj.split(", ")[0];

  sub_div.textContent = ` Lista de vendas do dia: ${f_date}`;
  data_div.textContent = `Vendas do Dia: ${f_date}`;

  // DEBUG — se quiser forçar renderizar os primeiros N itens caso não haja support
  if (!("IntersectionObserver" in window)) {
    console.warn(
      "IntersectionObserver não suportado — renderizando primeiros 20 items"
    );
    
    socket.on("recive_seels_h", (data) => {
      container.innerHTML = "";
      (data || []).slice(0, 20).forEach((item) => {
        const wrapper = document.createElement("div");
        wrapper.innerHTML = item_div_render(item);
        container.appendChild(wrapper);
      });
    });
  }
});
