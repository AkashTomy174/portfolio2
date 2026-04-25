import { motion, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { MailIcon, LinkedinIcon, GithubIcon, MessageSquareIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';
import { SITE } from '../siteConfig';

const SOCIALS = [
  { href: SITE.linkedin, Icon: LinkedinIcon, label: 'LinkedIn', hover: 'hover:border-blue-400 hover:text-blue-500' },
  { href: SITE.github, Icon: GithubIcon, label: 'GitHub', hover: 'hover:border-violet-400 hover:text-violet-600' },
];

const ContactSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(SITE.email);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="contact" className="py-32 relative z-10">
      <div className="container mx-auto px-6 max-w-4xl text-center">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: reduced ? 0 : 60 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="glass-card-elevated rounded-3xl p-12 md:p-20 relative overflow-hidden"
        >
          <div className="absolute top-[-30%] left-[-20%] w-3/4 h-3/4 bg-violet-100/50 blur-3xl rounded-full pointer-events-none" aria-hidden="true" />
          <div className="absolute bottom-[-30%] right-[-20%] w-2/3 h-2/3 bg-blue-100/40 blur-3xl rounded-full pointer-events-none" aria-hidden="true" />

          <div className="relative z-10">
            <div className="section-line mx-auto mb-6" aria-hidden="true" />

            <h2 className="text-4xl md:text-6xl font-black text-accent-dark mb-5 tracking-tight leading-tight">
              Open to Work
              <br />
              <span className="text-gradient">Let's Talk</span>
            </h2>

            <p className="text-accent-gray text-lg max-w-xl mx-auto mb-4 leading-relaxed">
              I'm actively looking for full-time roles in backend or full-stack development.
            </p>
            <p className="text-accent-gray/70 text-sm max-w-md mx-auto mb-12">
              Django · React · AWS · Open to remote or on-site in India
            </p>

            {/* Primary CTA — mailto opens default email client */}
            <motion.a
              href={`mailto:${SITE.email}?subject=Hiring Inquiry&body=Hi Akash,`}
              whileHover={reduced ? {} : { scale: 1.04, y: -3 }}
              whileTap={reduced ? {} : { scale: 0.97 }}
              className="interactive inline-flex items-center gap-3 px-10 py-5 rounded-full bg-accent-dark text-white font-bold text-base tracking-wide shadow-[0_8px_32px_rgba(17,17,17,0.2)] hover:shadow-[0_12px_40px_rgba(109,40,217,0.3)] hover:bg-gradient-to-r hover:from-accent-purple hover:to-accent-blue transition-all duration-300 mb-4"
            >
              <MessageSquareIcon className="w-5 h-5" aria-hidden="true" />
              Email Me
            </motion.a>

            {/* Fallback — copy email */}
            <div className="mb-10">
              <button
                onClick={handleCopy}
                className="interactive inline-flex items-center gap-2 text-xs font-medium text-accent-gray hover:text-accent-dark transition-colors"
                aria-label="Copy email address"
              >
                <MailIcon className="w-3.5 h-3.5" aria-hidden="true" />
                {copied ? '✓ Copied!' : `Copy email — ${SITE.email}`}
              </button>
            </div>

            <div className="flex justify-center items-center gap-4">
              {SOCIALS.map(({ href, Icon, label, hover }) => (
                <motion.a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={reduced ? {} : { y: -3 }}
                  className={`interactive p-4 rounded-full bg-white border border-black/8 text-accent-gray transition-all duration-200 ${hover}`}
                  aria-label={label}
                >
                  <Icon className="w-5 h-5" aria-hidden="true" />
                </motion.a>
              ))}
            </div>
          </div>
        </motion.div>

        <div className="mt-14 text-accent-gray/50 text-xs font-medium tracking-widest uppercase">
          © {new Date().getFullYear()} {SITE.name} · Designed & Built with React & Tailwind
        </div>
      </div>
    </section>
  );
};

export default ContactSection;
