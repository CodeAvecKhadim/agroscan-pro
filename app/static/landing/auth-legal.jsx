// AgroScan Landing — Auth (Connexion/Inscription) + Legal modals
// Mounted once. Exposes window.openAuth('login'|'signup') and window.openLegal('privacy'|'terms').

function AuthLegalModals() {
  const { Button, Input } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  const [auth, setAuth] = React.useState(null);   // null | 'login' | 'signup'
  const [legal, setLegal] = React.useState(null); // null | 'privacy' | 'terms'
  const [analysis, setAnalysis] = React.useState(false);

  React.useEffect(() => {
    window.openAuth = (mode = 'login') => { setLegal(null); setAnalysis(false); setAuth(mode); };
    window.openLegal = (doc = 'privacy') => { setAuth(null); setAnalysis(false); setLegal(doc); };
    window.openAnalysis = () => { setAuth(null); setLegal(null); setAnalysis(true); };
    const onKey = (e) => { if (e.key === 'Escape') { setAuth(null); setLegal(null); setAnalysis(false); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const open = auth || legal || analysis;
  React.useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);
  if (!open) return null;

  const close = () => { setAuth(null); setLegal(null); setAnalysis(false); };

  return (
    <div className="lp-modal" role="dialog" aria-modal="true">
      <div className="lp-modal__backdrop" onClick={close} />
      {auth ? <AuthPanel mode={auth} setMode={setAuth} close={close} Button={Button} Input={Input} Icon={Icon} />
            : analysis ? <AnalysisPanel close={close} Button={Button} Input={Input} Icon={Icon} />
            : <LegalPanel doc={legal} setDoc={setLegal} close={close} Icon={Icon} />}
    </div>
  );
}

function AuthPanel({ mode, setMode, close, Button, Input, Icon }) {
  const isSignup = mode === 'signup';
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const submit = (e) => { e.preventDefault(); window.location.href = isSignup ? '/register' : '/login'; };

  return (
    <div className="lp-modal__panel">
      <button className="lp-modal__close" aria-label="Fermer" onClick={close}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
      </button>

      {/* Brand panel */}
      <div className="lp-auth__brand">
        <div>
          <span className="lp-brand" style={{ pointerEvents: 'none' }}>
            <img className="lp-brand__mark" src={(window.IMG && window.IMG.emblem) || "../../assets/logo-emblem.webp"} alt="" style={{ width: 46, height: 46 }} />
            <span className="lp-brand__name" style={{ color: '#fff' }}>AgroScan<span style={{ color: 'var(--green-300)' }}> Pro</span></span>
          </span>
          <h2 style={{ font: 'var(--fw-display) 28px/1.12 var(--font-display)', letterSpacing: 'var(--ls-tight)', marginTop: 28 }}>
            {isSignup ? 'Rejoignez l\u2019agriculture de précision.' : 'Bon retour parmi nous.'}
          </h2>
          <p style={{ font: 'var(--fw-medium) var(--text-sm)/1.6 var(--font-ui)', color: 'rgba(255,255,255,.85)', marginTop: 14, maxWidth: '30ch' }}>
            {isSignup ? 'Cartographiez vos parcelles, suivez vos cultures par satellite et discutez avec Polélé.' : 'Accédez à vos parcelles, vos analyses NDVI et vos recommandations.'}
          </p>
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: '24px 0 0', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {['Cartographie GPS & superficie auto', 'NDVI satellite & stress hydrique', 'Polélé — conseillère IA 24h/24'].map((t) => (
            <li key={t} style={{ display: 'flex', alignItems: 'center', gap: 10, font: 'var(--fw-semibold) var(--text-sm)/1.3 var(--font-ui)', color: '#fff' }}>
              <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(255,255,255,.18)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}><Icon n="check" size={13} color="#fff" /></span>{t}
            </li>
          ))}
        </ul>
      </div>

      {/* Form */}
      <div className="lp-auth__form">
        <div className="lp-auth__tabs">
          <button className={'lp-auth__tab' + (!isSignup ? ' is-active' : '')} onClick={() => setMode('login')}>Connexion</button>
          <button className={'lp-auth__tab' + (isSignup ? ' is-active' : '')} onClick={() => setMode('signup')}>Inscription</button>
        </div>

        <button className="lp-auth__social" type="button" onClick={submit}>
          <Icon n="smartphone" size={18} color="var(--brand-strong)" /> Continuer avec mon numéro
        </button>
        <div className="lp-auth__divider">ou par e-mail</div>

        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {isSignup && <Input label="Nom complet" icon={<Icon n="user-round" size={17} />} placeholder="Awa Diop" />}
          <Input label="E-mail" type="email" icon={<Icon n="mail" size={17} />} placeholder="vous@exemple.sn" />
          {isSignup && <Input label="Téléphone" icon={<Icon n="phone" size={17} />} placeholder="+221 …" />}
          <Input label="Mot de passe" type="password" icon={<Icon n="lock" size={17} />} placeholder="••••••••" />
          {!isSignup && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: -6 }}>
              <a style={{ font: 'var(--fw-semibold) var(--text-xs)/1 var(--font-ui)', color: 'var(--text-link)', cursor: 'pointer' }}>Mot de passe oublié ?</a>
            </div>
          )}
          <Button variant="primary" size="lg" fullWidth iconRight={<Icon n="arrow-right" size={18} color="#fff" />}>
            {isSignup ? 'Créer mon compte' : 'Se connecter'}
          </Button>
        </form>

        {isSignup && (
          <p style={{ font: 'var(--fw-medium) var(--text-xs)/1.5 var(--font-ui)', color: 'var(--text-subtle)', marginTop: 16, textAlign: 'center' }}>
            En continuant, vous acceptez nos <a onClick={() => window.openLegal('terms')} style={{ color: 'var(--text-link)', cursor: 'pointer' }}>Conditions</a> et notre <a onClick={() => window.openLegal('privacy')} style={{ color: 'var(--text-link)', cursor: 'pointer' }}>Politique de confidentialité</a>.
          </p>
        )}
        <p style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-muted)', marginTop: 18, textAlign: 'center' }}>
          {isSignup ? 'Déjà un compte ?' : 'Pas encore de compte ?'}{' '}
          <a onClick={() => setMode(isSignup ? 'login' : 'signup')} style={{ color: 'var(--text-link)', fontWeight: 'var(--fw-bold)', cursor: 'pointer' }}>
            {isSignup ? 'Se connecter' : 'Créer un compte'}
          </a>
        </p>
      </div>
    </div>
  );
}

function LegalPanel({ doc, setDoc, close, Icon }) {
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  return (
    <div className="lp-modal__panel lp-modal__panel--doc">
      <button className="lp-modal__close" aria-label="Fermer" onClick={close}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
      </button>
      <div className="lp-doc__head">
        <span className="lp-eyebrow"><Icon n="shield-check" size={14} /> Informations légales</span>
        <div className="lp-doc__tabs">
          <button className={'lp-doc__tab' + (doc === 'privacy' ? ' is-active' : '')} onClick={() => setDoc('privacy')}>Confidentialité</button>
          <button className={'lp-doc__tab' + (doc === 'terms' ? ' is-active' : '')} onClick={() => setDoc('terms')}>Conditions d'utilisation</button>
        </div>
      </div>
      <div className="lp-doc__body">
        {doc === 'privacy' ? <PrivacyText /> : <TermsText />}
        <p style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border-subtle)', color: 'var(--text-subtle)' }}>
          Dernière mise à jour : juin 2026 · AgroScan Pro, développé par Social Technologie · +221 78 491 90 11. Modèle indicatif — à faire valider par un conseil juridique avant publication.
        </p>
      </div>
    </div>
  );
}

function PrivacyText() {
  return (
    <React.Fragment>
      <p>AgroScan Pro (« nous ») attache une grande importance à la protection des données de ses utilisateurs producteurs, coopératives et conseillers agricoles. Cette politique explique quelles données nous collectons et comment nous les utilisons.</p>
      <h4>1. Données que nous collectons</h4>
      <ul>
        <li>Informations de compte : nom, e-mail, numéro de téléphone.</li>
        <li>Données agricoles : contours de parcelles, position GPS, cultures, historiques d'analyse.</li>
        <li>Données techniques : type d'appareil, logs d'utilisation de l'application.</li>
      </ul>
      <h4>2. Utilisation des données</h4>
      <p>Vos données servent exclusivement à fournir le service : calcul de superficie, analyses satellite (NDVI), recommandations de l'assistant Polélé et prévisions météo localisées. Elles ne sont jamais vendues à des tiers.</p>
      <h4>3. Partage</h4>
      <p>Un partage limité peut intervenir avec votre coopérative ou conseiller, uniquement si vous y consentez explicitement, et avec nos prestataires d'imagerie satellite et d'hébergement, dans le cadre du service.</p>
      <h4>4. Conservation & sécurité</h4>
      <p>Les données sont conservées tant que votre compte est actif et protégées par chiffrement. Vous pouvez demander leur suppression à tout moment.</p>
      <h4>5. Vos droits</h4>
      <p>Vous disposez d'un droit d'accès, de rectification et de suppression de vos données. Pour l'exercer, contactez-nous au +221 78 491 90 11.</p>
    </React.Fragment>
  );
}

function TermsText() {
  return (
    <React.Fragment>
      <p>Les présentes conditions régissent l'utilisation de la plateforme AgroScan Pro. En créant un compte, vous les acceptez.</p>
      <h4>1. Service</h4>
      <p>AgroScan Pro fournit des outils d'agriculture de précision : cartographie GPS, analyse satellitaire, diagnostic des cultures, météo agricole et assistant IA. Les recommandations sont fournies à titre indicatif et ne remplacent pas le jugement de l'exploitant.</p>
      <h4>2. Compte</h4>
      <p>Vous êtes responsable de l'exactitude des informations fournies et de la confidentialité de vos identifiants.</p>
      <h4>3. Abonnements</h4>
      <ul>
        <li>Découverte : gratuit, fonctionnalités limitées.</li>
        <li>Pro & Coopérative : abonnements payants en FCFA, sans engagement, résiliables à tout moment.</li>
      </ul>
      <h4>4. Disponibilité</h4>
      <p>Les données satellite dépendent de la couverture nuageuse et des passages satellites ; des délais peuvent survenir. Nous nous efforçons d'assurer une disponibilité maximale du service.</p>
      <h4>5. Propriété</h4>
      <p>Vous restez propriétaire de vos données agricoles. La plateforme, ses marques et son code restent la propriété d'AgroScan Pro / Social Technologie.</p>
      <h4>6. Contact</h4>
      <p>Pour toute question : +221 78 491 90 11.</p>
    </React.Fragment>
  );
}

function AnalysisPanel({ close, Button, Input, Icon }) {
  const [sent, setSent] = React.useState(false);
  const [crop, setCrop] = React.useState('');
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
  const submit = (e) => { e.preventDefault(); setSent(true); };

  return (
    <div className="lp-modal__panel lp-modal__panel--doc">
      <button className="lp-modal__close" aria-label="Fermer" onClick={close}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
      </button>
      <div className="lp-doc__head" style={{ paddingBottom: 0 }}>
        <span className="lp-eyebrow"><Icon n="satellite" size={14} /> Analyse à la demande</span>
        <h2 style={{ font: 'var(--fw-display) 26px/1.12 var(--font-display)', letterSpacing: 'var(--ls-tight)', color: 'var(--text-strong)', marginTop: 12 }}>Commander une analyse</h2>
        <p style={{ font: 'var(--fw-medium) var(--text-sm)/1.55 var(--font-ui)', color: 'var(--text-muted)', margin: '8px 0 18px' }}>
          Analyse satellite ponctuelle d'une parcelle — NDVI, stress hydrique, recommandations Polélé et rapport de synthèse. <b style={{ color: 'var(--text-body)' }}>À partir de 1 500 FCFA / analyse.</b>
        </p>
      </div>
      <div className="lp-doc__body" style={{ paddingTop: 0 }}>
        {sent ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, padding: '24px 10px 8px' }}>
            <span style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--brand-soft)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><Icon n="check" size={28} color="var(--brand-strong)" /></span>
            <div style={{ font: 'var(--fw-bold) var(--text-lg)/1.2 var(--font-display)', color: 'var(--text-strong)' }}>Demande envoyée !</div>
            <div style={{ font: 'var(--fw-medium) var(--text-sm)/1.55 var(--font-ui)', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '40ch' }}>Notre équipe vous recontacte sous 24 h pour lancer l'analyse et organiser le paiement mobile.</div>
            <Button variant="secondary" onClick={close}>Fermer</Button>
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Input label="Nom complet" icon={<Icon n="user-round" size={17} />} placeholder="Ex. Awa Diop" required />
            <Input label="Téléphone (paiement mobile)" icon={<Icon n="phone" size={17} />} placeholder="+221 …" required />
            <Input label="Localisation de la parcelle" icon={<Icon n="map-pin" size={17} />} placeholder="Village, région ou coordonnées GPS" required />
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 150 }}><Input label="Superficie (ha)" icon={<Icon n="ruler" size={17} />} placeholder="Ex. 4,2" /></div>
              <div style={{ flex: 1, minWidth: 150, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ font: 'var(--fw-semibold) var(--text-sm)/1.2 var(--font-ui)', color: 'var(--text-body)' }}>Culture</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, height: 46, padding: '0 14px', background: 'var(--surface-card)', border: '1.5px solid var(--border-default)', borderRadius: 'var(--radius-md)' }}>
                  <Icon n="sprout" size={17} style={{ color: 'var(--text-subtle)' }} />
                  <select value={crop} onChange={(e) => setCrop(e.target.value)} style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', font: 'var(--fw-medium) var(--text-base)/1.2 var(--font-ui)', color: 'var(--text-strong)' }}>
                    <option value="" disabled>Choisir…</option>
                    {['Mil', 'Sorgho', 'Arachide', 'Niébé', 'Riz', 'Maïs', 'Manioc', 'Coton', 'Sésame', 'Oignon', 'Autre'].map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <Button variant="primary" size="lg" fullWidth iconRight={<Icon n="arrow-right" size={18} color="#fff" />} type="submit">Envoyer ma demande d'analyse</Button>
            <p style={{ font: 'var(--fw-medium) var(--text-xs)/1.5 var(--font-ui)', color: 'var(--text-subtle)', textAlign: 'center', marginTop: 2 }}>Sans paiement immédiat — nous vous contactons pour confirmer.</p>
          </form>
        )}
      </div>
    </div>
  );
}

window.AuthLegalModals = AuthLegalModals;
