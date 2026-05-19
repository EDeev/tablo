// ═══ Предпросмотр изображения на странице загрузки ═══════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const drop    = document.getElementById('file-drop-area');
  const input   = document.getElementById('file-input');
  const preview = document.getElementById('file-preview');
  const changeBtn = document.getElementById('change-file-btn');
  if (!drop || !input) return;

  drop.addEventListener('click', () => input.click());

  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      if (preview) {
        preview.src = e.target.result;
        preview.hidden = false;
      }
      if (changeBtn) changeBtn.hidden = false;
      drop.querySelector('.t-upload-drop-text')?.style.setProperty('display', 'none');
    };
    reader.readAsDataURL(file);
  });

  changeBtn?.addEventListener('click', e => {
    e.stopPropagation();
    input.value = '';
    if (preview) preview.hidden = true;
    changeBtn.hidden = true;
    drop.querySelector('.t-upload-drop-text')?.style.removeProperty('display');
  });
});
