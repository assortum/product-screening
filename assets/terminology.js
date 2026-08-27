// UI terminology: colors describe regulatory entry complexity, not a business go/no-go decision.
function resultBadge(summary) {
  const map = {
    green: ['green', 'ПРОСТОЙ ВХОД'],
    yellow: ['yellow', 'ТРЕБУЕТ УТОЧНЕНИЯ'],
    red: ['red', 'СЛОЖНЫЙ ВХОД'],
    pending: ['', 'НЕ ПРОВЕРЕНО']
  };
  const [cls, label] = map[summary.result] || map.pending;
  return `<span class="badge ${cls}">${label}</span>`;
}

function scenarioHtml(s) {
  const o = s.output || {};
  const codes = (o.tnvedCandidates || []).map(x => typeof x === 'string' ? x : x.code).filter(Boolean).join(' / ') || 'Не определён';
  const docs = (o.documents?.items || []).map(x => x.label || x.type || x).join(', ') || (o.documents?.status === 'none' ? 'Обязательных не обнаружено' : 'Требует проверки');
  const result = o.result ? ({green:'ПРОСТОЙ ВХОД',yellow:'ТРЕБУЕТ УТОЧНЕНИЯ',red:'СЛОЖНЫЙ ВХОД'}[o.result] || o.result) : 'Не определён';
  const marking = o.marking ? [`сейчас: ${statusText(o.marking.current?.status)}`,`будущее: ${statusText(o.marking.future?.status)}`,`эксперимент: ${statusText(o.marking.experiment?.status)}`].join('; ') : 'Без отдельного изменения';
  return `<div class="scenario-box"><h4>${esc(s.label || 'Подходящий сценарий')}</h4>${s.note ? `<div class="note">${esc(s.note)}</div>` : ''}<div class="scenario-output"><div class="mini-field"><span>ТН ВЭД</span><strong>${esc(codes)}</strong></div><div class="mini-field"><span>Документы</span><strong>${esc(docs)}</strong></div><div class="mini-field"><span>Честный знак</span><strong>${esc(marking)}</strong></div><div class="mini-field"><span>Регуляторный вход</span><strong>${esc(result)}</strong></div></div></div>`;
}

document.addEventListener('DOMContentLoaded', () => {
  const labels = {green:'Простой вход', yellow:'Требует уточнения', red:'Сложный вход', pending:'Не проверено'};
  document.querySelectorAll('.filter-pill[data-result]').forEach(btn => {
    const key = btn.dataset.result;
    if (labels[key]) btn.textContent = labels[key];
  });
  const legend = document.querySelector('.legend');
  if (legend) legend.innerHTML = '<span class="dot green"></span> низкая регуляторная нагрузка <span class="dot yellow"></span> нужны уточнения <span class="dot red"></span> обязательные требования / сложный вход';
});
