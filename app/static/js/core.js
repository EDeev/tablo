// ─── CSRF ────────────────────────────────────────────────────────────────────
const csrfToken = () =>
  document.querySelector('meta[name="csrf-token"]')?.content || '';

// ─── Fetch-обёртка ───────────────────────────────────────────────────────────
async function apiFetch(url, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
  };
  if (body !== null) opts.body = JSON.stringify(body);
  let res;
  try {
    res = await fetch(url, opts);
  } catch (e) {
    return { error: 'Нет соединения' };
  }
  if (res.redirected || res.status === 401 || res.status === 302) {
    return { error: 'Сессия истекла, обновите страницу' };
  }
  try {
    return await res.json();
  } catch {
    return { error: `Ошибка сервера (${res.status})` };
  }
}

// ─── Модальные окна ──────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// ─── URL-encode ──────────────────────────────────────────────────────────────
function enc(s) { return encodeURIComponent(s); }

// ─── Режим редактирования ────────────────────────────────────────────────────
function initEditMode() {
  const btn = document.getElementById('edit-mode-btn');
  if (!btn) return;
  const key = 'edit-mode-' + (typeof SCHEDULE_ID !== 'undefined' ? SCHEDULE_ID : '');
  if (sessionStorage.getItem(key) === '1') {
    document.body.classList.add('edit-mode');
    btn.classList.add('on');
  }
  btn.addEventListener('click', () => {
    const active = document.body.classList.toggle('edit-mode');
    btn.classList.toggle('on', active);
    sessionStorage.setItem(key, active ? '1' : '0');
  });
}

// ─── Флеш «сохранено» на кнопке ─────────────────────────────────────────────
function flashSaved(btn) {
  if (!btn) return;
  const orig = btn.textContent;
  btn.textContent = '✓';
  setTimeout(() => btn.textContent = orig, 1200);
}

// ─── Универсальный модал переименования ─────────────────────────────────────
let _renameCb = null;
function openRenameModal(title, currentVal, cb) {
  _renameCb = cb;
  document.getElementById('rename-modal-title').textContent = title;
  const input = document.getElementById('rename-input');
  input.value = currentVal;
  openModal('renameModalBackdrop');
  setTimeout(() => input.select(), 50);
}
function initRenameModal() {
  const confirmBtn = document.getElementById('rename-confirm-btn');
  if (!confirmBtn) return;
  const doSave = async () => {
    const val = document.getElementById('rename-input').value.trim();
    if (!val) return;
    closeModal('renameModalBackdrop');
    if (_renameCb) { await _renameCb(val); _renameCb = null; }
  };
  confirmBtn.addEventListener('click', doSave);
  document.getElementById('rename-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') doSave();
  });
}
