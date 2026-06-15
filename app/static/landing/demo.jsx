// AgroScan Landing — Section 4: product demonstration (real rendered interfaces)
function LandingDemo() {
  const { FieldMap, NDVILegend, HealthGauge, StatTile, Badge, SegmentedControl } = window.AgroScanProDesignSystem_74357e;
  const { Icon } = window;
  const [tab, setTab] = React.useState('gps');
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const TABS = [
    { id: 'gps', label: 'Cartographie GPS', icon: 'map-pinned' },
    { id: 'sat', label: 'Données satellitaires', icon: 'satellite' },
    { id: 'dash', label: 'Dashboard agricole', icon: 'layout-dashboard' },
    { id: 'ia', label: 'IA Agricole', icon: 'bot' },
  ];

  const Panel = () => {
    if (tab === 'sat') return (
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 18, alignItems: 'stretch' }}>
        <FieldMap mode="ndvi" height={300} label="Indice NDVI · 11 juin" pins={[{ x: 62, y: 28, tone: '#D9483B' }, { x: 40, y: 64, tone: '#F4D03F' }]} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: 'var(--radius-lg)', padding: 16 }}><NDVILegend min="0.12" max="0.88" /></div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1, background: '#fff', borderRadius: 'var(--radius-lg)', padding: 14, display: 'flex', justifyContent: 'center' }}><HealthGauge value={78} size={88} label="NDVI" caption="Santé" /></div>
          </div>
        </div>
      </div>
    );
    if (tab === 'dash') return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        <StatTile label="Surface suivie" value="12,4" unit="ha" tone="brand" icon={<Icon n="map" size={18} />} delta="+2 ha" deltaDir="up" />
        <StatTile label="NDVI moyen" value="0.78" tone="info" icon={<Icon n="activity" size={18} />} delta="+0.04" deltaDir="up" />
        <StatTile label="Pluie 7 j" value="18" unit="mm" tone="info" icon={<Icon n="cloud-rain" size={18} />} />
        <StatTile label="Alertes" value="2" tone="stress" icon={<Icon n="triangle-alert" size={18} />} delta="+1" deltaDir="up" />
        <div style={{ gridColumn: '1 / -1', background: '#fff', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <FieldMap mode="moisture" height={220} rounded={false} label="Humidité du sol · toutes parcelles" />
        </div>
      </div>
    );
    if (tab === 'ia') return (
      <div style={{ maxWidth: 560, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ alignSelf: 'flex-start', maxWidth: '85%', padding: '11px 14px', borderRadius: '16px 16px 16px 4px', background: '#fff', color: 'var(--text-body)', font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)' }}>Bonjour 👋 Posez une question ou envoyez une photo d'une feuille à diagnostiquer.</div>
        <div style={{ alignSelf: 'flex-end', maxWidth: '85%', padding: '11px 14px', borderRadius: '16px 16px 4px 16px', background: 'var(--brand)', color: '#fff', font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)' }}>Des taches jaunes sur mon maïs, parcelle Nord.</div>
        <div style={{ alignSelf: 'flex-start', maxWidth: '90%', padding: 14, borderRadius: '16px 16px 16px 4px', background: '#fff', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}><Badge tone="warning" solid>Confiance 86 %</Badge></div>
          <div style={{ font: 'var(--fw-bold) var(--text-base)/1.2 var(--font-display)', color: 'var(--text-strong)' }}>Carence en azote probable</div>
          <div style={{ font: 'var(--fw-medium) var(--text-sm)/1.5 var(--font-ui)', color: 'var(--text-muted)', marginTop: 6 }}>Jaunissement en « V » sur les feuilles basses. Apport d'azote de 60 kg/ha recommandé avant la pluie de mercredi.</div>
        </div>
      </div>
    );
    // gps
    return (
      <div style={{ position: 'relative' }}>
        <FieldMap mode="satellite" height={320} label="Tracé GPS · Parcelle Nord" pins={[{ x: 28, y: 30, tone: '#9BD4F5' }, { x: 70, y: 22, tone: '#9BD4F5' }, { x: 80, y: 70, tone: '#9BD4F5' }, { x: 35, y: 76, tone: '#9BD4F5' }]} />
        <div style={{ position: 'absolute', top: 16, right: 16, background: 'rgba(255,255,255,.95)', borderRadius: 'var(--radius-md)', padding: '10px 14px', boxShadow: 'var(--shadow-md)' }}>
          <div style={{ font: 'var(--fw-semibold) 11px/1 var(--font-ui)', color: 'var(--text-muted)', letterSpacing: 'var(--ls-caps)', textTransform: 'uppercase' }}>Superficie</div>
          <div className="as-num" style={{ font: 'var(--fw-bold) 24px/1 var(--font-display)', color: 'var(--text-strong)', marginTop: 4 }}>4,2 <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>ha</span></div>
          <div className="as-num" style={{ font: 'var(--fw-medium) 11px/1.3 var(--font-mono)', color: 'var(--text-subtle)', marginTop: 6 }}>14°41'N 17°27'W</div>
        </div>
      </div>
    );
  };

  return (
    <section className="lp-section lp-container">
      <div className="lp-center reveal">
        <span className="lp-eyebrow"><Icon n="monitor-play" size={14} /> Démonstration produit</span>
        <h2 className="lp-h2">De vraies interfaces, pas des maquettes</h2>
        <p className="lp-lead">Cartographie GPS, données satellitaires, tableau de bord et assistant IA — explorez l'expérience AgroScan Pro.</p>
      </div>
      <div className="lp-demo reveal" style={{ marginTop: 44, padding: 'clamp(20px, 3vw, 32px)' }}>
        <div className="lp-demo__tabs">
          {TABS.map((t) => (
            <button key={t.id} className={'lp-demo__tab' + (t.id === tab ? ' is-active' : '')} onClick={() => setTab(t.id)}>
              <Icon n={t.icon} size={16} color={t.id === tab ? 'var(--green-700)' : 'rgba(255,255,255,.8)'} /> {t.label}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 22, background: 'var(--surface-page)', borderRadius: 'var(--radius-xl)', padding: 'clamp(14px, 2vw, 22px)' }}>
          <Panel />
        </div>
      </div>
    </section>
  );
}
window.LandingDemo = LandingDemo;
