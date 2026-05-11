import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const FIT_POINTS = [
  ['If you need Django APIs', 'I have shipped real auth, order, seller, admin, payment, and webhook flows.'],
  ['If your app is slow', 'I will count queries before making guesses. EasyBuy went from 36 to 21 in one optimized path.'],
  ['If payments matter', 'I care about locks, signatures, retries, and not celebrating success too early.'],
  ['If you want someone junior but serious', 'I ask why, read the boring docs, and try not to hide behind buzzwords.'],
];

const RecruiterFitSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="fit" className="relative z-10 py-16">
      <div className="container mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: reduced ? 0 : 36 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.65, ease: [0.16, 1, 0.3, 1] }}
          className="relative border-y border-accent-dark py-10"
        >
          <div className="absolute -left-3 -top-4 rotate-[-6deg] bg-accent-purple px-3 py-1 font-mono text-xs font-black uppercase tracking-widest text-accent-dark">
            recruiter shortcut
          </div>
          <div className="grid gap-8 lg:grid-cols-[0.7fr_1.3fr]">
            <div>
              <h2 className="text-4xl font-extralight leading-none tracking-tight text-accent-dark md:text-6xl">
                Hire me for <span className="font-black">the backend bits.</span>
              </h2>
            </div>

            <div className="space-y-4">
              {FIT_POINTS.map(([label, text], index) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, x: reduced ? 0 : 24 }}
                  animate={inView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: reduced ? 0 : 0.45, delay: reduced ? 0 : index * 0.07 }}
                  className="grid gap-2 border-b border-accent-dark/15 pb-4 md:grid-cols-[13rem_1fr]"
                >
                  <div className="text-sm font-black text-accent-dark">{label}</div>
                  <div className="text-sm leading-relaxed text-accent-gray">{text}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default RecruiterFitSection;
