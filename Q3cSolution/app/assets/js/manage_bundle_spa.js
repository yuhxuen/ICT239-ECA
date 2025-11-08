(async function () {
  const root = document.getElementById("bundles-root");
  const empty = document.getElementById("empty-state");
  const msg = document.getElementById("msg");

  function note(text, cls = "alert-info") {
    msg.innerHTML = `<div class="alert ${cls} p-2">${text}</div>`;
    setTimeout(() => (msg.innerHTML = ""), 2500);
  }

  function rowDivider(full = true) {
    return `<div class="${full ? "rule-full" : "rule-partial"}"></div>`;
  }

  function render(bundles) {
    root.innerHTML = "";
    empty.style.display = bundles.length ? "none" : "block";
    bundles.forEach((b, bi) => {
      const dates =
        `<div class="col-2">${fmt(b.purchased_date)}</div>` +
        `<div class="col-2">${fmt(b.expiry_date)}</div>`;
      let itemsHtml = "";
      b.items.forEach((it, i) => {
        const util = it.utilised
          ? `<div>Utilised: Yes</div>`
          : `<div>Utilised: Not Yet</div>`;
        const expiredTag = b.expired
          ? `<div class="text-danger">Expired</div>`
          : "";
        const bookForm =
          !b.expired && !it.utilised
            ? `
            <form class="form-inline ml-auto" data-bid="${b.id}" data-pid="${it.package_id}">
              <label class="mr-2 mb-0">Check-in Date</label>
              <input type="date" name="check_in_date" class="form-control form-control-sm mr-2"
                     min="${b.purchased_date}" required />
              <button class="btn btn-primary btn-sm">Book</button>
            </form>
            `
            : ``;

        itemsHtml += `
          <div class="d-flex align-items-center">
            <img class="pkg-thumb mr-3" src="${it.image_url}" />
            <div class="flex-grow-1">
              <div class="font-weight-semibold">${it.hotel_name}</div>
              ${util}${expiredTag}
            </div>
            ${bookForm}
          </div>
          ${i < b.items.length - 1 ? rowDivider(false) : ""}`;
      });

      root.insertAdjacentHTML(
        "beforeend",
        `
        <div class="row no-gutters col-12 align-items-center">
          ${dates}
          <div class="col ml-1">${itemsHtml}</div>
        </div>
        ${bi < bundles.length - 1 ? rowDivider(true) : ""}`
      );
    });
  }

  function fmt(ymd) {
    // "YYYY-MM-DD" -> "dd/mm/YYYY"
    const [y, m, d] = ymd.split("-");
    return `${d}/${m}/${y}`;
  }

  async function load() {
    const r = await fetch("/api/bundles");
    render(await r.json());
  }

  root.addEventListener("submit", async (e) => {
    if (e.target.tagName !== "FORM") return;
    e.preventDefault();
    const f = e.target;
    const payload = {
      bundle_id: f.getAttribute("data-bid"),
      package_id: f.getAttribute("data-pid"),
      check_in_date: new FormData(f).get("check_in_date"),
    };
    const r = await fetch("/api/bundle/book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const res = await r.json();
    if (!res.ok) {
      note(res.msg || "Booking failed", "alert-warning");
      return;
    }
    note("Booking created from bundle.");
    await load(); // refresh view without page reload
  });

  await load();
})();
