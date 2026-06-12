/**
 * AgroScan Pro — Module i18n
 * Charge la langue depuis localStorage['agro_lang'] (fr | wo | pu).
 * Utilisation :
 *   await i18n.load();
 *   i18n.t('parcelle.ajouter')   → "Yokku Tànk" (wolof)
 *   i18n.setLang('wo')           → recharge la page dans la langue choisie
 */
const i18n = (() => {
  const STORAGE_KEY = 'agro_lang';
  const SUPPORTED   = ['fr'];
  const LABELS      = { fr: 'Français' };
  const FLAGS       = { fr: '🇫🇷' };

  let _translations = {};
  let _lang = localStorage.getItem(STORAGE_KEY) || 'fr';
  if (!SUPPORTED.includes(_lang)) _lang = 'fr';

  function _get(obj, path) {
    return path.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : null), obj);
  }

  async function load(lang) {
    if (lang) _lang = lang;
    try {
      const r = await fetch(`/static/i18n/${_lang}.json`);
      _translations = await r.json();
    } catch (e) {
      console.warn('i18n: fallback fr', e);
      const r = await fetch('/static/i18n/fr.json');
      _translations = await r.json();
      _lang = 'fr';
    }
    _applyPage();
    return _translations;
  }

  function t(key, fallback) {
    const v = _get(_translations, key);
    return v !== null ? v : (fallback || key);
  }

  function lang() { return _lang; }

  function setLang(code) {
    if (!SUPPORTED.includes(code)) return;
    localStorage.setItem(STORAGE_KEY, code);
    location.reload();
  }

  // Applique data-i18n sur la page
  function _applyPage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const v = t(key);
      if (v) el.textContent = v;
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const key = el.getAttribute('data-i18n-ph');
      const v = t(key);
      if (v) el.placeholder = v;
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const v = t(key);
      if (v) el.title = v;
    });
  }

  // Génère le sélecteur de langue (boutons inline)
  function renderSwitcher(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = SUPPORTED.map(code =>
      `<button
        onclick="i18n.setLang('${code}')"
        style="padding:4px 10px;border-radius:20px;border:1.5px solid ${code===_lang?'#16a34a':'#d1d5db'};
               background:${code===_lang?'#dcfce7':'#fff'};cursor:pointer;font-size:13px;font-weight:${code===_lang?'700':'400'};
               color:${code===_lang?'#166534':'#374151'};margin-right:4px;"
        title="${LABELS[code]}"
      >${FLAGS[code]} ${LABELS[code]}</button>`
    ).join('');
  }

  return { load, t, lang, setLang, renderSwitcher, LABELS, FLAGS, SUPPORTED };
})();
