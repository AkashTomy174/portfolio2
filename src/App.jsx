import { useEffect, useRef, useState, Component, lazy, Suspense } from 'react';
import { MotionPrefsContext } from './contexts/MotionPrefsContext';
import CustomCursor from './components/CustomCursor';
import AnimatedBackground from './components/AnimatedBackground';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';

const AboutSection = lazy(() => import('./components/AboutSection'));
const SkillsSection = lazy(() => import('./components/SkillsSection'));
const ProjectsSection = lazy(() => import('./components/ProjectsSection'));
const ContactSection = lazy(() => import('./components/ContactSection'));

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
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setPrefersReducedMotion(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
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
        <div id="scroll-progress" ref={progressRef} aria-hidden="true" />
        <CustomCursor />
        <AnimatedBackground />
        <div className="noise-overlay" aria-hidden="true" />
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-accent-dark focus:text-white focus:text-sm focus:font-semibold">
          Skip to content
        </a>
        <NavBar />
        <ErrorBoundary>
          <main id="main" className="flex flex-col relative z-10">
            <HeroSection />
            <Suspense fallback={null}>
              <AboutSection />
              <SkillsSection />
              <ProjectsSection />
              <ContactSection />
            </Suspense>
          </main>
        </ErrorBoundary>
      </div>
    </MotionPrefsContext.Provider>
  );
}

export default App;
