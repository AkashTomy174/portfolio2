import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { DatabaseIcon, LinkIcon, CloudIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const NOTES = [
  {
    title: 'Query Reduction Log',
    Icon: DatabaseIcon,
    before: '36 repeated reads in a product/order-heavy flow',
    after: '21 queries after caching and ORM planning',
    lesson: 'I do not treat optimization as a vibe. I compare the before and after, then keep the change if it improves the path that users actually touch.',
  },
  {
    title: 'Payment Consistency Log',
    Icon: LinkIcon,
    before: 'Payment callbacks can arrive twice or be retried',
    after: 'Order mutation guarded by transaction + row lock',
    lesson: 'In payment systems, a success response is not enough. The backend needs a deterministic state transition that survives retries and timing issues.',
  },
  {
    title: 'Deployment Reality Log',
    Icon: CloudIcon,
    before: 'Local app behavior is not production behavior',
    after: 'EC2, Gunicorn, Nginx, RDS, S3, GitHub Actions',
    lesson: 'I like building with the deployment target in mind early, because infrastructure decisions shape file storage, environment config, CORS, SSL, and background jobs.',
  },
];

const EngineeringNotesSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="notes" className="py-24 relative z-10">
      <div className="container mx-auto px-6 max-w-6xl">
        <div ref={ref} className="mb-14">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={inView ? { scaleX: 1 } : {}}
            transition={{ duration: reduced ? 0 : 0.7, ease: [0.16, 1, 0.3, 1] }}
            style={{ transformOrigin: 'left' }}
            className="section-line"
            aria-hidden="true"
          />
          <motion.h2
            initial={{ opacity: 0, y: reduced ? 0 : 24 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.1 }}
            className="text-4xl md:text-5xl font-black tracking-tight text-accent-dark"
          >
            Engineering <span className="text-gradient">Notes</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.2 }}
            className="mt-3 max-w-2xl text-lg leading-relaxed text-accent-gray"
          >
            A few short notes that show how I think about backend work when the site visitor does not have time to read the full codebase.
          </motion.p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {NOTES.map(({ title, Icon, before, after, lesson }, index) => (
            <motion.article
              key={title}
              initial={{ opacity: 0, y: reduced ? 0 : 28 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: reduced ? 0 : 0.55, delay: reduced ? 0 : 0.08 * index }}
              className="rounded-[1.5rem] border border-black/8 bg-white/80 p-6 shadow-[0_14px_46px_rgba(17,17,17,0.05)]"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-dark text-white">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-black tracking-tight text-accent-dark">{title}</h3>
              </div>

              <div className="mt-6 space-y-3">
                <div className="rounded-2xl border border-rose-100 bg-rose-50/60 p-4">
                  <div className="text-[10px] font-black uppercase tracking-widest text-rose-600">Before</div>
                  <p className="mt-1 text-sm font-medium leading-relaxed text-accent-gray">{before}</p>
                </div>
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
                  <div className="text-[10px] font-black uppercase tracking-widest text-emerald-700">After</div>
                  <p className="mt-1 text-sm font-medium leading-relaxed text-accent-gray">{after}</p>
                </div>
              </div>

              <p className="mt-5 text-sm leading-relaxed text-accent-gray">{lesson}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default EngineeringNotesSection;
