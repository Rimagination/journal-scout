const SOURCE_INFO = {
  core: {
    title: "核心指标说明",
    body: `
      <p>本页展示期刊投稿常用的核心评价信息，帮助你快速判断目标期刊定位与风险。</p>
      <p>主要包括 JCR 分区、影响因子、中科院分区、预警信息与科协分级等维度。</p>
      <p>若同一期刊存在多年份数据，页面默认优先展示最新年份结果。</p>
    `,
  },
  showjcr: {
    title: "历年数据说明",
    body: `
      <p>趋势图用于展示同一期刊在不同年份中的 IF 与中科院分区变化。</p>
      <p>你可以将鼠标移动到图中节点，查看该年的具体数值。</p>
      <p>图表用于辅助比较，不替代你所在单位的正式认定规则。</p>
    `,
  },
  hq: {
    title: "科协高质量期刊分级说明",
    body: `
      <p>为贯彻落实《关于深化改革 培育世界一流科技期刊的意见》，推动建设中外期刊同质等效的评价导向，引导更多高水平成果在国内期刊发表，中国科协自 2019 年起分批支持全国学会面向学科领域国内外科技期刊编制并发布高质量期刊分级目录，为科技工作者论文发表和科研机构学术评价提供参考。截至 2025 年 12 月 1 日，已完成 59 个学科领域的分级目录编制。</p>
      <p>2025 年度《高质量科技期刊分级目录总汇（第五版）》新增药学领域分级目录，并由 20 家全国学会牵头对已发布的 20 个学科领域目录进行了优化调整，持续完善分级标准与目录结构。</p>
      <p>参与优化调整的学会包括：中国自动化学会、中国地理学会、中国细胞生物学学会、中国汽车工程学会、中国生态学学会、中国材料研究学会、中国通信学会、中国仪器仪表学会、中国计算机学会、中国核学会、中国硅酸盐学会、中华预防医学会、中国环境科学学会、中国仿真学会、中国纺织工程学会、中国兵工学会、中国地球物理学会、中国航海学会、中国公路学会、中国优选法统筹法与经济数学研究会。</p>
      <p>本页面中的“科协评级”展示对应期刊在相关学科目录中的分级结果（如 T1、T2）。同一期刊可能在多个学科目录中出现并对应多条记录，建议与 JCR、中科院分区及本单位政策结合使用。</p>
    `,
  },
  warning: {
    title: "预警信息说明",
    body: `
      <p>预警信息用于提示投稿风险，帮助你在选刊阶段规避潜在问题。</p>
      <p>不同年份的预警标签可能存在口径差异，建议以当年官方说明为准。</p>
      <p>最终是否投稿，请结合课题方向、单位政策与导师建议综合判断。</p>
    `,
  },
  citescore: {
    title: "CiteScore 说明",
    body: `
      <p>CiteScore 是 Scopus 期刊评价指标之一，本页同时展示 SJR、SNIP 与学科分区信息。</p>
      <p>学科表格包含大类/小类、分区、排名和百分位，便于横向比较期刊位置。</p>
      <p>当官方数据暂不可用时，页面会显示“参考值”提示，方便先做初筛。</p>
    `,
  },
  annual_articles: {
    title: "年发文量说明",
    body: `
      <p>“年发文量（最新年）”及右侧“年发文量变化”图主要来自 OpenAlex 的公开聚合数据（按期刊 Source 分组统计）。</p>
      <p>该口径受数据收录范围、索引延迟、期刊更名/合并及回溯更新影响，可能与出版社官网、JCR 或 Scopus 的正式统计存在差异。</p>
      <p>本页面数据用于选刊阶段的趋势参考，不建议作为单位考核或正式评价的唯一依据。</p>
    `,
  },
};

const els = {
  backLink: document.getElementById("backLink"),
  title: document.getElementById("title"),
  subtitle: document.getElementById("subtitle"),
  topTags: document.getElementById("topTags"),
  coreGrid: document.getElementById("coreGrid"),
  spotlightCover: document.getElementById("spotlightCover"),
  journalSummary: document.getElementById("journalSummary"),
  journalWebsite: document.getElementById("journalWebsite"),
  citeScoreCard: document.getElementById("citeScoreCard"),
  citeScoreValue: document.getElementById("citeScoreValue"),
  citeScoreMetrics: document.getElementById("citeScoreMetrics"),
  citeScoreStars: document.getElementById("citeScoreStars"),
  citeScoreMeta: document.getElementById("citeScoreMeta"),
  citeScoreSource: document.getElementById("citeScoreSource"),
  citeScorePercentLabel: document.getElementById("citeScorePercentLabel"),
  citeScorePercentValue: document.getElementById("citeScorePercentValue"),
  citeScorePercentFill: document.getElementById("citeScorePercentFill"),
  citeScoreBreakdown: document.getElementById("citeScoreBreakdown"),
  spotPublisher: document.getElementById("spotPublisher"),
  spotIndexType: document.getElementById("spotIndexType"),
  spotOA: document.getElementById("spotOA"),
  spotPublishYear: document.getElementById("spotPublishYear"),
  spotAnnualArticles: document.getElementById("spotAnnualArticles"),
  ifTrendChart: document.getElementById("ifTrendChart"),
  casTrendChart: document.getElementById("casTrendChart"),
  annualTrendChart: document.getElementById("annualTrendChart"),
  hqMetaGrid: document.getElementById("hqMetaGrid"),
  hqRecordList: document.getElementById("hqRecordList"),
  relatedList: document.getElementById("relatedList"),
  genInfo: document.getElementById("genInfo"),
  sourceModal: document.getElementById("sourceModal"),
  sourceModalTitle: document.getElementById("sourceModalTitle"),
  sourceModalBody: document.getElementById("sourceModalBody"),
  sourceModalClose: document.getElementById("sourceModalClose"),
  chartModal: document.getElementById("chartModal"),
  chartModalTitle: document.getElementById("chartModalTitle"),
  chartModalBody: document.getElementById("chartModalBody"),
  chartModalClose: document.getElementById("chartModalClose"),
};
const homepagePreviewImageCache = new Map();
const annualArticlesSeriesCache = new Map();
const pageState = {
  journal: null,
  latestCas: null,
  openAlexSource: null,
};

const API_BASE = ["127.0.0.1", "localhost"].includes(window.location.hostname)
  ? "http://127.0.0.1:8000/api"
  : "https://www.scansci.com/api";

const CHUNK_MANIFEST_PATHS = [
  "./data/journal_chunks_manifest.json",
  "/data/journal_chunks_manifest.json",
  "./xuankan/demo_site/data/journal_chunks_manifest.json",
  "/xuankan/demo_site/data/journal_chunks_manifest.json",
];

const SEARCH_INDEX_PATHS = [
  "./data/search_index.json",
  "/data/search_index.json",
  "./xuankan/demo_site/data/search_index.json",
  "/xuankan/demo_site/data/search_index.json",
];

const FULL_DATA_PATHS = [
  "./data/journals.json",
  "/data/journals.json",
  "./xuankan/demo_site/data/journals.json",
  "/xuankan/demo_site/data/journals.json",
];

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

function toBoolText(v) {
  if (v === true) return "是";
  if (v === false) return "否";
  return "-";
}

function levelRank(level) {
  const s = String(level || "").toUpperCase().trim();
  if (/^T[1-4]$/.test(s)) return Number(s.slice(1));
  if (s === "A类") return 11;
  if (s === "B类") return 12;
  if (s === "C类") return 13;
  return 99;
}

function yearNum(v) {
  const n = Number(String(v || "").replace(/[^\d]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function formatIFAcademicYear(rawYear) {
  const y = yearNum(rawYear);
  if (!y) return "";
  return `${y}-${y + 1}年度`;
}

function casRankNumber(raw) {
  const m = String(raw || "").match(/([1-4])\s*区/);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) ? n : null;
}

function formatCASSubcategoriesMultiline(subcategories) {
  const rows = Array.isArray(subcategories)
    ? subcategories
        .map((r) => ({
          name: String(r?.name || "").trim(),
          rank: String(r?.rank || "").trim(),
        }))
        .filter((r) => r.name || r.rank)
    : [];
  if (!rows.length) return "-";
  return rows
    .map((r) => {
      if (r.name && r.rank) return `${r.name}（${r.rank}）`;
      return r.name || r.rank;
    })
    .join("\n");
}

function collectIndexSignals(j, latestCas = null) {
  const casRows = Array.isArray(j?.cas_history) ? j.cas_history : [];
  const texts = [];
  if (latestCas?.wos) texts.push(String(latestCas.wos));
  for (const row of casRows) {
    if (row?.wos) texts.push(String(row.wos));
  }
  const tags = Array.isArray(j?.tags) ? j.tags : [];
  for (const t of tags) {
    if (t !== null && t !== undefined) texts.push(String(t));
  }

  const merged = texts.join(" ").toUpperCase();
  const tokenSet = new Set(
    merged
      .replace(/[^A-Z0-9]+/g, " ")
      .split(/\s+/)
      .map((x) => x.trim())
      .filter(Boolean)
  );

  const hasSCIE = merged.includes("SCIE") || tokenSet.has("SCIE");
  const hasESCI = merged.includes("ESCI") || tokenSet.has("ESCI");

  return {
    hasSCI: tokenSet.has("SCI") || hasSCIE,
    hasSCIE,
    hasESCI,
    hasEI: tokenSet.has("EI"),
    hasSSCI: merged.includes("SSCI") || tokenSet.has("SSCI"),
  };
}

function buildInclusionTypeText(signals) {
  const types = [];
  if (signals?.hasSCI) types.push("SCI");
  if (signals?.hasSCIE) types.push("SCIE");
  if (signals?.hasESCI) types.push("ESCI");
  if (signals?.hasEI) types.push("EI");
  return types.length ? types.join(" / ") : "-";
}

function numberOrNull(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function parseFloatLoose(v) {
  if (v === null || v === undefined) return null;
  if (typeof v === "number" && Number.isFinite(v)) return v;
  const s = String(v).trim();
  if (!s) return null;
  const m = s.match(/-?\d+(?:\.\d+)?/);
  if (!m) return null;
  const n = Number(m[0]);
  return Number.isFinite(n) ? n : null;
}

function extractYearToken(raw) {
  const m = String(raw || "").match(/(20\d{2})/);
  return m ? Number(m[1]) : null;
}

function walkObject(node, visitor, path = []) {
  if (node === null || node === undefined) return;
  if (Array.isArray(node)) {
    node.forEach((v, i) => walkObject(v, visitor, path.concat(String(i))));
    return;
  }
  if (typeof node === "object") {
    Object.entries(node).forEach(([k, v]) => {
      visitor(k, v, path.concat(k));
      walkObject(v, visitor, path.concat(k));
    });
  }
}

function getParams() {
  const u = new URL(window.location.href);
  return {
    id: Number(u.searchParams.get("id") || 0),
    q: u.searchParams.get("q") || "",
  };
}

function lastYearToken(text) {
  const arr = String(text || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  return arr.length ? arr[arr.length - 1] : "";
}

function buildPriorityTags(row) {
  const tags = [];
  const rowTags = Array.isArray(row.tags) ? row.tags.map((x) => String(x || "").trim()).filter(Boolean) : [];
  const pushTag = (text, cls) => {
    const t = String(text || "").trim();
    if (!t) return;
    if (tags.some((x) => x.text === t)) return;
    tags.push({ text: t, cls });
  };

  if (row.jcr_quartile) {
    pushTag(`JCR ${row.jcr_quartile}`, "tag--jcr");
  }
  if (row.cas_2025) {
    const top = row.is_top === true ? " (Top)" : "";
    pushTag(`中科院${row.cas_2025}${top}`, "tag--cas");
  }
  if (row.hq_level) {
    pushTag(`科协-${row.hq_level}`, "tag--hq");
  }
  if (row.pku_core === true || rowTags.includes("北大核心")) {
    pushTag("北大核心", "tag--pku");
  }
  let cssciType = String(row.cssci_type || "").trim();
  if (!cssciType) {
    if (rowTags.includes("CSSCI(扩展)") || rowTags.includes("CSSCI扩展")) cssciType = "扩展版";
    else if (rowTags.includes("CSSCI")) cssciType = "来源版";
  }
  if (cssciType) {
    pushTag(cssciType === "扩展版" ? "CSSCI(扩展)" : "CSSCI", "tag--cssci");
  }
  let cscdType = String(row.cscd_type || "").trim();
  if (!cscdType) {
    const cscdTag = rowTags.find((t) => t.startsWith("CSCD-"));
    if (cscdTag) cscdType = cscdTag.slice(5);
    else if (rowTags.includes("CSCD(核心)") || rowTags.includes("CSCD核心")) cscdType = "核心库";
    else if (rowTags.includes("CSCD(扩展)") || rowTags.includes("CSCD扩展")) cscdType = "扩展库";
    else if (rowTags.includes("CSCD")) cscdType = "核心库";
  }
  if (cscdType) {
    pushTag(`CSCD-${cscdType}`, "tag--cscd");
  }

  const wosKnown = new Set(["SCI", "SCIE", "SSCI", "ESCI", "AHCI"]);
  const wosOut = new Set();
  for (const raw of rowTags) {
    const upper = String(raw || "").toUpperCase();
    const parts = upper.replace(/[^A-Z]+/g, " ").split(/\s+/).filter(Boolean);
    for (const p of parts) {
      if (wosKnown.has(p)) wosOut.add(p);
    }
    if (upper.includes("SCIE")) wosOut.add("SCIE");
    if (upper.includes("SSCI")) wosOut.add("SSCI");
    if (upper.includes("ESCI")) wosOut.add("ESCI");
    if (upper.includes("AHCI")) wosOut.add("AHCI");
    if (/\bSCI\b/.test(upper.replace(/[^A-Z]/g, " "))) wosOut.add("SCI");
  }
  for (const token of wosOut) {
    pushTag(token, "tag--wos");
  }
  if (rowTags.some((t) => String(t).toUpperCase() === "EI")) {
    pushTag("EI", "tag--ei");
  }
  if (row.warning_latest) {
    pushTag("中科院预警", "tag--warn");
  }
  return tags;
}

function renderTopTags(row) {
  const tags = buildPriorityTags(row);
  els.topTags.innerHTML = tags.length
    ? tags.map((t) => `<span class="tag ${t.cls}">${escapeHtml(t.text)}</span>`).join("")
    : "<span class='tag tag--empty'>无核心标签</span>";
}

function infoButton(infoKey) {
  return `<button class="inline-info" type="button" data-info="${escapeHtml(infoKey)}" aria-label="查看数据说明">?</button>`;
}

function textHash(input) {
  let h = 0;
  const s = String(input || "");
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) % 360;
  }
  return h;
}

function normalizeHttpUrl(raw) {
  const s = String(raw || "").trim();
  if (!s) return "";
  if (/^https?:\/\//i.test(s)) return s;
  return `https://${s}`;
}

const NON_OFFICIAL_HOST_PATTERNS = [
  /(^|\.)dblp\.org$/i,
  /(^|\.)dblp\.uni-trier\.de$/i,
  /(^|\.)letpub\.com\.cn$/i,
  /(^|\.)wikipedia\.org$/i,
  /(^|\.)baidu\.com$/i,
  /(^|\.)resurchify\.com$/i,
  /(^|\.)scijournal\.org$/i,
  /(^|\.)x-mol\.com$/i,
  /(^|\.)aminer\.cn$/i,
  /(^|\.)ccf\.org\.cn$/i,
];

function isLikelyOfficialWebsite(url) {
  if (!url) return false;
  try {
    const u = new URL(url);
    const host = u.hostname.toLowerCase();
    if (NON_OFFICIAL_HOST_PATTERNS.some((r) => r.test(host))) return false;
    if (u.pathname.toLowerCase().includes("/db/journals/")) return false;
    return true;
  } catch (_) {
    return false;
  }
}

function resolveWebsite(j) {
  const normalized = normalizeHttpUrl(j.official_url);
  return isLikelyOfficialWebsite(normalized) ? normalized : "";
}

function parseDomain(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./i, "");
  } catch (_) {
    return "";
  }
}

function buildLogoUrl(url) {
  const domain = parseDomain(url);
  if (!domain) return "";
  return `https://logo.clearbit.com/${domain}?size=360`;
}

function setSpotlightWebsite(url, label = "访问期刊官网") {
  if (!url) {
    els.journalWebsite.href = "#";
    els.journalWebsite.textContent = "官网待识别";
    els.journalWebsite.classList.add("is-disabled");
    return;
  }
  els.journalWebsite.href = url;
  els.journalWebsite.textContent = label;
  els.journalWebsite.classList.remove("is-disabled");
}

function resetSpotlight(reason = "无数据") {
  els.spotlightCover.style.background = "transparent";
  els.spotlightCover.innerHTML = `<p class="placeholder">${escapeHtml(reason)}</p>`;
  els.journalSummary.textContent = "";
  setSpotlightWebsite("");
  els.spotPublisher.textContent = "-";
  if (els.spotIndexType) els.spotIndexType.textContent = "-";
  els.spotOA.textContent = "-";
  els.spotPublishYear.textContent = "-";
  if (els.spotAnnualArticles) els.spotAnnualArticles.textContent = "-";
  setCiteScoreCardState({
    score: null,
    isProxy: false,
    year: "",
    percentile: null,
    meta: "暂无 CiteScore 数据",
    source: "数据来源：待更新",
  });
}

async function fetchElsevierViaApi(issn) {
  const normalizedIssn = String(issn || "").trim();
  if (!normalizedIssn) return { ok: false, reason: "missing_issn", payload: null };

  const url = `${API_BASE}/elsevier/serial-title?issn=${encodeURIComponent(normalizedIssn)}`;
  const headers = { Accept: "application/json" };

  try {
    const resp = await fetch(url, { method: "GET", headers });
    let payload = null;
    try {
      payload = await resp.json();
    } catch (_) {
      payload = null;
    }
    if (!resp.ok) {
      const proxyError = String(payload?.error || "").trim();
      const reason = proxyError ? `api_${proxyError}` : `api_http_${resp.status}`;
      return { ok: false, reason, payload };
    }
    return { ok: true, reason: "", payload };
  } catch (_) {
    return { ok: false, reason: "api_unreachable", payload: null };
  }
}

async function fetchHomepagePreviewImage(url) {
  const normalizedUrl = normalizeHttpUrl(url);
  if (!normalizedUrl) return "";
  if (homepagePreviewImageCache.has(normalizedUrl)) {
    return homepagePreviewImageCache.get(normalizedUrl) || "";
  }

  const endpoint = `${API_BASE}/web/preview-image?url=${encodeURIComponent(normalizedUrl)}`;
  try {
    const resp = await fetch(endpoint, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!resp.ok) {
      homepagePreviewImageCache.set(normalizedUrl, "");
      return "";
    }
    const payload = await resp.json();
    const coverUrl = normalizeHttpUrl(payload?.cover_url || "");
    homepagePreviewImageCache.set(normalizedUrl, coverUrl || "");
    return coverUrl || "";
  } catch (_) {
    homepagePreviewImageCache.set(normalizedUrl, "");
    return "";
  }
}

function buildCiteScoreStars(rating5) {
  const safeRating = Math.max(0, Math.min(Number(rating5) || 0, 5));
  const stars = [];
  for (let i = 0; i < 5; i += 1) {
    const fill = Math.max(0, Math.min(safeRating - i, 1));
    stars.push(
      `<span class="cs-star"><span class="cs-star__base">★</span><span class="cs-star__fill" style="width:${(
        fill * 100
      ).toFixed(1)}%">★</span></span>`
    );
  }
  return stars.join("");
}

function normalizeCiteScoreToStars(score, percentile = null) {
  if (percentile !== null && percentile !== undefined) {
    const p = Math.max(0, Math.min(Number(percentile), 100));
    return (p / 100) * 5;
  }
  const s = Math.max(0, Number(score) || 0);
  return Math.min(s / 20, 5);
}

function deriveQuartileFromPercentile(percentile) {
  const p = Number(percentile);
  if (!Number.isFinite(p)) return "";
  if (p >= 75) return "Q1";
  if (p >= 50) return "Q2";
  if (p >= 25) return "Q3";
  return "Q4";
}

function normalizeCiteScoreSubjectRows(subjects) {
  if (!Array.isArray(subjects)) return [];
  const normalized = subjects
    .map((item) => {
      const level = String(item?.level || "").trim();
      const category = String(item?.category || "").trim();
      const subject = String(item?.subject || "").trim();
      const name = String(item?.name || "").trim();
      const rank = String(item?.rank || "").trim();
      const quartileRaw = String(item?.quartile || "").trim().toUpperCase();
      const quartile = /^Q[1-4]$/.test(quartileRaw)
        ? quartileRaw
        : deriveQuartileFromPercentile(item?.percentile);
      const percentileNum = parseFloatLoose(item?.percentile);
      const percentile = percentileNum !== null ? Math.max(0, Math.min(percentileNum, 100)) : null;
      const displayName = name || [category, subject].filter(Boolean).join(" / ");
      if (!displayName) return null;
      if (!quartile && !rank && percentile === null) return null;
      return {
        level: level || "学科",
        name: displayName,
        rank,
        quartile,
        percentile,
      };
    })
    .filter(Boolean);

  const deduped = [];
  const seen = new Set();
  for (const row of normalized) {
    const key = `${row.level}|${row.name}|${row.quartile}|${row.rank}|${row.percentile}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(row);
  }

  deduped.sort((a, b) => {
    const levelOrder = { 大类: 1, 小类: 2, 学科: 3 };
    const la = levelOrder[a.level] || 9;
    const lb = levelOrder[b.level] || 9;
    if (la !== lb) return la - lb;
    const pa = a.percentile === null ? -1 : a.percentile;
    const pb = b.percentile === null ? -1 : b.percentile;
    if (pa !== pb) return pb - pa;
    return a.name.localeCompare(b.name, "zh-CN");
  });

  return deduped;
}

function formatMetricValue(v, digits = 3) {
  const n = parseFloatLoose(v);
  if (n === null) return "-";
  if (Math.abs(n) >= 100) return n.toFixed(1);
  return n.toFixed(digits).replace(/\.?0+$/, "");
}

function renderCiteScoreMetrics({ year = "", sjr = null, snip = null, isProxy = false } = {}) {
  if (!els.citeScoreMetrics) return;
  const yearText = year ? `${year}年` : "最新";
  const chips = [
    `<span class="citescore-metric-chip"><b>CiteScore</b><em>${escapeHtml(yearText)}</em></span>`,
    `<span class="citescore-metric-chip"><b>SJR</b><em>${escapeHtml(formatMetricValue(sjr, 3))}</em></span>`,
    `<span class="citescore-metric-chip"><b>SNIP</b><em>${escapeHtml(formatMetricValue(snip, 3))}</em></span>`,
  ];
  els.citeScoreMetrics.innerHTML = chips.join("");
  els.citeScoreMetrics.classList.toggle("is-proxy", Boolean(isProxy));
}

function renderCiteScoreBreakdown(subjects, isProxy = false) {
  if (!els.citeScoreBreakdown) return;
  if (isProxy) {
    els.citeScoreBreakdown.innerHTML = "<div class='citescore-breakdown-empty'>当前未获取到官方学科分区明细</div>";
    return;
  }
  const rows = normalizeCiteScoreSubjectRows(subjects);
  if (!rows.length) {
    els.citeScoreBreakdown.innerHTML = "<div class='citescore-breakdown-empty'>暂无学科分区明细</div>";
    return;
  }

  const maxRows = 10;
  const visible = rows.slice(0, maxRows);
  const header = `
    <div class="citescore-breakdown-head">
      <span>学科</span>
      <span>分区</span>
      <span>排名</span>
      <span>百分位</span>
    </div>
  `;
  const body = visible
    .map((row) => {
      const percentileText = row.percentile === null ? "-" : `${Math.round(row.percentile)}%`;
      const fill = row.percentile === null ? 0 : Math.max(0, Math.min(Math.round(row.percentile), 100));
      return `
        <div class="citescore-breakdown-item">
          <div class="citescore-breakdown-name-cell">
            <span class="citescore-breakdown-level">${escapeHtml(row.level)}</span>
            <span class="citescore-breakdown-name" title="${escapeHtml(row.name)}">${escapeHtml(row.name)}</span>
          </div>
          <div class="citescore-breakdown-q">${escapeHtml(row.quartile || "-")}</div>
          <div class="citescore-breakdown-rank">${escapeHtml(row.rank || "-")}</div>
          <div class="citescore-breakdown-percent">
            <span>${escapeHtml(percentileText)}</span>
            <i><b style="width:${fill}%"></b></i>
          </div>
        </div>
      `;
    })
    .join("");
  const extra = rows.length > maxRows ? `<div class="citescore-breakdown-more">另有 ${rows.length - maxRows} 条学科记录</div>` : "";
  els.citeScoreBreakdown.innerHTML = header + body + extra;
}

function renderCiteScoreSourceLine({ sourceText = "", isProxy = false, reason = "" } = {}) {
  if (!els.citeScoreSource) return;
  const normalizedReason = String(reason || "").trim();
  const reasonText = normalizedReason ? mapElsevierFailureReason(normalizedReason) : "";

  let displayText = String(sourceText || "").trim() || "数据来源：待更新";
  if (isProxy && reasonText) {
    displayText = `${displayText} · ${reasonText}`;
  }

  const actionButtons = [];
  if (isProxy) {
    actionButtons.push(`<button class="citescore-inline-btn" type="button" data-citescore-refresh="1">重试</button>`);
  }

  const actionsHtml = actionButtons.length
    ? `<span class="citescore-inline-actions">${actionButtons.join("")}</span>`
    : "";
  els.citeScoreSource.innerHTML = `<span>${escapeHtml(displayText)}</span>${actionsHtml}`;
}

function setCiteScoreCardState({
  score = null,
  year = "",
  percentile = null,
  subjects = [],
  sjr = null,
  snip = null,
  isProxy = false,
  meta = "",
  source = "",
  reason = "",
} = {}) {
  if (!els.citeScoreCard) return;
  const hasScore = score !== null && score !== undefined && Number.isFinite(Number(score));
  const numericScore = hasScore ? Number(score) : null;

  els.citeScoreCard.classList.toggle("is-proxy", Boolean(isProxy));
  els.citeScoreCard.classList.toggle("is-empty", !hasScore);
  els.citeScoreValue.textContent = hasScore ? numericScore.toFixed(numericScore >= 10 ? 1 : 2) : "-";

  if (hasScore) {
    const stars = normalizeCiteScoreToStars(numericScore, percentile);
    if (isProxy) {
      els.citeScoreStars.innerHTML = "<span class='citescore-empty'>代理值（非官方 CiteScore）</span>";
    } else {
      els.citeScoreStars.innerHTML = buildCiteScoreStars(stars);
    }
    renderCiteScoreMetrics({ year, sjr, snip, isProxy });

    const pct = percentile !== null && percentile !== undefined ? Math.max(0, Math.min(Number(percentile), 100)) : null;
    const showPercentile = !isProxy && pct !== null;
    els.citeScorePercentLabel.textContent = "学科百分位";
    els.citeScorePercentValue.textContent = showPercentile ? `${Math.round(pct)}%` : "-";
    els.citeScorePercentFill.style.width = showPercentile ? `${Math.round(pct)}%` : "0%";

    const yearLabel = year ? `${year} 年` : "最新年度";
    els.citeScoreMeta.textContent = meta || `更新：${yearLabel} · CiteScore ${numericScore.toFixed(2)}`;
    renderCiteScoreSourceLine({
      sourceText: source || "数据来源：Scopus CiteScore",
      isProxy,
      reason,
    });
    renderCiteScoreBreakdown(subjects, isProxy);
  } else {
    els.citeScoreStars.innerHTML = "<span class='citescore-empty'>暂无评分</span>";
    renderCiteScoreMetrics({ year, sjr, snip, isProxy });
    els.citeScorePercentLabel.textContent = "学科百分位";
    els.citeScorePercentValue.textContent = "-";
    els.citeScorePercentFill.style.width = "0%";
    els.citeScoreMeta.textContent = meta || "暂无 CiteScore 数据";
    renderCiteScoreSourceLine({
      sourceText: source || "数据来源：待更新",
      isProxy,
      reason,
    });
    renderCiteScoreBreakdown(subjects, isProxy);
  }
}

function normalizeIntroText(text, maxLen = 300) {
  const noLangLabel = String(text || "")
    .replace(/（\s*(?:英语|英語|英文|英文名)\s*[：:]\s*([^（）]+?)\s*）/g, "（$1）")
    .replace(/\(\s*english\s*[：:]\s*([^)]+?)\s*\)/gi, "（$1）");
  const clean = noLangLabel.replace(/\s+/g, " ").trim();
  if (!clean) return "";
  if (clean.length <= maxLen) return clean;
  return `${clean.slice(0, maxLen - 1)}…`;
}

function parseWikidataQid(rawUrl) {
  const m = String(rawUrl || "").match(/Q\d+/i);
  return m ? m[0].toUpperCase() : "";
}

async function fetchWikipediaExtract(title, lang) {
  const t = String(title || "").trim();
  if (!t) return "";
  const params = new URLSearchParams({
    action: "query",
    prop: "extracts",
    exintro: "1",
    explaintext: "1",
    format: "json",
    origin: "*",
    titles: t,
  });
  const url = `https://${lang}.wikipedia.org/w/api.php?${params.toString()}`;
  const payload = await fetchJsonWithTimeout(url, 6500);
  const pages = payload?.query?.pages || {};
  const first = Object.values(pages)[0];
  return normalizeIntroText(first?.extract || "");
}

async function fetchWikidataEntity(qid) {
  const id = String(qid || "").trim().toUpperCase();
  if (!id) return null;
  const params = new URLSearchParams({
    action: "wbgetentities",
    ids: id,
    props: "descriptions|sitelinks|claims",
    languages: "zh|en",
    format: "json",
    origin: "*",
  });
  const url = `https://www.wikidata.org/w/api.php?${params.toString()}`;
  const payload = await fetchJsonWithTimeout(url, 6500);
  return payload?.entities?.[id] || null;
}

function getWikidataClaimFile(entity, prop) {
  return entity?.claims?.[prop]?.[0]?.mainsnak?.datavalue?.value || "";
}

function buildCommonsImageUrl(fileName, width = 900) {
  const file = String(fileName || "").trim();
  if (!file) return "";
  return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(file)}?width=${width}`;
}

function pickWikidataCoverUrl(entity) {
  const coverFile = getWikidataClaimFile(entity, "P18");
  if (coverFile) return buildCommonsImageUrl(coverFile, 920);
  const logoFile = getWikidataClaimFile(entity, "P154");
  if (logoFile) return buildCommonsImageUrl(logoFile, 760);
  return "";
}

async function fetchJournalIntro(j, source, prefetchedEntity = null) {
  const qid = parseWikidataQid(source?.ids?.wikidata);
  if (qid) {
    const entity = prefetchedEntity || (await fetchWikidataEntity(qid));
    const zhTitle = entity?.sitelinks?.zhwiki?.title || "";
    const enTitle = entity?.sitelinks?.enwiki?.title || source?.display_name || j.title || "";

    const zhExtract = await fetchWikipediaExtract(zhTitle, "zh");
    if (zhExtract) return zhExtract;

    const enExtract = await fetchWikipediaExtract(enTitle, "en");
    if (enExtract) return enExtract;

    const zhDesc = normalizeIntroText(entity?.descriptions?.zh?.value || "", 180);
    if (zhDesc) return zhDesc;
    const enDesc = normalizeIntroText(entity?.descriptions?.en?.value || "", 180);
    if (enDesc) return enDesc;
  }

  const titleZh = await fetchWikipediaExtract(j.title, "zh");
  if (titleZh) return titleZh;

  const titleEn = await fetchWikipediaExtract(source?.display_name || j.title, "en");
  if (titleEn) return titleEn;

  return "";
}

function renderSpotlightCover(j, latestCas, website, externalCoverUrl = "") {
  const hue = textHash(j.title || j.issn || j.cn_number || "");
  const bg = `linear-gradient(145deg, hsl(${hue} 54% 30%), hsl(${(hue + 28) % 360} 48% 24%))`;
  const previewUrl = externalCoverUrl || "";
  const title = String(j.title || "Unknown Journal").trim();
  const issnText = safe(j.issn);

  els.spotlightCover.classList.toggle("spotlight-cover--fallback", !previewUrl);
  els.spotlightCover.style.background = previewUrl ? "#f1ece3" : bg;
  els.spotlightCover.innerHTML = `
    ${previewUrl ? `<img class="spotlight-cover__bg spotlight-cover__bg--cover" src="${escapeHtml(previewUrl)}" alt="${escapeHtml(
      `${title} 封面`
    )}" loading="lazy" onerror="const p=this.closest('.spotlight-cover');if(p){p.classList.add('spotlight-cover--fallback');p.style.background='${escapeHtml(
      bg
    )}';}this.remove();" />` : ""}
    <div class="spotlight-cover__classic" aria-hidden="${previewUrl ? "true" : "false"}">
      <div class="spotlight-cover__classic-frame"></div>
      <div class="spotlight-cover__classic-ornament"></div>
      <div class="spotlight-cover__classic-kicker">Journal Archive</div>
      <div class="spotlight-cover__classic-title">${escapeHtml(title)}</div>
      <div class="spotlight-cover__classic-foot">${escapeHtml(issnText)}</div>
    </div>
  `;
}

async function fetchJsonWithTimeout(url, timeoutMs = 4500, fetchOptions = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, { ...fetchOptions, signal: controller.signal });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (_) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function normalizeTitleKey(v) {
  return String(v || "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu, "");
}

function pickOpenAlexSource(results, j) {
  if (!Array.isArray(results) || !results.length) return null;
  const targetTitle = normalizeTitleKey(j.title);
  const targetIssn = String(j.issn || "").replace("-", "");
  const targetEissn = String(j.eissn || "").replace("-", "");

  for (const item of results) {
    const name = normalizeTitleKey(item.display_name);
    if (targetTitle && name === targetTitle) return item;
  }
  for (const item of results) {
    const issns = Array.isArray(item.issn) ? item.issn.map((x) => String(x || "").replace("-", "")) : [];
    if ((targetIssn && issns.includes(targetIssn)) || (targetEissn && issns.includes(targetEissn))) {
      return item;
    }
  }
  return results[0];
}

async function fetchOpenAlexProfile(j) {
  const select = "id,ids,display_name,homepage_url,host_organization_name,is_oa,issn,issn_l,summary_stats,works_count,cited_by_count";
  const issns = [j.issn, j.eissn].filter(Boolean);
  for (const issn of issns) {
    const url = `https://api.openalex.org/sources?filter=issn:${encodeURIComponent(issn)}&per-page=6&select=${select}`;
    const payload = await fetchJsonWithTimeout(url);
    const hit = pickOpenAlexSource(payload?.results || [], j);
    if (hit) return hit;
  }

  if (j.title) {
    const url = `https://api.openalex.org/sources?search=${encodeURIComponent(j.title)}&per-page=8&select=${select}`;
    const payload = await fetchJsonWithTimeout(url);
    const hit = pickOpenAlexSource(payload?.results || [], j);
    if (hit) return hit;
  }
  return null;
}

function parseOpenAlexSourceId(rawId) {
  const m = String(rawId || "").match(/S\d+/i);
  return m ? m[0].toUpperCase() : "";
}

async function fetchOpenAlexStartYear(source) {
  const sourceId = parseOpenAlexSourceId(source?.id);
  if (!sourceId) return null;

  const url = `https://api.openalex.org/works?filter=primary_location.source.id:${encodeURIComponent(
    sourceId
  )}&sort=publication_year:asc&per-page=1&select=publication_year`;
  const payload = await fetchJsonWithTimeout(url, 6000);
  const y = Number(payload?.results?.[0]?.publication_year);
  if (!Number.isFinite(y)) return null;
  const now = new Date().getFullYear();
  if (y < 1600 || y > now + 1) return null;
  return y;
}

async function fetchOpenAlexAnnualArticlesSeries(source) {
  const sourceId = parseOpenAlexSourceId(source?.id);
  if (!sourceId) return [];
  if (annualArticlesSeriesCache.has(sourceId)) {
    return annualArticlesSeriesCache.get(sourceId) || [];
  }

  const url = `https://api.openalex.org/works?filter=primary_location.source.id:${encodeURIComponent(
    sourceId
  )}&group_by=publication_year&per-page=200`;
  const payload = await fetchJsonWithTimeout(url, 7000);
  const groups = Array.isArray(payload?.group_by) ? payload.group_by : [];
  if (!groups.length) {
    annualArticlesSeriesCache.set(sourceId, []);
    return [];
  }

  const currentYear = new Date().getFullYear();
  const rows = groups
    .map((g) => {
      const y = Number(g?.key);
      const c = Number(g?.count);
      if (!Number.isFinite(y) || !Number.isFinite(c)) return null;
      if (y < 1600 || y > currentYear + 1 || c < 0) return null;
      return { year: Math.trunc(y), count: Math.trunc(c) };
    })
    .filter(Boolean)
    .sort((a, b) => a.year - b.year);

  annualArticlesSeriesCache.set(sourceId, rows);
  return rows;
}

function pickLatestCompletedAnnualArticles(rows) {
  if (!Array.isArray(rows) || !rows.length) return null;
  const currentYear = new Date().getFullYear();
  const sorted = [...rows].sort((a, b) => b.year - a.year);
  const latestCompleted = sorted.find((r) => r.year < currentYear) || sorted[0];
  return latestCompleted || null;
}

function asArray(v) {
  if (Array.isArray(v)) return v;
  if (v === null || v === undefined) return [];
  return [v];
}

function parseIntLoose(v) {
  if (typeof v === "number" && Number.isFinite(v)) return Math.trunc(v);
  const m = String(v || "").match(/-?\d+/);
  if (!m) return null;
  const n = Number(m[0]);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

function mapElsevierSubjectAreas(entry) {
  const areaMap = new Map();
  const areas = asArray(entry?.["subject-area"] || entry?.subjectArea || entry?.subject_area);
  for (const area of areas) {
    if (!area || typeof area !== "object") continue;
    const code = parseIntLoose(area?.["@code"] ?? area?.code ?? area?.subjectCode);
    if (code === null) continue;
    const name = String(area?.["$"] ?? area?.name ?? area?.subject ?? area?.subjectName ?? "").trim();
    const abbrev = String(area?.["@abbrev"] ?? area?.abbrev ?? "").trim();
    areaMap.set(String(code), { name, abbrev });
  }
  return areaMap;
}

function classifyAsjcLevel(subjectCode) {
  const code = parseIntLoose(subjectCode);
  if (code === null) return "学科";
  return code % 100 === 0 ? "大类" : "小类";
}

function parseElsevierSubjectRanks(rawRanks, subjectAreaMap) {
  const subjects = [];
  for (const row of asArray(rawRanks)) {
    if (!row || typeof row !== "object") continue;
    const code = parseIntLoose(row?.subjectCode ?? row?.["@subjectCode"] ?? row?.code ?? row?.["@code"]);
    const areaFromMap = code === null ? null : subjectAreaMap.get(String(code));
    const majorCode = code === null ? null : Math.floor(code / 100) * 100;
    const majorAreaFromMap = majorCode === null ? null : subjectAreaMap.get(String(majorCode));
    const explicitName = String(row?.subjectName ?? row?.subjectLongName ?? row?.subject ?? row?.category ?? "").trim();
    const displayName = explicitName || areaFromMap?.name || (code === null ? "" : `ASJC ${code}`);
    const rankRaw = String(row?.rank ?? row?.["@rank"] ?? "").trim();
    const rankOutOfRaw = row?.rankOutOf ?? row?.["@rankOutOf"] ?? row?.total ?? row?.["@total"];
    const rankOutOf = parseIntLoose(rankOutOfRaw);
    let rank = /^\d+(?:\.0+)?$/.test(rankRaw) ? String(Math.round(Number(rankRaw))) : rankRaw;
    if (rank && rankOutOf && !rank.includes("/")) rank = `${rank}/${rankOutOf}`;
    const percentile = parseFloatLoose(row?.percentile ?? row?.["@percentile"] ?? row?.percent);
    const quartileRaw = String(row?.quartile ?? row?.["@quartile"] ?? "").trim().toUpperCase();
    const quartile = /^Q[1-4]$/.test(quartileRaw) ? quartileRaw : deriveQuartileFromPercentile(percentile);
    if (!displayName && !rank && percentile === null && !quartile) continue;
    subjects.push({
      level: classifyAsjcLevel(code),
      category: majorAreaFromMap?.name || areaFromMap?.name || "",
      subject: explicitName || displayName,
      name: displayName,
      quartile,
      rank,
      percentile,
    });
  }
  return normalizeCiteScoreSubjectRows(subjects);
}

function getByPath(root, path) {
  let cur = root;
  for (const k of path) {
    if (cur === null || cur === undefined) return null;
    cur = cur[k];
  }
  return cur;
}

function collectElsevierMetricCandidates(entry, metricKeys) {
  const keys = metricKeys.map((k) => String(k).toLowerCase());
  const candidates = [];
  walkObject(entry, (key, value, path) => {
    const keyLower = String(key || "").toLowerCase();
    const pathText = path.map((x) => String(x).toLowerCase()).join(">");
    const hasMetricScope = keys.some((k) => keyLower === k || keyLower.includes(k) || pathText.includes(k));
    if (!hasMetricScope) return;
    if (keyLower.includes("rank") || keyLower.includes("percent") || keyLower.includes("year")) return;
    if (pathText.includes("subjectrank")) return;
    const num = parseFloatLoose(value);
    if (num === null) return;
    if (num < 0 || num > 10000) return;
    const parent = getByPath(entry, path.slice(0, -1)) || {};
    const year = extractYearToken(parent?.["@year"] ?? parent?.year ?? parent?.date ?? "");
    if (pathText.includes("subjects")) return;
    candidates.push({ value: num, year: year || 0, pathText });
  });
  return candidates;
}

function pickElsevierMetric(entry, metricKeys) {
  const candidates = collectElsevierMetricCandidates(entry, metricKeys);
  if (!candidates.length) return null;
  candidates.sort((a, b) => {
    if (a.year !== b.year) return b.year - a.year;
    return b.value - a.value;
  });
  return candidates[0].value;
}

function parseElsevierYearInfoRows(entry, subjectAreaMap) {
  const yearInfoRoot = entry?.citeScoreYearInfoList || entry?.["citeScoreYearInfoList"] || {};
  const yearRows = asArray(yearInfoRoot?.citeScoreYearInfo || yearInfoRoot?.["citeScoreYearInfo"]);
  const parsedRows = [];

  for (const row of yearRows) {
    if (!row || typeof row !== "object") continue;
    const infoList = asArray(row?.citeScoreInformationList || row?.["citeScoreInformationList"]);
    const infoNodes = [];
    for (const item of infoList) {
      if (!item || typeof item !== "object") continue;
      const scoreNodes = asArray(item?.citeScoreInfo || item?.["citeScoreInfo"]);
      if (scoreNodes.length) {
        infoNodes.push(...scoreNodes);
      } else {
        infoNodes.push(item);
      }
    }
    if (!infoNodes.length) infoNodes.push(row);

    let scoreNode = infoNodes[0];
    for (const item of infoNodes) {
      const scoreVal = parseFloatLoose(item?.citeScore ?? item?.citeScoreCurrentMetric ?? item?.currentMetric);
      if (scoreVal !== null) {
        scoreNode = item;
        break;
      }
    }

    const year = extractYearToken(row?.["@year"] ?? row?.year ?? scoreNode?.year ?? scoreNode?.["@year"]);
    const score = parseFloatLoose(scoreNode?.citeScore ?? scoreNode?.citeScoreCurrentMetric ?? scoreNode?.currentMetric);
    const subjects = parseElsevierSubjectRanks(
      scoreNode?.citeScoreSubjectRank ??
        scoreNode?.["citeScoreSubjectRank"] ??
        row?.citeScoreSubjectRank ??
        row?.["citeScoreSubjectRank"],
      subjectAreaMap
    );
    const subjectPercentiles = subjects.map((x) => parseFloatLoose(x.percentile)).filter((x) => x !== null);
    const percentileFromSubjects = subjectPercentiles.length ? Math.max(...subjectPercentiles) : null;
    const percentileDirect = parseFloatLoose(scoreNode?.percentile ?? row?.percentile);
    const percentile = percentileFromSubjects !== null ? percentileFromSubjects : percentileDirect;
    const status = String(row?.["@status"] ?? row?.status ?? "").trim();

    if (score === null && !subjects.length && percentile === null) continue;
    parsedRows.push({
      year: year ? String(year) : "",
      score,
      percentile: percentile === null ? null : Math.max(0, Math.min(percentile, 100)),
      status,
      subjects,
    });
  }

  parsedRows.sort((a, b) => {
    const yearDiff = yearNum(b.year) - yearNum(a.year);
    if (yearDiff !== 0) return yearDiff;
    const scoreA = a.score === null ? -1 : a.score;
    const scoreB = b.score === null ? -1 : b.score;
    return scoreB - scoreA;
  });
  return parsedRows;
}

function parseElsevierCiteScorePayload(payload) {
  const entry = payload?.["serial-metadata-response"]?.entry?.[0] || payload?.entry?.[0] || payload;
  if (!entry || typeof entry !== "object") {
    return { score: null, year: "", percentile: null, subjects: [], status: "", sjr: null, snip: null };
  }

  const subjectAreaMap = mapElsevierSubjectAreas(entry);
  const sjr = pickElsevierMetric(entry, ["sjr"]);
  const snip = pickElsevierMetric(entry, ["snip"]);
  const yearRows = parseElsevierYearInfoRows(entry, subjectAreaMap);
  if (yearRows.length) {
    const best = yearRows.find((x) => x.score !== null) || yearRows[0];
    return {
      score: best.score,
      year: best.year,
      percentile: best.percentile,
      subjects: best.subjects || [],
      status: best.status || "",
      sjr,
      snip,
    };
  }

  const scoreCandidates = [];
  const percentileCandidates = [];
  const yearCandidates = [];
  walkObject(entry, (key, value) => {
    const k = String(key || "").toLowerCase();
    const n = parseFloatLoose(value);
    if (n !== null) {
      if (k.includes("citescore") && !k.includes("percent") && !k.includes("rank") && !k.includes("year")) {
        scoreCandidates.push(n);
      }
      if (k.includes("percent")) {
        percentileCandidates.push(n);
      }
    }
    if (k.includes("year")) {
      const y = extractYearToken(value);
      if (y) yearCandidates.push(y);
    }
  });

  const validScores = scoreCandidates.filter((x) => x >= 0 && x <= 500);
  const validPercentiles = percentileCandidates.filter((x) => x >= 0 && x <= 100);
  const score = validScores.length ? Math.max(...validScores) : null;
  const percentile = validPercentiles.length ? Math.max(...validPercentiles) : null;
  const year = yearCandidates.length ? String(Math.max(...yearCandidates)) : "";
  const fallbackSubjects = parseElsevierSubjectRanks(entry?.citeScoreSubjectRank || entry?.["citeScoreSubjectRank"], subjectAreaMap);
  return {
    score,
    year,
    percentile,
    subjects: fallbackSubjects,
    status: "",
    sjr,
    snip,
  };
}

async function fetchElsevierCiteScore(j) {
  const issns = [j.issn, j.eissn].filter(Boolean);
  if (!issns.length) {
    return {
      score: null,
      year: "",
      percentile: null,
      subjects: [],
      status: "",
      sjr: null,
      snip: null,
      source: "数据来源：暂缺 ISSN",
      isProxy: false,
      reason: "missing_issn",
    };
  }

  const failReasons = [];
  for (const rawIssn of issns) {
    const issn = String(rawIssn).trim();
    if (!issn) continue;

    const proxy = await fetchElsevierViaApi(issn);
    if (proxy.ok && proxy.payload) {
      const parsed = parseElsevierCiteScorePayload(proxy.payload);
      if (parsed.score !== null || parsed.sjr !== null || parsed.snip !== null || (parsed.subjects || []).length) {
        const statusText = parsed.status ? ` · ${parsed.status}` : "";
        return {
          ...parsed,
          source: `数据来源：Scopus CiteScore${statusText}`,
          isProxy: false,
          reason: "",
        };
      }
      failReasons.push("api_no_metric");
    } else {
      failReasons.push(proxy.reason || "api_failed");
    }
  }

  const reason = failReasons[0] || "elsevier_unavailable";
  return {
    score: null,
    year: "",
    percentile: null,
    subjects: [],
    status: "",
    sjr: null,
    snip: null,
    source: "数据来源：Scopus CiteScore",
    isProxy: false,
    reason,
  };
}

function mapElsevierFailureReason(reason) {
  const r = String(reason || "").trim();
  if (!r) return "";
  if (r === "openalex_unavailable") return "无法识别期刊来源";
  if (r === "citescore_request_failed") return "请求失败";
  if (r === "missing_issn") return "缺少 ISSN";
  if (r === "api_missing_api_key") return "服务端尚未配置 Elsevier Key";
  if (r === "api_elsevier_unreachable") return "Elsevier 服务暂不可达";
  if (r === "api_unreachable") return "CiteScore 服务暂不可用";
  if (r.startsWith("api_http_401")) return "CiteScore 服务认证失败";
  if (r.startsWith("api_http_403")) return "CiteScore 服务请求被拒绝";
  if (r.startsWith("api_http_429")) return "CiteScore 服务请求超限";
  if (r.startsWith("api_elsevier_http_error")) return "Elsevier 接口返回错误";
  if (r === "api_no_metric") return "Elsevier 返回中缺少所需指标字段";
  return `Elsevier 不可用（${r}）`;
}

function buildOpenAlexProxyCiteScore(source, elsevierReason = "") {
  const proxy = parseFloatLoose(source?.summary_stats?.["2yr_mean_citedness"]);
  const reasonText = mapElsevierFailureReason(elsevierReason);
  if (proxy === null) {
    return {
      score: null,
      year: "",
      percentile: null,
      subjects: [],
      status: "",
      sjr: null,
      snip: null,
      source: "数据来源：OpenAlex",
      isProxy: true,
      reason: elsevierReason || "",
      meta: reasonText ? `当前暂未获取到官方 CiteScore 数据（${reasonText}）。` : "当前暂未获取到官方 CiteScore 数据。",
    };
  }

  const works = parseFloatLoose(source?.works_count);
  const citedBy = parseFloatLoose(source?.cited_by_count);
  const pieces = [];
  if (works !== null) pieces.push(`Works ${Math.round(works).toLocaleString()}`);
  if (citedBy !== null) pieces.push(`Citations ${Math.round(citedBy).toLocaleString()}`);

  return {
    score: proxy,
    year: "近2年",
    percentile: null,
    subjects: [],
    status: "",
    sjr: null,
    snip: null,
    source: "数据来源：OpenAlex（参考值）",
    isProxy: true,
    reason: elsevierReason || "",
    meta: reasonText
      ? `当前显示的是参考值（${reasonText}）。${pieces.length ? ` 参考信息：${pieces.join(" · ")}` : ""}`
      : pieces.length
      ? `参考信息：${pieces.join(" · ")}`
      : "当前显示的是参考值。",
  };
}

async function fetchCiteScoreMetric(j, source) {
  const scopus = await fetchElsevierCiteScore(j);
  if (scopus.score !== null || scopus.sjr !== null || scopus.snip !== null || (scopus.subjects || []).length) return scopus;
  return buildOpenAlexProxyCiteScore(source, scopus.reason || "");
}

async function refreshCiteScoreForCurrentJournal() {
  const j = pageState.journal;
  if (!j) return;

  let source = pageState.openAlexSource;
  if (!source) {
    source = await fetchOpenAlexProfile(j);
    pageState.openAlexSource = source || null;
  }

  if (!source) {
    setCiteScoreCardState({
      score: null,
      isProxy: true,
      year: "",
      percentile: null,
      meta: "无法获取期刊来源信息，暂不能刷新 CiteScore。",
      source: "数据来源：暂不可用",
      reason: "openalex_unavailable",
    });
    return;
  }

  setCiteScoreCardState({
    score: null,
    isProxy: false,
    year: "",
    percentile: null,
    meta: "正在刷新 CiteScore…",
    source: "数据来源：正在更新",
    reason: "",
  });

  const citeScore = await fetchCiteScoreMetric(j, source);
  setCiteScoreCardState({
    score: citeScore.score,
    year: citeScore.year,
    percentile: citeScore.percentile,
    subjects: citeScore.subjects || [],
    sjr: citeScore.sjr,
    snip: citeScore.snip,
    isProxy: citeScore.isProxy,
    meta: citeScore.meta || "",
    source: citeScore.source || "",
    reason: citeScore.reason || "",
  });
}

async function enrichSpotlightFromOpenAlex(j, latestCas) {
  const source = await fetchOpenAlexProfile(j);
  pageState.openAlexSource = source || null;
  if (!source) {
    const fallbackWebsite = resolveWebsite(j);
    if (fallbackWebsite) {
      setSpotlightWebsite(fallbackWebsite, "访问期刊官网");
      const fallbackCover = await fetchHomepagePreviewImage(fallbackWebsite);
      if (fallbackCover) {
        renderSpotlightCover(j, latestCas, fallbackWebsite, fallbackCover);
      }
    }

    const introWithoutSource = await fetchJournalIntro(j, null, null);
    els.journalSummary.textContent = introWithoutSource || "暂无可用的公开期刊简介。";
    setCiteScoreCardState({
      score: null,
      isProxy: false,
      year: "",
      percentile: null,
      meta: "暂无 CiteScore 数据",
      source: "数据来源：暂不可用",
      reason: "openalex_unavailable",
    });
    renderAnnualArticlesTrend([]);
    return;
  }

  const homepage = normalizeHttpUrl(source.homepage_url || "");
  const fallbackWebsite = resolveWebsite(j);
  const effectiveWebsite = homepage || fallbackWebsite;
  if (effectiveWebsite) {
    setSpotlightWebsite(effectiveWebsite, "访问期刊官网");
  }

  const homepageCoverPromise = effectiveWebsite ? fetchHomepagePreviewImage(effectiveWebsite) : Promise.resolve("");

  const qid = parseWikidataQid(source?.ids?.wikidata);
  const wikidataEntityPromise = qid ? fetchWikidataEntity(qid).catch(() => null) : Promise.resolve(null);
  const [homepageCover, wikidataEntity] = await Promise.all([homepageCoverPromise, wikidataEntityPromise]);
  const wikidataCover = pickWikidataCoverUrl(wikidataEntity);
  const selectedCover = homepageCover || wikidataCover || "";
  if (selectedCover || effectiveWebsite) {
    renderSpotlightCover(j, latestCas, effectiveWebsite, selectedCover);
  }

  if ((!j.publisher || j.publisher === "-") && source.host_organization_name) {
    els.spotPublisher.textContent = String(source.host_organization_name);
  }
  if ((!j.oa_status || j.oa_status === "-") && typeof source.is_oa === "boolean") {
    els.spotOA.textContent = source.is_oa ? "是" : "否";
  }

  const startYear = await fetchOpenAlexStartYear(source);
  if (startYear) {
    els.spotPublishYear.textContent = String(startYear);
  }

  const annualSeries = await fetchOpenAlexAnnualArticlesSeries(source);
  const annual = pickLatestCompletedAnnualArticles(annualSeries);
  if (annual && els.spotAnnualArticles) {
    els.spotAnnualArticles.textContent = `${annual.year} 年 · ${annual.count.toLocaleString()} 篇`;
  }
  renderAnnualArticlesTrend(annualSeries);

  const citeScore = await fetchCiteScoreMetric(j, source);
  setCiteScoreCardState({
    score: citeScore.score,
    year: citeScore.year,
    percentile: citeScore.percentile,
    subjects: citeScore.subjects || [],
    sjr: citeScore.sjr,
    snip: citeScore.snip,
    isProxy: citeScore.isProxy,
    meta: citeScore.meta || "",
    source: citeScore.source || "",
    reason: citeScore.reason || "",
  });

  const intro = await fetchJournalIntro(j, source, wikidataEntity);
  els.journalSummary.textContent = intro || "暂无可用的公开期刊简介。";
}

function renderSpotlight(j, latestCas, indexTypeText = "-") {
  const website = resolveWebsite(j);
  renderSpotlightCover(j, latestCas, website);
  setSpotlightWebsite(website, "访问期刊官网");

  els.journalSummary.textContent = "正在从公开知识库加载期刊简介…";
  els.spotPublisher.textContent = safe(j.publisher);
  if (els.spotIndexType) els.spotIndexType.textContent = safe(indexTypeText);
  els.spotOA.textContent = safe(j.oa_status);
  els.spotPublishYear.textContent = "-";
  if (els.spotAnnualArticles) els.spotAnnualArticles.textContent = "-";
  setCiteScoreCardState({
    score: null,
    isProxy: false,
    year: "",
    percentile: null,
    meta: "正在加载 CiteScore…",
    source: "数据来源：正在更新",
    reason: "",
  });
}

function renderRow(j, meta) {
  els.title.textContent = j.title || "未知期刊";
  els.subtitle.textContent = [j.issn, j.cn_number].filter(Boolean).join(" / ") || "无 ISSN/CN 信息";
  renderTopTags(j);

  const ifYear = safe(j.if_year || lastYearToken(meta.showjcr_jcr_year)).replace(/^-$/, "");
  const casYear = safe(j.cas_year || lastYearToken(meta.showjcr_fqb_year)).replace(/^-$/, "");
  const ifAcademicYear = formatIFAcademicYear(ifYear);
  const ifLabel = ifAcademicYear ? `IF (${ifAcademicYear})` : "IF";
  const jcrLabel = ifYear ? `JCR分区 (${ifYear})` : "JCR分区";
  const casLabel = casYear ? `中科院分区（${casYear}）` : "中科院分区";
  const warningLabel = j.warning_latest_year ? `中科院预警 (${j.warning_latest_year})` : "中科院预警";
  const latestCas = [...(Array.isArray(j.cas_history) ? j.cas_history : [])].sort((a, b) => yearNum(b.year) - yearNum(a.year))[0];
  pageState.journal = j;
  pageState.latestCas = latestCas || null;
  pageState.openAlexSource = null;
  const casText = j.cas_2025 ? `${j.cas_2025}${j.is_top === true ? " (Top)" : ""}` : "-";
  const casSubText = formatCASSubcategoriesMultiline(latestCas?.subcategories);
  const indexSignals = collectIndexSignals(j, latestCas);
  const inclusionTypeText = buildInclusionTypeText(indexSignals);
  const ssciText = indexSignals.hasSSCI ? "是" : "-";
  const pkuCoreText = j.pku_core ? "是" : "-";
  const cssciText = (() => {
    if (j.cssci_type) return safe(j.cssci_type);
    const tags = Array.isArray(j.tags) ? j.tags : [];
    if (tags.includes("CSSCI(扩展)")) return "扩展版";
    if (tags.includes("CSSCI")) return "来源版";
    return "-";
  })();

  renderSpotlight(j, latestCas, inclusionTypeText);
  enrichSpotlightFromOpenAlex(j, latestCas).catch(() => {
    els.journalSummary.textContent = "暂无可用的公开期刊简介。";
    setCiteScoreCardState({
      score: null,
      isProxy: false,
      year: "",
      percentile: null,
      meta: "CiteScore 请求失败",
      source: "数据来源：暂不可用",
      reason: "citescore_request_failed",
    });
  });

  const kv = [
    { k: "ISSN", v: safe(j.issn) },
    { k: "eISSN", v: safe(j.eissn) },
    { k: "CN号", v: safe(j.cn_number) },
    { k: ifLabel, v: safe(j.if_2023), info: "showjcr" },
    { k: jcrLabel, v: safe(j.jcr_quartile), info: "showjcr" },
    { k: casLabel, v: casText, info: "showjcr" },
    { k: `中科院大类${casYear ? `（${casYear}）` : ""}`, v: safe(latestCas?.category || ""), info: "showjcr", span: 2 },
    { k: `中科院小类${casYear ? `（${casYear}）` : ""}`, v: safe(casSubText), info: "showjcr", span: 2, multiline: true },
    { k: "SSCI", v: ssciText },
    { k: "CSCD", v: safe(j.cscd_type) },
    { k: "北大核心", v: pkuCoreText },
    { k: "CSSCI", v: cssciText },
    { k: warningLabel, v: safe(j.warning_latest), info: "warning", span: 2 },
  ];

  els.coreGrid.innerHTML = kv
    .map((item) => {
      const label = escapeHtml(item.k);
      const cls = item.span === 2 ? "kv is-span-2" : "kv";
      const valueCls = item.multiline ? "v is-multiline" : "v";
      return `<div class="${cls}"><div class="k">${label}</div><div class="${valueCls}">${escapeHtml(item.v)}</div></div>`;
    })
    .join("");
}

function buildIFTrend(ifRows) {
  const rows = ifRows
    .map((r) => ({ year: String(r.year || ""), value: numberOrNull(r.if_value) }))
    .filter((r) => r.value !== null)
    .sort((a, b) => yearNum(a.year) - yearNum(b.year));

  if (!rows.length) {
    return "<p class='placeholder'>可绘制趋势的数据不足</p>";
  }

  const width = 640;
  const height = 280;
  const padLeft = 66;
  const padRight = 18;
  const padTop = 18;
  const padBottom = 52;
  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const values = rows.map((r) => Number(r.value));
  const minData = Math.min(...values);
  const maxData = Math.max(...values);

  const rawRange = Math.max(maxData - minData, 1e-6);
  const rawStep = rawRange / 4;
  const mag = 10 ** Math.floor(Math.log10(rawStep));
  const norm = rawStep / mag;
  const stepBase = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10;
  const tickStep = stepBase * mag;
  const tickDecimals = (() => {
    let s = Math.abs(Number(tickStep));
    if (!Number.isFinite(s) || s <= 0) return 0;
    let decimals = 0;
    while (decimals < 6 && Math.abs(s - Math.round(s)) > 1e-9) {
      s *= 10;
      decimals += 1;
    }
    return decimals;
  })();

  let minV = Math.floor(minData / tickStep) * tickStep;
  let maxV = Math.ceil(maxData / tickStep) * tickStep;
  if (minV === maxV) {
    minV -= tickStep;
    maxV += tickStep;
  }

  const xAt = (i) => {
    if (rows.length === 1) return padLeft + chartW / 2;
    return padLeft + (i * chartW) / (rows.length - 1);
  };
  const yAt = (v) => padTop + ((maxV - v) * chartH) / (maxV - minV);

  const points = rows.map((r, i) => ({ x: xAt(i), y: yAt(Number(r.value)), year: r.year, value: r.value }));
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");
  const areaPath = [
    `M${points[0].x.toFixed(2)} ${(height - padBottom).toFixed(2)}`,
    ...points.map((p) => `L${p.x.toFixed(2)} ${p.y.toFixed(2)}`),
    `L${points[points.length - 1].x.toFixed(2)} ${(height - padBottom).toFixed(2)}`,
    "Z",
  ].join(" ");

  const yTicks = [];
  for (let v = minV; v <= maxV + tickStep * 0.5; v += tickStep) {
    yTicks.push(Number(v.toFixed(6)));
  }

  const yGrid = yTicks
    .map((v) => {
      const y = yAt(v);
      return `<line x1="${padLeft}" y1="${y.toFixed(2)}" x2="${(width - padRight).toFixed(2)}" y2="${y.toFixed(
        2
      )}" class="if-grid-line"></line>`;
    })
    .join("");

  const yLabels = yTicks
    .map((v) => {
      const y = yAt(v);
      const text = Number(v).toFixed(tickDecimals);
      return `<text x="${(padLeft - 10).toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="end" class="if-tick-label">${escapeHtml(
        text
      )}</text>`;
    })
    .join("");

  const xTicks = points
    .map((p) => {
      const y0 = height - padBottom;
      return `<line x1="${p.x.toFixed(2)}" y1="${y0.toFixed(2)}" x2="${p.x.toFixed(2)}" y2="${(y0 + 5).toFixed(
        2
      )}" class="if-axis-tick"></line>`;
    })
    .join("");

  const xLabels = points
    .map((p, idx) => {
      const isFirst = idx === 0;
      const isLast = idx === points.length - 1;
      const anchor = isFirst ? "start" : isLast ? "end" : "middle";
      const x = p.x + (isFirst ? 4 : isLast ? -4 : 0);
      return `<text x="${x.toFixed(2)}" y="${(height - 18).toFixed(2)}" text-anchor="${anchor}" class="if-tick-label">${escapeHtml(
        formatIFAcademicYear(p.year) || p.year
      )}</text>`;
    })
    .join("");

  const pointDots = points
    .map(
      (p) =>
        `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="3.6" class="if-trend-dot"><title>${escapeHtml(
          `${formatIFAcademicYear(p.year) || p.year} · IF ${p.value}`
        )}</title></circle>`
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" class="if-trend-svg" role="img" aria-label="IF 历年变化趋势图">
      ${yGrid}
      <line x1="${padLeft}" y1="${(height - padBottom).toFixed(2)}" x2="${(width - padRight).toFixed(
        2
      )}" y2="${(height - padBottom).toFixed(2)}" class="if-axis-line"></line>
      <line x1="${padLeft}" y1="${padTop}" x2="${padLeft}" y2="${(height - padBottom).toFixed(2)}" class="if-axis-line"></line>
      <path d="${areaPath}" class="if-trend-area"></path>
      <path d="${linePath}" class="if-trend-line"></path>
      ${pointDots}
      ${xTicks}
      ${xLabels}
      ${yLabels}
      <text x="16" y="${(height / 2).toFixed(2)}" text-anchor="middle" class="if-axis-title" transform="rotate(-90 16 ${
        height / 2
      })">影响因子 (IF)</text>
    </svg>
  `;
}

function buildCASTrend(casRows) {
  const rows = casRows
    .map((r) => ({ year: String(r.year || ""), rankText: String(r.rank || ""), rank: casRankNumber(r.rank) }))
    .filter((r) => r.rank !== null)
    .sort((a, b) => yearNum(a.year) - yearNum(b.year));

  if (!rows.length) {
    return "<p class='placeholder'>暂无可绘制的中科院分区趋势</p>";
  }

  const width = 640;
  const height = 280;
  const padLeft = 66;
  const padRight = 18;
  const padTop = 18;
  const padBottom = 52;
  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const xAt = (i) => {
    if (rows.length === 1) return padLeft + chartW / 2;
    return padLeft + (i * chartW) / (rows.length - 1);
  };
  const yAt = (rankNum) => {
    const ratio = (Number(rankNum) - 1) / 3;
    return padTop + ratio * chartH;
  };

  const points = rows.map((r, i) => ({ x: xAt(i), y: yAt(r.rank), year: r.year, rank: r.rank, rankText: r.rankText }));
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");

  const yTicks = [1, 2, 3, 4];
  const yGrid = yTicks
    .map((rank) => {
      const y = yAt(rank);
      return `<line x1="${padLeft}" y1="${y.toFixed(2)}" x2="${(width - padRight).toFixed(2)}" y2="${y.toFixed(
        2
      )}" class="cas-grid-line"></line>`;
    })
    .join("");

  const yLabels = yTicks
    .map((rank) => {
      const y = yAt(rank);
      return `<text x="${(padLeft - 10).toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="end" class="cas-tick-label">${escapeHtml(
        `${rank}区`
      )}</text>`;
    })
    .join("");

  const xTicks = points
    .map((p) => {
      const y0 = height - padBottom;
      return `<line x1="${p.x.toFixed(2)}" y1="${y0.toFixed(2)}" x2="${p.x.toFixed(2)}" y2="${(y0 + 5).toFixed(
        2
      )}" class="cas-axis-tick"></line>`;
    })
    .join("");

  const xLabels = points
    .map((p, idx) => {
      const isFirst = idx === 0;
      const isLast = idx === points.length - 1;
      const anchor = isFirst ? "start" : isLast ? "end" : "middle";
      const x = p.x + (isFirst ? 4 : isLast ? -4 : 0);
      return `<text x="${x.toFixed(2)}" y="${(height - 18).toFixed(2)}" text-anchor="${anchor}" class="cas-tick-label">${escapeHtml(
        p.year
      )}</text>`;
    })
    .join("");

  const pointDots = points
    .map(
      (p) =>
        `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="3.8" class="cas-trend-dot"><title>${escapeHtml(
          `${p.year} · 中科院${p.rankText || `${p.rank}区`}`
        )}</title></circle>`
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" class="cas-trend-svg" role="img" aria-label="中科院分区发布年份变化趋势图">
      ${yGrid}
      <line x1="${padLeft}" y1="${(height - padBottom).toFixed(2)}" x2="${(width - padRight).toFixed(
        2
      )}" y2="${(height - padBottom).toFixed(2)}" class="cas-axis-line"></line>
      <line x1="${padLeft}" y1="${padTop}" x2="${padLeft}" y2="${(height - padBottom).toFixed(2)}" class="cas-axis-line"></line>
      <path d="${linePath}" class="cas-trend-line"></path>
      ${pointDots}
      ${xTicks}
      ${xLabels}
      ${yLabels}
      <text x="16" y="${(height / 2).toFixed(2)}" text-anchor="middle" class="cas-axis-title" transform="rotate(-90 16 ${
        height / 2
      })">中科院分区</text>
    </svg>
  `;
}

function buildAnnualTrend(annualRows) {
  const rows = annualRows
    .map((r) => ({
      year: String(r?.year || "").trim(),
      value: numberOrNull(r?.count),
    }))
    .filter((r) => r.year && r.value !== null)
    .sort((a, b) => yearNum(a.year) - yearNum(b.year));

  if (!rows.length) {
    return "<p class='placeholder'>暂无可绘制的年发文量数据</p>";
  }

  const series = rows.length > 10 ? rows.slice(-10) : rows;
  const width = 640;
  const height = 280;
  const padLeft = 72;
  const padRight = 18;
  const padTop = 18;
  const padBottom = 52;
  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const values = series.map((r) => Number(r.value));
  const minData = Math.min(...values);
  const maxData = Math.max(...values);

  const rawRange = Math.max(maxData - minData, 1);
  const rawStep = rawRange / 4;
  const mag = 10 ** Math.floor(Math.log10(rawStep));
  const norm = rawStep / mag;
  const stepBase = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10;
  const tickStep = Math.max(1, Math.round(stepBase * mag));

  let minV = Math.floor(minData / tickStep) * tickStep;
  let maxV = Math.ceil(maxData / tickStep) * tickStep;
  if (minV === maxV) {
    minV = Math.max(0, minV - tickStep);
    maxV += tickStep;
  }
  if (minV > 0) {
    minV = Math.max(0, minV - tickStep);
  }

  const xAt = (i) => {
    if (series.length === 1) return padLeft + chartW / 2;
    return padLeft + (i * chartW) / (series.length - 1);
  };
  const yAt = (v) => padTop + ((maxV - v) * chartH) / Math.max(maxV - minV, 1);

  const points = series.map((r, i) => ({ x: xAt(i), y: yAt(Number(r.value)), year: r.year, value: Number(r.value) }));
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");
  const areaPath = [
    `M${points[0].x.toFixed(2)} ${(height - padBottom).toFixed(2)}`,
    ...points.map((p) => `L${p.x.toFixed(2)} ${p.y.toFixed(2)}`),
    `L${points[points.length - 1].x.toFixed(2)} ${(height - padBottom).toFixed(2)}`,
    "Z",
  ].join(" ");

  const yTicks = [];
  for (let v = minV; v <= maxV + tickStep * 0.5; v += tickStep) {
    yTicks.push(Math.round(v));
  }

  const yGrid = yTicks
    .map((v) => {
      const y = yAt(v);
      return `<line x1="${padLeft}" y1="${y.toFixed(2)}" x2="${(width - padRight).toFixed(2)}" y2="${y.toFixed(
        2
      )}" class="annual-grid-line"></line>`;
    })
    .join("");

  const yLabels = yTicks
    .map((v) => {
      const y = yAt(v);
      return `<text x="${(padLeft - 10).toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="end" class="annual-tick-label">${escapeHtml(
        Number(v).toLocaleString()
      )}</text>`;
    })
    .join("");

  const xTicks = points
    .map((p) => {
      const y0 = height - padBottom;
      return `<line x1="${p.x.toFixed(2)}" y1="${y0.toFixed(2)}" x2="${p.x.toFixed(2)}" y2="${(y0 + 5).toFixed(
        2
      )}" class="annual-axis-tick"></line>`;
    })
    .join("");

  const xLabels = points
    .map((p, idx) => {
      const isFirst = idx === 0;
      const isLast = idx === points.length - 1;
      const anchor = isFirst ? "start" : isLast ? "end" : "middle";
      const x = p.x + (isFirst ? 4 : isLast ? -4 : 0);
      return `<text x="${x.toFixed(2)}" y="${(height - 18).toFixed(2)}" text-anchor="${anchor}" class="annual-tick-label">${escapeHtml(
        p.year
      )}</text>`;
    })
    .join("");

  const pointDots = points
    .map(
      (p) =>
        `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="3.8" class="annual-trend-dot"><title>${escapeHtml(
          `${p.year} · 发文量 ${Math.round(p.value).toLocaleString()} 篇`
        )}</title></circle>`
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" class="annual-trend-svg" role="img" aria-label="年发文量变化趋势图">
      ${yGrid}
      <line x1="${padLeft}" y1="${(height - padBottom).toFixed(2)}" x2="${(width - padRight).toFixed(
        2
      )}" y2="${(height - padBottom).toFixed(2)}" class="annual-axis-line"></line>
      <line x1="${padLeft}" y1="${padTop}" x2="${padLeft}" y2="${(height - padBottom).toFixed(2)}" class="annual-axis-line"></line>
      <path d="${areaPath}" class="annual-trend-area"></path>
      <path d="${linePath}" class="annual-trend-line"></path>
      ${pointDots}
      ${xTicks}
      ${xLabels}
      ${yLabels}
      <text x="16" y="${(height / 2).toFixed(2)}" text-anchor="middle" class="annual-axis-title" transform="rotate(-90 16 ${
        height / 2
      })">年发文量（篇）</text>
    </svg>
  `;
}

function renderAnnualArticlesTrend(rows) {
  if (!els.annualTrendChart) return;
  els.annualTrendChart.innerHTML = buildAnnualTrend(Array.isArray(rows) ? rows : []);
}

function renderShowJCRHistory(j) {
  const ifRows = [...(Array.isArray(j.if_history) ? j.if_history : [])].sort((a, b) => yearNum(b.year) - yearNum(a.year));
  const casRows = [...(Array.isArray(j.cas_history) ? j.cas_history : [])].sort((a, b) => yearNum(b.year) - yearNum(a.year));

  els.ifTrendChart.innerHTML = buildIFTrend(ifRows);
  els.casTrendChart.innerHTML = buildCASTrend(casRows);
  if (els.annualTrendChart) {
    els.annualTrendChart.innerHTML = "<p class='placeholder'>正在加载年发文量数据…</p>";
  }
}

function renderHQ(j) {
  const records = Array.isArray(j.hq_records) ? j.hq_records : [];
  const fields = Array.isArray(j.hq_fields) ? j.hq_fields : [];
  const societies = Array.isArray(j.hq_societies) ? j.hq_societies : [];

  const summary = [
    ["科协评级", safe(j.hq_level)],
    ["涉及领域数", String(fields.length || 0)],
    ["涉及学会数", String(societies.length || 0)],
    ["目录条目数", String(records.length || 0)],
  ];

  els.hqMetaGrid.innerHTML = summary
    .map(([k, v]) => `<div class="kv"><div class="k">${escapeHtml(k)}</div><div class="v">${escapeHtml(v)}</div></div>`)
    .join("");

  if (!records.length) {
    els.hqRecordList.innerHTML = "<p class='placeholder'>该期刊未在科协高质量期刊分级中命中条目</p>";
    return;
  }

  const sorted = [...records].sort((a, b) => {
    const la = levelRank(a.level);
    const lb = levelRank(b.level);
    if (la !== lb) return la - lb;
    return String(a.field || "").localeCompare(String(b.field || ""), "zh-CN");
  });

  els.hqRecordList.innerHTML = sorted
    .map((r) => {
      const sub = r.subfield ? `<div class="hq-record-sub">${escapeHtml(r.subfield)}</div>` : "";
      return `
        <div class="hq-record-item">
          <div>
            <div class="hq-record-field">${escapeHtml(safe(r.field))}</div>
            <div class="hq-record-society">${escapeHtml(safe(r.society))}</div>
            ${sub}
          </div>
          <span class="hq-level">${escapeHtml(safe(r.level))}</span>
        </div>
      `;
    })
    .join("");
}

function normalizeCASKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu, "");
}

function pickLatestCASRecord(row) {
  const rows = Array.isArray(row?.cas_history) ? row.cas_history : [];
  if (!rows.length) return null;
  let latest = rows[0];
  let latestYear = yearNum(rows[0]?.year);
  for (let i = 1; i < rows.length; i += 1) {
    const y = yearNum(rows[i]?.year);
    if (y > latestYear) {
      latest = rows[i];
      latestYear = y;
    }
  }
  return latest || null;
}

function buildCASProfile(row) {
  const latest = pickLatestCASRecord(row);
  const majorRaw = String(latest?.category || "").trim();
  const majorKey = normalizeCASKey(majorRaw);
  const subRows = Array.isArray(latest?.subcategories) ? latest.subcategories : [];
  const subKeys = new Set();
  const subNameMap = new Map();
  for (const item of subRows) {
    const name = String(item?.name || "").trim();
    if (!name) continue;
    const key = normalizeCASKey(name);
    if (!key) continue;
    subKeys.add(key);
    if (!subNameMap.has(key)) subNameMap.set(key, name);
  }
  return {
    majorRaw,
    majorKey,
    subKeys,
    subNameMap,
  };
}

function computeRelatedSimilarity(base, candidate, baseCAS = null, candidateCAS = null) {
  let score = 0;
  const reasons = [];
  const baseProfile = baseCAS || buildCASProfile(base);
  const candidateProfile = candidateCAS || buildCASProfile(candidate);
  const majorMatch = Boolean(baseProfile.majorKey && candidateProfile.majorKey && baseProfile.majorKey === candidateProfile.majorKey);

  const matchedSubNames = [];
  if (baseProfile.subKeys.size && candidateProfile.subKeys.size) {
    for (const key of baseProfile.subKeys) {
      if (!candidateProfile.subKeys.has(key)) continue;
      matchedSubNames.push(baseProfile.subNameMap.get(key) || candidateProfile.subNameMap.get(key) || key);
    }
  }
  const subMatchCount = matchedSubNames.length;

  if (subMatchCount > 0) {
    score += 240 + Math.min(subMatchCount, 3) * 36;
    const label = matchedSubNames.slice(0, 2).join(" / ");
    reasons.push(label ? `同中科院小类（${label}）` : "同中科院小类");
  }
  if (majorMatch) {
    score += 150;
    reasons.push("同中科院大类");
  }

  if (base.cas_2025 && candidate.cas_2025 && base.cas_2025 === candidate.cas_2025) {
    score += 56;
    reasons.push("同中科院分区");
  }
  if (base.jcr_quartile && candidate.jcr_quartile && base.jcr_quartile === candidate.jcr_quartile) {
    score += 34;
    reasons.push("同JCR分区");
  }
  if (base.hq_level && candidate.hq_level && base.hq_level === candidate.hq_level) {
    score += 10;
    reasons.push("同科协等级");
  }
  if (base.is_top === true && candidate.is_top === true) {
    score += 8;
    reasons.push("均为Top");
  }

  const baseIF = numberOrNull(base.if_2023);
  const candIF = numberOrNull(candidate.if_2023);
  let ifDiff = Number.POSITIVE_INFINITY;
  if (baseIF !== null && candIF !== null) {
    ifDiff = Math.abs(baseIF - candIF);
    score += Math.max(0, 18 - ifDiff * 1.8);
  }

  const casPriority = subMatchCount > 0 && majorMatch ? 3 : subMatchCount > 0 ? 2 : majorMatch ? 1 : 0;
  return { score, reasons, ifDiff, casPriority, majorMatch, subMatchCount };
}

function findRelated(all, current, limit = 24) {
  const baseCAS = buildCASProfile(current);
  const candidates = all
    .filter((r) => r.id !== current.id)
    .map((r) => {
      const candidateCAS = buildCASProfile(r);
      return { journal: r, sim: computeRelatedSimilarity(current, r, baseCAS, candidateCAS) };
    })
    .filter((x) => x.sim.score > 0);

  candidates.sort((a, b) => {
    if (b.sim.casPriority !== a.sim.casPriority) return b.sim.casPriority - a.sim.casPriority;
    if (b.sim.subMatchCount !== a.sim.subMatchCount) return b.sim.subMatchCount - a.sim.subMatchCount;
    if (Number(b.sim.majorMatch) !== Number(a.sim.majorMatch)) return Number(b.sim.majorMatch) - Number(a.sim.majorMatch);
    if (b.sim.score !== a.sim.score) return b.sim.score - a.sim.score;
    if (a.sim.ifDiff !== b.sim.ifDiff) return a.sim.ifDiff - b.sim.ifDiff;
    return (numberOrNull(b.journal.if_2023) || -1) - (numberOrNull(a.journal.if_2023) || -1);
  });

  return candidates.slice(0, limit).map((x) => ({
    ...x.journal,
    _relatedScore: x.sim.score,
    _relatedReasons: x.sim.reasons,
  }));
}

function renderRelated(all, current, q) {
  const rel = findRelated(all, current);
  if (!rel.length) {
    els.relatedList.innerHTML = "<p class='placeholder'>暂无相近期刊建议</p>";
    return;
  }

  els.relatedList.innerHTML = rel
    .map((r) => {
      const u = new URL("./journal.html", window.location.href);
      u.searchParams.set("id", String(r.id));
      if (q) u.searchParams.set("q", q);
      const casTag = r.is_top === true ? `${safe(r.cas_2025)} (Top)` : safe(r.cas_2025);
      return `
        <a class="related-item" href="${u.toString()}">
          <div class="related-title">${escapeHtml(r.title || "未知期刊")}</div>
          <div class="related-meta">${escapeHtml(safe(r.issn))} / ${escapeHtml(safe(r.cn_number))}</div>
          <div class="related-meta">IF ${escapeHtml(safe(r.if_2023))} · ${escapeHtml(safe(r.jcr_quartile))} · ${escapeHtml(casTag)}</div>
        </a>
      `;
    })
    .join("");
}

function openSourceModal(key) {
  const conf = SOURCE_INFO[key] || SOURCE_INFO.core;
  els.sourceModalTitle.textContent = conf.title;
  els.sourceModalBody.innerHTML = conf.body;
  els.sourceModal.hidden = false;
}

function closeSourceModal() {
  els.sourceModal.hidden = true;
}

function openChartModal(chartId, chartTitle = "") {
  if (!els.chartModal || !els.chartModalBody || !els.chartModalTitle) return;
  const id = String(chartId || "").trim();
  const chart = id ? document.getElementById(id) : null;
  if (!chart) return;

  const content = String(chart.innerHTML || "").trim();
  if (!content) {
    els.chartModalBody.innerHTML = "<p class='placeholder'>暂无可放大的图表</p>";
  } else {
    els.chartModalBody.innerHTML = `<div class="chart-modal__chart-wrap">${content}</div>`;
  }
  els.chartModalTitle.textContent = chartTitle ? `${chartTitle}（大图）` : "图表大图";
  els.chartModal.hidden = false;
}

function closeChartModal() {
  if (!els.chartModal || !els.chartModalBody) return;
  els.chartModal.hidden = true;
  els.chartModalBody.innerHTML = "";
}

function bindSourceModalEvents() {
  document.addEventListener("click", async (e) => {
    const retryTrigger = e.target.closest("[data-citescore-refresh]");
    if (retryTrigger) {
      await refreshCiteScoreForCurrentJournal();
      return;
    }

    const infoTrigger = e.target.closest("[data-info]");
    if (infoTrigger) {
      openSourceModal(infoTrigger.dataset.info || "core");
      return;
    }
    if (e.target.closest("[data-close-source]")) {
      closeSourceModal();
    }
  });

  els.sourceModalClose.addEventListener("click", closeSourceModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !els.sourceModal.hidden) {
      closeSourceModal();
    }
  });
}

function bindChartModalEvents() {
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-chart-zoom]");
    if (trigger) {
      const chartId = trigger.dataset.chartZoom || "";
      const chartTitle = trigger.dataset.chartTitle || "";
      openChartModal(chartId, chartTitle);
      return;
    }
    if (e.target.closest("[data-close-chart]")) {
      closeChartModal();
    }
  });

  if (els.chartModalClose) {
    els.chartModalClose.addEventListener("click", closeChartModal);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && els.chartModal && !els.chartModal.hidden) {
      closeChartModal();
    }
  });
}

async function tryFetchJson(path, cache = "default") {
  const res = await fetch(path, { cache, headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} @ ${path}`);
  return res.json();
}

async function fetchJsonWithFallback(paths, cache = "default") {
  let lastError = null;
  for (const path of paths) {
    try {
      return await tryFetchJson(path, cache);
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error("json_fetch_failed");
}

function resolveDataPathCandidates(relativePath) {
  const clean = String(relativePath || "").replace(/^\.?\/*/, "");
  if (!clean) return [];
  return [
    `./data/${clean}`,
    `/data/${clean}`,
    `./xuankan/demo_site/data/${clean}`,
    `/xuankan/demo_site/data/${clean}`,
  ];
}

function toSafeBucket(id, chunkCount) {
  const n = Number(id);
  if (!Number.isFinite(n) || chunkCount <= 0) return 0;
  return Math.abs(Math.trunc(n)) % chunkCount;
}

async function loadJournalFromChunks(id) {
  const manifest = await fetchJsonWithFallback(CHUNK_MANIFEST_PATHS, "force-cache");
  const meta = manifest?.meta || {};
  const chunkCountRaw = Number(meta.chunk_count);
  const chunkCount = Number.isFinite(chunkCountRaw) && chunkCountRaw > 0 ? chunkCountRaw : 64;
  const bucket = toSafeBucket(id, chunkCount);

  const chunkMeta = Array.isArray(manifest?.chunks)
    ? manifest.chunks.find((x) => Number(x?.bucket) === bucket)
    : null;
  const defaultRel = `journal_chunks/chunk-${String(bucket).padStart(2, "0")}.json`;
  const rel = String(chunkMeta?.file || defaultRel);

  const chunkPayload = await fetchJsonWithFallback(resolveDataPathCandidates(rel), "force-cache");
  const rows = Array.isArray(chunkPayload?.journals) ? chunkPayload.journals : [];
  const row = rows.find((r) => Number(r?.id) === Number(id)) || null;
  return { row, meta, rows };
}

async function loadJournalFromFullData(id) {
  const payload = await fetchJsonWithFallback(FULL_DATA_PATHS, "default");
  const rows = Array.isArray(payload?.journals) ? payload.journals : [];
  const meta = payload?.meta || {};
  const row = rows.find((r) => Number(r?.id) === Number(id)) || null;
  return { row, meta, rows };
}

async function loadJournalById(id) {
  try {
    const chunkResult = await loadJournalFromChunks(id);
    if (chunkResult.row) return chunkResult;
  } catch (err) {
    console.warn("Chunk loading failed, fallback to full data:", err);
  }
  return loadJournalFromFullData(id);
}

async function loadRelatedRows() {
  const payload = await fetchJsonWithFallback(SEARCH_INDEX_PATHS, "force-cache");
  return {
    rows: Array.isArray(payload?.journals) ? payload.journals : [],
    meta: payload?.meta || {},
  };
}

async function bootstrap() {
  bindSourceModalEvents();
  bindChartModalEvents();
  const { id, q } = getParams();

  const backUrl = new URL("./index.html", window.location.href);
  if (q) backUrl.searchParams.set("q", q);
  els.backLink.href = backUrl.toString();

  const relatedPromise = loadRelatedRows().catch(() => ({ rows: [], meta: {} }));
  const detailPayload = await loadJournalById(id);
  const row = detailPayload.row;
  const meta = detailPayload.meta || {};

  els.genInfo.textContent = `数据更新时间：${meta.generated_at || "-"}`;

  if (!row) {
    els.title.textContent = "未找到期刊";
    els.subtitle.textContent = "请返回查询页重新检索";
    els.topTags.innerHTML = "";
    els.coreGrid.innerHTML = "";
    resetSpotlight("无数据");
    els.ifTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
    els.casTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
    if (els.annualTrendChart) els.annualTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
    els.hqMetaGrid.innerHTML = "";
    els.hqRecordList.innerHTML = "<p class='placeholder'>无数据</p>";
    els.relatedList.innerHTML = "<p class='placeholder'>无数据</p>";
    return;
  }

  renderRow(row, meta);
  renderShowJCRHistory(row);
  renderHQ(row);
  els.relatedList.innerHTML = "<p class='placeholder'>正在加载相近期刊...</p>";
  relatedPromise.then((relatedPayload) => {
    const relatedRows =
      Array.isArray(relatedPayload.rows) && relatedPayload.rows.length
        ? relatedPayload.rows
        : Array.isArray(detailPayload.rows)
        ? detailPayload.rows
        : [];
    renderRelated(relatedRows, row, q);
  });
}

bootstrap().catch((err) => {
  console.error(err);
  els.title.textContent = "加载失败";
  els.subtitle.textContent = "请刷新重试";
  resetSpotlight("加载失败");
  if (els.ifTrendChart) els.ifTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
  if (els.casTrendChart) els.casTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
  if (els.annualTrendChart) els.annualTrendChart.innerHTML = "<p class='placeholder'>无数据</p>";
});

