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
    Object.assign(img, {
      alt: result.meta.title,
      width: 20,
      height: 20,
      className: "notion-icon",
      src: result.meta.icon,
    });
    img.style.cssText = "object-fit:contain;object-position:center";
    return img;
  };

  const render = () => {
    box.querySelectorAll(":scope > :not(.notion-search__input)").forEach((element) => {
      element.remove();
    });
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
    const label = footer.querySelector("strong + span");
    label.textContent = results.length === 1 ? label.dataset.one : label.dataset.many;
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

// Breadcrumbs that don't fit, from the second, in a dropdown menu after the first, as on Super.so.
const breadcrumb = document.querySelector(".notion-breadcrumb");
if (breadcrumb) {
  const crumbs = [...breadcrumb.children];
  const item = document.createElement("li");
  item.innerHTML = `<span class="notion-breadcrumb__divider" aria-hidden="true">/</span><div class="notion-dropdown">
    <button type="button" class="notion-breadcrumb__item notion-breadcrumb__ellipsis" aria-expanded="false">...</button>
    <div class="notion-dropdown__menu-wrapper"><div class="notion-dropdown__menu initial-state">
      <div class="notion-breadcrumb__dropdown"><ul class="notion-dropdown__option-list"></ul></div>
    </div></div>
  </div>`;
  const button = item.querySelector("button");
  const menu = item.querySelector(".notion-dropdown__menu");
  const list = item.querySelector("ul");
  button.setAttribute("aria-label", breadcrumb.dataset.label);

  const toggle = (open) => {
    if (open === (button.getAttribute("aria-expanded") === "true")) return;
    button.setAttribute("aria-expanded", open);
    menu.classList.remove("initial-state", "animate-in", "animate-out");
    menu.classList.add(open ? "animate-in" : "animate-out");
  };

  // The breadcrumbs don't fit if they overflow, or if the last crumb's title is narrower than it would be.
  const last = crumbs.at(-1).querySelector(".notion-breadcrumb__title");
  const fits = () =>
    breadcrumb.scrollWidth <= breadcrumb.clientWidth &&
    last.clientWidth >= Math.min(last.scrollWidth, Number.parseFloat(getComputedStyle(last).maxWidth) || Infinity);

  const fit = () => {
    toggle(false);
    item.remove();
    list.replaceChildren();
    crumbs.forEach((crumb) => {
      crumb.hidden = false;
    });
    for (const crumb of crumbs.slice(1, -1)) {
      if (fits()) break;
      if (!item.isConnected) crumbs[0].after(item);
      crumb.hidden = true;
      const link = crumb.querySelector("a");
      const option = document.createElement("li");
      // Crumbs after the first are its descendants.
      const arrow = list.children.length
        ? `<p class="notion-breadcrumb__dropdown-option-arrow" aria-hidden="true">↳</p>`
        : "";
      option.innerHTML = `<a class="notion-link"><div class="notion-dropdown__option">${arrow}<p class="notion-breadcrumb__dropdown-option-title"></p></div></a>`;
      option.querySelector("a").href = link.href;
      const title = option.querySelector(".notion-breadcrumb__dropdown-option-title");
      title.textContent = link.textContent.trim();
      const icon = link.querySelector("img");
      if (icon) title.before(icon.cloneNode());
      list.append(option);
    }
  };

  button.addEventListener("click", () => toggle(button.getAttribute("aria-expanded") !== "true"));
  document.addEventListener("click", (event) => {
    if (!item.contains(event.target)) toggle(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") toggle(false);
  });
  new ResizeObserver(fit).observe(breadcrumb);
  document.fonts.ready.then(fit);
}

// The sidebar's and languages' menus on phones: close them on Escape or a click outside them.
document.querySelectorAll(".sidebar-menu, .language-menu").forEach((menu) => {
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (menu.open && !menu.contains(event.target)) menu.open = false;
  });
});

// Tables that scroll: a hint above them, and a fade at the edges that have more.
document.querySelectorAll(".notion-table__wrapper").forEach((wrapper) => {
  const hint = document.createElement("p");
  hint.className = "notion-table__scroll-hint";
  hint.setAttribute("aria-hidden", "true");
  hint.textContent = `${wrapper.dataset.scrollLabel} →`;
  wrapper.before(hint);
  const update = () => {
    const scrolls = wrapper.scrollWidth > wrapper.clientWidth + 1;
    hint.hidden = !scrolls;
    wrapper.classList.toggle("more-start", scrolls && wrapper.scrollLeft > 1);
    wrapper.classList.toggle(
      "more-end",
      scrolls && wrapper.scrollLeft + wrapper.clientWidth < wrapper.scrollWidth - 1,
    );
  };
  wrapper.addEventListener("scroll", update, { passive: true });
  new ResizeObserver(update).observe(wrapper);
});
