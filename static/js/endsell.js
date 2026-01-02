var pagamentoSelecionado = null;

function abrirModalPagamento() {
  const modal = document.getElementById("modal_pagamento");
  const box = document.getElementById("modal_pagamento_box");

  modal.classList.remove("hidden");

  setTimeout(() => {
    modal.classList.remove("opacity-0");
    // modal.classList.add("items-center justify-center")
    box.classList.remove("scale-90");
    // box.classList.add("items-center justify-center")

  }, 10);
}


function fecharModalPagamento() {
  const modal = document.getElementById("modal_pagamento");
  const box = document.getElementById("modal_pagamento_box");

  modal.classList.add("opacity-0");
  box.classList.add("scale-90");

  setTimeout(() => {
    modal.classList.add("hidden");
  }, 300);
}


document.addEventListener("DOMContentLoaded", () => {


  
// import sacola  from "./painel";


// ⭐ Destacar botão selecionado
document.querySelectorAll(".btnPagamento").forEach(btn => {
  btn.addEventListener("click", () => {

    // Remove destaque dos outros
    document.querySelectorAll(".btnPagamento").forEach(b => {
      b.classList.remove("ring-4", "ring-green-400", "scale-105");
    });

    // Salva seleção
    pagamentoSelecionado = btn.getAttribute("data-pagamento");

    // Adiciona destaque visual
    btn.classList.add("ring-4", "ring-green-400", "scale-105");
  });
});

// ⭐ Botão salvar
document.getElementById("btnSalvarPagamento").addEventListener("click", () => {
  if (!pagamentoSelecionado) {
    alert("Selecione uma forma de pagamento!");
    return;
  }

  console.log("Forma escolhida:", pagamentoSelecionado);

  // Aqui você pode chamar sua função, ex.:
  // salvarPagamento(pagamentoSelecionado);
  send_sell(pagamentoSelecionado)
  fecharModalPagamento();

});


function send_sell(typePay) {
  socket.emit("end_sell", { "sacola": sacola, "typepay": typePay } );


  socket.once("error_send_sell", (data_error) => {
    let error_ = document.querySelector("#modal_erro p");
    error_.textContent = `${data_error}`;

    abrirModalErro();

    // alert("ok")
  });


  socket.once("sucess_send_sell", (data_sucess) => {
    let sucess_ = document.querySelector("#modal_sucesso  p")
    sucess_.textContent = `${data_sucess}`
    abrirModalSucesso()
  });
}
  

})

