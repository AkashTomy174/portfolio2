import { useEffect, useRef, useState, Component, lazy, Suspense } from 'react';
import { MotionPrefsContext } from './contexts/MotionPrefsContext';
import CustomCursor from './components/CustomCursor';
import AnimatedBackground from './components/AnimatedBackground';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';
import AiChatWidget from './components/AiChatWidget';
import NotFoundPage from './components/NotFoundPage';

const AboutSection = lazy(() => import('./components/AboutSection'));
const NowSection = lazy(() => import('./components/NowSection'));
const SystemArchitectureSection = lazy(() => import('./components/SystemArchitectureSection'));
const RecruiterFitSection = lazy(() => import('./components/RecruiterFitSection'));
const SkillsSection = lazy(() => import('./components/SkillsSection'));
const ProjectsSection = lazy(() => import('./components/ProjectsSection'));
const EngineeringNotesSection = lazy(() => import('./components/EngineeringNotesSection'));
const AiPromptSection = lazy(() => import('./components/AiPromptSection'));
const ContactSection = lazy(() => import('./components/ContactSection'));

const KONAMI = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center text-accent-gray text-sm">
          Something went wrong. Please refresh the page.
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const progressRef = useRef(null);
  const konamiRef = useRef([]);
  const [booting, setBooting] = useState(true);
  const [easterEgg, setEasterEgg] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
  const isUnknownRoute = typeof window !== 'undefined' && !['/', '/index.html'].includes(window.location.pathname);

  useEffect(() => {
    console.log('Akash note: if you are reading this, ask me about the Razorpay webhook bug. That one taught me humility.');
    const timer = window.setTimeout(() => setBooting(false), prefersReducedMotion ? 200 : 1050);
    return () => window.clearTimeout(timer);
  }, [prefersReducedMotion]);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setPrefersReducedMotion(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    const onKey = (event) => {
      const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
      konamiRef.current = [...konamiRef.current, key].slice(-KONAMI.length);
      if (KONAMI.every((code, index) => code === konamiRef.current[index])) {
        setEasterEgg(true);
        window.setTimeout(() => setEasterEgg(false), 4200);
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const el = progressRef.current;
          if (!el) return;
          const scrolled = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
          el.style.transform = `scaleX(${Math.min(scrolled, 1)})`;
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <MotionPrefsContext.Provider value={prefersReducedMotion}>
      <div className="relative w-full min-h-screen overflow-x-hidden">
        {booting && (
          <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-accent-dark text-primary-dark">
            <div className="terminal-scan border border-accent-purple px-8 py-6 text-center">
              <div className="text-[10px] font-black uppercase tracking-[0.45em] text-accent-purple">booting portfolio</div>
              <div className="mt-4 text-4xl font-black tracking-tight" style={{ animation: 'stamp-in 720ms cubic-bezier(0.16,1,0.3,1) both' }}>
                AKASH.TOMY
              </div>
              <div className="mt-3 font-mono text-xs text-primary-dark/60">loading the unglamorous backend bits...</div>
            </div>
          </div>
        )}
        {easterEgg && (
          <div className="fixed bottom-24 left-1/2 z-[9999] -translate-x-1/2 rotate-[-2deg] border border-accent-dark bg-accent-purple px-5 py-3 text-sm font-black text-accent-dark shadow-[8px_8px_0_#151512]">
            You found the secret. Payment webhooks still scare me, respectfully.
          </div>
        )}
        <div id="scroll-progress" ref={progressRef} aria-hidden="true" />
        <CustomCursor />
        <AnimatedBackground />
        <div className="noise-overlay" aria-hidden="true" />
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-accent-dark focus:text-white focus:text-sm focus:font-semibold">
          Skip to content
        </a>
        <NavBar />
        <ErrorBoundary>
          {isUnknownRoute ? (
            <NotFoundPage />
          ) : (
            <>
              <main id="main" className="flex flex-col relative z-10">
                <HeroSection />
                <Suspense fallback={null}>
                  <SystemArchitectureSection />
                  <ProjectsSection />
                  <EngineeringNotesSection />
                  <NowSection />
                  <AboutSection />
                  <RecruiterFitSection />
                  <SkillsSection />
                  <AiPromptSection />
                  <ContactSection />
                </Suspense>
              </main>
              <AiChatWidget />
            </>
          )}
        </ErrorBoundary>
      </div>
    </MotionPrefsContext.Provider>
  );
}

export default App;
