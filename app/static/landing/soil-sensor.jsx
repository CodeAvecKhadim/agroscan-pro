// AgroScan Landing — Section: Analyse de sol (capteur 8-en-1)
function LandingSoilSensor() {
  const { Button } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const params = [
    { icon: 'thermometer', label: 'Température du sol' },
    { icon: 'droplet', label: 'Humidité' },
    { icon: 'flask-conical', label: 'pH' },
    { icon: 'zap', label: 'Conductivité (EC)' },
    { icon: 'leaf', label: 'Azote (N)' },
    { icon: 'atom', label: 'Phosphore (P)' },
    { icon: 'circle-dot', label: 'Potassium (K)' },
    { icon: 'waves', label: 'Salinité' },
  ];

  return (
    <section className="lp-section" id="capteur" style={{ background: 'var(--surface-page)' }}>
      <div className="lp-container">
        <div className="lp-center reveal">
          <span className="lp-eyebrow"><Icon n="cpu" size={14} /> Capteur de sol 8-en-1</span>
          <h2 className="lp-h2">Analysez votre sol en temps réel</h2>
          <p className="lp-lead">Le capteur AgroScan mesure 8 paramètres essentiels du sol et les envoie directement dans l'application. Plus de rendement, moins de pertes — un sol bien connu, une récolte assurée.</p>
        </div>

        <div className="lp-soil reveal">
          {/* Banner image */}
          <figure className="lp-soil__media">
            <img src={(window.IMG && window.IMG.soil) || "../../assets/photos/soil-sensor.webp"} alt="Capteur de sol AgroScan 8-en-1 : température, humidité, pH, conductivité, azote, phosphore, potassium, salinité — analyse en temps réel dans un champ de piment au Sénégal" loading="lazy" />
          </figure>

          {/* Side panel */}
          <div className="lp-soil__panel">
            <p className="lp-soil__kicker">8 paramètres essentiels mesurés</p>
            <div className="lp-soil__grid">
              {params.map((p) => (
                <div key={p.label} className="lp-soil__param">
                  <span className="lp-soil__paramicon"><Icon n={p.icon} size={18} color="#fff" /></span>
                  <span className="lp-soil__paramlabel">{p.label}</span>
                </div>
              ))}
            </div>
            <div className="lp-soil__benefits">
              {[['trending-up', 'Améliorez vos récoltes'], ['piggy-bank', 'Économisez engrais & eau'], ['sprout', 'Des cultures plus saines']].map(([ic, t]) => (
                <span key={t} className="lp-soil__benefit"><Icon n={ic} size={15} color="var(--brand-strong)" /> {t}</span>
              ))}
            </div>
            <div className="lp-soil__actions">
              <Button variant="primary" size="lg" iconLeft={<Icon n="scan-line" size={18} color="#fff" />} onClick={() => window.openAnalysis && window.openAnalysis()}>Commander une analyse de sol</Button>
              <Button variant="secondary" size="lg" iconLeft={<Icon n="file-text" size={17} />} onClick={() => { const el = document.getElementById('contact'); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 64, behavior: 'smooth' }); }}>Demander un devis capteur</Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
window.LandingSoilSensor = LandingSoilSensor;
