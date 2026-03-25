document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".filter-btn");
  const cards = document.querySelectorAll(".card");
  const articles = document.querySelector(".articles");

  // フィルター結果が0件の場合に表示するメッセージ要素
  const emptyMsg = document.createElement("p");
  emptyMsg.className = "filter-empty";
  emptyMsg.textContent = "該当する記事はありません。";
  if (articles) articles.appendChild(emptyMsg);

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const filter = btn.dataset.filter;

      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      let visibleCount = 0;
      cards.forEach((card) => {
        if (filter === "all" || card.dataset.priority === filter) {
          card.style.display = "";
          visibleCount++;
        } else {
          card.style.display = "none";
        }
      });

      emptyMsg.style.display = visibleCount === 0 ? "block" : "none";
    });
  });
});
