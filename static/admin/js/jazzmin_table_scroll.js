// Place in: static/admin/js/jazzmin_table_scroll.js

(function () {
  window.addEventListener("load", function () {
    // 1. Find the table
    const table =
      document.querySelector("#result_list") ||
      document.querySelector("table.table-striped") ||
      document.querySelector(".card-body table") ||
      document.querySelector(".table-responsive table");

    if (!table) return;

    const tableContainer =
      table.closest(".table-responsive") ||
      table.closest(".card-body") ||
      table.parentElement;

    // 2. INJECT BUTTONS WITH SVG ICONS (Removes the "Cube" emoji effect)
    const arrowsHTML = `
        <div id="table-nav-arrows" style="
            position: fixed !important;
            top: 150px !important;
            right: 20px !important;
            z-index: 999999 !important;
            display: none;
            flex-direction: column;
            gap: 10px;
        ">
            <button id="scroll-left-btn" type="button" style="
                width: 45px; height: 45px; border-radius: 50%; border: 2px solid #fff;
                background: linear-gradient(145deg, #007bff, #0056b3); 
                color: white; cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;
                padding: 0; outline: none;
            ">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>

            <button id="scroll-right-btn" type="button" style="
                width: 45px; height: 45px; border-radius: 50%; border: 2px solid #fff;
                background: linear-gradient(145deg, #007bff, #0056b3); 
                color: white; cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;
                padding: 0; outline: none;
            ">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
        </div>
    `;

    // Remove old arrows if they exist
    const existing = document.getElementById("table-nav-arrows");
    if (existing) existing.remove();

    document.body.insertAdjacentHTML("beforeend", arrowsHTML);

    const navArrows = document.getElementById("table-nav-arrows");
    const leftBtn = document.getElementById("scroll-left-btn");
    const rightBtn = document.getElementById("scroll-right-btn");
    const scrollAmount = 300;

    // 3. Make table scrollable
    if (tableContainer) {
      tableContainer.style.overflowX = "auto";
      tableContainer.style.position = "relative";
      tableContainer.style.display = "block";
    }

    // 4. Logic to show/hide
    function updateButtons() {
      if (!tableContainer) return;

      const scrollLeft = tableContainer.scrollLeft;
      const maxScroll = tableContainer.scrollWidth - tableContainer.clientWidth;

      if (maxScroll > 0) {
        navArrows.style.display = "flex";

        leftBtn.style.opacity = scrollLeft <= 0 ? "0.4" : "1";
        leftBtn.style.pointerEvents = scrollLeft <= 0 ? "none" : "auto";

        rightBtn.style.opacity = scrollLeft >= maxScroll - 1 ? "0.4" : "1";
        rightBtn.style.pointerEvents =
          scrollLeft >= maxScroll - 1 ? "none" : "auto";
      } else {
        navArrows.style.display = "none";
      }
    }

    // Events
    leftBtn.addEventListener("click", function (e) {
      e.preventDefault();
      tableContainer.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    rightBtn.addEventListener("click", function (e) {
      e.preventDefault();
      tableContainer.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });

    if (tableContainer) {
      tableContainer.addEventListener("scroll", updateButtons);
    }
    window.addEventListener("resize", updateButtons);

    setTimeout(updateButtons, 500);
    setTimeout(updateButtons, 1500);
  });
})();
