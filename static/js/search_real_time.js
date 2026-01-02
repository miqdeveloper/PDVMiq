// static/search.js
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("search_item");
  // const resultsList = document.getElementById('results');

  input.addEventListener("input", () => {
    const term = input.value;
    socket.emit("search_product", { "term": term });
  });
});


// socket.on('search_results', data => {
//     const results = data.results;
//     resultsList.innerHTML = '';  // limpa resultados anteriores
//     results.forEach(item => {
//         const li = document.createElement('li');
//         li.textContent = item;
//         resultsList.appendChild(li);
//     });
// });
