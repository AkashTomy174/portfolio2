import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const NOW_ITEMS = [
  ['building', 'a portfolio assistant that can explain my work without sounding like a sales intern'],
  ['reading', 'Django ORM docs and random postmortems about payment systems'],
  ['obsessing', 'how many database queries one page really needs before I start side-eyeing it'],
  ['trying', 'to make my UI feel less perfect and more mine'],
];

const NowSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="now" className="relative z-10 py-20">
      <div className="container mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, rotate: reduced ? 0 : -1.5, y: reduced ? 0 : 32 }}
          animate={inView ? { opacity: 1, rotate: -1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.65, ease: [0.16, 1, 0.3, 1] }}
          className="hard-panel relative max-w-4xl bg-primary-dark p-6 md:ml-16 md:p-8"
        >
          <div className="absolute -right-4 -top-4 rotate-[6deg] bg-accent-purple px-4 py-2 text-xs font-black uppercase tracking-widest text-accent-dark shadow-[5px_5px_0_#151512]">
            updated by hand
          </div>
          <div className="grid gap-8 md:grid-cols-[0.7fr_1.3fr]">
            <div>
              <div className="section-line" aria-hidden="true" />
              <h2 className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-7xl">
                now<span className="font-black">.</span>
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-accent-gray">
                This is the little shelf I update when I remember the site should feel alive.
              </p>
            </div>
            <div className="space-y-4">
              {NOW_ITEMS.map(([label, text]) => (
                <div key={label} className="grid gap-2 border-b border-accent-dark/15 pb-4 md:grid-cols-[7rem_1fr]">
                  <div className="font-mono text-xs font-black uppercase tracking-widest text-accent-dark">{label}</div>
                  <div className="text-base leading-relaxed text-accent-gray">{text}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default NowSection;
