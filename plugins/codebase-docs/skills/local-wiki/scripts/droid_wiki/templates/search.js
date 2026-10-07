(function () {
  const input = document.getElementById("wiki-search");
  const results = document.getElementById("search-results");
  if (!input || !results) return;

  let pages = [];
  let searchBase = null;
  fetch(input.dataset.searchJson)
    .then((response) => {
      if (!response.ok) throw new Error("Search index unavailable");
      searchBase = new URL(response.url || input.dataset.searchJson, window.location.href);
      return response.json();
    })
    .then((data) => {
      pages = data;
      render(input.value);
    })
    .catch(() => {
      pages = [];
      input.placeholder = "Search index unavailable";
    });

  function render(query) {
    const normalized = query.trim().toLowerCase();
    results.replaceChildren();
    if (!normalized) return;

    const matches = pages
      .map((page) => {
        const haystack = `${page.title} ${page.summary} ${page.text}`.toLowerCase();
        return haystack.includes(normalized) ? page : null;
      })
      .filter(Boolean)
      .slice(0, 8);

    for (const page of matches) {
      const link = document.createElement("a");
      link.className = "search-result";
      link.href = searchBase ? new URL(page.url, searchBase).href : page.url;
      const title = document.createElement("strong");
      title.textContent = page.title;
      const summary = document.createElement("small");
      summary.textContent = page.summary || page.path;
      link.append(title, summary);
      results.appendChild(link);
    }
  }

  input.addEventListener("input", () => render(input.value));
})();
