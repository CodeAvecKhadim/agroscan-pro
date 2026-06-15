// AgroScan Landing — Section 2: flagship modules
function LandingModules() {
  const { FieldMap } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const IAMedia = () => (
    <div style={{ height: '100%', position: 'relative', overflow: 'hidden', background: 'radial-gradient(130% 130% at 80% 6%, #2DA15D 0%, #0F5C33 56%, #0A3A22 100%)' }}>
      <img src={(window.IMG && window.IMG.polele) || "/static/assets/polele-avatar.svg"} alt="Polélé" width="66" height="66" style={{ position: 'absolute', left: 16, top: 18, borderRadius: '50%', boxShadow: '0 8px 20px -6px rgba(0,0,0,.4)' }} />
      <div style={{ position: 'absolute', left: 92, top: 30, font: 'var(--fw-bold) var(--text-md)/1 var(--font-display)', color: '#fff' }}>Polélé<div style={{ font: 'var(--fw-medium) 11px/1.2 var(--font-ui)', color: 'rgba(255,255,255,.8)', marginTop: 4 }}>Conseillère agricole</div></div>
      <div style={{ position: 'absolute', right: 16, bottom: 18, maxWidth: 200, padding: '8px 12px', borderRadius: '14px 14px 4px 14px', background: 'rgba(255,255,255,.16)', backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,.28)', font: 'var(--fw-semibold) 12px/1.35 var(--font-ui)', color: '#fff' }}>Irriguez sous 48 h, avant la pluie de mercredi.</div>
    </div>
  );

  const PhotoMedia = ({ src, alt, label, labelIcon, tone = 'green' }) => (
    <div style={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
      <img src={src} alt={alt} loading="lazy" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
      <div style={{ position: 'absolute', inset: 0, background: tone === 'blue'
        ? 'linear-gradient(165deg, rgba(27,143,204,0.10) 0%, rgba(15,92,51,0.30) 100%)'
        : 'linear-gradient(165deg, rgba(26,139,79,0.12) 0%, rgba(15,92,51,0.34) 100%)' }} />
      {label && (
        <div style={{ position: 'absolute', top: 14, left: 14, display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 'var(--radius-pill)', background: 'rgba(8,24,16,.5)', backdropFilter: 'blur(4px)', color: '#fff', font: 'var(--fw-semibold) 11px/1 var(--font-ui)' }}>
          {labelIcon && <Icon n={labelIcon} size={12} color="#fff" />}{label}
        </div>
      )}
    </div>
  );

  const MODULES = [
    {
      n: 1, icon: 'map-pinned', accent: 'green', route: '/mon-champ',
      title: 'Mon Champ',
      desc: 'Cartographiez vos parcelles et calculez automatiquement leur superficie par GPS.',
      media: <PhotoMedia src={(window.IMG && window.IMG.producer) || "/static/assets/photos/producer-smartphone.webp"} alt="Producteur cartographiant son champ" label="GPS terrain" labelIcon="map-pinned" />,
    },
    {
      n: 2, icon: 'satellite', accent: 'green', route: '/sante-cultures',
      title: 'Santé des Cultures Pro',
      desc: 'Analyse satellitaire et surveillance NDVI de la santé de vos cultures, zone par zone.',
      media: <PhotoMedia src={(window.IMG && window.IMG.field) || "/static/assets/photos/field-rice.webp"} alt="Rizière analysée par satellite" label="NDVI satellite" labelIcon="satellite" />,
    },
    {
      n: 3, icon: 'bot', accent: 'green', route: '/conseiller',
      title: 'IA Agricole — Polélé',
      desc: 'Polélé, votre conseillère agricole intelligente, disponible 24h/24 en français et en wolof.',
      media: <IAMedia />,
    },
    {
      n: 4, icon: 'cloud-sun-rain', accent: 'blue', route: '/meteo',
      title: 'Météo Agricole',
      desc: 'Prévisions météo locales adaptées à votre exploitation et à vos fenêtres d’intervention.',
      media: <PhotoMedia src={(window.IMG && window.IMG.sky) || "/static/assets/photos/sky-weather.webp"} alt="Ciel de pluie au-dessus d’un champ" tone="blue" label="31 °C · pluie" labelIcon="cloud-rain" />,
    },
    {
      n: 5, icon: 'camera', accent: 'green', route: '/scan',
      title: 'Diagnostic Maladies',
      desc: 'Prenez une photo d’une feuille et obtenez un diagnostic instantané, avec plan d’action.',
      media: <PhotoMedia src={(window.IMG && window.IMG.leaf) || "/static/assets/photos/leaf-disease.webp"} alt="Feuilles atteintes par une maladie" label="Analyse photo" labelIcon="scan-line" />,
    },
  ];

  return (
    <section className="lp-section lp-container" id="fonctionnalites">
      <div className="lp-center reveal">
        <span className="lp-eyebrow"><Icon n="layout-grid" size={14} /> Modules phares</span>
        <h2 className="lp-h2">Cinq outils, une seule plateforme</h2>
        <p className="lp-lead">De l’analyse de sol au suivi satellite, de la météo à l’IA — tout ce qu’il faut pour piloter votre exploitation.</p>
      </div>
      <div className="lp-modules__grid">
        {MODULES.map((m, i) => {
          const accent = m.accent === 'blue' ? 'var(--blue-500)' : 'var(--brand)';
          const accentStrong = m.accent === 'blue' ? 'var(--blue-600)' : 'var(--brand-strong)';
          return (
            <article key={m.title} className="lp-mod reveal" data-delay={(i % 3) + 1}>
              <div className="lp-mod__media">{m.media}</div>
              <div className="lp-mod__icon" style={{ background: accent }}><Icon n={m.icon} size={25} color="#fff" sw={2.2} /></div>
              <div className="lp-mod__body">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ font: 'var(--fw-bold) 11px/1 var(--font-mono)', color: accent, letterSpacing: 'var(--ls-wide)' }}>0{m.n}</span>
                  <span style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
                </div>
                <h3 className="lp-mod__title">{m.title}</h3>
                <p className="lp-mod__desc">{m.desc}</p>
                <a href={m.route} className="lp-mod__link" style={{ color: accentStrong }}>Accéder <Icon n="arrow-right" size={16} color={accentStrong} /></a>
              </div>
            </article>
          );
        })}
        {/* 6th cell: CTA tile */}
        <article className="lp-mod reveal" data-delay="3" style={{ background: 'var(--brand-soft)', border: '1px dashed var(--green-300)', alignItems: 'center', justifyContent: 'center', textAlign: 'center', cursor: 'pointer' }} onClick={() => window.location.href = '/app'}>
          <div className="lp-mod__body" style={{ alignItems: 'center', justifyContent: 'center', paddingTop: 24 }}>
            <span style={{ width: 56, height: 56, borderRadius: 'var(--radius-lg)', background: 'var(--brand)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}><Icon n="arrow-right" size={26} color="#fff" /></span>
            <h3 className="lp-mod__title">Tout AgroScan Pro</h3>
            <p className="lp-mod__desc" style={{ flex: 'initial' }}>Découvrez la plateforme complète, gratuitement.</p>
            <a href="/app" className="lp-mod__link" style={{ color: 'var(--brand-strong)', justifyContent: 'center' }}>Ouvrir l’app <Icon n="arrow-right" size={16} color="var(--brand-strong)" /></a>
          </div>
        </article>
      </div>
    </section>
  );
}
window.LandingModules = LandingModules;
