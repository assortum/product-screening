function renderPager(totalPages) {
  const wrap = $('pager');
  if (totalPages <= 1) { wrap.innerHTML = ''; return; }
  const pages = [];
  const from = Math.max(1, state.page - 2);
  const to = Math.min(totalPages, state.page + 2);
  if (from > 1) pages.push(1);
  if (from > 2) pages.push('…');
  for (let p = from; p <= to; p++) pages.push(p);
  if (to < totalPages - 1) pages.push('…');
  if (to < totalPages) pages.push(totalPages);
  wrap.innerHTML = pages.map(p => p === '…' ? '<span>…</span>' : `<button type="button" class="${p === state.page ? 'active' : ''}" data-page="${p}">${p}</button>`).join('');
  wrap.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    state.page = Number(btn.dataset.page);
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }));
}

function writeUrlState() {
  const url = new URL(location.href);
  const set = (key, value) => value ? url.searchParams.set(key, value) : url.searchParams.delete(key);
  set('q', $('searchInput').value.trim());
  set('main', $('mainCategoryFilter').value);
  set('category', $('categoryFilter').value);
  set('result', state.result === 'all' ? '' : state.result);
  set('marking', $('markingFilter').value);
  set('document', $('documentFilter').value);
  history.replaceState(null, '', url);
}

function restoreFromUrl() {
  const params = new URLSearchParams(location.search);
  $('searchInput').value = params.get('q') || '';
  const main = params.get('main') || '';
  if ([...$('mainCategoryFilter').options].some(o => o.value === main)) $('mainCategoryFilter').value = main;
  refreshCategoryOptions();
  const category = params.get('category') || '';
  if ([...$('categoryFilter').options].some(o => o.value === category)) $('categoryFilter').value = category;
  const result = params.get('result') || 'all';
  if (['all','green','yellow','red','pending'].includes(result)) state.result = result;
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b.dataset.result === state.result));
  $('markingFilter').value = params.get('marking') || '';
  $('documentFilter').value = params.get('document') || '';
}

function setProductInUrl(id) {
  const url = new URL(location.href);
  url.searchParams.set('product', String(id));
  history.replaceState(null, '', url);
}

function openProductFromUrl() {
  const id = Number(new URLSearchParams(location.search).get('product'));
  if (Number.isInteger(id) && id > 0) openProduct(id, false);
}

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

init().catch(error => {
  console.error(error);
  $('results').innerHTML = `<div class="empty">Не удалось загрузить базу: ${esc(error.message)}. При локальном запуске открывайте проект через HTTP-сервер.</div>`;
});
