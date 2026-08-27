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
  const variants = buildTnvedVariants(detail, rule, summary);
  $('productDetails').innerHTML = detailHtml(row, summary, detail, rule, variants);
  bindDetailActions(row, detail, variants);
}

function closeProductDialog() {
  $('productDialog').close();
  const url = new URL(location.href);
  url.searchParams.delete('product');
  history.replaceState(null, '', url);
}

function detailHtml(row, summary, detail, rule, variants) {
  const normalized = detail?.normalizedName && detail.normalizedName !== row.type
    ? `<div class="note">Нормализованное наименование: <strong>${esc(detail.normalizedName)}</strong></div>` : '';
  const checked = detail?.lastChecked || summary.lastChecked;
  const reason = detail?.screeningReason ? `<div class="screening-reason"><strong>Почему такой уровень:</strong> ${esc(detail.screeningReason)}</div>` : '';

  return `<div class="eyebrow">${esc(row.mainCategory)} · ${esc(row.category)}</div>
    <h2 class="detail-title">${esc(row.type)}</h2>
    <div class="badges">${resultBadge(summary)}<span class="badge">${checked ? `Проверено: ${esc(checked)}` : 'Регуляторная проверка не загружена'}</span></div>
    ${normalized}${reason}
    <div class="detail-grid simplified-detail">
      <section class="detail-card full"><h3>Возможные варианты ТН ВЭД и риски</h3>${variantsHtml(variants, detail)}</section>
      <section class="detail-card"><h3>Общая картина Честного знака</h3>${markingDetail(detail, summary)}</section>
      <section class="detail-card"><h3>Что влияет на точный код</h3>${influenceDetail(detail, rule)}</section>
      <section class="detail-card full"><h3>Точная классификация конкретного товара</h3>${assistantBlock(row, variants)}</section>
      <section class="detail-card full"><h3>Нормативные основания и источники</h3>${sourcesDetail(detail, checked)}</section>
    </div>`;
}

function markingDetail(detail, summary) {
  const m = detail?.marking || {};
  return [
    statusRow('Обязателен сейчас', m.current?.status ?? summary.markingCurrent, m.current?.label, m.current?.date),
    statusRow('Утверждён на будущее', m.future?.status ?? summary.markingFuture, m.future?.label, m.future?.date),
    statusRow('Эксперимент / пилот', m.experiment?.status ?? summary.experiment, m.experiment?.label, m.experiment?.date)
  ].join('');
}

function statusRow(label, status, text, date) {
  const value = statusText(status);
  const suffix = [text, date].filter(Boolean).join(' · ');
  return `<div class="status-row"><span>${esc(label)}</span><strong class="${status === 'unknown' ? 'value-unknown' : ''}">${esc(suffix || value)}</strong></div>`;
}

function buildTnvedVariants(detail, rule, summary) {
  const scenarios = rule?.scenarios || [];
  const variants = [];

  for (const scenario of scenarios) {
    const output = scenario.output || {};
    const rawCodes = output.tnvedCandidates || [];
    const codes = rawCodes.map(x => typeof x === 'string' ? x : x.code).filter(Boolean);
    if (!codes.length) continue;
    variants.push({
      codes,
      applies: [scenario.label || conditionsToText(scenario.when) || 'Один из возможных сценариев классификации'],
      note: scenario.note || '',
      result: output.result || summary.result,
      marking: output.marking || detail?.marking || null,
      documents: output.documents || detail?.documents || null,
      sourceIds: scenario.sourceIds || output.sourceIds || detail?.sourceIds || []
    });
  }

  if (!variants.length) {
    for (const candidate of detail?.tnved?.candidates || []) {
      variants.push({
        codes: [candidate.code].filter(Boolean),
        applies: [candidate.description || 'Предварительный вариант по имеющимся данным'],
        note: candidate.confidence ? `Уверенность: ${candidate.confidence}` : '',
        result: summary.result,
        marking: detail?.marking || null,
        documents: detail?.documents || null,
        sourceIds: candidate.sourceIds || detail?.sourceIds || []
      });
    }
  }

  return mergeEquivalentVariants(variants);
}

function mergeEquivalentVariants(variants) {
  const map = new Map();
  for (const item of variants) {
    const docs = documentText(item.documents);
    const mark = markingKey(item.marking);
    const key = JSON.stringify([item.codes, item.result, docs, mark]);
    if (!map.has(key)) map.set(key, {...item, applies: []});
    const target = map.get(key);
    for (const label of item.applies || []) if (label && !target.applies.includes(label)) target.applies.push(label);
    if (!target.note && item.note) target.note = item.note;
    for (const id of item.sourceIds || []) if (!target.sourceIds.includes(id)) target.sourceIds.push(id);
  }
  return [...map.values()];
}

function conditionsToText(when) {
  return Object.entries(when || {}).map(([key, expected]) => {
    const label = state.attributes?.definitions?.[key]?.label || key;
    let value = expected;
    if (expected && typeof expected === 'object') {
      if ('eq' in expected) value = expected.eq;
      else if (Array.isArray(expected.in)) value = expected.in.join(' / ');
      else return '';
    }
    if (value === 'yes') value = 'Да';
    if (value === 'no') value = 'Нет';
    if (value === 'unknown') value = 'Не указано';
    return `${label}: ${value}`;
  }).filter(Boolean).join('; ');
}

function markingKey(marking) {
  if (!marking) return '';
  return ['current','future','experiment'].map(k => marking[k]?.status || 'unknown').join('|');
}

function variantsHtml(variants, detail) {
  if (!variants.length) {
    return `<div class="value-unknown">Возможные коды пока не определены. Карточка не подставляет ТН ВЭД по аналогии без достаточного основания.</div>${influenceList(detail?.tnved?.needsClarification || [])}`;
  }
  return `<div class="variant-intro">Это не окончательная классификация конкретного товара. Ниже показаны реалистичные варианты, которые удалось выделить на уровне типа товара Ozon. Требования оцениваются отдельно для каждого варианта.</div><div class="variant-list">${variants.map((v,i) => variantHtml(v,i)).join('')}</div>`;
}

function variantHtml(v, index) {
  const risk = riskMeta(v.result);
  const marking = v.marking || {};
  const applies = (v.applies || []).filter(Boolean);
  const sources = sourceLinks(v.sourceIds || []);
  const precision = v.codes.map(codePrecision).filter(Boolean);
  return `<article class="tnved-variant ${risk.cls}">
    <div class="variant-head"><div><div class="variant-kicker">Вариант ${index + 1}</div><div class="tnved-code">${v.codes.map(esc).join(' / ')}</div>${precision.length ? `<div class="code-precision">${esc([...new Set(precision)].join(' · '))}</div>` : ''}</div><span class="badge ${risk.cls}">${risk.label}</span></div>
    ${applies.length ? `<div class="variant-when"><strong>Когда применим:</strong> ${applies.map(esc).join(' / ')}</div>` : ''}
    ${v.note ? `<div class="variant-note">${esc(v.note)}</div>` : ''}
    <div class="variant-facts">
      <div class="mini-field"><span>ЧЗ сейчас</span><strong>${esc(markingValue(marking.current))}</strong></div>
      <div class="mini-field"><span>ЧЗ в будущем</span><strong>${esc(markingValue(marking.future))}</strong></div>
      <div class="mini-field"><span>Эксперимент</span><strong>${esc(markingValue(marking.experiment))}</strong></div>
      <div class="mini-field wide"><span>Документы</span><strong>${esc(documentText(v.documents))}</strong></div>
      <div class="mini-field"><span>Отказное письмо</span><strong>${esc(refusalText(v.documents))}</strong></div>
    </div>
    ${sources ? `<div class="variant-sources"><span>Источники:</span>${sources}</div>` : '<div class="variant-sources value-unknown"><span>Источники:</span> ещё не привязаны к этому варианту</div>'}
  </article>`;
}

function markingValue(item) {
  if (!item) return 'Не проверено';
  const label = item.label || statusText(item.status);
  return [label, item.date].filter(Boolean).join(' · ');
}

function documentText(docs) {
  if (!docs) return 'Не проверено';
  const items = (docs.items || []).map(x => {
    if (typeof x === 'string') return x;
    const label = x.label || x.type || '';
    return x.status ? `${label} — ${x.status}` : label;
  }).filter(Boolean);
  if (items.length) return items.join('; ');
  if (docs.status === 'none') return 'Обязательных документов не обнаружено';
  if (docs.status === 'mandatory') return 'Есть обязательные требования; форма требует проверки';
  return 'Не проверено';
}

function refusalText(docs) {
  if (!docs) return 'Не проверено';
  if (docs.refusalLetter) return docs.refusalLetter;
  if (docs.status === 'none') return 'Возможно / зависит от выбранного кода и области применения';
  if (docs.status === 'mandatory') return 'Как основной документ — нет';
  return 'Требует проверки';
}

function riskMeta(result) {
  const map = {
    green: {cls:'green',label:'ПРОСТОЙ ВХОД'},
    yellow:{cls:'yellow',label:'ВНИМАНИЕ'},
    red:{cls:'red',label:'СЛОЖНЫЙ ВХОД'},
    pending:{cls:'',label:'НЕ ПРОВЕРЕНО'}
  };
  return map[result] || map.pending;
}

function codePrecision(code) {
  const text = String(code || '').trim();
  const digits = text.replace(/\D/g,'');
  if (/^\d{10}$/.test(text.replace(/\s/g,''))) return 'полный 10-значный код';
  if (/[–—-]|\.\.\.|либо|группа|возмож/i.test(text)) return 'группа / диапазон — требуется уточнение';
  if (digits.length >= 4 && digits.length < 10) return 'неполный код — требуется уточнение';
  return '';
}

function influenceDetail(detail, rule) {
  const explicit = detail?.tnved?.needsClarification || detail?.clarifications || [];
  const fromRules = (rule?.questionIds || []).map(id => state.attributes?.definitions?.[id]?.label).filter(Boolean);
  const items = [...new Set([...explicit, ...fromRules])];
  if (!items.length) return '<div class="note">Дополнительные характеристики для выбора между вариантами пока не зафиксированы.</div>';
  return `<div class="note">Эти признаки стоит подготовить для точного определения 10-значного ТН ВЭД:</div>${influenceList(items)}`;
}

function influenceList(items) {
  if (!items?.length) return '';
  return `<ul class="clarification-list">${items.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
}

function sourceLinks(ids) {
  const items = [...new Set(ids)].map(id => state.sources[id]).filter(Boolean);
  if (!items.length) return '';
  return items.map(src => `<a href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">${esc(src.title)}</a>`).join('');
}

function sourcesDetail(detail, checked) {
  const ids = detail?.sourceIds || [];
  const items = [...new Set(ids)].map(id => state.sources[id]).filter(Boolean);
  const freshness = checked ? `<div class="source-freshness"><strong>Дата последней проверки карточки:</strong> ${esc(checked)}</div>` : '<div class="source-freshness value-unknown">Дата нормативной проверки не зафиксирована.</div>';
  if (!items.length) return `${freshness}<div class="value-unknown">Подтверждённые нормативные источники ещё не привязаны.</div>`;
  return `${freshness}<div class="source-list">${items.map(src => `<div><a href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">${esc(src.title)}</a>${src.authority ? `<div class="breadcrumb">${esc(src.authority)}</div>` : ''}</div>`).join('')}</div>`;
}

function assistantBlock(row, variants) {
  const url = state.manifest?.tnvedAssistant?.url || 'https://chatgpt.com/g/g-69f2fdccdb3c8191ad9b7e2daf4c9f20-tn-ved-marketpleisy';
  return `<div class="assistant-box">
    <div class="assistant-copy"><div class="assistant-title">Нужен точный ТН ВЭД для конкретного товара?</div><p>Screening-база показывает возможные варианты и регуляторные риски. Для окончательной классификации передайте специализированному ассистенту фото товара, материал, состав, назначение и технические характеристики.</p><div class="assistant-warning">Коды выше — исходные варианты для проверки, а не готовое таможенное классификационное решение.</div></div>
    <div class="assistant-actions"><a class="primary-action" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Уточнить ТН ВЭД у ассистента</a><button id="copyTnvedPrompt" class="secondary-btn copy-btn" type="button">Скопировать данные для проверки</button></div>
  </div>`;
}

function buildAssistantPrompt(row, detail, variants) {
  const lines = [
    `Товар: ${row.type}`,
    `Основная категория Ozon: ${row.mainCategory}`,
    `Категория Ozon: ${row.category}`,
    '',
    'Предварительные варианты ТН ВЭД из базы Product Screening:'
  ];
  if (variants.length) {
    variants.forEach((v, i) => {
      lines.push(`${i + 1}. ${v.codes.join(' / ')}`);
      if (v.applies?.length) lines.push(`   Когда применим: ${v.applies.join(' / ')}`);
    });
  } else {
    lines.push('Варианты пока не определены.');
  }
  const influence = detail?.tnved?.needsClarification || detail?.clarifications || [];
  if (influence.length) {
    lines.push('', `Для уточнения важны: ${influence.join(', ')}.`);
  }
  lines.push('', 'Нужно определить наиболее корректный 10-значный код ТН ВЭД ЕАЭС именно для конкретного товара. Проверь варианты выше, не принимай их автоматически. Учитывай фотографии, материал, состав, конструкцию, назначение и технические характеристики, которые я пришлю дополнительно.');
  return lines.join('\n');
}

function bindDetailActions(row, detail, variants) {
  const button = $('copyTnvedPrompt');
  if (!button) return;
  button.addEventListener('click', async () => {
    const text = buildAssistantPrompt(row, detail, variants);
    try {
      await navigator.clipboard.writeText(text);
      const old = button.textContent;
      button.textContent = 'Скопировано';
      setTimeout(() => { button.textContent = old; }, 1600);
    } catch (_) {
      const area = document.createElement('textarea');
      area.value = text;
      area.style.position = 'fixed'; area.style.opacity = '0';
      document.body.appendChild(area); area.select(); document.execCommand('copy'); area.remove();
      button.textContent = 'Скопировано';
    }
  });
}
