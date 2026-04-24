import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { aboutStats } from '../data/about';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const AboutSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="about" className="py-24 relative z-10">
      <div className="container mx-auto px-6 max-w-5xl">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: reduced ? 0 : 48 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="glass-card-elevated rounded-3xl p-8 md:p-14 relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-bl from-violet-100/60 to-transparent rounded-full blur-3xl pointer-events-none" aria-hidden="true" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-blue-100/40 to-transparent rounded-full blur-2xl pointer-events-none" aria-hidden="true" />

          <div className="relative z-10">
            <div className="section-line" aria-hidden="true" />
            <h2 className="text-3xl md:text-4xl font-black text-accent-dark mb-5 tracking-tight leading-tight">
              Full-Stack Developer
              <br />
              <span className="text-gradient-static">Scaling Django E-Commerce</span>
            </h2>

            <p className="text-accent-gray text-lg leading-relaxed mb-12 max-w-3xl">
              With over 5 years of backend experience, I architect and deploy robust multi-vendor marketplaces. My strength lies in bridging complex Django ecosystems—Celery, Redis caching, integrated AI services—with highly interactive React frontends. I build platforms that look premium and perform flawlessly under heavy traffic.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-8 border-t border-black/5">
              {aboutStats.map(({ num, label, accent }, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: reduced ? 0 : 24 }}
                  animate={inView ? { opacity: 1, y: 0 } : {}}
                  transition={{ duration: reduced ? 0 : 0.5, delay: reduced ? 0 : 0.3 + i * 0.1, ease: [0.16, 1, 0.3, 1] }}
                  whileHover={reduced ? {} : { y: -4 }}
                  className="p-6 rounded-2xl bg-white/60 border border-black/5 hover:border-black/10 hover:shadow-md transition-all duration-300"
                >
                  <div className={`text-4xl font-black bg-gradient-to-br ${accent} bg-clip-text text-transparent mb-1`}>
                    {num}
                  </div>
                  <div className="text-xs font-semibold text-accent-gray uppercase tracking-widest">{label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default AboutSection;
