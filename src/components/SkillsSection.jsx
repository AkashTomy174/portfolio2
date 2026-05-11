import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { skillsData } from '../data/skills';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const SkillsSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="skills" className="relative z-10 py-24">
      <div className="container mx-auto max-w-6xl px-6">
        <div ref={ref} className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr]">
          <div className="lg:sticky lg:top-28 lg:self-start">
            <div className="section-line" aria-hidden="true" />
            <h2 className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-7xl">
              Stuff I actually <span className="font-black">use.</span>
            </h2>
            <p className="mt-5 text-base leading-relaxed text-accent-gray">
              No progress bars. I am not “92% Django.” These are the tools and habits I reach for when the app needs to behave.
            </p>
          </div>

          <div className="space-y-3">
            {skillsData.map((item, index) => (
              <motion.div
                key={item.category}
                initial={{ opacity: 0, x: reduced ? 0 : 36 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: reduced ? 0 : 0.45, delay: reduced ? 0 : index * 0.06 }}
                className="group border-b border-accent-dark/15 py-5 transition hover:translate-x-2"
              >
                <div className="grid gap-3 md:grid-cols-[12rem_1fr]">
                  <h3 className="text-xl font-black text-accent-dark group-hover:bg-accent-purple">{item.category}</h3>
                  <div>
                    <p className="text-sm leading-relaxed text-accent-gray">{item.summary}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.proof.map((skill) => (
                        <span key={skill} className="border border-accent-dark/20 bg-primary-dark px-2.5 py-1 font-mono text-[11px] font-bold text-accent-dark">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default SkillsSection;
