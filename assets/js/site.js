// Toggle blocks.
document.querySelectorAll(".notion-toggle__summary").forEach((summary) => {
  summary.addEventListener("click", () => {
    const toggle = summary.parentElement;
    const open = toggle.classList.toggle("open");
    toggle.classList.toggle("closed", !open);
    summary.nextElementSibling.style.display = open ? "" : "none";
  });
});

// Copy buttons on code blocks.
document.querySelectorAll(".notion-code__copy-button").forEach((button) => {
  button.addEventListener("click", () => {
    navigator.clipboard.writeText(button.parentElement.querySelector("code").innerText);
  });
});

// Search, with Pagefind's index (built after Jekyll), in Super.so's search dialog.
const search = document.querySelector(".notion-search");
if (search) {
  const box = search.querySelector(".notion-search__box");
  const input = box.querySelector("input");
  const templates = search.querySelector(".notion-search__templates").content;
  const template = (selector) => templates.querySelector(selector).cloneNode(true);
  let pagefind;
  let results = [];
  let active = 0;
  let query = 0; // the latest query's number, to ignore earlier queries' results

  const open = () => {
    search.classList.replace("close", "open");
    input.focus();
    input.select();
    pagefind ||= import("/pagefind/pagefind.js");
  };
  const close = () => search.classList.replace("open", "close");

  // Pagefind's URLs are the built files'.
  const url = (result) => result.url.replace(/\.html$/, "");

  const icon = (result) => {
    if (!result.meta.icon) return template(".notion-icon__page");
    const img = document.createElement("img");
    Object.assign(img, { alt: result.meta.title, width: 20, height: 20, className: "notion-icon", src: result.meta.icon });
    img.style.cssText = "object-fit:contain;object-position:center";
    return img;
  };

  const render = () => {
    box.querySelectorAll(":scope > :not(.notion-search__input)").forEach((element) => element.remove());
    if (!input.value.trim()) return;
    if (!results.length) {
      box.append(template(".notion-search__empty-state"));
      return;
    }
    const list = template(".notion-search__result-list");
    results.forEach((result, index) => {
      const wrapper = document.createElement("div");
      wrapper.id = `search-result-${index}`;
      wrapper.className = "notion-search__result-item-wrapper";
      wrapper.classList.toggle("first", index === 0);
      wrapper.classList.toggle("last", index === results.length - 1);
      const link = document.createElement("a");
      link.className = "notion-link notion-search__result-item page";
      link.classList.toggle("active", index === active);
      link.href = url(result);
      const iconWrapper = document.createElement("div");
      iconWrapper.className = "notion-search__result-item-icon";
      iconWrapper.append(icon(result));
      const content = document.createElement("div");
      content.className = "notion-search__result-item-content";
      const title = document.createElement("div");
      title.className = "notion-search__result-item-title notion-semantic-string";
      title.textContent = result.meta.title;
      const excerpt = document.createElement("div");
      excerpt.className = "notion-search__result-item-text";
      excerpt.innerHTML = result.excerpt; // Pagefind escapes the text, and marks the matches.
      content.append(title, excerpt);
      link.append(iconWrapper, content);
      if (index === active) link.append(template(".notion-search__result-item-enter-icon"));
      link.addEventListener("mousemove", () => {
        if (active !== index) {
          active = index;
          render();
        }
      });
      wrapper.append(link);
      list.append(wrapper);
    });
    const footer = template(".notion-search__result-footer");
    footer.querySelector("strong").textContent = results.length;
    box.append(list, footer);
    list.querySelector(".active")?.scrollIntoView({ block: "nearest" });
  };

  input.addEventListener("input", async () => {
    const number = ++query;
    const { search: find } = await pagefind;
    const response = await find(input.value);
    const data = await Promise.all((response?.results || []).map((result) => result.data()));
    if (number === query) {
      results = data;
      active = 0;
      render();
    }
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (results.length) {
        active = (active + (event.key === "ArrowDown" ? 1 : -1) + results.length) % results.length;
        render();
      }
    } else if (event.key === "Enter" && results[active]) {
      if (event.metaKey || event.ctrlKey) window.open(url(results[active]), "_blank");
      else window.location.href = url(results[active]);
    }
  });

  document.querySelector(".notion-navbar__search").addEventListener("click", open);
  search.querySelector(".notion-search__clear").addEventListener("click", () => {
    input.value = "";
    results = [];
    render();
    input.focus();
  });
  search.querySelector(".notion-search__wrapper").addEventListener("click", (event) => {
    if (event.target === event.currentTarget) close();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
}
