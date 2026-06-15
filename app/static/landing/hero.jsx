// AgroScan Landing — Section 1: composed hero banner (uploaded artwork)
function LandingHero() {
  const { Icon } = window;
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  return (
    <header className="lp-hero lp-hero--composed" id="accueil">
      <div className="lp-hero__composedwrap">
        <img className="lp-hero__composed"
          src={(window.IMG && window.IMG.hero) || "../../assets/photos/hero-composed.webp"}
          alt="AgroScan Pro — Toute votre ferme, vue du ciel et du sol. Données satellite, analyse du sol, santé des cultures, gestion de ferme et assistant IA."
          loading="eager" fetchpriority="high" />
        {/* Real clickable CTA placed precisely over the baked "Analyser ma ferme maintenant" button */}
        <a className="lp-hero__hotspot" href="#contact" aria-label="Analyser ma ferme maintenant"></a>
      </div>
      <a className="lp-hero__cue" href="#fonctionnalites" aria-label="Découvrir">
        <span>Découvrir</span>
        <Icon n="chevron-down" size={20} color="#0F5C33" />
      </a>
    </header>
  );
}
window.LandingHero = LandingHero;
