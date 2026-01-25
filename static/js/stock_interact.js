const socket = io();

// FUNÇÃO: cria o card completo
function criarCardProduto(element) {
  let {
    id,
    nome,
    descricao_breve,
    preco,
    aviso_acabando,
    imagem,
    categoria,
    descricao_completa,
    quantidade_prd,
  } = element;

  const card = document.createElement("div");
  card.className = "bg-blue-900/70 rounded-xl p-4 flex items-center justify-between shadow-lg";

  const infoWrapper = document.createElement("div");
  infoWrapper.className = "flex items-center gap-4";

  const imgEl = document.createElement("img");
  imgEl.src = `/static/imgs/stock/${imagem}`;
  imgEl.alt = nome;
  imgEl.className = "w-20 h-20 rounded-lg object-cover bg-white";

  const textos = document.createElement("div");

  const titulo = document.createElement("h2");
  titulo.className = "text-white text-lg font-semibold";
  titulo.textContent = nome;

  const precoEl = document.createElement("p");
  precoEl.className = "text-green-400 font-bold text-xl";
  precoEl.textContent = `R$ ${preco}`;

  const descBreve = document.createElement("p");
  descBreve.className = "text-slate-300 text-sm";
  descBreve.textContent = descricao_breve;

  const estoque = document.createElement("p");
  estoque.className = "text-slate-400 text-xs";
  estoque.textContent = `Estoque: ${quantidade_prd}`;

  textos.appendChild(titulo);
  textos.appendChild(precoEl);
  textos.appendChild(descBreve);
  textos.appendChild(estoque);

  infoWrapper.appendChild(imgEl);
  infoWrapper.appendChild(textos);

  const acoes = document.createElement("div");
  acoes.className = "flex gap-2";

  const btnEditar = document.createElement("button");
  btnEditar.className = "flex items-center gap-1 bg-sky-500 hover:bg-sky-600 text-white px-4 py-2 rounded-lg text-sm";
  btnEditar.textContent = "Editar";
  btnEditar.addEventListener("click", () => console.log("Editar produto:", id));

  const btnExcluir = document.createElement("button");
  btnExcluir.className = "flex items-center gap-1 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm";
  btnExcluir.textContent = "Excluir";
  btnExcluir.addEventListener("click", () => console.log("Excluir produto:", id));

  acoes.appendChild(btnEditar);
  acoes.appendChild(btnExcluir);

  card.appendChild(infoWrapper);
  card.appendChild(acoes);

  return card;
}

// -------------------
// OBSERVER para product cards
// -------------------
const observerProdutos = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !entry.target.dataset.rendered) {
        const index = Number(entry.target.dataset.index);
        const element = window.produtosEstoque[index];
        if (!element) return;

        const card = criarCardProduto(element);
        entry.target.replaceWith(card);

        entry.target.dataset.rendered = "true";
        observer.unobserve(entry.target);
      }
    });
  },
  {
    root: null,          // viewport principal
    rootMargin: "100px", // começa a carregar antes de entrar
    threshold: 0.1,
  }
);

socket.on("connect", () => {
  socket.emit("get_stock_products", socket.id);
});

document.addEventListener("DOMContentLoaded", () => {
  const elm_container = document.getElementById("product-list-container");

  // Recebe produtos e cria placeholders
  socket.on("recive_stock_products", (data) => {
    let data_json = JSON.parse(data);

    // Guarda globalmente pra referência no Observer
    window.produtosEstoque = data_json;

    elm_container.innerHTML = ""; // limpa antes

    data_json.forEach((element, index) => {
      const placeholder = document.createElement("div");
      placeholder.className = "produto-slot min-h-[100px]  md:min-h-[120px]"; // altura mínima pra observar
      placeholder.dataset.index = index;
      elm_container.appendChild(placeholder);

      observerProdutos.observe(placeholder);
    });
  });
});
