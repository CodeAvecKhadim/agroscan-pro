// AgroScan Landing — Sections 3, 5, 6, 7, 8, 9 + footer

// ---- S3: Comment ça marche ----
function LandingSteps() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const steps = [
    { n: '01', icon: 'map-pinned', title: 'Cartographiez votre champ', desc: 'Tracez vos parcelles par GPS depuis votre téléphone — la superficie est calculée automatiquement.' },
    { n: '02', icon: 'satellite', title: 'AgroScan analyse vos données', desc: 'Imagerie satellite, NDVI, météo et historique sont croisés par notre intelligence artificielle agricole.' },
    { n: '03', icon: 'lightbulb', title: 'Recevez des recommandations', desc: 'Des conseils clairs et priorisés : quand irriguer, fertiliser, traiter — parcelle par parcelle.' },
  ];
  return (
    <section className="lp-section" style={{ background: 'var(--surface-page)' }}>
      <div className="lp-container">
        <div className="lp-center reveal">
          <span className="lp-eyebrow"><Icon n="route" size={14} /> Comment ça marche</span>
          <h2 className="lp-h2">Trois étapes, des résultats concrets</h2>
        </div>
        <div className="reveal" style={{ marginTop: 36, position: 'relative', borderRadius: 'var(--radius-2xl)', overflow: 'hidden', boxShadow: 'var(--shadow-md)', aspectRatio: '21 / 9' }}>
          <img src={(window.IMG && window.IMG.drone) || "../../assets/photos/drone-ag.webp"} alt="Drone agricole pulvérisant un champ de cultures" loading="lazy" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(15,92,51,0.10) 0%, rgba(15,92,51,0.46) 100%)' }} />
          <div style={{ position: 'absolute', left: 24, bottom: 20 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '7px 14px', borderRadius: 'var(--radius-pill)', background: 'rgba(255,255,255,.16)', backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,.26)', color: '#fff', font: 'var(--fw-semibold) var(--text-xs)/1 var(--font-ui)' }}>
              <Icon n="plane" size={14} color="#fff" /> Drones &amp; données satellite au service de vos cultures
            </span>
          </div>
        </div>
        <div className="lp-steps">
          {steps.map((s, i) => (
            <div key={s.n} className="lp-step reveal" data-delay={i + 1}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <span style={{ width: 52, height: 52, borderRadius: 'var(--radius-lg)', background: 'var(--brand)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: 'var(--shadow-brand)' }}><Icon n={s.icon} size={24} color="#fff" /></span>
                <span className="lp-step__num">{s.n}</span>
              </div>
              <div className="lp-step__title">{s.title}</div>
              <div className="lp-step__desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
window.LandingSteps = LandingSteps;

// ---- S5: Pourquoi AgroScan ----
function LandingWhy() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const feats = [
    { icon: 'crosshair', title: 'Agriculture de précision', desc: 'Gérez chaque parcelle à l\u2019hectare près, avec des données fiables et actualisées.' },
    { icon: 'bot', title: 'Intelligence artificielle', desc: 'Un moteur agronomique qui transforme vos données en décisions simples.' },
    { icon: 'map-pinned', title: 'Cartographie GPS', desc: 'Délimitez et mesurez vos parcelles directement depuis le terrain.' },
    { icon: 'satellite', title: 'Données satellitaires', desc: 'Suivi NDVI régulier pour repérer le stress avant qu\u2019il ne soit visible.' },
    { icon: 'cloud-sun-rain', title: 'Météo agricole', desc: 'Prévisions locales et fenêtres d\u2019intervention adaptées à vos cultures.' },
    { icon: 'camera', title: 'Diagnostic intelligent', desc: 'Identifiez maladies et carences à partir d\u2019une simple photo.' },
  ];
  return (
    <section className="lp-section lp-container">
      <div id="apropos" className="reveal" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 40, alignItems: 'center', marginBottom: 72 }}>
        <div style={{ position: 'relative', borderRadius: 'var(--radius-2xl)', overflow: 'hidden', boxShadow: 'var(--shadow-lg)', aspectRatio: '4 / 3' }}>
          <img src={(window.IMG && window.IMG.producer) || "../../assets/photos/producer-smartphone.webp"} alt="Producteur sénégalais utilisant AgroScan Pro sur son smartphone" loading="lazy" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg, rgba(26,139,79,0.10) 0%, rgba(15,92,51,0.24) 100%)' }} />
        </div>
        <div>
          <span className="lp-eyebrow"><Icon n="sprout" size={14} /> À propos</span>
          <h2 className="lp-h2" style={{ fontSize: 'clamp(24px,3.6vw,36px)' }}>Conçu pour les producteurs africains</h2>
          <p className="lp-lead">AgroScan Pro met l'agriculture de précision — satellite, IA et météo — entre les mains des producteurs, coopératives et conseillers du Sénégal. Une interface simple, en français et en wolof, pensée pour le terrain et le plein soleil.</p>
        </div>
      </div>
      <div className="lp-center reveal">
        <span className="lp-eyebrow"><Icon n="badge-check" size={14} /> Pourquoi AgroScan Pro</span>
        <h2 className="lp-h2">La technologie au service du rendement</h2>
      </div>
      <div className="lp-why">
        {feats.map((f, i) => (
          <div key={f.title} className="lp-feature reveal" data-delay={(i % 3) + 1}>
            <span className="lp-feature__icon"><Icon n={f.icon} size={24} color="#fff" /></span>
            <div className="lp-feature__title">{f.title}</div>
            <div className="lp-feature__desc">{f.desc}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
window.LandingWhy = LandingWhy;

// ---- S6: Statistiques (animated counters) ----
function Counter({ to, suffix = '', plus = false }) {
  const [val, setVal] = React.useState(0);
  const ref = React.useRef(null);
  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const start = performance.now(), dur = 1400;
          const tick = (now) => {
            const p = Math.min(1, (now - start) / dur);
            const eased = 1 - Math.pow(1 - p, 3);
            setVal(Math.round(eased * to));
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
          io.unobserve(el);
        }
      });
    }, { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, [to]);
  return <span ref={ref} className="as-num">{plus ? val + '+' : val}{suffix}</span>;
}

function LandingStats() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const stats = [
    { node: <Counter to={171} plus />, label: 'API intégrées' },
    { node: <Counter to={500} plus />, label: 'Règles agronomiques' },
    { node: <Counter to={29} />, label: 'Cultures prises en charge' },
    { node: <span className="as-num">24/24</span>, label: 'IA agricole disponible' },
  ];
  return (
    <section className="lp-section lp-stats">
      <div className="lp-container">
        <div className="lp-stats__grid">
          {stats.map((s, i) => (
            <div key={s.label} className="lp-stat reveal" data-delay={i + 1}>
              <div className="lp-stat__num">{s.node}</div>
              <div className="lp-stat__label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
window.LandingStats = LandingStats;

// ---- S7: Témoignages ----
function LandingTestimonials() {
  const { Avatar, Icon } = window.AgroScanProDesignSystem_74357e ? { ...window.AgroScanProDesignSystem_74357e, Icon: window.Icon } : {};
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const quotes = [
    { text: 'Avant, je découvrais les problèmes trop tard. Avec AgroScan, j\u2019ai vu le stress hydrique sur la carte NDVI avant que les plants ne jaunissent.', name: 'Awa Diop', role: 'Productrice de maïs · Mbour' },
    { text: 'L\u2019assistant IA répond en wolof à mes questions sur la fertilisation. C\u2019est comme avoir un agronome dans la poche.', name: 'Moussa Sané', role: 'Coopérative de Thiès' },
    { text: 'La cartographie GPS nous a permis de mesurer précisément 240 hectares répartis sur nos membres. Un gain de temps énorme.', name: 'Fatou Ba', role: 'Conseillère agricole' },
  ];
  return (
    <section className="lp-section" style={{ background: 'var(--surface-page)' }}>
      <div className="lp-container">
        <div className="lp-center reveal">
          <span className="lp-eyebrow"><window.Icon n="quote" size={14} /> Témoignages</span>
          <h2 className="lp-h2">Ils cultivent déjà avec AgroScan</h2>
        </div>
        <div className="lp-tgrid">
          {quotes.map((q, i) => (
            <figure key={q.name} className="lp-quote reveal" data-delay={(i % 3) + 1} style={{ margin: 0 }}>
              <div style={{ display: 'flex', gap: 2 }}>{[0, 1, 2, 3, 4].map((s) => <window.Icon key={s} n="star" size={16} color="var(--c-warning)" />)}</div>
              <blockquote className="lp-quote__text" style={{ margin: 0 }}>« {q.text} »</blockquote>
              <figcaption className="lp-quote__author">
                <span title="Photo producteur à ajouter" style={{ position: 'relative', width: 48, height: 48, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, var(--green-100), var(--blue-100))', boxShadow: '0 0 0 2px var(--surface-card), 0 0 0 4px var(--green-300)' }}>
                  <window.Icon n="user-round" size={22} color="var(--green-700)" />
                </span>
                <div><div style={{ font: 'var(--fw-bold) var(--text-sm)/1.2 var(--font-ui)', color: 'var(--text-strong)' }}>{q.name}</div><div style={{ font: 'var(--fw-medium) var(--text-xs)/1.3 var(--font-ui)', color: 'var(--text-muted)', marginTop: 2 }}>{q.role}</div></div>
              </figcaption>
            </figure>
          ))}
        </div>
        <p className="lp-center" style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-subtle)', marginTop: 22 }}>Producteurs et coopératives du Sénégal — ajoutez ici leurs vraies photos.</p>
      </div>
    </section>
  );
}
window.LandingTestimonials = LandingTestimonials;

// ---- S8: Partenaires ----
function LandingPartners() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const partners = [
    { icon: 'building-2', label: 'Coopératives' },
    { icon: 'landmark', label: 'Ministères' },
    { icon: 'heart-handshake', label: 'ONG' },
    { icon: 'graduation-cap', label: 'Instituts' },
    { icon: 'briefcase', label: 'Agro-entreprises' },
  ];
  return (
    <section className="lp-section lp-container lp-section--tight">
      <div className="lp-center reveal">
        <span className="lp-eyebrow"><Icon n="handshake" size={14} /> Partenaires</span>
        <h2 className="lp-h2" style={{ fontSize: 'clamp(22px,3.4vw,32px)' }}>Aux côtés des acteurs de l'agriculture africaine</h2>
      </div>
      <div className="reveal" style={{ marginTop: 40 }}>
        <p className="lp-center" style={{ font: 'var(--fw-bold) var(--text-2xs)/1 var(--font-ui)', letterSpacing: 'var(--ls-caps)', textTransform: 'uppercase', color: 'var(--text-subtle)', marginBottom: 16 }}>Cultures africaines prises en charge</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center' }}>
          {['Mil', 'Sorgho', 'Arachide', 'Niébé', 'Riz', 'Maïs', 'Manioc', 'Coton', 'Sésame', 'Oignon'].map((c) => (
            <span key={c} style={{ padding: '8px 16px', borderRadius: 'var(--radius-pill)', background: 'var(--brand-soft)', color: 'var(--brand-strong)', font: 'var(--fw-semibold) var(--text-sm)/1 var(--font-ui)', border: '1px solid var(--green-200)' }}>{c}</span>
          ))}
        </div>
      </div>
      <div className="lp-partners reveal">
        {partners.map((p) => (
          <div key={p.label} className="lp-partner">
            <Icon n={p.icon} size={26} color="var(--text-subtle)" sw={1.6} />
            <span style={{ font: 'var(--fw-semibold) var(--text-xs)/1 var(--font-ui)' }}>{p.label}</span>
          </div>
        ))}
      </div>
      <p className="lp-center" style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-subtle)', marginTop: 18 }}>Emplacements réservés — déposez ici les logos de vos partenaires.</p>
    </section>
  );
}
window.LandingPartners = LandingPartners;

// ---- S9: Final CTA + footer ----
function LandingFooter() {
  const { Button } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const cols = [
    { h: 'Produit', links: ['Mon Champ', 'Santé des Cultures Pro', 'IA Agricole', 'Météo Agricole', 'Diagnostic Maladies'] },
    { h: 'Entreprise', links: ['À propos', 'Tarifs', 'Partenaires', 'Contact'] },
    { h: 'Ressources', links: ['Centre d\u2019aide', 'Guides agronomiques', 'API'] },
  ];
  return (
    <React.Fragment>
      <section className="lp-section lp-container">
        <div className="lp-finalcta reveal">
          <div style={{ position: 'absolute', inset: 0, opacity: .5 }}>
            <window.AgroScanProDesignSystem_74357e.FieldMap mode="satellite" height={400} rounded={false} grid={true} />
          </div>
          <div style={{ position: 'relative' }}>
            <h2>Prêt à moderniser votre exploitation agricole ?</h2>
            <p style={{ font: 'var(--fw-medium) var(--text-md)/1.5 var(--font-ui)', color: 'rgba(255,255,255,.9)', maxWidth: '46ch', margin: '16px auto 0' }}>Rejoignez les producteurs qui pilotent leurs cultures avec le satellite et l'IA. Sans engagement.</p>
            <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap', marginTop: 28 }}>
              <Button variant="secondary" size="lg" iconLeft={<Icon n="rocket" size={18} />} onClick={() => window.openAuth && window.openAuth('signup')}>Essayer AgroScan gratuitement</Button>
              <Button variant="glass" size="lg" style={{ background: 'rgba(255,255,255,.14)', color: '#fff', border: '1.5px solid rgba(255,255,255,.4)', backdropFilter: 'blur(8px)' }} onClick={() => { const el = document.getElementById('contact'); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 64, behavior: 'smooth' }); }}>Parler à un conseiller</Button>
            </div>
          </div>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-container">
          <div className="lp-footer__grid">
            <div className="lp-footer__col">
              <span className="lp-brand">
                <img className="lp-brand__mark" src={(window.IMG && window.IMG.emblem) || "../../assets/logo-emblem.webp"} alt="AgroScan Pro" style={{ width: 44, height: 44 }} />
                <span className="lp-brand__name" style={{ color: '#fff', fontSize: 22 }}>AgroScan<span style={{ color: 'var(--green-300)' }}> Pro</span></span>
              </span>
              <p style={{ font: 'var(--fw-medium) var(--text-sm)/1.6 var(--font-ui)', color: 'rgba(255,255,255,.6)', marginTop: 16, maxWidth: '34ch' }}>L'agriculture de précision au service des producteurs africains.</p>
              <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
                {['facebook', 'twitter', 'linkedin', 'youtube'].map((s) => (
                  <span key={s} style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(255,255,255,.08)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}><Icon n={s} size={17} color="rgba(255,255,255,.7)" /></span>
                ))}
              </div>
            </div>
            {cols.map((c) => (
              <div key={c.h} className="lp-footer__col">
                <h4>{c.h}</h4>
                {c.links.map((l) => <a key={l}>{l}</a>)}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', justifyContent: 'space-between', marginTop: 40, padding: '20px 22px', borderRadius: 'var(--radius-lg)', background: 'rgba(255,255,255,.05)', border: '1px solid rgba(255,255,255,.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,.08)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}><Icon n="code-xml" size={20} color="#9BD4F5" /></span>
              <div>
                <div style={{ font: 'var(--fw-medium) var(--text-2xs)/1 var(--font-ui)', letterSpacing: 'var(--ls-caps)', textTransform: 'uppercase', color: 'rgba(255,255,255,.5)' }}>Développé par</div>
                <div style={{ font: 'var(--fw-bold) var(--text-md)/1.1 var(--font-display)', color: '#fff', marginTop: 4 }}>Social Technologie</div>
              </div>
            </div>
            <a href="tel:+221784919011" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '11px 18px', borderRadius: 'var(--radius-pill)', background: 'var(--brand)', color: '#fff', textDecoration: 'none', font: 'var(--fw-bold) var(--text-sm)/1 var(--font-ui)' }}>
              <Icon n="phone" size={16} color="#fff" /> +221 78 491 90 11
            </a>
          </div>
          <div className="lp-footer__bottom">
            <span>© 2026 AgroScan Pro. Tous droits réservés.</span>
            <span style={{ display: 'flex', gap: 18 }}><a onClick={() => window.openLegal && window.openLegal('privacy')} style={{ color: 'inherit', textDecoration: 'none', cursor: 'pointer' }}>Confidentialité</a><a onClick={() => window.openLegal && window.openLegal('terms')} style={{ color: 'inherit', textDecoration: 'none', cursor: 'pointer' }}>Conditions</a></span>
          </div>
        </div>
      </footer>
    </React.Fragment>
  );
}
window.LandingFooter = LandingFooter;
