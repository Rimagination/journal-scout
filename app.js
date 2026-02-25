const state = {
  rows: [],
  suggestions: [],
  activeIndex: -1,
  minIF: null,
  meta: null,
};

const els = {
  searchShell: document.querySelector(".search-shell"),
  searchInput: document.getElementById("searchInput"),
  activeFilter: document.getElementById("activeFilter"),
  suggestionPanel: document.getElementById("suggestionPanel"),
  genInfo: document.getElementById("genInfo"),
  cmdTrigger: document.getElementById("cmdTrigger"),
  cmdModal: document.getElementById("cmdModal"),
  cmdClose: document.getElementById("cmdClose"),
  cmdInput: document.getElementById("cmdInput"),
  cmdList: document.getElementById("cmdList"),
};

function safe(v) {
  return v === null || v === undefined || v === "" ? "-" : String(v);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getHaystack(r) {
  return [r.title, r.issn, r.eissn, r.cn_number].join(" ").toLowerCase();
}

function scoreRow(r, query) {
  const q = query.toLowerCase();
  const title = (r.title || "").toLowerCase();
  const issn = (r.issn || "").toLowerCase();
  const eissn = (r.eissn || "").toLowerCase();
  const cn = (r.cn_number || "").toLowerCase();

  let score = 0;
  if (title === q) score += 1000;
  if (issn === q || eissn === q || cn === q) score += 950;
  if (title.startsWith(q)) score += 450;
  if (issn.startsWith(q) || eissn.startsWith(q) || cn.startsWith(q)) score += 330;
  if (title.includes(q)) score += 180;
  if (getHaystack(r).includes(q)) score += 70;
  if (r.if_2023 !== null && r.if_2023 !== undefined) score += Math.min(80, Number(r.if_2023) / 8);
  if (r.jcr_quartile === "Q1") score += 40;
  if (r.cas_2025 === "1区") score += 30;
  return score;
}

function buildPriorityTags(row) {
  const tags = [];
  if (row.jcr_quartile) tags.push({ text: `JCR ${row.jcr_quartile}`, cls: "tag--jcr" });
  if (row.cas_2025) {
    const suffix = row.is_top === true ? " (Top)" : "";
    tags.push({ text: `中科院${row.cas_2025}${suffix}`, cls: "tag--cas" });
  }
  if (row.hq_level) tags.push({ text: `科协-${row.hq_level}`, cls: "tag--hq" });
  if (row.warning_latest) tags.push({ text: "中科院预警", cls: "tag--warn" });
  return tags;
}

function renderTagList(tags) {
  if (!tags.length) return "<span class='tag tag--empty'>无核心标签</span>";
  return tags.map((t) => `<span class="tag ${t.cls}">${escapeHtml(t.text)}</span>`).join("");
}

function findSuggestions(query, limit = 12) {
  const q = query.trim();
  if (!q) return [];

  return state.rows
    .filter((r) => getHaystack(r).includes(q.toLowerCase()))
    .filter((r) => {
      if (state.minIF === null) return true;
      const v = Number(r.if_2023);
      return Number.isFinite(v) && v >= state.minIF;
    })
    .map((r) => ({ row: r, score: scoreRow(r, q) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((x) => x.row);
}

function suggestionItem(row, idx) {
  const ids = [row.issn, row.cn_number].filter(Boolean).join(" / ");
  const tagsHtml = renderTagList(buildPriorityTags(row));
  const ifYear = row.if_year ? `(${row.if_year})` : "";
  const ifText = row.if_2023 === null || row.if_2023 === undefined ? "-" : safe(row.if_2023);
  const activeCls = idx === state.activeIndex ? "is-active" : "";

  return `
    <button class="suggestion ${activeCls}" data-id="${row.id}" data-idx="${idx}" type="button">
      <div class="suggestion__main">
        <div class="suggestion__title">${escapeHtml(row.title || "未知期刊")}</div>
        <div class="suggestion__meta">${escapeHtml(safe(ids))}</div>
      </div>
      <div class="suggestion__side">
        <div class="suggestion__if">IF${escapeHtml(ifYear)} ${escapeHtml(ifText)}</div>
        <div class="tags">${tagsHtml}</div>
      </div>
    </button>
  `;
}

function closeSuggestionPanel() {
  state.suggestions = [];
  state.activeIndex = -1;
  els.suggestionPanel.classList.remove("is-open");
  els.suggestionPanel.innerHTML = "";
}

function openSuggestionPanel() {
  els.suggestionPanel.classList.add("is-open");
}

function gotoDetail(id, q = "") {
  const url = new URL("./journal.html", window.location.href);
  url.searchParams.set("id", String(id));
  if (q) url.searchParams.set("q", q);
  window.location.href = url.toString();
}

function ensureActiveVisible() {
  const active = els.suggestionPanel.querySelector(".suggestion.is-active");
  if (active) active.scrollIntoView({ block: "nearest" });
}

function renderSuggestions() {
  const q = els.searchInput.value.trim();
  if (!q) {
    closeSuggestionPanel();
    return;
  }

  state.suggestions = findSuggestions(q);
  state.activeIndex = state.suggestions.length ? 0 : -1;
  openSuggestionPanel();

  if (!state.suggestions.length) {
    els.suggestionPanel.innerHTML = "<p class='placeholder'>未找到匹配期刊，请尝试更完整的名称、ISSN 或 CN号</p>";
    return;
  }

  els.suggestionPanel.innerHTML = state.suggestions.map((x, i) => suggestionItem(x, i)).join("");
  els.suggestionPanel.querySelectorAll(".suggestion").forEach((btn) => {
    btn.addEventListener("click", () => gotoDetail(Number(btn.dataset.id), q));
    btn.addEventListener("mouseenter", () => {
      state.activeIndex = Number(btn.dataset.idx);
      els.suggestionPanel.querySelectorAll(".suggestion").forEach((s) => s.classList.remove("is-active"));
      btn.classList.add("is-active");
    });
  });
}

function applyFilterHint() {
  if (state.minIF === null) {
    els.activeFilter.hidden = true;
    els.activeFilter.textContent = "";
    return;
  }
  els.activeFilter.hidden = false;
  els.activeFilter.innerHTML = `<span class="status-badge status-badge--neutral">筛选中：IF ≥ ${escapeHtml(String(state.minIF))}</span>`;
}

function restoreQueryFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  if (!q) return;
  els.searchInput.value = q;
  renderSuggestions();
}

function openCommandPalette() {
  els.cmdModal.hidden = false;
  els.cmdInput.value = "";
  renderCommandList("");
  setTimeout(() => els.cmdInput.focus(), 0);
}

function closeCommandPalette() {
  els.cmdModal.hidden = true;
}

function runCommand(handler) {
  closeCommandPalette();
  handler();
}

function parseFilterCommand(input) {
  const m = input.match(/^\s*>\s*filter\s+if\s*>\s*(\d+(?:\.\d+)?)\s*$/i);
  if (!m) return null;
  return Number(m[1]);
}

function commandEntries() {
  return [
    {
      key: "hq",
      title: "打开科协目录核对",
      desc: "跳转到 59 领域核对页面",
      run: () => {
        window.location.href = "./hq_stats.html";
      },
    },
    {
      key: "clear",
      title: "清空搜索框",
      desc: "清空关键词并关闭联想面板",
      run: () => {
        els.searchInput.value = "";
        closeSuggestionPanel();
        els.searchInput.focus();
      },
    },
    {
      key: "reset-filter",
      title: "清除 IF 筛选",
      desc: "恢复不过滤的检索状态",
      run: () => {
        state.minIF = null;
        applyFilterHint();
        renderSuggestions();
      },
    },
    {
      key: "sample-nature",
      title: "打开示例期刊 Nature",
      desc: "快速查看高影响力期刊详情",
      run: () => {
        const row = state.rows.find((r) => String(r.title || "").toUpperCase() === "NATURE");
        if (row) gotoDetail(row.id, "Nature");
      },
    },
  ];
}

function renderCommandList(input) {
  const filterValue = parseFilterCommand(input);
  let list = commandEntries();

  if (filterValue !== null) {
    list = [
      {
        key: "filter-if",
        title: `应用筛选：IF ≥ ${filterValue}`,
        desc: "仅在联想结果中保留满足阈值的期刊",
        run: () => {
          state.minIF = filterValue;
          applyFilterHint();
          renderSuggestions();
        },
      },
    ];
  } else if (input.trim()) {
    const q = input.trim().toLowerCase();
    list = list.filter((x) => x.title.toLowerCase().includes(q) || x.desc.toLowerCase().includes(q) || x.key.includes(q));
  }

  if (!list.length) {
    els.cmdList.innerHTML = "<p class='placeholder'>无可用命令</p>";
    return;
  }

  els.cmdList.innerHTML = list
    .map(
      (item, idx) => `
        <button class="cmd-item ${idx === 0 ? "is-active" : ""}" data-cmd="${escapeHtml(item.key)}" type="button">
          <div class="cmd-item__title">${escapeHtml(item.title)}</div>
          <div class="cmd-item__desc">${escapeHtml(item.desc)}</div>
        </button>
      `
    )
    .join("");

  els.cmdList.querySelectorAll(".cmd-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = list.find((x) => x.key === btn.dataset.cmd);
      if (item) runCommand(item.run);
    });
    btn.addEventListener("mouseenter", () => {
      els.cmdList.querySelectorAll(".cmd-item").forEach((x) => x.classList.remove("is-active"));
      btn.classList.add("is-active");
    });
  });

  els.cmdInput.onkeydown = (e) => {
    const items = [...els.cmdList.querySelectorAll(".cmd-item")];
    if (!items.length) return;
    const current = items.findIndex((x) => x.classList.contains("is-active"));
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = current < items.length - 1 ? current + 1 : 0;
      items.forEach((x) => x.classList.remove("is-active"));
      items[next].classList.add("is-active");
      items[next].scrollIntoView({ block: "nearest" });
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = current > 0 ? current - 1 : items.length - 1;
      items.forEach((x) => x.classList.remove("is-active"));
      items[next].classList.add("is-active");
      items[next].scrollIntoView({ block: "nearest" });
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      items[Math.max(0, current)].click();
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      closeCommandPalette();
    }
  };
}

function bindEvents() {
  els.searchInput.addEventListener("input", renderSuggestions);
  els.searchInput.addEventListener("focus", () => {
    if (els.searchInput.value.trim()) renderSuggestions();
  });

  els.searchInput.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!state.suggestions.length) return;
      e.preventDefault();
      if (e.key === "ArrowDown") {
        state.activeIndex = state.activeIndex < state.suggestions.length - 1 ? state.activeIndex + 1 : 0;
      } else {
        state.activeIndex = state.activeIndex > 0 ? state.activeIndex - 1 : state.suggestions.length - 1;
      }
      els.suggestionPanel.querySelectorAll(".suggestion").forEach((btn, idx) => {
        btn.classList.toggle("is-active", idx === state.activeIndex);
      });
      ensureActiveVisible();
      return;
    }

    if (e.key === "Enter") {
      e.preventDefault();
      const picked = state.suggestions[state.activeIndex >= 0 ? state.activeIndex : 0];
      if (picked) gotoDetail(picked.id, els.searchInput.value.trim());
    }
  });

  document.addEventListener("click", (e) => {
    if (!els.searchShell.contains(e.target)) closeSuggestionPanel();
    if (e.target.closest("[data-close-cmd]")) closeCommandPalette();
  });

  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openCommandPalette();
      return;
    }
    if (e.key === "Escape" && !els.cmdModal.hidden) closeCommandPalette();
  });

  els.cmdTrigger.addEventListener("click", openCommandPalette);
  els.cmdClose.addEventListener("click", closeCommandPalette);
  els.cmdInput.addEventListener("input", () => renderCommandList(els.cmdInput.value));
}

async function bootstrap() {
  const res = await fetch("./data/journals.json");
  const payload = await res.json();
  state.rows = payload.journals || [];
  state.meta = payload.meta || {};
  els.genInfo.textContent = `数据更新时间：${state.meta.generated_at || "-"}`;

  applyFilterHint();
  bindEvents();
  restoreQueryFromUrl();
}

bootstrap().catch((err) => {
  console.error(err);
  openSuggestionPanel();
  els.suggestionPanel.innerHTML = "<p class='placeholder'>数据加载失败，请刷新重试</p>";
});
