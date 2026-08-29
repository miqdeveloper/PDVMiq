const socket = io();

document.addEventListener("DOMContentLoaded", () => {
  socket.emit("load_ordens", socket.id);

  const container = document.getElementById("item_container");
  const totalAbertasEl = document.getElementById("total_abertas");
  const totalFechadasEl = document.getElementById("total_fechadas");
  const searchInput = document.getElementById("search_os");
  const modalOs = document.getElementById("modal_os");
  const formOs = document.getElementById("form_os");
  const modalTitle = document.getElementById("modal_os_title");

  let osData = [];
  let editandoId = null;

  // Function to render HTML for a single OS item
  const item_div_render = (item) => {
    const {
      id,
      cliente = "",
      telefone = "",
      aparelho = "",
      problema = "",
      observacoes = "",
      status = "aberta",
      quem_abriu = "",
      data_abertura = "",
      data_fechamento = ""
    } = item;

    const isFechada = status === "fechada";
    const statusBg = isFechada ? "bg-green-500/20 text-green-400 border-green-500/30" : "bg-red-500/20 text-red-400 border-red-500/30";
    const statusDot = isFechada ? "bg-green-500" : "bg-red-500";

    return `
      <div class="w-full max-w-5xl mx-auto bg-gradient-to-r from-slate-900 to-slate-800 
          rounded-xl p-5 flex flex-col md:flex-row md:items-center 
          justify-between gap-4 shadow-lg border border-slate-700/50">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center text-indigo-400 font-bold text-lg">
            OS
          </div>
          <div>
            <div class="flex items-center gap-2">
              <p class="text-white font-semibold text-base">${cliente || "Cliente sem nome"}</p>
              <span class="text-xs px-2.5 py-0.5 rounded-full border ${statusBg} font-medium flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full ${statusDot}"></span>
                ${status.toUpperCase()}
              </span>
            </div>
            <p class="text-slate-300 text-sm mt-0.5">
              📱 Telefone: <span class="text-white font-medium">${telefone || "-"}</span>
            </p>
            <p class="text-slate-400 text-xs mt-0.5">
              📅 Abertura: ${data_abertura || "-"} ${data_fechamento ? ` • Fechamento: ${data_fechamento}` : ""} ${quem_abriu ? ` • Por: ${quem_abriu}` : ""}
            </p>
          </div>
        </div>

        <div class="flex flex-col gap-1 text-sm max-w-md">
          <div>
            <span class="text-slate-400 text-xs block">Aparelho / Modelo</span>
            <span class="text-white font-semibold">${aparelho || "-"}</span>
          </div>
          <div>
            <span class="text-slate-400 text-xs block">Defeito / Problema</span>
            <span class="text-slate-200 text-xs">${problema || "-"}</span>
          </div>
          ${observacoes ? `<div><span class="text-slate-400 text-xs block">Obs</span><span class="text-slate-400 text-xs italic">${observacoes}</span></div>` : ""}
        </div>

        <div class="flex items-center gap-2">
          <button 
            data-id="${id}" data-action="toggle"
            class="btn-os-action px-3 py-1.5 rounded-lg border border-slate-600 text-xs text-white hover:bg-slate-700 transition flex items-center gap-1">
            ${isFechada ? "🔓 Reabrir" : "✅ Fechar"}
          </button>
          <button 
            data-id="${id}" data-action="edit"
            class="btn-os-action px-3 py-1.5 rounded-lg bg-indigo-600/80 text-xs text-white hover:bg-indigo-600 transition">
            ✏️ Editar
          </button>
          <button 
            data-id="${id}" data-action="delete"
            class="btn-os-action px-3 py-1.5 rounded-lg bg-red-600/80 text-xs text-white hover:bg-red-600 transition">
            🗑️ Apagar
          </button>
        </div>
      </div>
    `;
  };

  // IntersectionObserver for lazy slot rendering
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const target = entry.target;
        if (entry.isIntersecting && !target.dataset.rendered) {
          const index = Number(target.dataset.index);
          const item = osData[index];
          if (!item) return;

          target.innerHTML = item_div_render(item);
          target.dataset.rendered = "true";
          target.classList.add("rendered");
          observer.unobserve(target);
        }
      });
    },
    {
      root: container,
      rootMargin: "200px",
      threshold: 0.1,
    }
  );

  function populateSlots(data) {
    if (!container) return;
    container.innerHTML = "";

    if (!data || data.length === 0) {
      container.innerHTML = `<div class="text-center py-12 text-slate-400 text-sm">Nenhuma ordem de serviço encontrada.</div>`;
      return;
    }

    data.forEach((item, index) => {
      const placeholder = document.createElement("div");
      placeholder.className = "os-slot";
      placeholder.dataset.index = index;
      container.appendChild(placeholder);
      observer.observe(placeholder);
    });
  }

  // Receive data from socket
  socket.on("recive_ordens", (data) => {
    let list = data;
    if (typeof list === "string") {
      try { list = JSON.parse(list); } catch (e) { list = []; }
    }
    if (!Array.isArray(list)) list = [];
    osData = list;
    populateSlots(osData);
  });

  socket.on("ordens_counters", (data) => {
    let counters = data;
    if (typeof counters === "string") {
      try { counters = JSON.parse(counters); } catch (e) { counters = { abertas: 0, fechadas: 0 }; }
    }
    if (totalAbertasEl) totalAbertasEl.textContent = counters.abertas || 0;
    if (totalFechadasEl) totalFechadasEl.textContent = counters.fechadas || 0;
  });

  // Event Delegation for action buttons click
  if (container) {
    container.addEventListener("click", (ev) => {
      const btn = ev.target.closest(".btn-os-action");
      if (!btn) return;

      const id = btn.dataset.id;
      const action = btn.dataset.action;
      const item = osData.find((o) => o.id === id);

      if (action === "toggle") {
        socket.emit("toggle_os_status", { id });
      } else if (action === "delete") {
        if (confirm("Tem certeza que deseja excluir esta ordem de serviço?")) {
          socket.emit("delete_os", { id });
        }
      } else if (action === "edit" && item) {
        abrirModalEditarOs(item);
      }
    });
  }

  // Search input filter
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const term = e.target.value.trim().toLowerCase();
      if (!term) {
        populateSlots(osData);
        return;
      }
      const filtered = osData.filter(
        (o) =>
          (o.cliente || "").toLowerCase().includes(term) ||
          (o.telefone || "").toLowerCase().includes(term) ||
          (o.aparelho || "").toLowerCase().includes(term) ||
          (o.problema || "").toLowerCase().includes(term)
      );
      populateSlots(filtered);
    });
  }

  // Modal helpers
  window.abrirModalNovaOs = function () {
    editandoId = null;
    if (modalTitle) modalTitle.innerText = "Nova Ordem de Serviço";
    document.getElementById("os_id_edit").value = "";
    document.getElementById("os_cliente").value = "";
    document.getElementById("os_telefone").value = "";
    document.getElementById("os_aparelho").value = "";
    document.getElementById("os_problema").value = "";
    document.getElementById("os_observacoes").value = "";
    if (modalOs) modalOs.classList.remove("hidden");
  };

  function abrirModalEditarOs(item) {
    editandoId = item.id;
    if (modalTitle) modalTitle.innerText = "Editar Ordem de Serviço";
    document.getElementById("os_id_edit").value = item.id || "";
    document.getElementById("os_cliente").value = item.cliente || "";
    document.getElementById("os_telefone").value = item.telefone || "";
    document.getElementById("os_aparelho").value = item.aparelho || "";
    document.getElementById("os_problema").value = item.problema || "";
    document.getElementById("os_observacoes").value = item.observacoes || "";
    if (modalOs) modalOs.classList.remove("hidden");
  }

  window.fecharModalOs = function () {
    if (modalOs) modalOs.classList.add("hidden");
    editandoId = null;
  };

  if (formOs) {
    formOs.addEventListener("submit", (e) => {
      e.preventDefault();
      const payload = {
        cliente: document.getElementById("os_cliente").value.trim(),
        telefone: document.getElementById("os_telefone").value.trim(),
        aparelho: document.getElementById("os_aparelho").value.trim(),
        problema: document.getElementById("os_problema").value.trim(),
        observacoes: document.getElementById("os_observacoes").value.trim(),
      };

      if (editandoId) {
        payload.id = editandoId;
        socket.emit("edit_os", payload);
      } else {
        socket.emit("open_os", payload);
      }

      window.fecharModalOs();
    });
  }

  // Fallback for browsers without IntersectionObserver
  if (!("IntersectionObserver" in window)) {
    socket.on("recive_ordens", (data) => {
      container.innerHTML = "";
      (data || []).forEach((item) => {
        const slot = document.createElement("div");
        slot.innerHTML = item_div_render(item);
        container.appendChild(slot);
      });
    });
  }
});
