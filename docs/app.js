document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".filter-btn");
  const cards = document.querySelectorAll(".card");
  const articles = document.querySelector(".articles");
  const statsCount = document.getElementById("stats-count");
  const totalCount = cards.length;

  // フィルター結果が0件の場合に表示するメッセージ要素
  const emptyMsg = document.createElement("p");
  emptyMsg.className = "filter-empty";
  emptyMsg.textContent = "該当する記事はありません。";
  if (articles) articles.appendChild(emptyMsg);

  function applyFilter(filter) {
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
    if (statsCount) {
      statsCount.textContent = filter === "all"
        ? `${totalCount} 件`
        : `${visibleCount} / ${totalCount} 件`;
    }
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      applyFilter(btn.dataset.filter);
    });
  });

  // 初期表示: active なボタンのフィルターを適用
  const activeBtn = document.querySelector(".filter-btn.active");
  if (activeBtn) applyFilter(activeBtn.dataset.filter);
});
