import { useState, useEffect } from 'react';
import { SITE } from '../siteConfig';
import { motion, AnimatePresence } from 'framer-motion';

const NAV_LINKS = [
  { label: 'About', href: '#about' },
  { label: 'Skills', href: '#skills' },
  { label: 'Projects', href: '#projects' },
  { label: 'Contact', href: '#contact' },
];

const NavBar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);

  const scrollToSection = (href) => {
    const target = document.querySelector(href);
    setMenuOpen(false);
    setActive(href);

    if (!target) {
      window.location.hash = href;
      return;
    }

    window.history.pushState(null, '', href);
    requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const sections = NAV_LINKS.map(({ href }) => document.querySelector(href)).filter(Boolean);
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(`#${entry.target.id}`);
        });
      },
      { threshold: 0.6 }
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setMenuOpen(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 ${
        scrolled ? 'glass-card-elevated shadow-sm' : 'bg-transparent'
      }`}
    >
      <nav aria-label="Main navigation" className="container mx-auto px-6 max-w-6xl h-16 flex items-center justify-between">
        {/* Logo */}
        <a
          href="#"
          className="interactive text-sm font-black tracking-tight text-accent-dark hover:text-accent-purple transition-colors"
        >
          {SITE.initials}<span className="text-accent-purple">.</span>
        </a>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ label, href }) => (
            <li key={href}>
              <a
                href={href}
                aria-current={active === href ? 'page' : undefined}
                className={`interactive relative px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 ${
                  active === href
                    ? 'text-accent-purple'
                    : 'text-accent-gray hover:text-accent-dark'
                }`}
              >
                {label}
                {active === href && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full bg-violet-50 border border-violet-100 -z-10"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
              </a>
            </li>
          ))}
        </ul>

        {/* CTA */}
        <a
          href={`mailto:${SITE.email}`}
          className="interactive hidden md:inline-flex items-center gap-2 px-5 py-2 rounded-full bg-accent-dark text-white text-sm font-semibold hover:bg-accent-purple transition-colors duration-200"
        >
          Hire Me
        </a>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen((o) => !o)}
          className="interactive md:hidden p-2 rounded-lg text-accent-gray hover:text-accent-dark transition-colors"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
        >
          <span className="block w-5 h-px bg-current mb-1.5 transition-all" style={{ transform: menuOpen ? 'rotate(45deg) translate(2px, 2px)' : 'none' }} />
          <span className="block w-5 h-px bg-current mb-1.5 transition-all" style={{ opacity: menuOpen ? 0 : 1 }} />
          <span className="block w-5 h-px bg-current transition-all" style={{ transform: menuOpen ? 'rotate(-45deg) translate(2px, -2px)' : 'none' }} />
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            id="mobile-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="md:hidden glass-card-elevated border-t border-black/5 overflow-hidden"
          >
            <ul className="flex flex-col px-6 py-4 gap-1">
              {NAV_LINKS.map(({ label, href }) => (
                <li key={href}>
                  <a
                    href={href}
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToSection(href);
                    }}
                    aria-current={active === href ? 'page' : undefined}
                    className={`interactive block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      active === href
                        ? 'text-accent-purple bg-violet-50'
                        : 'text-accent-gray hover:text-accent-dark hover:bg-black/4'
                    }`}
                  >
                    {label}
                  </a>
                </li>
              ))}
              <li className="pt-2">
                <a
                  href={`mailto:${SITE.email}`}
                  onClick={() => setMenuOpen(false)}
                  className="interactive block text-center px-4 py-3 rounded-xl bg-accent-dark text-white text-sm font-semibold"
                >
                  Hire Me
                </a>
              </li>
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default NavBar;
