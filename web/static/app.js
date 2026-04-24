(function () {
  const viewBrowse = document.getElementById("view-browse");
  const viewDetail = document.getElementById("view-detail");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  const btnNot = document.getElementById("btn-not");
  const btnYes = document.getElementById("btn-yes");
  const cardShell = document.getElementById("card-shell");
  const studyCard = document.getElementById("study-card");
  const cardImage = document.getElementById("card-image");
  const cardTitle = document.getElementById("card-title");
  const cardSubtitle = document.getElementById("card-subtitle");
  const cardMeta = document.getElementById("card-meta");
  const progress = document.getElementById("progress");
  const btnRefresh = document.getElementById("btn-refresh");
  const btnBack = document.getElementById("btn-back");
  const toast = document.getElementById("toast");
  const bgA = document.getElementById("bg-a");
  const bgB = document.getElementById("bg-b");

  const detailImage = document.getElementById("detail-image");
  const detailKicker = document.getElementById("detail-kicker");
  const detailTitle = document.getElementById("detail-title");
  const detailUrl = document.getElementById("detail-url");
  const detailSummary = document.getElementById("detail-summary");
  const detailLensNote = document.getElementById("detail-lens-note");
  const detailSupport = document.getElementById("detail-support");
  const detailCritic = document.getElementById("detail-critic");

  let items = [];
  let index = 0;
  let animating = false;
  let bgActive = 0;
  const imageCache = new Map();

  function showToast(msg, ms) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), ms || 3200);
  }

  function formatDate(d) {
    if (!d) return "—";
    return d.length >= 10 ? d.slice(0, 10) : d;
  }

  function cssBgFromUrl(url) {
    return `linear-gradient(165deg, rgba(246,247,251,0.9), rgba(255,255,255,0.78)), url(${JSON.stringify(
      url || ""
    )})`;
  }

  function setAmbientBackground(url) {
    const next = 1 - bgActive;
    const el = next === 0 ? bgA : bgB;
    const prevEl = bgActive === 0 ? bgA : bgB;
    el.style.backgroundImage = cssBgFromUrl(url);
    el.classList.add("is-visible");
    prevEl.classList.remove("is-visible");
    bgActive = next;
  }

  async function fetchImageUrl(itemId) {
    if (imageCache.has(itemId)) return imageCache.get(itemId);
    const r = await fetch("/api/image/" + encodeURIComponent(itemId));
    const data = await r.json();
    if (!data.ok) throw new Error(data.error || "Image failed");
    imageCache.set(itemId, data.url);
    return data.url;
  }

  function currentItem() {
    return items[index] || null;
  }

  function updateNavState() {
    const n = items.length;
    btnPrev.disabled = n === 0 || index <= 0 || animating;
    btnNext.disabled = n === 0 || index >= n - 1 || animating;
    const has = !!currentItem();
    btnNot.disabled = !has || animating;
    btnYes.disabled = !has || animating;
    progress.textContent = n ? index + 1 + " / " + n : "0 / 0";
  }

  function stripMotion() {
    studyCard.classList.remove(
      "motion-exit-left",
      "motion-exit-right",
      "motion-enter-left",
      "motion-enter-right"
    );
  }

  async function applyCardContent(it) {
    if (!it) {
      cardTitle.textContent = "No signals yet";
      cardSubtitle.textContent = "Tap “Refresh signals” to load your vault.";
      cardMeta.textContent = "";
      cardImage.removeAttribute("src");
      studyCard.disabled = true;
      return;
    }
    studyCard.disabled = false;
    cardTitle.textContent = it.title || "(Untitled)";
    cardSubtitle.textContent = it.source || "";
    cardMeta.textContent =
      [formatDate(it.date), it.topic ? "#" + it.topic : "", it.kind || ""].filter(Boolean).join(" · ");
    try {
      const url = await fetchImageUrl(it.id);
      cardImage.src = url;
      cardImage.alt = "Lead image for: " + (it.title || "signal");
      setAmbientBackground(url);
    } catch (e) {
      cardImage.removeAttribute("src");
      showToast(String(e.message || e), 3500);
    }
  }

  function renderBrowseCardImmediate() {
    stripMotion();
    const it = currentItem();
    updateNavState();
    return applyCardContent(it);
  }

  function onMotionEndOnce(fn) {
    const handler = (ev) => {
      if (ev.target !== studyCard) return;
      studyCard.removeEventListener("animationend", handler);
      fn();
    };
    studyCard.addEventListener("animationend", handler);
  }

  async function go(delta) {
    const n = items.length;
    if (!n || animating) return;
    const next = index + delta;
    if (next < 0 || next >= n) return;

    animating = true;
    updateNavState();

    const exitClass = delta > 0 ? "motion-exit-left" : "motion-exit-right";
    stripMotion();
    void studyCard.offsetWidth;
    studyCard.classList.add(exitClass);

    onMotionEndOnce(async () => {
      stripMotion();
      index = next;
      const enterClass = delta > 0 ? "motion-enter-right" : "motion-enter-left";
      await applyCardContent(currentItem());
      void studyCard.offsetWidth;
      studyCard.classList.add(enterClass);
      onMotionEndOnce(() => {
        stripMotion();
        animating = false;
        updateNavState();
        prefetchNeighbors();
      });
    });
  }

  function prefetchNeighbors() {
    const ids = [items[index + 1], items[index - 1]].filter(Boolean).map((x) => x.id);
    ids.forEach((id) => {
      if (!imageCache.has(id)) {
        fetchImageUrl(id).catch(() => {});
      }
    });
  }

  async function sendFeedback(signal) {
    const it = currentItem();
    if (!it || animating) return;
    try {
      const r = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: it.id, signal: signal }),
      });
      const data = await r.json();
      if (!data.ok) throw new Error(data.error || "Feedback failed");
      showToast(signal === "interested" ? "We’ll show more like this." : "We’ll show less like this.", 2800);
      await loadItems();
      if (index >= items.length) index = Math.max(0, items.length - 1);
      await renderBrowseCardImmediate();
      prefetchNeighbors();
    } catch (e) {
      showToast(String(e.message || e), 4500);
    }
  }

  function showBrowse() {
    viewDetail.classList.add("hidden");
    viewDetail.hidden = true;
    viewBrowse.classList.remove("hidden");
    viewBrowse.hidden = false;
  }

  function showDetail() {
    viewBrowse.classList.add("hidden");
    viewBrowse.hidden = true;
    viewDetail.classList.remove("hidden");
    viewDetail.hidden = false;
  }

  async function openDetail() {
    const it = currentItem();
    if (!it) return;
    showDetail();
    detailKicker.textContent = (it.kind || "signal").toUpperCase() + " · " + formatDate(it.date);
    detailTitle.textContent = it.title || "";
    detailUrl.href = it.url || "#";
    detailSummary.textContent = "Loading…";
    detailLensNote.textContent = "";
    detailSupport.textContent = "";
    detailCritic.textContent = "";

    try {
      const imgUrl = await fetchImageUrl(it.id);
      detailImage.src = imgUrl;
      detailImage.alt = "";
      setAmbientBackground(imgUrl);

      const r = await fetch("/api/signal/" + encodeURIComponent(it.id));
      const data = await r.json();
      if (!data.ok) throw new Error(data.error || "Failed");
      const full = data.item;
      detailSummary.textContent = full.summary || "No summary for this item.";
      const lens = data.dual_lens || {};
      detailLensNote.textContent = lens.disclaimer || "";
      detailSupport.textContent = lens.supporters || "";
      detailCritic.textContent = lens.critics || "";
    } catch (e) {
      detailSummary.textContent = String(e.message || e);
    }
  }

  async function loadItems() {
    const r = await fetch("/api/items");
    const data = await r.json();
    items = data.items || [];
    if (index >= items.length) index = Math.max(0, items.length - 1);
    imageCache.clear();
    await renderBrowseCardImmediate();
    prefetchNeighbors();
  }

  async function onRefresh() {
    btnRefresh.disabled = true;
    try {
      const r = await fetch("/api/update", { method: "POST" });
      const data = await r.json();
      if (!data.ok) throw new Error(data.error || "Update failed");
      const s = data.stats || {};
      showToast(
        "Updated — " +
          (s.stored_total ?? "?") +
          " items (" +
          (s.rss_entries ?? 0) +
          " RSS, " +
          (s.legislation ?? 0) +
          " bills).",
        4000
      );
      await loadItems();
    } catch (e) {
      showToast(String(e.message || e), 5000);
    } finally {
      btnRefresh.disabled = false;
    }
  }

  btnPrev.addEventListener("click", () => go(-1));
  btnNext.addEventListener("click", () => go(1));
  btnNot.addEventListener("click", () => sendFeedback("not_interested"));
  btnYes.addEventListener("click", () => sendFeedback("interested"));

  studyCard.addEventListener("click", () => {
    if (!currentItem() || animating) return;
    openDetail();
  });

  btnBack.addEventListener("click", () => {
    showBrowse();
  });

  btnRefresh.addEventListener("click", onRefresh);

  document.addEventListener("keydown", (e) => {
    if (!viewBrowse.hidden && !viewBrowse.classList.contains("hidden")) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        go(1);
      } else if (e.key === "Enter" && currentItem() && !animating) {
        e.preventDefault();
        openDetail();
      }
    } else if (!viewDetail.hidden && e.key === "Escape") {
      showBrowse();
    }
  });

  loadItems();
})();
