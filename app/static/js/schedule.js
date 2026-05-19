// ═══ Переименование расписания ═══════════════════════════════════════════════
function initRenameSchedule() {
  document.querySelector('.rename-schedule-btn')?.addEventListener('click', () => {
    const current = document.querySelector('.schedule-name-display')?.textContent.trim() || '';
    openRenameModal('Переименовать расписание', current, async (val) => {
      const res = await apiFetch(`/schedules/${SCHEDULE_ID}/rename`, 'POST', { name: val });
      if (res.ok) {
        document.querySelector('.schedule-name-display').textContent = val;
        document.title = val;
      } else alert(res.error || 'Ошибка');
    });
  });
}

// ─── Инициализация страницы расписания ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initRenameModal();
  initEditMode();
  initRenameSchedule();
});
