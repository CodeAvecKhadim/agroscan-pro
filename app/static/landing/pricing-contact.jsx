// AgroScan Landing — Section Tarifs + Section Contact

function LandingPricing() {
  const { Button } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  const [annual, setAnnual] = React.useState(false);
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const goContact = () => { const el = document.getElementById('contact'); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'smooth' }); };

  const plans = [
    {
      name: 'Découverte', price: '0', unit: 'FCFA', note: '7 jours gratuits', accent: false, badge: 'Sans engagement', badgeTone: 'neutral',
      desc: 'Pour découvrir l\u2019agriculture de précision sans risque.',
      features: ['1 parcelle', 'Cartographie GPS', 'Météo agricole', 'Polélé (version limitée)', 'Diagnostic maladies limité'],
      cta: 'Essayer gratuitement', variant: 'secondary', action: () => window.openAuth && window.openAuth('signup'),
    },
    {
      name: 'AgroScan Pro Producteur', accent: true, badge: 'Le plus populaire', badgeTone: 'blue',
      price: annual ? '50 000' : '5 000', unit: 'FCFA', note: annual ? '/ an · 2 mois offerts' : '/ mois',
      desc: 'Pour le producteur qui pilote toute son exploitation.',
      features: ['Parcelles illimitées', 'Analyses satellites illimitées', 'NDVI · stress hydrique · température', 'Historique des cultures', 'Diagnostic maladies illimité', 'Rapports PDF', 'Polélé illimitée', 'Météo agricole avancée'],
      cta: 'Commencer maintenant', variant: 'primary', action: () => window.openAuth && window.openAuth('signup'),
    },
    {
      name: 'Analyse Agricole', price: '1 500', unit: 'FCFA', note: 'à partir de · / analyse', accent: false, badge: 'À la demande', badgeTone: 'soil',
      desc: 'Une analyse ponctuelle, sans abonnement.',
      features: ['Analyse satellite', 'NDVI', 'Stress hydrique', 'Recommandations Polélé', 'Rapport de synthèse'],
      cta: 'Commander une analyse', variant: 'secondary', action: () => window.openAnalysis && window.openAnalysis(),
    },
  ];

  return (
    <section className="lp-section" id="tarifs" style={{ background: 'var(--surface-page)' }}>
      <div className="lp-container">
        <div className="lp-center reveal">
          <span className="lp-eyebrow"><Icon n="tag" size={14} /> Tarifs</span>
          <h2 className="lp-h2">Des offres simples et transparentes</h2>
          <p className="lp-lead">Commencez avec 7 jours gratuits, passez au Pro quand vous êtes prêt. Sans engagement, résiliable à tout moment.</p>
        </div>

        {/* Quote band — remontée EN PREMIER pour plus de visibilité */}
        <div className="lp-quoteband reveal" style={{ marginTop: 36, background: 'linear-gradient(135deg, var(--green-800) 0%, var(--n-900) 100%)', boxShadow: 'var(--shadow-xl)', border: '1.5px solid rgba(255,255,255,.12)' }}>
          <div className="lp-quoteband__icon" style={{ background: 'rgba(255,255,255,.15)', border: '1.5px solid rgba(255,255,255,.25)' }}><Icon n="building-2" size={26} color="#fff" /></div>
          <div className="lp-quoteband__body">
            <h3 style={{ fontSize: 'clamp(18px,2.4vw,22px)' }}>Besoins spécifiques ?</h3>
            <p>Coopérative, ONG, entreprise agricole ou projet de développement ? Services drone, cartographie terrain, études agricoles et accompagnement conseiller sur devis.</p>
          </div>
          <div className="lp-quoteband__actions">
            <Button variant="primary" size="lg" iconLeft={<Icon n="file-text" size={18} color="#fff" />} onClick={goContact}>Demander un devis</Button>
            <a className="lp-quoteband__wa" href="https://wa.me/221784919011" target="_blank" rel="noopener noreferrer">
              <Icon n="phone" size={16} color="var(--green-700)" /> +221 78 491 90 11
            </a>
          </div>
        </div>

        {/* Billing toggle */}
        <div className="reveal" style={{ display: 'flex', justifyContent: 'center', marginTop: 44 }}>
          <div className="lp-billing">
            <button className={'lp-billing__opt' + (!annual ? ' is-active' : '')} onClick={() => setAnnual(false)}>Mensuel</button>
            <button className={'lp-billing__opt' + (annual ? ' is-active' : '')} onClick={() => setAnnual(true)}>Annuel <span className="lp-billing__save">−2 mois</span></button>
          </div>
        </div>

        <div className="lp-pricing">
          {plans.map((p, i) => (
            <div key={p.name} className={'lp-plan reveal' + (p.accent ? ' lp-plan--accent' : '')} data-delay={i + 1}>
              {p.badge && <span className={'lp-plan__badge lp-plan__badge--' + p.badgeTone}>{p.badge}</span>}
              <div className="lp-plan__name">{p.name}</div>
              <div className="lp-plan__price">
                <span className="as-num lp-plan__amount">{p.price}</span>
                {p.unit && <span className="lp-plan__unit">{p.unit}</span>}
              </div>
              <div className="lp-plan__note">{p.note}</div>
              <p className="lp-plan__desc">{p.desc}</p>
              <ul className="lp-plan__list">
                {p.features.map((f) => (
                  <li key={f}><Icon n="check" size={16} color={p.accent ? '#fff' : 'var(--brand)'} /> <span>{f}</span></li>
                ))}
              </ul>
              <div style={{ marginTop: 'auto', paddingTop: 18 }}>
                {p.accent ? (
                  <Button variant="secondary" size="lg" fullWidth onClick={p.action}
                    style={{ background: '#fff', color: 'var(--green-700)', border: 'none' }}>{p.cta}</Button>
                ) : (
                  <Button variant={p.variant} size="lg" fullWidth onClick={p.action}>{p.cta}</Button>
                )}
              </div>
            </div>
          ))}
        </div>
        <p className="lp-center" style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-subtle)', marginTop: 22 }}>
          Tarifs en FCFA · paiement mobile (Orange Money, Wave) à venir.
        </p>

        {/* quoteband déplacée en haut — voir ci-dessus */}
      </div>
    </section>
  );
}
window.LandingPricing = LandingPricing;

function LandingContact() {
  const { Button, Input } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  const [sent, setSent] = React.useState(false);
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const infos = [
    { icon: 'phone', label: 'Téléphone', value: '+221 78 491 90 11', href: 'tel:+221784919011' },
    { icon: 'mail', label: 'E-mail', value: 'contact@agroscan.pro', href: 'mailto:contact@agroscan.pro' },
    { icon: 'map-pin', label: 'Adresse', value: 'Dakar, Sénégal' },
    { icon: 'clock', label: 'Horaires', value: 'Lun – Sam · 8h – 19h' },
  ];

  return (
    <section className="lp-section" id="contact">
      <div className="lp-container">
        <div className="lp-contact">
          {/* Left — info */}
          <div className="reveal">
            <span className="lp-eyebrow"><Icon n="headset" size={14} /> Contact</span>
            <h2 className="lp-h2">Parlons de votre exploitation</h2>
            <p className="lp-lead">Une question, une démonstration, un partenariat ? Notre équipe vous répond en français et en wolof.</p>
            <div className="lp-contact__infos">
              {infos.map((it) => (
                <div key={it.label} className="lp-contact__info">
                  <span className="lp-contact__icon"><Icon n={it.icon} size={20} color="var(--brand-strong)" /></span>
                  <div>
                    <div className="lp-contact__info-label">{it.label}</div>
                    {it.href
                      ? <a href={it.href} className="lp-contact__info-value">{it.value}</a>
                      : <div className="lp-contact__info-value">{it.value}</div>}
                  </div>
                </div>
              ))}
            </div>
            <div className="lp-contact__dev">
              <Icon n="code-xml" size={18} color="var(--text-subtle)" />
              <span>Développé par <b>Social Technologie</b></span>
            </div>
          </div>

          {/* Right — form */}
          <form className="lp-contact__form reveal" data-delay="2" onSubmit={(e) => { e.preventDefault(); setSent(true); }}>
            {sent ? (
              <div className="lp-contact__sent">
                <span style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--brand-soft)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><Icon n="check" size={28} color="var(--brand-strong)" /></span>
                <div style={{ font: 'var(--fw-bold) var(--text-lg)/1.2 var(--font-display)', color: 'var(--text-strong)' }}>Message envoyé !</div>
                <div style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-muted)', textAlign: 'center' }}>Merci. Nous vous recontactons sous 24 h ouvrées.</div>
                <Button variant="secondary" onClick={() => setSent(false)}>Nouveau message</Button>
              </div>
            ) : (
              <React.Fragment>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <Input label="Nom complet" icon={<Icon n="user-round" size={18} />} placeholder="Ex. Awa Diop" required />
                  <Input label="Téléphone" icon={<Icon n="phone" size={18} />} placeholder="+221 …" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ font: 'var(--fw-semibold) var(--text-sm)/1.2 var(--font-ui)', color: 'var(--text-body)' }}>Vous êtes…</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, height: 46, padding: '0 14px', background: 'var(--surface-card)', border: '1.5px solid var(--border-default)', borderRadius: 'var(--radius-md)' }}>
                      <Icon n="users" size={18} style={{ color: 'var(--text-subtle)' }} />
                      <select defaultValue="" style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', font: 'var(--fw-medium) var(--text-base)/1.2 var(--font-ui)', color: 'var(--text-strong)' }}>
                        <option value="" disabled>Choisir…</option>
                        <option>Producteur individuel</option>
                        <option>Coopérative</option>
                        <option>Conseiller agricole</option>
                        <option>ONG / Institution</option>
                        <option>Agro-entreprise</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ font: 'var(--fw-semibold) var(--text-sm)/1.2 var(--font-ui)', color: 'var(--text-body)' }}>Message</label>
                    <textarea rows="4" placeholder="Décrivez votre besoin…" style={{ resize: 'vertical', padding: '12px 14px', background: 'var(--surface-card)', border: '1.5px solid var(--border-default)', borderRadius: 'var(--radius-md)', font: 'var(--fw-medium) var(--text-base)/1.5 var(--font-ui)', color: 'var(--text-strong)', outline: 'none' }}></textarea>
                  </div>
                </div>
                <Button variant="primary" size="lg" fullWidth iconRight={<Icon n="send" size={17} color="#fff" />} style={{ marginTop: 16 }} type="submit">Envoyer le message</Button>
                <p style={{ font: 'var(--fw-medium) var(--text-xs)/1.5 var(--font-ui)', color: 'var(--text-subtle)', textAlign: 'center', marginTop: 12 }}>En envoyant, vous acceptez d'être recontacté par AgroScan Pro.</p>
              </React.Fragment>
            )}
          </form>
        </div>
      </div>
    </section>
  );
}
window.LandingContact = LandingContact;
