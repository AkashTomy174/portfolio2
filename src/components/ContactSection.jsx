import { motion, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { MailIcon, LinkedinIcon, GithubIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';
import { SITE } from '../siteConfig';

const SOCIALS = [
  { href: SITE.linkedin, Icon: LinkedinIcon, label: 'LinkedIn' },
  { href: SITE.github, Icon: GithubIcon, label: 'GitHub' },
];

const EMAIL_LINK = `mailto:${SITE.email}?subject=${encodeURIComponent('Backend / Full-stack role')}&body=${encodeURIComponent('Hi Akash,\n\nI saw your portfolio and wanted to talk about ')}`;

const copyText = async (text) => {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return true;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();

  try {
    return document.execCommand('copy');
  } finally {
    document.body.removeChild(textarea);
  }
};

const ContactSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();
  const [copyStatus, setCopyStatus] = useState('idle');
  const [clicks, setClicks] = useState(0);

  const handleCopy = async () => {
    try {
      const didCopy = await copyText(SITE.email);
      setCopyStatus(didCopy ? 'copied' : 'failed');
      setTimeout(() => setCopyStatus('idle'), 2500);
    } catch {
      setCopyStatus('failed');
      setTimeout(() => setCopyStatus('idle'), 2500);
    }
  };

  return (
    <section id="contact" className="relative z-10 py-32">
      <div className="container mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: reduced ? 0 : 50 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="grid gap-10 border-t border-accent-dark pt-12 lg:grid-cols-[1.15fr_0.85fr]"
        >
          <div>
            <h2 className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl">
              Send the email.
              <br />
              <span className="font-black">I will read it.</span>
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-accent-gray">
              If you have a backend/full-stack role, a Django problem, or a suspiciously slow page, I am interested. If your message starts with “quick call?”, I will still be brave.
            </p>
          </div>

          <div className="hard-panel rotate-[1deg] bg-primary-dark p-6">
            <a
              href={EMAIL_LINK}
              onClick={() => setClicks((value) => value + 1)}
              className="interactive hover-scrape flex items-center justify-center gap-3 border border-accent-dark bg-accent-dark px-6 py-4 text-sm font-black uppercase tracking-widest text-primary-dark"
            >
              <MailIcon className="h-4 w-4" aria-hidden="true" />
              write to me
            </a>

            <button
              type="button"
              onClick={handleCopy}
              className="interactive mt-4 w-full border border-accent-dark/20 px-4 py-3 text-left font-mono text-xs font-bold text-accent-gray transition hover:bg-accent-purple hover:text-accent-dark"
              aria-live="polite"
            >
              {copyStatus === 'copied' ? 'copied. tiny victory.' : copyStatus === 'failed' ? SITE.email : `copy email: ${SITE.email}`}
            </button>

            <div className="mt-5 flex gap-3">
              {SOCIALS.map(({ href, Icon, label }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="interactive hover-scrape flex h-12 w-12 items-center justify-center border border-accent-dark bg-primary-dark text-accent-dark"
                  aria-label={label}
                  title={`${label}, but make it useful`}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </a>
              ))}
            </div>

            <div className="mt-6 border-t border-accent-dark/20 pt-4 font-mono text-xs text-accent-gray">
              email button clicked: {clicks}
              <br />
              footer confession: I overthink button labels.
            </div>
          </div>
        </motion.div>

        <footer className="mt-16 flex flex-col gap-3 border-t border-accent-dark/20 pt-6 font-mono text-xs font-bold uppercase tracking-widest text-accent-gray md:flex-row md:items-center md:justify-between">
          <span>{new Date().getFullYear()} / {SITE.name} / built by hand, then argued with</span>
          <span>konami code works because why not</span>
        </footer>
      </div>
    </section>
  );
};

export default ContactSection;
