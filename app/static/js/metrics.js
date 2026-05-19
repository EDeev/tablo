// ═══ Ядро: чтение/запись прогресса через data-атрибут ════════════════════════

function getProgress(widget) {
  try { return JSON.parse(widget.dataset.progress || '{}'); } catch { return {}; }
}

function setProgress(widget, prog) {
  widget.dataset.progress = JSON.stringify(prog);
}

async function saveProgress(widget, prog) {
  setProgress(widget, prog);
  const id = widget.dataset.metricId;
  await apiFetch(`/api/metrics/${id}/progress`, 'POST', prog);
}

// ═══ Инициализация всех виджетов ═════════════════════════════════════════════

function initMetricWidgets() {
  document.querySelectorAll('.t-metric').forEach(w => initWidget(w));
}

function initWidget(w) {
  if (w._init) return;
  w._init = true;

  const type    = w.dataset.metricType;
  const canEdit = typeof CAN_EDIT !== 'undefined' ? CAN_EDIT : true;

  w.querySelector('.delete-metric-btn')?.addEventListener('click', async () => {
    if (!confirm('Удалить трекер?')) return;
    const res = await apiFetch(`/api/metrics/${w.dataset.metricId}`, 'DELETE');
    if (res.ok) w.remove();
  });

  if (!canEdit) return;

  if (type === 'checkpoints') {
    const total = w.querySelectorAll('.t-cp').length;
    w.querySelectorAll('button.t-cp').forEach(btn => {
      btn.addEventListener('click', async () => {
        const prog    = getProgress(w);
        const checked = prog.checked || [];
        const idx     = parseInt(btn.dataset.index);
        const pos     = checked.indexOf(idx);
        if (pos === -1) checked.push(idx); else checked.splice(pos, 1);
        prog.checked = checked;
        btn.classList.toggle('done', checked.includes(idx));
        const done    = checked.length;
        const fracEl  = w.querySelector('.t-cp-fraction');
        if (fracEl) fracEl.firstChild.textContent = done;
        const fill = w.querySelector('.t-cp-fill');
        if (fill && total) fill.style.width = Math.round(done / total * 100) + '%';
        await saveProgress(w, prog);
      });
    });
  }

  if (type === 'progress_bar') {
    const cfg = (() => { try { return JSON.parse(w.dataset.config || '{}'); } catch { return {}; } })();
    w.querySelector('.update-progress-btn')?.addEventListener('click', async () => {
      const input = w.querySelector('.progress-input');
      const val   = parseFloat(input.value) || 0;
      const mx    = parseFloat(cfg.max || 100);
      const pct   = Math.min(100, Math.round(val / mx * 100));
      const ring  = w.querySelector('.t-pb-ring-fill');
      if (ring) ring.style.strokeDashoffset = ((100 - pct) / 100 * 213.6).toFixed(1);
      const pctEl = w.querySelector('.t-pb-pct');
      if (pctEl) pctEl.textContent = pct + '%';
      const valEl = w.querySelector('.t-pb-val');
      if (valEl) valEl.firstChild.textContent = val;
      await saveProgress(w, { current: val });
    });
  }

  if (type === 'counter') {
    const cfg    = (() => { try { return JSON.parse(w.dataset.config || '{}'); } catch { return {}; } })();
    const valEl  = w.querySelector('.t-counter-val');
    const step   = parseFloat(cfg.step) || 1;
    const update = async delta => {
      const prog = getProgress(w);
      const max  = cfg.max ? parseFloat(cfg.max) : Infinity;
      const raw  = (prog.current || 0) + delta;
      const next = Math.max(0, Math.min(max, Math.round(raw * 1e9) / 1e9));
      prog.current = next;
      valEl.textContent = next;
      if (cfg.max) {
        const bar = w.querySelector('.t-counter-bar-fill');
        if (bar) bar.style.width = Math.min(100, Math.round(next / parseFloat(cfg.max) * 100)) + '%';
      }
      await saveProgress(w, prog);
    };
    w.querySelector('.counter-dec')?.addEventListener('click', () => update(-step));
    w.querySelector('.counter-inc')?.addEventListener('click', () => update(+step));
  }

  if (type === 'stages') {
    w.querySelectorAll('.stage-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const idx = parseInt(btn.dataset.index);
        w.querySelectorAll('.stage-btn').forEach((b, i) => {
          b.classList.toggle('done',   i < idx);
          b.classList.toggle('active', i === idx);
          if (i > idx) b.classList.remove('done', 'active');
        });
        w.querySelectorAll('.t-stage-conn').forEach((c, i) => {
          c.classList.toggle('done', i < idx);
        });
        await saveProgress(w, { current_stage: idx });
      });
    });
  }

  if (type === 'checklist') {
    w.querySelectorAll('.checklist-item').forEach(cb => {
      cb.addEventListener('change', async () => {
        const prog    = getProgress(w);
        const checked = prog.checked || [];
        const idx     = parseInt(cb.dataset.index);
        const pos     = checked.indexOf(idx);
        if (cb.checked && pos === -1) checked.push(idx);
        if (!cb.checked && pos !== -1) checked.splice(pos, 1);
        prog.checked = checked;
        cb.closest('.t-cl-item').classList.toggle('checked', cb.checked);
        await saveProgress(w, prog);
      });
    });
  }

  if (type === 'attendance') {
    w.querySelector('.add-att-btn')?.addEventListener('click', async () => {
      const dateVal = w.querySelector('.att-date').value;
      const status  = w.querySelector('.att-status').value;
      if (!dateVal) return;
      const prog    = getProgress(w);
      const records = prog.records || [];
      records.push({ date: dateVal, status });
      prog.records = records;
      // Добавить точку в историю
      const dot = document.createElement('span');
      dot.className = `t-att-dot t-att-dot--${status}`;
      dot.title = dateVal;
      w.querySelector('.t-att-dots')?.appendChild(dot);
      // Обновить счётчик нужного стата
      const statMap = { present: 't-att-stat--present', absent: 't-att-stat--absent', excused: 't-att-stat--excused' };
      const statEl = w.querySelector(`.${statMap[status]} .t-att-num`);
      if (statEl) statEl.textContent = parseInt(statEl.textContent || '0') + 1;
      w.querySelector('.att-date').value = '';
      await saveProgress(w, prog);
    });
  }

  if (type === 'grades') {
    w.querySelector('.save-grades-btn')?.addEventListener('click', async () => {
      const prog   = getProgress(w);
      const grades = {};
      w.querySelectorAll('.grade-input').forEach(inp => {
        if (inp.value !== '') grades[inp.dataset.work] = parseFloat(inp.value);
      });
      prog.grades = grades;
      await saveProgress(w, prog);
      flashSaved(w.querySelector('.save-grades-btn'));
    });
  }

  if (type === 'deadlines') {
    w.querySelectorAll('.deadline-item').forEach(cb => {
      cb.addEventListener('change', async () => {
        const prog      = getProgress(w);
        const completed = prog.completed || [];
        const idx       = parseInt(cb.dataset.index);
        const pos       = completed.indexOf(idx);
        if (cb.checked && pos === -1) completed.push(idx);
        if (!cb.checked && pos !== -1) completed.splice(pos, 1);
        prog.completed = completed;
        cb.closest('.t-dl-item').classList.toggle('done', cb.checked);
        await saveProgress(w, prog);
      });
    });
  }

  if (type === 'streak') {
    w.querySelector('.mark-today-btn')?.addEventListener('click', async () => {
      const today   = new Date().toISOString().split('T')[0];
      const prog    = getProgress(w);
      const records = prog.records || [];
      if (records.includes(today)) return;
      records.push(today);
      prog.records = records;
      w.querySelector('.t-streak-num').textContent = records.length;
      w.querySelector('.mark-today-btn').disabled = true;
      await saveProgress(w, prog);
    });
  }

  if (type === 'effort_hours') {
    const cfg = (() => { try { return JSON.parse(w.dataset.config || '{}'); } catch { return {}; } })();
    w.querySelector('.add-effort-btn')?.addEventListener('click', async () => {
      const add  = parseFloat(w.querySelector('.effort-input').value);
      if (!add || add <= 0) return;
      const prog  = getProgress(w);
      const total = +(prog.hours || 0) + add;
      prog.hours  = total;
      const numEl = w.querySelector('.t-ef-num');
      if (numEl) numEl.childNodes[0].textContent = total;
      const goal = parseFloat(cfg.goal_hours);
      if (goal) {
        const pct = Math.min(100, Math.round(total / goal * 100));
        const bar = w.querySelector('.t-ef-bar-fill');
        if (bar) bar.style.width = pct + '%';
        const pctEl = w.querySelector('.t-ef-bar-pct');
        if (pctEl) pctEl.textContent = pct + '%';
      }
      w.querySelector('.effort-input').value = '';
      await saveProgress(w, prog);
    });
  }

  if (type === 'rating_history') {
    const cfg = (() => { try { return JSON.parse(w.dataset.config || '{}'); } catch { return {}; } })();
    w.querySelector('.add-rating-btn')?.addEventListener('click', async () => {
      const dateVal = w.querySelector('.rating-date').value;
      const grade   = parseFloat(w.querySelector('.rating-grade').value);
      if (!dateVal || isNaN(grade)) return;
      const prog    = getProgress(w);
      const entries = prog.entries || [];
      entries.push({ date: dateVal, grade });
      prog.entries  = entries;
      const scale   = cfg.scale || 5;
      const list    = w.querySelector('.t-rh-list');
      const pct     = Math.round(grade / scale * 100);
      const row     = document.createElement('div');
      row.className = 't-rh-row';
      row.innerHTML = `<span class="t-rh-date">${dateVal}</span>`
                    + `<div class="t-rh-track"><div class="t-rh-fill" style="width:${pct}%"></div></div>`
                    + `<span class="t-rh-val">${grade}</span>`;
      // Удалить «Нет записей» если было
      list.querySelector('.t-metric-empty')?.remove();
      list.prepend(row);
      // Обновить summary — последняя оценка и среднее
      const avg = (entries.reduce((s, e) => s + e.grade, 0) / entries.length).toFixed(1);
      ['.t-rh-last-val', '.t-rh-big-val'].forEach(sel => {
        const el = w.querySelector(sel);
        if (el) el.textContent = grade;
      });
      ['.t-rh-avg', '.t-rh-big-avg'].forEach(sel => {
        const el = w.querySelector(sel);
        if (el) el.textContent = el.textContent.replace(/[\d.]+/, avg);
      });
      w.querySelector('.rating-date').value  = '';
      w.querySelector('.rating-grade').value = '';
      await saveProgress(w, prog);
    });
  }
}

// ═══ Форма добавления трекера ════════════════════════════════════════════════

const METRIC_SCHEMA = {
  checkpoints:    [{ name: 'total',      label: 'Количество точек',                    type: 'number', ph: '10' },
                   { name: 'labels',     label: 'Подписи через запятую (опц.)',         type: 'text',   ph: 'КТ1,КТ2' }],
  progress_bar:   [{ name: 'max',        label: 'Максимум',                            type: 'number', ph: '100' },
                   { name: 'unit',       label: 'Единица',                             type: 'text',   ph: 'баллов' },
                   { name: 'step',       label: 'Шаг',                                 type: 'number', ph: '1' }],
  counter:        [{ name: 'max',        label: 'Максимум (0 = ∞)',                    type: 'number', ph: '0' },
                   { name: 'step',       label: 'Шаг',                                 type: 'number', ph: '1' },
                   { name: 'unit',       label: 'Единица',                             type: 'text',   ph: 'раз' }],
  stages:         [{ name: 'stages',     label: 'Этапы через запятую',                 type: 'text',   ph: 'Старт,В работе,Сдано' }],
  checklist:      [{ name: 'items',      label: 'Пункты, каждый с новой строки',       type: 'textarea', ph: 'Пункт 1\nПункт 2' }],
  attendance:     [],
  grades:         [{ name: 'works',      label: 'Работы: имя=вес, через запятую',      type: 'text',   ph: 'ЛР1=1,ЛР2=2' },
                   { name: 'max_grade',  label: 'Макс. балл',                          type: 'number', ph: '5' }],
  deadlines:      [{ name: 'items',      label: 'Дедлайны: имя|ГГГГ-ММ-ДД, по строке', type: 'textarea', ph: 'Курсовая|2026-05-20' }],
  streak:         [],
  effort_hours:   [{ name: 'goal_hours', label: 'Цель (часов)',                        type: 'number', ph: '40' }],
  rating_history: [{ name: 'scale',      label: 'Шкала (макс. балл)',                  type: 'number', ph: '5' }],
};

function buildConfig(type, form) {
  const schema = METRIC_SCHEMA[type] || [];
  const cfg = {};
  for (const f of schema) {
    const el  = form.querySelector(`[data-cfg="${f.name}"]`);
    const val = el?.value.trim();
    if (!val) continue;
    if (type === 'checkpoints' && f.name === 'labels') { cfg.labels = val.split(',').map(s => s.trim()).filter(Boolean); continue; }
    if (type === 'stages'      && f.name === 'stages')  { cfg.stages = val.split(',').map(s => s.trim()).filter(Boolean); continue; }
    if (type === 'checklist'   && f.name === 'items')   { cfg.items  = val.split('\n').map(s => s.trim()).filter(Boolean); continue; }
    if (type === 'grades'      && f.name === 'works')   {
      cfg.works = val.split(',').map(s => { const [n, w] = s.split('=').map(x => x.trim()); return { name: n, weight: parseFloat(w) || 1 }; });
      continue;
    }
    if (type === 'deadlines' && f.name === 'items') {
      cfg.items = val.split('\n').map(s => { const [n, d] = s.split('|').map(x => x.trim()); return { name: n, date: d || '' }; }).filter(x => x.name);
      continue;
    }
    cfg[f.name] = f.type === 'number' ? parseFloat(val) || 0 : val;
  }
  return cfg;
}

function renderConfigFields(type, area) {
  area.innerHTML = '';
  for (const f of METRIC_SCHEMA[type] || []) {
    const wrap = document.createElement('div');
    wrap.className = 't-field';
    const lbl = document.createElement('label');
    lbl.className = 't-label';
    lbl.textContent = f.label;
    lbl.htmlFor = `cfg-${f.name}`;
    wrap.appendChild(lbl);
    let el;
    if (f.type === 'textarea') {
      el = document.createElement('textarea');
      el.rows = 3;
      el.className = 't-input t-textarea';
    } else {
      el = document.createElement('input');
      el.type = f.type;
      el.className = 't-input t-input-sm';
    }
    el.placeholder  = f.ph || '';
    el.dataset.cfg  = f.name;
    el.id           = `cfg-${f.name}`;
    wrap.appendChild(el);
    area.appendChild(wrap);
  }
}

function initAddMetric() {
  document.querySelectorAll('.add-metric-section').forEach(section => {
    const sid       = section.dataset.schedule;
    const subject   = section.dataset.subject;
    const slotId    = section.dataset.slot;
    const container = document.getElementById(`metrics-${slotId}`);
    const aiForm    = section.querySelector('.ai-metric-form');
    const manForm   = section.querySelector('.manual-metric-form');

    section.querySelector('.ai-metric-btn')?.addEventListener('click', () => {
      aiForm.classList.toggle('open');
      manForm.classList.remove('open');
    });
    section.querySelector('.manual-metric-btn')?.addEventListener('click', () => {
      manForm.classList.toggle('open');
      aiForm.classList.remove('open');
    });

    const typeSelect = section.querySelector('.metric-type-select');
    const configArea = section.querySelector('.metric-config-area');
    typeSelect?.addEventListener('change', () => renderConfigFields(typeSelect.value, configArea));

    // AI
    section.querySelector('.ai-prompt-submit')?.addEventListener('click', async () => {
      const prompt = section.querySelector('.ai-prompt-input').value.trim();
      if (!prompt) return;
      const submitBtn = section.querySelector('.ai-prompt-submit');
      submitBtn.innerHTML = '<span class="t-spinner"></span>';
      submitBtn.disabled  = true;
      const res = await apiFetch(
        `/schedules/${sid}/subjects/${enc(subject)}/metrics/ai`, 'POST', { prompt }
      );
      submitBtn.innerHTML = '<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>';
      submitBtn.disabled  = false;
      if (res.ok && container) {
        container.insertAdjacentHTML('beforeend', res.html);
        const newEl = container.lastElementChild;
        initWidget(newEl);
        gridRegisterNew(newEl, container);
        aiForm.classList.remove('open');
        section.querySelector('.ai-prompt-input').value = '';
      } else alert(res.error || 'Ошибка');
    });

    // Вручную
    section.querySelector('.manual-metric-submit')?.addEventListener('click', async () => {
      const type  = typeSelect?.value;
      const label = section.querySelector('.metric-label-input').value.trim();
      if (!type) { alert('Выберите тип'); return; }
      const cfg = buildConfig(type, section);
      const res = await apiFetch(
        `/schedules/${sid}/subjects/${enc(subject)}/metrics`, 'POST',
        { type, label, config: cfg }
      );
      if (res.ok && container) {
        container.insertAdjacentHTML('beforeend', res.html);
        const newEl = container.lastElementChild;
        initWidget(newEl);
        gridRegisterNew(newEl, container);
        manForm.classList.remove('open');
        section.querySelector('.metric-label-input').value = '';
        if (typeSelect) typeSelect.value = '';
        configArea.innerHTML = '';
      } else alert(res.error || 'Ошибка');
    });
  });
}

// ═══ Grid-редактор: размер и перетаскивание трекеров ═════════════════════════

const GRID_COLS   = 3;   // колонки (совпадает с --mg-cols в CSS)
const GRID_MAX_W  = 3;   // макс. ширина в колонках
const GRID_MAX_H  = 4;   // макс. высота в полустроках (4 = 2 строки)

// Применить размерные классы gw-N / gh-N (N = полустроки для высоты)
function applyGridSize(el) {
  const w = Math.max(1, Math.min(GRID_MAX_W, parseInt(el.dataset.gridW) || 1));
  const h = Math.max(1, Math.min(GRID_MAX_H, parseInt(el.dataset.gridH) || 2));
  el.classList.remove('gw-2', 'gw-3', 'gh-1', 'gh-2', 'gh-3', 'gh-4');
  if (w > 1) el.classList.add(`gw-${w}`);
  el.classList.add(`gh-${h}`);
}

// ─── Сохранение позиции/размера в БД ─────────────────────────────────────────
async function saveLayout(metricId, col, row, w, h) {
  await apiFetch(`/api/metrics/${metricId}/layout`, 'POST',
                 { grid_col: col, grid_row: row, grid_w: w, grid_h: h });
}

// ─── Resize (правый нижний угол) ──────────────────────────────────────────────
function initResize(el, grid) {
  const handle = el.querySelector('.t-metric-resize');
  if (!handle) return;

  handle.addEventListener('pointerdown', e => {
    if (!grid.classList.contains('drag-mode')) return;
    e.preventDefault();
    e.stopPropagation();
    handle.setPointerCapture(e.pointerId);

    const startX = e.clientX;
    const startY = e.clientY;
    const startW = parseInt(el.dataset.gridW) || 1;
    const startH = parseInt(el.dataset.gridH) || 2;

    // Ширина одной колонки; высота одной полустроки из CSS-переменной
    const gap      = parseFloat(getComputedStyle(grid).getPropertyValue('--mg-gap')) || 12;
    const colW     = (grid.offsetWidth - gap * (GRID_COLS - 1)) / GRID_COLS;
    const rowHpx   = parseFloat(getComputedStyle(grid).getPropertyValue('--row-h')) || 120;

    function onMove(ev) {
      const dx   = ev.clientX - startX;
      const dy   = ev.clientY - startY;
      const col  = parseInt(el.dataset.gridCol) || 0;
      const maxW = Math.min(GRID_MAX_W, GRID_COLS - col);
      const newW = Math.max(1, Math.min(maxW,      Math.round(startW + dx / (colW + gap))));
      const newH = Math.max(1, Math.min(GRID_MAX_H, Math.round(startH + dy / (rowHpx + gap))));
      el.dataset.gridW = newW;
      el.dataset.gridH = newH;
      applyGridSize(el);
    }

    async function onUp() {
      handle.removeEventListener('pointermove', onMove);
      handle.removeEventListener('pointerup',   onUp);
      const mid = el.dataset.metricId;
      const col = parseInt(el.dataset.gridCol) || 0;
      const row = parseInt(el.dataset.gridRow) || 0;
      const w   = parseInt(el.dataset.gridW)   || 1;
      const h   = parseInt(el.dataset.gridH)   || 2;
      await saveLayout(mid, col, row, w, h);
    }

    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup',   onUp);
  });
}

// ─── Drag-and-drop ────────────────────────────────────────────────────────────
function initDrag(grid) {
  let dragged = null;

  const items = () => [...grid.querySelectorAll(':scope > .t-metric')];

  // Сдвиг элементов вправо/вниз, освобождая место перед target
  function shiftBefore(target) {
    if (!dragged || target === dragged) return;
    const all = items();
    const fromIdx = all.indexOf(dragged);
    const toIdx   = all.indexOf(target);
    if (fromIdx === -1 || toIdx === -1) return;
    if (fromIdx < toIdx) {
      target.after(dragged);
    } else {
      target.before(dragged);
    }
  }

  grid.addEventListener('dragstart', e => {
    const metric = e.target.closest('.t-metric');
    if (!metric || !grid.classList.contains('drag-mode')) { e.preventDefault(); return; }
    dragged = metric;
    metric.classList.add('drag-ghost');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', metric.dataset.metricId);
  });

  grid.addEventListener('dragend', e => {
    const metric = e.target.closest('.t-metric');
    if (!metric) return;
    metric.classList.remove('drag-ghost');
    grid.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    dragged = null;
    // Сохранить новый порядок: обновляем grid_row / grid_col по позиции в DOM
    persistOrder(grid);
  });

  grid.addEventListener('dragover', e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const target = e.target.closest('.t-metric');
    if (!target || target === dragged) return;
    grid.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    target.classList.add('drag-over');
    shiftBefore(target);
  });

  grid.addEventListener('drop', e => {
    e.preventDefault();
    grid.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  });
}

// Пересчитать col/row по DOM-порядку и сохранить в БД одним батч-запросом
async function persistOrder(grid) {
  let col = 0, row = 0, rowMaxH = 2;
  const items = [];

  grid.querySelectorAll(':scope > .t-metric').forEach(el => {
    const w = parseInt(el.dataset.gridW) || 1;
    const h = parseInt(el.dataset.gridH) || 2;

    if (col + w > GRID_COLS) {
      col = 0;
      row += rowMaxH;
      rowMaxH = 2;
    }

    el.dataset.gridCol = col;
    el.dataset.gridRow = row;
    rowMaxH = Math.max(rowMaxH, h);
    col += w;

    items.push({ id: el.dataset.metricId, grid_col: col - w, grid_row: row, grid_w: w, grid_h: h });
  });

  await apiFetch('/api/metrics/layout_batch', 'POST', { items });
}

// ─── Переход к трекеру на дашборде с подсветкой ───────────────────────────────
function initMetricLinks() {
  document.querySelectorAll('.t-slot-metric-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const mid    = link.dataset.metricId;
      const target = document.getElementById(`metric-${mid}`);
      if (!target) return;
      // Закрыть слот если открыт
      const detail = link.closest('.t-slot-detail');
      if (detail) {
        const slot = detail.previousElementSibling;
        if (slot?.classList.contains('open')) {
          slot.classList.remove('open');
          detail.style.display = 'none';
        }
      }
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target.classList.remove('highlight');
      // Перезапуск анимации через reflow
      void target.offsetWidth;
      target.classList.add('highlight');
      target.addEventListener('animationend', () => target.classList.remove('highlight'), { once: true });
    });
  });
}

// ─── Кнопки включения режима редактирования сетки ────────────────────────────
function initGridEditButtons() {
  document.querySelectorAll('.t-grid-edit-btn').forEach(btn => {
    const gridId = btn.dataset.grid;
    const grid   = document.getElementById(gridId);
    if (!grid) return;

    btn.addEventListener('click', () => {
      const active = grid.classList.toggle('drag-mode');
      btn.classList.toggle('active', active);
      // draggable выставляем/снимаем на всех метриках
      grid.querySelectorAll(':scope > .t-metric').forEach(el => {
        el.draggable = active;
      });
    });
  });
}

// ─── Добавить resize-ручку к элементу ────────────────────────────────────────
function addResizeHandle(el) {
  if (el.querySelector('.t-metric-resize')) return;
  const h = document.createElement('div');
  h.className   = 't-metric-resize';
  h.title       = 'Изменить размер';
  h.innerHTML   = '<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M9 1L1 9M5 1L1 5M9 5L5 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
  el.appendChild(h);
}

// ─── Инициализация всех grid-контейнеров ─────────────────────────────────────
function initMetricsGrids() {
  document.querySelectorAll('.t-metrics-grid').forEach(grid => {
    grid.querySelectorAll(':scope > .t-metric').forEach(el => {
      applyGridSize(el);
      addResizeHandle(el);
      initResize(el, grid);
    });
    initDrag(grid);
  });
  initGridEditButtons();
}

// После динамической вставки нового виджета — подключить его к сетке
function gridRegisterNew(el, grid) {
  applyGridSize(el);
  addResizeHandle(el);
  initResize(el, grid);
  if (grid.classList.contains('drag-mode')) el.draggable = true;
}

// ─── Инициализация ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initMetricWidgets();
  initAddMetric();
  initMetricsGrids();
  initMetricLinks();
});
