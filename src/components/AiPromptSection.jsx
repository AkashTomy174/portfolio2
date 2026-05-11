import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { BotIcon, MessageSquareIcon } from './Icons';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const PROMPTS = [
  'What broke while building EasyBuy?',
  'Explain the payment locking in plain English.',
  'What would Akash improve next?',
  'Is he better for backend or frontend work?',
];

const AiPromptSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  const openChat = () => window.dispatchEvent(new CustomEvent('open-ai-akash'));

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
                I gave the site a <span className="font-black text-accent-purple">tiny backend brain.</span>
              </h2>
              <p className="mt-5 max-w-xl text-base leading-relaxed text-primary-dark/70">
                AI Akash is not here to be cute. It is a FastAPI endpoint with a small knowledge base so a reviewer can ask about my work instead of hunting for the right paragraph.
              </p>
              <button
                type="button"
                onClick={openChat}
                className="interactive mt-8 inline-flex items-center gap-3 border border-accent-purple bg-accent-purple px-6 py-3 text-sm font-black uppercase tracking-widest text-accent-dark shadow-[6px_6px_0_#f4f1e8] transition hover:-translate-y-1"
              >
                <MessageSquareIcon className="h-4 w-4" aria-hidden="true" />
                wake it up
              </button>
            </div>

            <div className="border border-primary-dark/20 bg-black/30 p-5 font-mono text-xs leading-relaxed">
              <div className="text-accent-purple"># sample conversation</div>
              <div className="mt-3 text-primary-dark">$ ask "why should I trust your backend work?"</div>
              <div className="mt-3 text-primary-dark/65">
                Because I can point to actual decisions: row locks for payment updates, HMAC webhook verification, query reduction from 36 to 21, Celery for async notifications, and AWS deployment instead of screenshots only.
              </div>

              <div className="mt-6 grid gap-2">
                {PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={openChat}
                    className="interactive border border-primary-dark/20 px-3 py-2 text-left text-primary-dark/80 transition hover:border-accent-purple hover:bg-accent-purple hover:text-accent-dark"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="mt-4 text-primary-dark/40">psst: this panel is draggable.</div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default AiPromptSection;
