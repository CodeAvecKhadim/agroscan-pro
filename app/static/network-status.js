/**
 * AgroScan Pro — Bandeau statut réseau
 * Injecter via <script src="/static/network-status.js"></script> dans chaque page.
 */
(function () {
  'use strict';

  const STYLES = `
    #agro-network-banner {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
      padding: 8px 16px;
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      font-size: .82rem;
      font-weight: 600;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transform: translateY(-100%);
      transition: transform .3s ease;
      pointer-events: none;
    }
    #agro-network-banner.visible {
      transform: translateY(0);
    }
    #agro-network-banner.offline {
      background: #7f1d1d;
      color: #fecaca;
    }
    #agro-network-banner.online {
      background: #166534;
      color: #bbf7d0;
    }
    #agro-network-banner .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    #agro-network-banner.offline .dot { background: #ef4444; animation: agro-pulse 1.5s infinite; }
    #agro-network-banner.online  .dot { background: #22c55e; }
    @keyframes agro-pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: .3; }
    }
  `;

  let banner = null;
  let hideTimer = null;

  function init() {
    const style = document.createElement('style');
    style.textContent = STYLES;
    document.head.appendChild(style);

    banner = document.createElement('div');
    banner.id = 'agro-network-banner';
    banner.innerHTML = '<span class="dot"></span><span class="msg"></span>';
    document.body.prepend(banner);

    window.addEventListener('online',  () => show(true));
    window.addEventListener('offline', () => show(false));

    // Afficher immédiatement si déjà hors ligne
    if (!navigator.onLine) show(false);
  }

  function show(online) {
    clearTimeout(hideTimer);
    const msg = banner.querySelector('.msg');

    if (online) {
      banner.className = 'online visible';
      msg.textContent = '🟢 Connexion rétablie';
      hideTimer = setTimeout(() => { banner.classList.remove('visible'); }, 3000);
    } else {
      banner.className = 'offline visible';
      msg.textContent = '🔴 Hors ligne — données en cache affichées';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
