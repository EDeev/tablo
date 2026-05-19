// ═══ Переименование предмета ══════════════════════════════════════════════════
function initSubjectRename() {
  document.querySelectorAll('.rename-subject-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('[data-subject]');
      const current = card?.querySelector('.subject-name-display')?.textContent.trim() || '';
      openRenameModal('Переименовать предмет', current, async (val) => {
        const res = await apiFetch(
          `/schedules/${btn.dataset.schedule}/subjects/${enc(btn.dataset.subject)}/field`,
          'POST', { field: 'name', value: val }
        );
        if (res.ok) location.reload(); else alert(res.error || 'Ошибка');
      });
    });
  });
}

// ═══ Удаление предмета ═══════════════════════════════════════════════════════
function initDeleteSubject() {
  document.querySelectorAll('.delete-subject-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm(`Удалить «${btn.dataset.subject}» полностью?`)) return;
      const res = await apiFetch(
        `/schedules/${btn.dataset.schedule}/subjects/${enc(btn.dataset.subject)}`, 'DELETE');
      if (res.ok) location.reload(); else alert(res.error || 'Ошибка');
    });
  });
}

// ═══ Inline-редактирование строк слотов ══════════════════════════════════════
function initSlotInlineEdit() {
  document.querySelectorAll('.slot-inline-edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const viewRow = btn.closest('.t-slot-row');
      const editRow = viewRow?.nextElementSibling;
      if (!editRow?.classList.contains('t-slot-edit-row')) return;
      viewRow.classList.add('hidden');
      editRow.classList.remove('hidden');
      editRow.querySelector('.edit-day')?.focus();
    });
  });

  document.querySelectorAll('.slot-cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const editRow = btn.closest('.t-slot-edit-row');
      const viewRow = editRow?.previousElementSibling;
      editRow.classList.add('hidden');
      viewRow?.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.slot-save-btn').forEach(btn => {
    btn.addEventListener('click', () => saveSlotEdit(btn.closest('.t-slot-edit-row')));
  });

  document.querySelectorAll('.t-slot-edit-row input').forEach(input => {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') saveSlotEdit(input.closest('.t-slot-edit-row'));
      if (e.key === 'Escape') input.closest('.t-slot-edit-row').querySelector('.slot-cancel-btn').click();
    });
  });
}

async function saveSlotEdit(editRow) {
  if (!editRow) return;
  const d = editRow.dataset;
  const newDay   = editRow.querySelector('.edit-day').value.trim().toLowerCase();
  const newTime  = editRow.querySelector('.edit-time').value.trim();
  const newRoom  = editRow.querySelector('.edit-room').value.trim();
  const newTeach = editRow.querySelector('.edit-teach').value.trim();

  const res = await apiFetch(
    `/schedules/${d.schedule}/subjects/${enc(d.subject)}/slot`,
    'PATCH',
    { old_day: d.day, old_time: d.time, type_name: d.type, date_range: d.period,
      day: newDay, time: newTime, classroom: newRoom, teacher: newTeach }
  );
  if (res.ok) {
    // Обновляем ячейки строки просмотра без перезагрузки
    const viewRow = editRow.previousElementSibling;
    viewRow.querySelector('.slot-view-day').textContent  = newDay ? newDay.charAt(0).toUpperCase() + newDay.slice(1) : '—';
    viewRow.querySelector('.slot-view-time').textContent = newTime || '—';
    viewRow.querySelector('.slot-view-room').textContent = newRoom || '—';
    viewRow.querySelector('.slot-view-teach').textContent = newTeach || '—';
    // Обновляем data-атрибуты обеих строк
    for (const row of [viewRow, editRow]) {
      row.dataset.day  = newDay;
      row.dataset.time = newTime;
    }
    // Обновляем data на кнопке удаления
    const delBtn = viewRow.querySelector('.slot-delete-btn');
    if (delBtn) { delBtn.dataset.day = newDay; delBtn.dataset.time = newTime; }
    editRow.classList.add('hidden');
    viewRow.classList.remove('hidden');
  } else {
    alert(res.error || 'Ошибка сохранения');
  }
}

// ═══ Удаление слота ══════════════════════════════════════════════════════════
function initDeleteSlot() {
  document.querySelectorAll('.slot-delete-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Удалить эту строку?')) return;
      const res = await apiFetch(
        `/schedules/${btn.dataset.schedule}/subjects/${enc(btn.dataset.subject)}/slot`,
        'DELETE',
        { day: btn.dataset.day, time: btn.dataset.time,
          type_name: btn.dataset.type, date_range: btn.dataset.daterange }
      );
      if (res.ok) {
        const viewRow = btn.closest('.t-slot-row');
        const editRow = viewRow?.nextElementSibling;
        viewRow?.remove();
        if (editRow?.classList.contains('t-slot-edit-row')) editRow.remove();
      } else {
        alert(res.error || 'Ошибка');
      }
    });
  });
}

// ═══ Добавление новой строки (слота) ════════════════════════════════════════
function initAddSlot() {
  document.querySelectorAll('.add-slot-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const section  = btn.closest('.t-subj-slots-section');
      const tbody    = section.querySelector('.slots-tbody');
      const schedule = btn.dataset.schedule;
      const subject  = btn.dataset.subject;
      const typeName = btn.dataset.type;
      const period   = btn.dataset.period;

      // Вставляем временную строку редактирования
      const tempId = 'newrow-' + Date.now();
      const tr = document.createElement('tr');
      tr.className = 't-slot-edit-row';
      tr.dataset.day = '';
      tr.dataset.time = '';
      tr.dataset.type = typeName;
      tr.dataset.period = period;
      tr.dataset.subject = subject;
      tr.dataset.schedule = schedule;
      tr.id = tempId;
      tr.innerHTML = `
        <td><input type="text" class="t-input t-input-sm edit-day" placeholder="пн" aria-label="День"></td>
        <td><input type="text" class="t-input t-input-sm edit-time" placeholder="09:00-10:30" aria-label="Время"></td>
        <td><input type="text" class="t-input t-input-sm edit-room" placeholder="Кабинет" aria-label="Кабинет"></td>
        <td><input type="text" class="t-input t-input-sm edit-teach" placeholder="Преподаватель" aria-label="Преподаватель"></td>
        <td>
          <div class="t-slot-edit-save-row">
            <button type="button" class="t-btn-icon new-slot-save-btn" title="Сохранить">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
            <button type="button" class="t-btn-icon new-slot-cancel-btn" title="Отмена">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </td>`;
      tbody.appendChild(tr);
      tr.querySelector('.edit-day').focus();

      const doSave = async () => {
        const day   = tr.querySelector('.edit-day').value.trim().toLowerCase();
        const time  = tr.querySelector('.edit-time').value.trim();
        const room  = tr.querySelector('.edit-room').value.trim();
        const teach = tr.querySelector('.edit-teach').value.trim();
        if (!day) { alert('Укажите день'); return; }

        const res = await apiFetch(
          `/schedules/${schedule}/subjects/${enc(subject)}/slot`,
          'PUT',
          { type_name: typeName, date_range: period, day, time, classroom: room, teacher: teach }
        );
        if (res.ok) location.reload();
        else alert(res.error || 'Ошибка');
      };

      tr.querySelector('.new-slot-save-btn').addEventListener('click', doSave);
      tr.querySelector('.new-slot-cancel-btn').addEventListener('click', () => tr.remove());
      tr.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('keydown', e => {
          if (e.key === 'Enter') doSave();
          if (e.key === 'Escape') tr.remove();
        });
      });
    });
  });
}

// ═══ Редактирование периода (date_range) ═════════════════════════════════════
function initEditPeriod() {
  document.querySelectorAll('.edit-period-btn').forEach(btn => {
    const section = btn.closest('.t-subj-slots-section');
    const form    = section.querySelector('.t-subj-period-form');
    const display = section.querySelector('.t-subj-period-display');

    btn.addEventListener('click', () => {
      form.classList.toggle('hidden');
      if (!form.classList.contains('hidden')) {
        form.querySelector('.period-input').select();
      }
    });

    const doSave = async () => {
      const newPeriod = form.querySelector('.period-input').value.trim();
      if (!newPeriod) return;
      const d = section.dataset;
      const res = await apiFetch(
        `/schedules/${d.schedule}/subjects/${enc(d.subject)}/period`,
        'POST',
        { type_name: d.type, old_period: d.period, new_period: newPeriod }
      );
      if (res.ok) {
        display.textContent = newPeriod;
        section.dataset.period = newPeriod;
        // Обновляем data-period на всех строках в секции
        section.querySelectorAll('[data-period]').forEach(el => el.dataset.period = newPeriod);
        section.querySelectorAll('.add-slot-btn').forEach(el => el.dataset.period = newPeriod);
        form.classList.add('hidden');
      } else {
        alert(res.error || 'Ошибка');
      }
    };

    section.querySelector('.save-period-btn')?.addEventListener('click', doSave);
    form.querySelector('.period-input')?.addEventListener('keydown', e => {
      if (e.key === 'Enter') doSave();
      if (e.key === 'Escape') form.classList.add('hidden');
    });
  });
}

// ═══ Описание предмета ════════════════════════════════════════════════════════
function initDescriptions() {
  document.querySelectorAll('.subject-description').forEach(block => {
    const { schedule: sid, subject } = block.dataset;
    const editBtn   = block.querySelector('.edit-desc-btn');
    const form      = block.querySelector('.edit-desc-form');
    const textEl    = block.querySelector('.description-text');
    const input     = block.querySelector('.desc-input');
    const saveBtn   = block.querySelector('.save-desc-btn');
    const cancelBtn = block.querySelector('.cancel-desc-btn');
    if (!editBtn) return;
    editBtn.addEventListener('click', () => {
      form.classList.add('open');
      editBtn.hidden = true;
    });
    cancelBtn.addEventListener('click', () => {
      form.classList.remove('open');
      editBtn.hidden = false;
    });
    saveBtn.addEventListener('click', async () => {
      const res = await apiFetch(
        `/schedules/${sid}/subjects/${enc(subject)}/description`,
        'POST', { description: input.value }
      );
      if (res.ok) {
        textEl.textContent = input.value || 'Нет описания';
        textEl.classList.toggle('text-muted', !input.value);
        textEl.classList.toggle('t-desc-italic', !input.value);
        form.classList.remove('open');
        editBtn.hidden = false;
      }
    });
  });
}

// ═══ Скрыть / показать предмет в расписании ══════════════════════════════════
function initToggleVisibility() {
  document.querySelectorAll('.toggle-visibility-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const res = await apiFetch(
        `/schedules/${btn.dataset.schedule}/subjects/${enc(btn.dataset.subject)}/visibility`,
        'POST'
      );
      if (!res.ok) { alert(res.error || 'Ошибка'); return; }
      const hidden = res.hidden;
      btn.dataset.hidden = hidden ? 'true' : 'false';
      btn.classList.toggle('subject-hidden', hidden);
      btn.title = hidden ? 'Показать в расписании' : 'Скрыть из расписания';
      btn.innerHTML = hidden
        ? `<svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
        : `<svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
      // Visual indicator on the card
      btn.closest('.t-subj-card')?.classList.toggle('subject-hidden', hidden);
    });
  });
}

// ═══ Переименование трекера ═══════════════════════════════════════════════════
function initRenameMetric() {
  const backdrop  = document.getElementById('renameMetricModalBackdrop');
  const input     = document.getElementById('rename-metric-input');
  const confirmBtn = document.getElementById('rename-metric-confirm-btn');
  if (!backdrop || !input || !confirmBtn) return;

  let _metricId   = null;
  let _titleEl    = null;

  document.querySelectorAll('.t-metric-rename-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const widget = btn.closest('.t-metric');
      _metricId  = widget?.dataset.metricId;
      _titleEl   = widget?.querySelector('.t-metric-title');
      input.value = _titleEl?.textContent.trim() || '';
      openModal('renameMetricModalBackdrop');
      setTimeout(() => { input.select(); }, 50);
    });
  });

  let _saving = false;
  const doSave = async () => {
    const label = input.value.trim();
    if (!label || !_metricId || _saving) return;
    _saving = true;
    confirmBtn.disabled = true;
    const res = await apiFetch(`/api/metrics/${_metricId}/rename`, 'POST', { label });
    _saving = false;
    confirmBtn.disabled = false;
    if (res.ok) {
      if (_titleEl) _titleEl.textContent = label;
      closeModal('renameMetricModalBackdrop');
    } else {
      alert(res.error || 'Ошибка');
    }
  };

  confirmBtn.addEventListener('click', doSave);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); doSave(); } });
}

// ═══ Тип сдачи предмета ═══════════════════════════════════════════════════════
function initCompletionType() {
  document.querySelectorAll('.completion-type-select').forEach(sel => {
    sel.addEventListener('change', async () => {
      const res = await apiFetch(
        `/schedules/${sel.dataset.schedule}/subjects/${enc(sel.dataset.subject)}/completion_type`,
        'POST', { completion_type: sel.value || null }
      );
      if (!res.ok) alert(res.error || 'Ошибка');
    });
  });
}

// ═══ Завершить / возобновить предмет ═════════════════════════════════════════
function initToggleCompleted() {
  document.querySelectorAll('.toggle-completed-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const res = await apiFetch(
        `/schedules/${btn.dataset.schedule}/subjects/${enc(btn.dataset.subject)}/completed`,
        'POST'
      );
      if (!res.ok) { alert(res.error || 'Ошибка'); return; }
      const done = res.completed;
      btn.classList.toggle('is-completed', done);
      btn.title = done ? 'Возобновить предмет' : 'Отметить как завершённый';
      btn.innerHTML = done
        ? `<svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`
        : `<svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="20 6 9 17 4 12" opacity=".3"/></svg>`;
      const card = btn.closest('.t-subj-card');
      card?.classList.toggle('subject-completed', done);
      // Обновляем бейдж
      const head = card?.querySelector('.t-subj-head-left');
      let badge = head?.querySelector('.t-completed-badge');
      if (done && !badge) {
        badge = document.createElement('span');
        badge.className = 't-completed-badge';
        badge.textContent = 'Завершён';
        head?.appendChild(badge);
      } else if (!done && badge) {
        badge.remove();
      }
    });
  });
}

// ═══ Ссылка на СДО ════════════════════════════════════════════════════════════
function initSdoUrl() {
  document.querySelectorAll('.t-subj-meta-sdo').forEach(block => {
    const section = block.closest('.t-subj-meta-section');
    if (!section) return;
    const { schedule, subject } = section.dataset;
    const saveBtn = block.querySelector('.save-sdo-btn');
    const input   = block.querySelector('.sdo-url-input');
    if (!saveBtn || !input) return;

    saveBtn.addEventListener('click', async () => {
      const res = await apiFetch(
        `/schedules/${schedule}/subjects/${enc(subject)}/sdo_url`,
        'POST', { sdo_url: input.value.trim() }
      );
      if (!res.ok) { alert(res.error || 'Ошибка'); return; }
      // Перезагружаем страницу, чтобы обновить кнопку открытия СДО
      location.reload();
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') saveBtn.click();
    });
  });
}

// ═══ Промт AI-трекера (клик по названию) ══════════════════════════════════════
function initMetricAiPromptView() {
  document.querySelectorAll('.t-metric-title-clickable').forEach(title => {
    title.addEventListener('click', async () => {
      const widget = title.closest('.t-metric');
      const id = widget?.dataset.metricId;
      if (!id) return;
      const res = await apiFetch(`/api/metrics/${id}/ai_prompt`, 'GET');
      if (res.ok) {
        document.getElementById('ai-prompt-text').textContent = res.prompt || '—';
        openModal('aiPromptModalBackdrop');
      } else {
        alert(res.error || 'Ошибка');
      }
    });
  });
}

// ─── Инициализация страницы предметов ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initRenameModal();
  initEditMode();
  initSubjectRename();
  initDeleteSubject();
  initSlotInlineEdit();
  initDeleteSlot();
  initAddSlot();
  initEditPeriod();
  initDescriptions();
  initToggleVisibility();
  initRenameMetric();
  initCompletionType();
  initToggleCompleted();
  initSdoUrl();
  initMetricAiPromptView();
});
