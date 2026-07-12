import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { BotIcon, MessageSquareIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const PROMPTS = [
  'What is AI Project Judge and why is it interesting?',
  'How does the repo ingestion and token budget work?',
  'Why mix static analysis with AI scoring?',
  'How would Celery and Redis handle evaluations?',
  'What should Akash improve in the AI backend?',
  'Where does Akash show backend judgment?',
];

const AI_FLOW = [
  ['UI', 'React chat widget sends the recruiter question'],
  ['API', 'FastAPI validates request, rate limits, checks cache'],
  ['Retrieve', 'Curated JSON knowledge chunks are scored by keyword/topic overlap'],
  ['Prompt', 'Only retrieved context is passed into the system prompt'],
  ['Model', 'Gemini answers with a strict "do not invent" instruction'],
  ['Fallback', 'If LLM/API fails, the backend returns the best retrieved chunk'],
];

const NEXT = [
  'replace keyword scoring with real embeddings + vector search',
  'add chunk versioning so resume/project updates are traceable',
  'keep showing source citations in the UI',
  'evaluate bad answers with a small regression prompt set',
];

const AiPromptSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  const openChat = (prompt) => window.dispatchEvent(new CustomEvent('open-ai-akash', { detail: { prompt } }));

  return (
    <section id="ai-akash" className="relative z-10 py-24">
      <div className="container mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          drag
          dragConstraints={{ top: -10, left: -10, right: 10, bottom: 10 }}
          dragElastic={0.08}
          initial={{ opacity: 0, rotate: reduced ? 0 : 1.5, y: reduced ? 0 : 44 }}
          animate={inView ? { opacity: 1, rotate: 1, y: 0 } : {}}
          transition={{ duration: reduced ? 0 : 0.75, ease: [0.16, 1, 0.3, 1] }}
          className="hard-panel terminal-scan bg-accent-dark p-6 text-primary-dark md:p-10"
        >
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <div>
              <div className="inline-flex h-12 w-12 items-center justify-center border border-accent-purple bg-accent-purple text-accent-dark">
                <BotIcon className="h-6 w-6" aria-hidden="true" />
              </div>
              <h2 className="mt-6 text-4xl font-extralight leading-tight tracking-tight md:text-6xl">
                The chatbot is a backend feature, <span className="font-black text-accent-purple">not a sticker.</span>
              </h2>
              <p className="mt-5 max-w-xl text-base leading-relaxed text-primary-dark/70">
                I am being honest about the implementation: today it is FastAPI, cached responses, rate limiting, curated knowledge chunks, retrieval, and a guarded Gemini prompt. It is not pretending to be a full vector-memory system yet.
              </p>
              <button
                type="button"
                onClick={() => openChat()}
                className="interactive mt-8 inline-flex items-center gap-3 border border-accent-purple bg-accent-purple px-6 py-3 text-sm font-black uppercase tracking-widest text-accent-dark shadow-[6px_6px_0_#f4f1e8] transition hover:-translate-y-1"
              >
                <MessageSquareIcon className="h-4 w-4" aria-hidden="true" />
                test the assistant
              </button>
            </div>

            <div className="space-y-5">
              <div className="border border-primary-dark/20 bg-black/30 p-5 font-mono text-xs leading-relaxed">
                <div className="text-accent-purple"># current request path</div>
                <div className="mt-4 grid gap-2">
                  {AI_FLOW.map(([label, text], index) => (
                    <div key={label} className="grid grid-cols-[5rem_1fr] gap-3 border-b border-primary-dark/10 pb-2">
                      <div className="text-accent-purple">{String(index + 1).padStart(2, '0')} {label}</div>
                      <div className="text-primary-dark/72">{text}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="border border-primary-dark/20 bg-black/30 p-5 font-mono text-xs leading-relaxed">
                  <div className="text-accent-purple"># ask it this</div>
                  <div className="mt-3 grid gap-2">
                    {PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => openChat(prompt)}
                        className="interactive border border-primary-dark/20 px-3 py-2 text-left text-primary-dark/80 transition hover:border-accent-purple hover:bg-accent-purple hover:text-accent-dark"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border border-primary-dark/20 bg-black/30 p-5 font-mono text-xs leading-relaxed">
                  <div className="text-accent-purple"># next version</div>
                  <ul className="mt-3 space-y-2 text-primary-dark/72">
                    {NEXT.map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                  <div className="mt-4 text-primary-dark/70">psst: this panel is draggable.</div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default AiPromptSection;
