// UI terminology: colors describe regulatory entry complexity, not a business go/no-go decision.
function resultBadge(summary) {
  const map = {
    green: ['green', 'ПРОСТОЙ ВХОД'],
    yellow: ['yellow', 'ВНИМАНИЕ'],
    red: ['red', 'СЛОЖНЫЙ ВХОД'],
    pending: ['', 'НЕ ПРОВЕРЕНО']
  };
  const [cls, label] = map[summary.result] || map.pending;
  return `<span class="badge ${cls}">${label}</span>`;
}

document.addEventListener('DOMContentLoaded', () => {
  const labels = {green:'Простой вход', yellow:'Внимание', red:'Сложный вход', pending:'Не проверено'};
  document.querySelectorAll('.filter-pill[data-result]').forEach(btn => {
    const key = btn.dataset.result;
    if (labels[key]) btn.textContent = labels[key];
  });
  const legend = document.querySelector('.legend');
  if (legend) legend.innerHTML = '<span class="dot green"></span> низкая регуляторная нагрузка <span class="dot yellow"></span> есть риск / развилка <span class="dot red"></span> существенные обязательные требования';
});
