import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { aboutStats } from '../data/about';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const AboutSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="about" className="relative z-10 py-24">
      <div className="container mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: reduced ? 0 : 40 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.75, ease: [0.16, 1, 0.3, 1] }}
          className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]"
        >
          <div className="hard-panel bg-primary-dark p-6 md:p-10">
            <div className="section-line" aria-hidden="true" />
            <h2 className="text-4xl font-extralight leading-tight tracking-tight text-accent-dark md:text-6xl">
              I like when software is <span className="font-black">boring for users</span> and interesting for me.
            </h2>
            <p className="mt-7 text-lg leading-relaxed text-accent-gray">
              I am from Alappuzha, Kerala. I mostly work with Django, React, MySQL, Redis, and AWS. The part I enjoy is not just making the page render. It is figuring out why a checkout can fail twice, why a page did 36 queries, or why a background job should not block a customer.
            </p>
            <p className="mt-5 text-lg leading-relaxed text-accent-gray">
              Weirdly specific opinion: skill bars should be banned from developer portfolios. Nobody is 87% Redis. Show me the bug, the tradeoff, and what changed after you touched it.
            </p>
          </div>

          <div className="space-y-4 lg:pt-16">
            {aboutStats.map(({ num, label }, index) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, x: reduced ? 0 : 36 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: reduced ? 0 : 0.5, delay: reduced ? 0 : 0.15 + index * 0.08 }}
                className={`hard-panel bg-primary-dark p-5 ${index === 1 ? 'md:ml-12 rotate-[1deg]' : index === 2 ? 'md:mr-10 rotate-[-1deg]' : 'rotate-[-0.5deg]'}`}
              >
                <div className="text-5xl font-black text-accent-dark">{num}</div>
                <div className="mt-2 font-mono text-xs font-black uppercase tracking-widest text-accent-gray">{label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default AboutSection;
