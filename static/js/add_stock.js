document.addEventListener("DOMContentLoaded", () => {
  const socket = io();
  socket.binaryType = "arraybuffer";
//   img_f = ""
  // ELEMENTOS
  const modal = document.getElementById("modal_add");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const cancelarBtn = document.getElementById("cancelarBtn");
  const form = document.getElementById("formProduto");
  const image_elm = document.getElementById("imagem_stk");
  const bt_s = document.getElementById("send_bnt");
  const modalSucesso = document.getElementById("modal_sucesso");
  const btnSucessoOk = document.getElementById("btnSucessoOk");
  // const btn_stock = document.getElementById("btn_stock");
  
  const modalErro = document.getElementById("modal_erro");
  const btnErroOk = document.getElementById("btnErroOk");

  socket.on("sucess_record", (data) => {
    // alert("Gravado com sucesso");
      abrirModalSucesso();
    socket.emit("json_painel_event_load",  "True")

      
  });

  socket.on("error_record", (data) => {
    abrirModalErro();
  });

  // ABRIR modal de erro
  window.abrirModalErro = function () {
    modalErro.classList.remove("hidden");
    modalErro.classList.add("flex");
  };

  // FECHAR modal de erro
  function fecharModalErro() {
    modalErro.classList.add("hidden");
    modalErro.classList.remove("flex");
  }

  btnErroOk.addEventListener("click", fecharModalErro);

  // ABRIR modal de sucesso
  window.abrirModalSucesso = function () {
    modalSucesso.classList.remove("hidden");
    modalSucesso.classList.add("flex");
  };

  // FECHAR modal
  function fecharModalSucesso() {
    modalSucesso.classList.add("hidden");
    modalSucesso.classList.remove("flex");
  }

  btnSucessoOk.addEventListener("click", fecharModalSucesso);

  // VERIFICAÇÃO
  if (!modal) {
    console.error("ERRO: modal_add NÃO ENCONTRADO!");
    return;
  }
  if (!closeModalBtn) {
    console.error("ERRO: closeModalBtn NÃO ENCONTRADO!");
    return;
  }
  if (!cancelarBtn) {
    console.error("ERRO: cancelarBtn NÃO ENCONTRADO!");
    return;
  }
  if (!form) {
    console.error("ERRO: formProduto NÃO ENCONTRADO!");
    return;
  }
  // if (!btn_stock) { console.warn("Aviso: botão #btn_stock não encontrado (ok se não existir)."); }

  // ABRIR MODAL
  function abrirModalAdd() {
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    console.log("Modal aberto");
  }
  window.abrirModalAdd = abrirModalAdd;

  // FECHAR MODAL
  function fecharModalAdd() {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    console.log("Modal fechado");
  }

  window.fecharModalAdd = fecharModalAdd;

  image_elm.addEventListener("change", () => {
    img_f = "";

    // const reader = new FileReader();
    const file = image_elm.files[0];
    console.info(file);

    file.arrayBuffer().then((buffer) => {
        socket.emit("send_img_stk", { "filename": file.name }, buffer);
        img_f = file.name
    //   console.info(buffer.length);
    });
  });

  // EVENTOS
  // if (btn_stock) btn_stock.addEventListener("click", abrirModalAdd);
  closeModalBtn.addEventListener("click", fecharModalAdd);
  cancelarBtn.addEventListener("click", fecharModalAdd);

  // SUBMISSÃO DO FORM
  bt_s.addEventListener("click", (e) => {
    // e.preventDefault();

    let produto = {
      nome: document.getElementById("nome").value,
      image_produto: String(img_f),
      preco: document.getElementById("preco").value,
      categoria: document.getElementById("categoria").value,
      quantidade: document.getElementById("quantidade").value,
      ps_pouco: document.getElementById("quantidade_pouco").value,
      breve: document.getElementById("breve").value,
      descricao: document.getElementById("descricao").value,
    };


    //   it = JSON.stringify(produto)
    // console.log(it)

    // socket.emit("send_img_byn", {"id": socket.id, "data":  } )
    socket.emit("send_products_to_stk", {"id": socket.id, "data":  produto} )

    fecharModalAdd();
  });
    
    
    
});
