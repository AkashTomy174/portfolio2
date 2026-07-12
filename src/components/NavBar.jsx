import { useState, useEffect } from 'react';
import { SITE } from '../siteConfig';

const NAV_LINKS = [
  { label: 'Architecture', href: '#architecture' },
  { label: 'Projects', href: '#projects' },
  { label: 'Notes', href: '#notes' },
  { label: 'Now', href: '#now' },
  { label: 'About', href: '#about' },
  { label: 'Contact', href: '#contact' },
];

const NAV_OFFSET = 80;

const NavBar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);

  const scrollToSection = (href, attempt = 0) => {
    const target = document.querySelector(href);

    if (!target) {
      if (attempt < 5) {
        window.setTimeout(() => scrollToSection(href, attempt + 1), 100);
      } else {
        window.history.replaceState(null, '', href);
      }
      return;
    }

    const top = target.getBoundingClientRect().top + window.scrollY - NAV_OFFSET;

    window.scrollTo({
      top: Math.max(top, 0),
      behavior: 'smooth',
    });
  };

  const handleNavClick = (e, href) => {
    e.preventDefault();
    setMenuOpen(false);
    setActive(href);
    window.history.pushState(null, '', href);
    window.setTimeout(() => scrollToSection(href), 50);
  };

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    let sectionObserver;
    let mutationObserver;
    let observedSectionIds = '';

    const observeSections = () => {
      const sections = NAV_LINKS.map(({ href }) => document.querySelector(href)).filter(Boolean);
      const nextObservedSectionIds = sections.map((section) => section.id).join(',');
      if (nextObservedSectionIds === observedSectionIds) return;

      observedSectionIds = nextObservedSectionIds;
      sectionObserver?.disconnect();

      if (sections.length === 0) return;

      sectionObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) setActive(`#${entry.target.id}`);
          });
        },
        { threshold: 0.6 }
      );
      sections.forEach((s) => sectionObserver.observe(s));
    };

    observeSections();

    mutationObserver = new MutationObserver(observeSections);
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      sectionObserver?.disconnect();
      mutationObserver?.disconnect();
    };
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
          {SITE.initials}<span className="text-accent-purple">_</span>
        </a>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ label, href }) => (
            <li key={href}>
              <a
                href={href}
                onClick={(e) => handleNavClick(e, href)}
                aria-current={active === href ? 'page' : undefined}
                className={`interactive relative px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 ${
                  active === href
                    ? 'text-accent-dark'
                    : 'text-accent-gray hover:text-accent-dark'
                }`}
              >
                {label}
                {active === href && (
                  <span className="absolute inset-0 border border-accent-dark bg-accent-purple -z-10" />
                )}
              </a>
            </li>
          ))}
        </ul>

        {/* CTA */}
        <a
          href={`mailto:${SITE.email}`}
          className="interactive hidden md:inline-flex items-center gap-2 px-5 py-2 rounded-full bg-accent-dark text-primary-dark text-sm font-semibold transition-colors duration-200 hover:bg-accent-purple hover:text-accent-dark"
        >
          email me
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
      {menuOpen && (
        <div
          id="mobile-menu"
          className="glass-card-elevated overflow-hidden border-t border-black/5 md:hidden"
        >
          <ul className="flex flex-col gap-1 px-6 py-4">
            {NAV_LINKS.map(({ label, href }) => (
              <li key={href}>
                <a
                  href={href}
                  onClick={(e) => handleNavClick(e, href)}
                  aria-current={active === href ? 'page' : undefined}
                  className={`interactive block rounded-xl px-4 py-3 text-sm font-medium transition-colors ${
                    active === href
                      ? 'bg-accent-purple text-accent-dark'
                      : 'text-accent-gray hover:bg-black/4 hover:text-accent-dark'
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
                className="interactive block rounded-xl bg-accent-dark px-4 py-3 text-center text-sm font-semibold text-primary-dark"
              >
                email me
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
};

export default NavBar;
