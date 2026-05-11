import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { DatabaseIcon, LinkIcon, CloudIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const NOTES = [
  {
    title: 'Why pure LLM scoring is unreliable',
    Icon: LinkIcon,
    premise: 'A model can sound confident while missing failing tests, weak coverage, or dependency CVEs.',
    systemChoice: 'AI Judge starts with deterministic metrics, then asks the model to interpret code with those facts injected into the prompt.',
    takeaway: 'The AI layer becomes an interpreter of evidence, not the only judge in the room.',
  },
  {
    title: 'Designing token-aware repo ingestion',
    Icon: DatabaseIcon,
    premise: 'A large repo can contain thousands of files, generated output, lockfiles, builds, and unrelated packages.',
    systemChoice: 'The ingestion plan ranks files by usefulness, filters noise, chunks large files, and caps the snapshot around 15k tokens.',
    takeaway: 'The system controls cost and context quality before the model ever sees the repo.',
  },
  {
    title: 'Scaling evaluations without blocking HTTP',
    Icon: CloudIcon,
    premise: 'Repository analysis can take too long for a normal request/response cycle, especially in batch mode.',
    systemChoice: 'FastAPI accepts the job, Celery workers process repo analysis, Redis coordinates queues/cache, and SSE streams progress.',
    takeaway: 'The UI feels live while the backend handles slow, failure-prone work asynchronously.',
  },
];

const EngineeringNotesSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="notes" className="relative z-10 py-24">
      <div className="container mx-auto max-w-6xl px-6">
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
            className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl"
          >
            Technical notes I should probably <span className="font-black">write fully.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.2 }}
            className="mt-5 max-w-2xl text-lg leading-relaxed text-accent-gray"
          >
            These are not blog posts yet, but they show where my thinking is going: reliability, cost control, queues, and making AI output more auditable.
          </motion.p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {NOTES.map(({ title, Icon, premise, systemChoice, takeaway }, index) => (
            <motion.article
              key={title}
              initial={{ opacity: 0, y: reduced ? 0 : 28 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: reduced ? 0 : 0.55, delay: reduced ? 0 : 0.08 * index }}
              className="hard-panel bg-primary-dark p-6"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center border border-accent-dark bg-accent-purple text-accent-dark">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-black tracking-tight text-accent-dark">{title}</h3>
              </div>

              <div className="mt-6 space-y-3">
                <div className="border border-accent-dark/15 p-4">
                  <div className="text-[10px] font-black uppercase tracking-widest text-accent-gray">Premise</div>
                  <p className="mt-1 text-sm font-medium leading-relaxed text-accent-gray">{premise}</p>
                </div>
                <div className="border border-accent-dark/15 bg-accent-purple p-4">
                  <div className="text-[10px] font-black uppercase tracking-widest text-accent-dark/60">System choice</div>
                  <p className="mt-1 text-sm font-bold leading-relaxed text-accent-dark">{systemChoice}</p>
                </div>
              </div>

              <p className="mt-5 text-sm leading-relaxed text-accent-gray">{takeaway}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default EngineeringNotesSection;
