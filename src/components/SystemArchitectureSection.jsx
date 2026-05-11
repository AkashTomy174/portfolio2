import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const PIPELINE = [
  ['01', 'GitHub ingest', 'repo tree, README, commits, language detection'],
  ['02', 'Noise filter', 'drop node_modules, dist, build, binaries, lockfile noise'],
  ['03', 'Token budgeter', 'rank files and cap snapshot around 15k tokens'],
  ['04', 'Static layer', 'coverage, lint, complexity, CVEs, type checks, CI'],
  ['05', 'AI layer', 'metrics-grounded prompts per evaluation criterion'],
  ['06', 'Scorecard', 'domain-aware weights, traceable feedback, export'],
];

const JOBS = [
  ['queued', 'repo snapshot waiting for worker', 'bg-accent-purple text-accent-dark'],
  ['running', 'ruff / eslint / coverage / radon', 'bg-primary-dark text-accent-dark'],
  ['streaming', 'SSE sends partial feedback to UI', 'bg-primary-dark text-accent-dark'],
  ['cached', 'prompt + repo fingerprint reused', 'bg-primary-dark text-accent-dark'],
];

const METRICS = [
  ['15k', 'token cap'],
  ['6x', 'parallel criteria'],
  ['300', 'repo hackathon target'],
  ['~Rs 950', 'optimized batch estimate'],
];

const SystemArchitectureSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <section id="architecture" className="relative z-10 py-24">
      <div className="container mx-auto max-w-6xl px-6">
        <div ref={ref} className="grid gap-10 lg:grid-cols-[0.78fr_1.22fr]">
          <div className="lg:sticky lg:top-24 lg:self-start">
            <div className="section-line" aria-hidden="true" />
            <motion.h2
              initial={{ opacity: 0, y: reduced ? 0 : 24 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: reduced ? 0 : 0.6 }}
              className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl"
            >
              Live System <span className="font-black">Architecture</span>
            </motion.h2>
            <p className="mt-5 text-lg leading-relaxed text-accent-gray">
              The AI Judge identity needs to look like infrastructure, so this page now leads with the pipeline: ingestion, queues, deterministic metrics, AI interpretation, and traceable scorecards.
            </p>
          </div>

          <div className="space-y-5">
            <motion.div
              initial={{ opacity: 0, x: reduced ? 0 : 32 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: reduced ? 0 : 0.65, delay: reduced ? 0 : 0.1 }}
              className="hard-panel bg-primary-dark p-5"
            >
              <div className="mb-4 font-mono text-xs font-black uppercase tracking-widest text-accent-gray">evaluation pipeline</div>
              <div className="space-y-3">
                {PIPELINE.map(([step, label, body], index) => (
                  <div key={label} className="grid gap-3 md:grid-cols-[4rem_10rem_1fr]">
                    <div className="border border-accent-dark bg-accent-purple px-2 py-2 text-center font-mono text-xs font-black text-accent-dark">
                      {step}
                    </div>
                    <div className="border border-accent-dark/20 px-3 py-2 text-sm font-black text-accent-dark">
                      {label}
                    </div>
                    <div className="relative border border-accent-dark/15 px-3 py-2 text-sm text-accent-gray">
                      {body}
                      {index < PIPELINE.length - 1 && <span className="absolute -bottom-4 left-5 h-4 w-px bg-accent-dark/20" aria-hidden="true" />}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <div className="grid gap-5 lg:grid-cols-[1fr_0.8fr]">
              <motion.div
                initial={{ opacity: 0, y: reduced ? 0 : 24 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: reduced ? 0 : 0.55, delay: reduced ? 0 : 0.18 }}
                className="terminal-scan border border-accent-dark bg-accent-dark p-5 font-mono text-xs leading-relaxed text-primary-dark"
              >
                <div className="text-accent-purple">worker.log</div>
                <div className="mt-3 text-primary-dark/70">job: repo_eval_047 status=queued</div>
                <div className="text-primary-dark/70">worker: ingest language=python files=184 kept=27</div>
                <div className="text-primary-dark/70">static: coverage=23 lint=14 cves=2 complexity=high</div>
                <div className="text-primary-dark/70">ai: criterion=code_quality prompt_cache=hit</div>
                <div className="text-primary-dark/70">stream: sending feedback chunk 04/06</div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: reduced ? 0 : 24 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: reduced ? 0 : 0.55, delay: reduced ? 0 : 0.24 }}
                className="hard-panel bg-primary-dark p-5"
              >
                <div className="font-mono text-xs font-black uppercase tracking-widest text-accent-gray">queue states</div>
                <div className="mt-4 space-y-2">
                  {JOBS.map(([state, body, color]) => (
                    <div key={state} className="grid grid-cols-[6rem_1fr] border border-accent-dark/15">
                      <div className={`${color} px-3 py-2 font-mono text-xs font-black`}>{state}</div>
                      <div className="px-3 py-2 text-xs text-accent-gray">{body}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              {METRICS.map(([value, label]) => (
                <div key={label} className="border border-accent-dark bg-primary-dark p-4 shadow-[5px_5px_0_rgba(21,21,18,0.16)]">
                  <div className="text-3xl font-black text-accent-dark">{value}</div>
                  <div className="mt-1 font-mono text-[10px] font-black uppercase tracking-widest text-accent-gray">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SystemArchitectureSection;
