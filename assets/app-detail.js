function shardRange(id) {
  const size = state.manifest.shardSize;
  const start = Math.floor((id - 1) / size) * size + 1;
  const end = start + size - 1;
  return { start, end, key: `${start}-${end}` };
}

function shardPath(template, id) {
  const {start, end} = shardRange(id);
  return template.replace('{start}', String(start).padStart(5,'0')).replace('{end}', String(end).padStart(5,'0'));
}

async function loadShard(cache, template, id) {
  const range = shardRange(id);
  if (cache.has(range.key)) return cache.get(range.key);
  const data = await fetchJson(shardPath(template, id), { optional: true });
  const value = data || {};
  cache.set(range.key, value);
  return value;
}

async function getDetail(id) {
  const shard = await loadShard(state.detailCache, state.manifest.detailPathTemplate, id);
  return shard[String(id)] || null;
}

async function getRule(id) {
  const shard = await loadShard(state.ruleCache, state.manifest.rulePathTemplate, id);
  return shard[String(id)] || null;
}

async function openProduct(id, pushUrl = true) {
  const row = state.catalog.find(p => p.id === id);
  if (!row) return;
  const summary = getSummary(id);
  $('productDetails').innerHTML = `<div class="eyebrow">${esc(row.mainCategory)} · ${esc(row.category)}</div><h2 class="detail-title">${esc(row.type)}</h2><div class="empty">Загрузка подробной карточки…</div>`;
  $('productDialog').showModal();
  if (pushUrl) setProductInUrl(id);

  const [detail, rule] = await Promise.all([getDetail(id), getRule(id)]);
  $('productDetails').innerHTML = detailHtml(row, summary, detail, rule);
  bindQuestionnaire(row, summary, detail, rule);
}

function closeProductDialog() {
  $('productDialog').close();
  const url = new URL(location.href);
  url.searchParams.delete('product');
  history.replaceState(null, '', url);
}

function detailHtml(row, summary, detail, rule) {
  const normalized = detail?.normalizedName && detail.normalizedName !== row.type ? `<div class="note">Нормализованное наименование: <strong>${esc(detail.normalizedName)}</strong></div>` : '';
  const checked = detail?.lastChecked || summary.lastChecked;
  return `<div class="eyebrow">${esc(row.mainCategory)} · ${esc(row.category)}</div><h2 class="detail-title">${esc(row.type)}</h2><div class="badges">${resultBadge(summary)}<span class="badge">${checked ? `Проверено: ${esc(checked)}` : 'Регуляторная проверка не загружена'}</span></div>${normalized}<div class="detail-grid"><section class="detail-card"><h3>Честный знак</h3>${markingDetail(detail, summary)}</section><section class="detail-card"><h3>ТН ВЭД ЕАЭС</h3>${tnvedDetail(detail)}</section><section class="detail-card"><h3>Обязательные документы</h3>${documentsDetail(detail)}</section><section class="detail-card"><h3>Основание и источники</h3>${sourcesDetail(detail)}</section><section class="detail-card full"><h3>Уточняющие характеристики</h3>${clarificationIntro(detail, rule)}<div class="questionnaire" id="questionnaire">${questionsHtml(rule)}</div><div id="scenarioResult"></div></section></div>`;
}

function markingDetail(detail, summary) {
  const m = detail?.marking || {};
  return [statusRow('Обязателен сейчас', m.current?.status ?? summary.markingCurrent, m.current?.label, m.current?.date),statusRow('Утверждён на будущее', m.future?.status ?? summary.markingFuture, m.future?.label, m.future?.date),statusRow('Эксперимент / пилот', m.experiment?.status ?? summary.experiment, m.experiment?.label, m.experiment?.date)].join('');
}

function statusRow(label, status, text, date) {
  const value = statusText(status);
  const suffix = [text, date].filter(Boolean).join(' · ');
  return `<div class="status-row"><span>${esc(label)}</span><strong class="${status === 'unknown' ? 'value-unknown' : ''}">${esc(suffix || value)}</strong></div>`;
}

function tnvedDetail(detail) {
  const candidates = detail?.tnved?.candidates || [];
  if (!candidates.length) return '<div class="value-unknown">ТН ВЭД ещё не определён.</div>';
  const rows = candidates.map(item => `<div class="status-row"><span><strong>${esc(item.code)}</strong>${item.description ? `<br><small>${esc(item.description)}</small>` : ''}</span><strong>${esc(item.confidence || '')}</strong></div>`).join('');
  const clarifications = detail?.tnved?.needsClarification || [];
  return rows + (clarifications.length ? `<ul class="clarification-list">${clarifications.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '');
}

function documentsDetail(detail) {
  const docs = detail?.documents;
  if (!docs) return '<div class="value-unknown">Форма подтверждения соответствия ещё не определена.</div>';
  const items = docs.items || [];
  const rows = items.length ? items.map(item => `<div class="status-row"><span>${esc(item.label || item.type)}</span><strong>${esc(item.status || '')}</strong></div>`).join('') : '<div class="status-row"><span>Обязательные документы</span><strong>Не обнаружены</strong></div>';
  const refusal = docs.refusalLetter ? `<div class="status-row"><span>Отказное письмо</span><strong>${esc(docs.refusalLetter)}</strong></div>` : '';
  const basis = docs.basis ? `<div class="note">${esc(docs.basis)}</div>` : '';
  return rows + refusal + basis;
}

function sourcesDetail(detail) {
  const ids = detail?.sourceIds || [];
  if (!ids.length) return '<div class="value-unknown">Подтверждённые нормативные источники ещё не привязаны.</div>';
  const items = ids.map(id => state.sources[id]).filter(Boolean);
  if (!items.length) return '<div class="value-unknown">Ссылки на источники не найдены в реестре.</div>';
  return `<div class="source-list">${items.map(src => `<div><a href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">${esc(src.title)}</a>${src.authority ? `<div class="breadcrumb">${esc(src.authority)}</div>` : ''}</div>`).join('')}</div>`;
}

function clarificationIntro(detail, rule) {
  if (rule?.questionIds?.length) return '<div class="note">Выберите только известные характеристики. Система покажет сценарии, которые совпадают с выбранными признаками; отсутствие сценария не означает автоматического отсутствия требований.</div>';
  const needs = detail?.tnved?.needsClarification || detail?.clarifications || [];
  if (needs.length) return `<div class="note">Для точной классификации необходимо уточнить:</div><ul class="clarification-list">${needs.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
  return '<div class="note">Для этого типа товара дерево уточняющих признаков ещё не заполнено. Код ТН ВЭД автоматически не присваивается.</div>';
}

function questionsHtml(rule) {
  if (!rule?.questionIds?.length) return '';
  return rule.questionIds.map(id => {
    const q = state.attributes.definitions[id];
    if (!q) return '';
    const show = q.showWhen ? ' hidden' : '';
    const dependency = q.showWhen ? ` data-show-when='${esc(JSON.stringify(q.showWhen))}'` : '';
    if (q.type === 'boolean') return `<div class="question${show}" data-question="${esc(id)}"${dependency}><div class="question-label">${esc(q.label)}</div><div class="option-row">${choice(id,'unknown','Не указано',true)}${choice(id,'yes','Да')}${choice(id,'no','Нет')}</div></div>`;
    return `<div class="question${show}" data-question="${esc(id)}"${dependency}><div class="question-label">${esc(q.label)}</div><div class="option-row">${choice(id,'','Не указано',true)}${(q.options || []).map(option => choice(id, option, option)).join('')}</div></div>`;
  }).join('');
}

function choice(name, value, label, checked = false) {
  const id = `q_${name}_${Math.random().toString(36).slice(2)}`;
  return `<label class="choice" for="${id}"><input id="${id}" type="radio" name="${esc(name)}" value="${esc(value)}" ${checked ? 'checked' : ''}><span>${esc(label)}</span></label>`;
}

function bindQuestionnaire(row, summary, detail, rule) {
  const inputs = [...document.querySelectorAll('#questionnaire input')];
  if (!inputs.length) return;
  inputs.forEach(input => input.addEventListener('change', () => { updateConditionalQuestions(); evaluateScenario(row, summary, detail, rule); }));
  updateConditionalQuestions();
  evaluateScenario(row, summary, detail, rule);
}

function selectedAnswers() {
  const answers = {};
  document.querySelectorAll('#questionnaire input:checked').forEach(input => {
    const question = input.closest('.question');
    if (!question?.classList.contains('hidden')) answers[input.name] = input.value;
  });
  return answers;
}

function updateConditionalQuestions() {
  const answers = selectedAnswers();
  document.querySelectorAll('#questionnaire .question[data-show-when]').forEach(node => {
    let condition = {};
    try { condition = JSON.parse(node.dataset.showWhen); } catch (_) {}
    const visible = Object.entries(condition).every(([key, value]) => answers[key] === value);
    node.classList.toggle('hidden', !visible);
    if (!visible) {
      const fallback = node.querySelector('input[value="unknown"], input[value=""]');
      if (fallback) fallback.checked = true;
    }
  });
}

function conditionMatches(when, answers) {
  return Object.entries(when || {}).every(([key, expected]) => {
    const actual = answers[key];
    if (expected && typeof expected === 'object') {
      if ('eq' in expected) return actual === expected.eq;
      if (Array.isArray(expected.in)) return expected.in.includes(actual);
      if (Array.isArray(expected.notIn)) return !expected.notIn.includes(actual);
      return false;
    }
    return actual === expected;
  });
}

function scenarioSpecificity(scenario) { return Object.keys(scenario.when || {}).length; }

function evaluateScenario(row, summary, detail, rule) {
  const output = $('scenarioResult');
  if (!output || !rule) return;
  const answers = selectedAnswers();
  const chosen = Object.values(answers).filter(v => v && v !== 'unknown').length;
  if (!chosen) { output.innerHTML = '<div class="note" style="margin-top:12px">После выбора характеристик здесь появится наиболее подходящий сценарий.</div>'; return; }
  const matches = (rule.scenarios || []).filter(s => conditionMatches(s.when, answers)).sort((a,b) => scenarioSpecificity(b) - scenarioSpecificity(a));
  if (!matches.length) { output.innerHTML = '<div class="note" style="margin-top:12px">Для выбранной комбинации нет проверенного сценария. Требуется ручная классификация; система не будет подставлять ТН ВЭД по аналогии.</div>'; return; }
  const bestSpecificity = scenarioSpecificity(matches[0]);
  output.innerHTML = matches.filter(s => scenarioSpecificity(s) === bestSpecificity).map(scenarioHtml).join('');
}

function scenarioHtml(s) {
  const o = s.output || {};
  const codes = (o.tnvedCandidates || []).map(x => typeof x === 'string' ? x : x.code).filter(Boolean).join(' / ') || 'Не определён';
  const docs = (o.documents?.items || []).map(x => x.label || x.type || x).join(', ') || (o.documents?.status === 'none' ? 'Обязательных не обнаружено' : 'Требует проверки');
  const result = o.result ? ({green:'ПОДХОДИТ',yellow:'ПРОВЕРИТЬ',red:'ИСКЛЮЧИТЬ'}[o.result] || o.result) : 'Не определён';
  const marking = o.marking ? [`сейчас: ${statusText(o.marking.current?.status)}`,`будущее: ${statusText(o.marking.future?.status)}`,`эксперимент: ${statusText(o.marking.experiment?.status)}`].join('; ') : 'Без отдельного изменения';
  return `<div class="scenario-box"><h4>${esc(s.label || 'Подходящий сценарий')}</h4>${s.note ? `<div class="note">${esc(s.note)}</div>` : ''}<div class="scenario-output"><div class="mini-field"><span>ТН ВЭД</span><strong>${esc(codes)}</strong></div><div class="mini-field"><span>Документы</span><strong>${esc(docs)}</strong></div><div class="mini-field"><span>Честный знак</span><strong>${esc(marking)}</strong></div><div class="mini-field"><span>Итог</span><strong>${esc(result)}</strong></div></div></div>`;
}
