// AgroScan Landing — Section 1: hero banner + technology strip
function LandingHero() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const techTags = [
    { icon: 'cpu', label: 'Capteurs de sol' },
    { icon: 'satellite', label: 'Satellite & NDVI' },
    { icon: 'sparkles', label: 'IA agricole' },
    { icon: 'cloud-sun-rain', label: 'Météo agricole' },
    { icon: 'map-pinned', label: 'Cartographie GPS' },
  ];

  return (
    <header id="accueil">
      {/* Composed hero image */}
      <div className="lp-hero lp-hero--composed">
        <div className="lp-hero__composedwrap">
          <img
            className="lp-hero__composed"
            src={(window.IMG && window.IMG.hero) || "/static/assets/photos/hero-composed.webp"}
            alt="AgroScan Pro — Toute votre ferme vue du ciel et du sol : capteurs de sol, satellite NDVI, IA agricole Polélé et météo."
            loading="eager"
            fetchpriority="high"
          />
          {/* Clickable hotspot over the baked CTA button in the image */}
          <a className="lp-hero__hotspot" href="#contact" aria-label="Analyser ma ferme maintenant"></a>
        </div>
        <a className="lp-hero__cue" href="#fonctionnalites" aria-label="Découvrir les fonctionnalités">
          <span>Découvrir</span>
          <Icon n="chevron-down" size={20} color="#0F5C33" />
        </a>
      </div>

      {/* Technology strip — always visible below hero */}
      <div style={{
        background: 'var(--n-900)',
        borderBottom: '1px solid rgba(255,255,255,.08)',
        padding: '14px 24px',
        display: 'flex',
        gap: 10,
        justifyContent: 'center',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}>
        <span style={{ font: 'var(--fw-semibold) var(--text-2xs)/1 var(--font-ui)', letterSpacing: 'var(--ls-caps)', textTransform: 'uppercase', color: 'rgba(255,255,255,.45)', marginRight: 6 }}>Propulsé par</span>
        {techTags.map((t) => (
          <span key={t.label} style={{
            display: 'inline-flex', alignItems: 'center', gap: 7,
            padding: '7px 14px',
            borderRadius: 'var(--radius-pill)',
            background: 'rgba(255,255,255,.07)',
            border: '1px solid rgba(255,255,255,.12)',
            backdropFilter: 'blur(4px)',
            color: 'rgba(255,255,255,.88)',
            font: 'var(--fw-semibold) var(--text-xs)/1 var(--font-ui)',
          }}>
            <Icon n={t.icon} size={13} color="var(--green-300)" />
            {t.label}
          </span>
        ))}
      </div>
    </header>
  );
}
window.LandingHero = LandingHero;
