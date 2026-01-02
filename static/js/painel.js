const socket = io();

// src="{{ url_for('static', filename='imgs/grelhos_foto.jpg') }}"

sacola = [];
total_ = 0;

// Função para criar os blocos de itens a partir de um array de objetos JSON

calc_total = () => {
  total_ = 0;

  sacola.forEach((intem) => {
    // console.log(intem.preco)
    total_ += Number(intem.preco);
  });

  return total_;
};

create_items = (obj_arr) => {

  manipuleCart = (arg, index) => {
    let item_l = document.getElementById("sacola_item_total");
    let item_click = obj_arr[Number(index)];

    const total_real = document.getElementById("total_real");
    total_real.innerHTML = "";

    // console.log(arg.trim() === "pop", arg.trim() === "push", arg)

    if (arg.trim() === "push") {
      sacola.push(item_click);
    }

    if (arg.trim() === "pop") {
      let id = item_click.id;
      let index = sacola.findIndex((prod) => prod.id === id);

      if (index !== -1) {
        // remove 1 elemento a partir desse índice
        sacola.splice(index, 1);
      }
    }

    total_real.innerHTML = ` R$ ${calc_total().toFixed(2)}`;
    item_l.innerHTML = sacola.length;
  };


  const itemListContainer = document.getElementById("list_items");
  const qt_i = document.getElementById("qt_item_");
  // String para acumular o HTML de todos os novos itens
  let allItemsHtml = "";
  itemListContainer.innerHTML = allItemsHtml;
  let qt_itens = obj_arr.length;
  qt_i.textContent = `itens ${qt_itens}`;

  obj_arr.forEach((item, index) => {
    // Desestruturação dos dados do objeto JSON para facilitar o uso
    console.log(item)
    const { id, nome, descricao, preco, imagem, categoria, quantidade_prd } = item;
    // Formato o preço, garantindo que o R$ esteja presente,
    // caso o JSON não o forneça (exemplo simples)
    const precoFormatado = preco.startsWith("R$") ? preco : `R$${preco}`;

    // ----------------------------------------------------
    // Template String (com backticks `) para gerar o HTML
    // ----------------------------------------------------
    // Este template reproduz a estrutura HTML/Tailwind que você forneceu,
    // mas injeta os dados do JSON usando ${variavel}.
    const itemHtml = `
            <div 
                id="item-${id}" 
                class="bg-blue-900/50  border-white rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4 hover:border-brand-light/30 transition-colors group"
                data-descricao="${descricao}"
            >
                
                <div class="w-65 h-45  shrink-0 bg-navy-800 rounded-lg overflow-hidden border border-white">
                    <div class="w-full h-full flex items-center justify-center text-navy-700">
                        ${`<img src="/static/imgs/stock/${imagem}" alt="${nome}" class="w-full h-full object-cover">`}
                    </div>
                </div>
                
                <div class="flex-1 text-center sm:text-left">
                    <h3 class="text-text-primary font-large text-[32px]">${nome}</h3>

                    <div class="flex flex-col gap-1 sm:gap-4 text-md mt-1">
                        <span class="text-brand-light font-semibold text-[35px]">${precoFormatado}</span>
                        <span class="text-text-secondary text-[20px]"> ${categoria}</span>
                        <span class="text-text-secondary text-[15px]"> Stock: ${quantidade_prd}</span>

                    </div>
                </div>

                <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                    <button
                        data-id="${id}"
                        onclick="manipuleCart('push ', '${index}')" 
                        class="  px-4 py-1.5 rounded-full border border-text-secondary/30 text-text-secondary text-xs font-medium hover:bg-white/20   hover:text-white   transition-all duration-60
         active:bg-brand-light active:scale-90">
                        Adicionar ao carrinho
                    </button>
                    <button
                        data-id="${id}"
                        onclick="manipuleCart('pop', '${index}')" 
                        class="px-4 py-1.5 rounded-full border border-text-secondary/30 text-text-secondary text-xs font-medium hover:bg-white/20  hover:text-white   active:bg-brand-light active:shadow-innertransition-colors whitespace-nowrap   transition-all duration-60
         active:bg-brand-light active:scale-90">
                        remover  do carrinho
                    </button>
                  
                </div>
            </div>
        `;

    // Adiciona o HTML do item atual ao acumulador
    allItemsHtml += itemHtml;

    // console.log(`Item ${nome} criado.`);
  });

  // ----------------------------------------------------
  // 3. INSERÇÃO NO DOM (ÚNICA OPERAÇÃO)
  // ----------------------------------------------------
  // Adiciona todos os itens de uma vez no final do container
  itemListContainer.innerHTML = allItemsHtml;

  // Opcional: Aqui você pode chamar uma função para inicializar listeners de eventos
  // initializeEventListeners();
};

limparSacola = () => {
  let item_l = document.getElementById("sacola_item_total");
  let total_real = document.getElementById("total_real");

  sacola.splice(0, sacola.length);
  total_real.innerHTML = ` R$ ${calc_total().toFixed(2)}`;
  item_l.innerHTML = sacola.length;
};

socket.on("connect", () => {
  socket.emit("json_painel_event_load", socket.id);
  console.log("Connected to server");
});

socket.on("json_painel_event_return_products", (data) => {
  let products;

  if (typeof data === "string") {
    try {
      products = JSON.parse(data);
    } catch (err) {
      console.error("Erro ao parsear JSON:", err, data);
      return;
    }
  } else {
    products = data;
  }

  if (!Array.isArray(products) || products.length === 0) {
    console.log("nenhum produto retornado / array vazio");
    return;
  }

  create_items(products);
});
