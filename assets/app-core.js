const state = {
  catalog: [], summary: {}, meta: null, manifest: null, attributes: null, sources: {},
  filtered: [], page: 1, perPage: 30, result: 'all', detailCache: new Map(), ruleCache: new Map()
};

const $ = id => document.getElementById(id);
const normalize = value => String(value ?? '').toLowerCase().replace(/ё/g, 'е').replace(/\s+/g, ' ').trim();
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatNum = n => Number(n || 0).toLocaleString('ru-RU');

async function fetchJson(path, { optional = false } = {}) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) {
    if (optional && response.status === 404) return null;
    throw new Error(`${path}: HTTP ${response.status}`);
  }
  return response.json();
}

async function init() {
  const [manifest, meta, attributes] = await Promise.all([
    fetchJson('data/manifest.json'),
    fetchJson('data/meta.json'),
    fetchJson('data/rules/attributes.json')
  ]);
  state.manifest = manifest;
  state.meta = meta;
  state.attributes = attributes;

  const [catalog, summary, sources] = await Promise.all([
    loadCompressedCatalog(manifest.catalogFragments || []),
    fetchJson(manifest.summaryFile),
    fetchJson(manifest.sourcesFile)
  ]);
  state.catalog = expandCatalog(catalog);
  state.summary = summary || {};
  state.sources = sources?.sources || {};

  $('catalogMeta').textContent = `${formatNum(meta.rows)} строк · ${formatNum(meta.uniqueTypes)} уникальных типов · проверено ${formatNum(meta.checkedProducts)}`;
  fillCategoryFilters();
  bindEvents();
  restoreFromUrl();
  applyFilters();
  openProductFromUrl();
}

async function loadCompressedCatalog(fragmentPaths) {
  if (!fragmentPaths.length) throw new Error('Каталог не указан в manifest.json');
  const parts = await Promise.all(fragmentPaths.map(async path => {
    const r = await fetch(path, { cache: 'no-store' });
    if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
    return r.text();
  }));
  const binary = Uint8Array.from(atob(parts.join('')), ch => ch.charCodeAt(0));
  if (typeof DecompressionStream === 'undefined') throw new Error('Браузер не поддерживает распаковку каталога gzip');
  const stream = new Blob([binary]).stream().pipeThrough(new DecompressionStream('gzip'));
  const text = await new Response(stream).text();
  return JSON.parse(text);
}

function expandCatalog(payload) {
  if (Array.isArray(payload)) return payload;
  const mains = payload?.m || [];
  const categories = payload?.c || [];
  return (payload?.r || []).map(([id, categoryIndex, type]) => {
    const [mainIndex, category] = categories[categoryIndex] || [0, ''];
    return { id, mainCategory: mains[mainIndex] || '', category: category || '', type };
  });
}

function getSummary(id) {
  return state.summary[String(id)] || {
    result: 'pending',
    markingCurrent: 'unknown',
    markingFuture: 'unknown',
    experiment: 'unknown',
    documentFlags: [],
    tnvedCodes: [],
    lastChecked: null
  };
}

function enrichedProduct(row) { return { ...row, summary: getSummary(row.id) }; }

function fillCategoryFilters() {
  const mains = [...new Set(state.catalog.map(p => p.mainCategory))].sort((a,b) => a.localeCompare(b, 'ru'));
  $('mainCategoryFilter').innerHTML = '<option value="">Все</option>' + mains.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  refreshCategoryOptions();
}

function refreshCategoryOptions() {
  const main = $('mainCategoryFilter').value;
  const cats = [...new Set(state.catalog.filter(p => !main || p.mainCategory === main).map(p => p.category))].sort((a,b) => a.localeCompare(b, 'ru'));
  const current = $('categoryFilter').value;
  $('categoryFilter').innerHTML = '<option value="">Все</option>' + cats.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  if (cats.includes(current)) $('categoryFilter').value = current;
}

function bindEvents() {
  $('searchInput').addEventListener('input', debounce(() => { state.page = 1; applyFilters(true); }, 100));
  $('clearSearch').addEventListener('click', () => { $('searchInput').value = ''; state.page = 1; applyFilters(true); });
  $('mainCategoryFilter').addEventListener('change', () => { refreshCategoryOptions(); state.page = 1; applyFilters(true); });
  ['categoryFilter','markingFilter','documentFilter','sortSelect'].forEach(id => $(id).addEventListener('change', () => { state.page = 1; applyFilters(true); }));
  $('resetFilters').addEventListener('click', resetFilters);
  document.querySelectorAll('.filter-pill').forEach(btn => btn.addEventListener('click', () => {
    state.result = btn.dataset.result;
    document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b === btn));
    state.page = 1;
    applyFilters(true);
  }));
  $('closeDialog').addEventListener('click', closeProductDialog);
  $('productDialog').addEventListener('click', e => { if (e.target === $('productDialog')) closeProductDialog(); });
}

function resetFilters() {
  $('searchInput').value = '';
  $('mainCategoryFilter').value = '';
  refreshCategoryOptions();
  $('categoryFilter').value = '';
  $('markingFilter').value = '';
  $('documentFilter').value = '';
  $('sortSelect').value = 'type';
  state.result = 'all';
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b.dataset.result === 'all'));
  state.page = 1;
  applyFilters(true);
}

function matchesMarking(summary, filter) {
  if (!filter) return true;
  if (filter === 'current') return summary.markingCurrent === 'yes';
  if (filter === 'future') return summary.markingFuture === 'yes';
  if (filter === 'experiment') return summary.experiment === 'yes';
  if (filter === 'none') return [summary.markingCurrent, summary.markingFuture, summary.experiment].every(v => v === 'no');
  if (filter === 'unknown') return [summary.markingCurrent, summary.markingFuture, summary.experiment].some(v => v === 'unknown');
  return true;
}

function matchesDocument(summary, filter) {
  if (!filter) return true;
  const flags = summary.documentFlags || [];
  if (filter === 'unknown') return !flags.length || flags.includes('unknown');
  if (filter === 'none') return flags.includes('none');
  return flags.includes(filter);
}

function applyFilters(updateUrl = false) {
  const q = normalize($('searchInput').value);
  const main = $('mainCategoryFilter').value;
  const cat = $('categoryFilter').value;
  const marking = $('markingFilter').value;
  const doc = $('documentFilter').value;

  let rows = state.catalog.filter(row => {
    const s = getSummary(row.id);
    const haystack = normalize([row.mainCategory, row.category, row.type, ...(s.tnvedCodes || [])].join(' '));
    return (!q || haystack.includes(q))
      && (!main || row.mainCategory === main)
      && (!cat || row.category === cat)
      && (state.result === 'all' || s.result === state.result)
      && matchesMarking(s, marking)
      && matchesDocument(s, doc);
  });

  const sort = $('sortSelect').value;
  const resultOrder = { green: 0, yellow: 1, red: 2, pending: 3 };
  rows.sort((a,b) => {
    if (sort === 'category') return `${a.mainCategory}\u0000${a.category}\u0000${a.type}`.localeCompare(`${b.mainCategory}\u0000${b.category}\u0000${b.type}`, 'ru');
    if (sort === 'result') {
      const delta = (resultOrder[getSummary(a.id).result] ?? 9) - (resultOrder[getSummary(b.id).result] ?? 9);
      return delta || a.type.localeCompare(b.type, 'ru');
    }
    return a.type.localeCompare(b.type, 'ru');
  });

  state.filtered = rows;
  render();
  if (updateUrl) writeUrlState();
}

function render() {
  $('resultCount').textContent = formatNum(state.filtered.length);
  const totalPages = Math.max(1, Math.ceil(state.filtered.length / state.perPage));
  state.page = Math.min(state.page, totalPages);
  const start = (state.page - 1) * state.perPage;
  const rows = state.filtered.slice(start, start + state.perPage);
  $('results').innerHTML = rows.length ? rows.map(row => cardHtml(enrichedProduct(row))).join('') : '<div class="empty">По текущим фильтрам ничего не найдено</div>';
  document.querySelectorAll('[data-open-id]').forEach(btn => btn.addEventListener('click', () => openProduct(Number(btn.dataset.openId))));
  renderPager(totalPages);
}

function resultBadge(summary) {
  const map = { green: ['green','ПОДХОДИТ'], yellow: ['yellow','ПРОВЕРИТЬ'], red: ['red','ИСКЛЮЧИТЬ'], pending: ['','НЕ ПРОВЕРЕНО'] };
  const [cls, label] = map[summary.result] || map.pending;
  return `<span class="badge ${cls}">${label}</span>`;
}

function statusText(value) { if (value === 'yes') return 'Да'; if (value === 'no') return 'Нет'; return 'Не проверено'; }

function markingSummary(s) {
  if (s.markingCurrent === 'yes') return 'ЧЗ: обязателен сейчас';
  if (s.markingFuture === 'yes') return 'ЧЗ: утверждён на будущее';
  if (s.experiment === 'yes') return 'ЧЗ: эксперимент';
  if ([s.markingCurrent, s.markingFuture, s.experiment].every(v => v === 'no')) return 'ЧЗ: не обнаружен';
  return 'ЧЗ: не проверено';
}

function documentSummary(s) {
  const flags = s.documentFlags || [];
  if (flags.includes('certificate')) return 'Документы: сертификат';
  if (flags.includes('declaration')) return 'Документы: декларация';
  if (flags.includes('sgr')) return 'Документы: СГР';
  if (flags.includes('refusal')) return 'Документы: возможен отказной';
  if (flags.includes('none')) return 'Документы: обязательных нет';
  return 'Документы: не проверено';
}

function tnvedSummary(s) { return s.tnvedCodes?.length ? `ТН ВЭД: ${s.tnvedCodes.slice(0,2).join(' / ')}` : 'ТН ВЭД: не определён'; }

function cardHtml({id, mainCategory, category, type, summary}) {
  return `<article class="product-card"><div><div class="breadcrumb">${esc(mainCategory)} · ${esc(category)}</div><h2 class="product-title">${esc(type)}</h2><div class="badges">${resultBadge(summary)}<span class="badge">${esc(markingSummary(summary))}</span><span class="badge">${esc(tnvedSummary(summary))}</span><span class="badge">${esc(documentSummary(summary))}</span></div></div><div class="card-side"><button class="open-btn" type="button" data-open-id="${id}">Открыть карточку</button></div></article>`;
}
