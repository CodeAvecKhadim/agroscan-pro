// AgroScan Landing — fixed top navigation + mobile sheet
function LandingNav() {
  const { Button } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  const [stuck, setStuck] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 40);
    window.addEventListener('scroll', onScroll); onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  });
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const links = ['Accueil', 'Fonctionnalités', 'Tarifs', 'À propos', 'Contact'];
  const ANCHORS = { 'Accueil': 'top', 'Fonctionnalités': 'fonctionnalites', 'Tarifs': 'tarifs', 'À propos': 'apropos', 'Contact': 'contact', 'Connexion': 'contact' };
  const goTo = (label) => {
    const id = ANCHORS[label];
    if (!id || id === 'top') { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    const el = document.getElementById(id);
    if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 64, behavior: 'smooth' });
  };
  // Nav is "is-hero" (white text) only at the very top, before stuck.
  const heroMode = !stuck;

  return (
    <React.Fragment>
      <nav className={'lp-nav' + (stuck ? ' is-stuck' : '') + (heroMode ? ' is-hero' : '')}>
        <div className="lp-container lp-nav__inner">
          <a className="lp-brand" onClick={() => goTo('Accueil')} aria-label="AgroScan Pro — accueil">
            <img className="lp-brand__mark" src={(window.IMG && window.IMG.emblem) || "../../assets/logo-emblem.webp"} alt="AgroScan Pro" />
            <span className="lp-brand__name">AgroScan<span className="lp-brand__pro"> Pro</span></span>
          </a>
          <div className="lp-nav__links">
            {links.map((l) => <a key={l} className="lp-nav__link" onClick={() => goTo(l)}>{l}</a>)}
          </div>
          <div className="lp-nav__spacer" />
          <div className="lp-nav__actions">
            <a className="lp-nav__login" onClick={() => window.openAuth && window.openAuth('login')}>Connexion</a>
            <span className="lp-btn-essai"><Button variant="primary" size="sm" onClick={() => window.openAuth && window.openAuth('signup')}>Essayer gratuitement</Button></span>
            <button className="lp-burger" aria-label="Menu" onClick={() => setOpen(true)}><Icon n="menu" size={24} /></button>
          </div>
        </div>
      </nav>

      <div className={'lp-msheet' + (open ? ' is-open' : '')} onClick={() => setOpen(false)}>
        <div className="lp-msheet__panel" onClick={(e) => e.stopPropagation()}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span className="lp-brand">
              <img className="lp-brand__mark" src={(window.IMG && window.IMG.emblem) || "../../assets/logo-emblem.webp"} alt="AgroScan Pro" />
              <span className="lp-brand__name" style={{ color: 'var(--text-strong)' }}>AgroScan<span style={{ color: 'var(--brand)' }}> Pro</span></span>
            </span>
            <button className="lp-burger" style={{ color: 'var(--text-strong)' }} aria-label="Fermer" onClick={() => setOpen(false)}><Icon n="x" size={24} /></button>
          </div>
          {links.concat(['Connexion']).map((l) => <a key={l} className="lp-msheet__link" onClick={() => { setOpen(false); if (l === 'Connexion') { setTimeout(() => window.openAuth && window.openAuth('login'), 60); } else { setTimeout(() => goTo(l), 60); } }}>{l}</a>)}
          <div style={{ marginTop: 16 }}>
            <Button variant="primary" size="lg" fullWidth onClick={() => { setOpen(false); setTimeout(() => window.openAuth && window.openAuth('signup'), 60); }}>Essayer gratuitement</Button>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
}
window.LandingNav = LandingNav;
