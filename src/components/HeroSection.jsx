import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { useRef } from 'react';
import { useReducedMotion } from '../contexts/MotionPrefsContext';
import profilePhoto from '../assets/portfolioimage.jpeg';

const COMMANDS = [
  ['whoami', 'Akash, backend-first full-stack dev'],
  ['current_stack', 'Django / React / MySQL / Redis / AWS'],
  ['latest_obsession', 'making payment flows boring in the best way'],
];

const HeroSection = () => {
  const ref = useRef(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });
  const titleY = useSpring(useTransform(scrollYProgress, [0, 1], [0, reduced ? 0 : 130]), { stiffness: 80, damping: 20 });
  const photoY = useSpring(useTransform(scrollYProgress, [0, 1], [0, reduced ? 0 : -80]), { stiffness: 80, damping: 20 });

  return (
    <section ref={ref} className="relative min-h-screen overflow-hidden pt-24">
      <div className="container relative z-10 mx-auto max-w-6xl px-6">
        <div className="grid min-h-[calc(100vh-6rem)] grid-cols-1 items-center gap-10 lg:grid-cols-[1.2fr_0.8fr]">
          <motion.div style={{ y: titleY }} className="relative">
            <div className="mb-8 inline-block rotate-[-2deg] border border-accent-dark bg-accent-purple px-4 py-2 text-xs font-black uppercase tracking-[0.28em] shadow-[5px_5px_0_#151512]">
              available, caffeinated, debugging
            </div>

            <h1 className="max-w-4xl text-6xl font-extralight leading-[0.88] tracking-tight text-accent-dark md:text-8xl lg:text-9xl">
              I build
              <br />
              <span className="font-black">the parts</span>
              <br />
              users never
              <br />
              <span className="font-black">thank.</span>
            </h1>

            <p className="mt-8 max-w-2xl text-lg leading-relaxed text-accent-gray md:text-xl">
              I am Akash. I like Django, React, Redis, payment webhooks, query counts, and the quiet joy of making a checkout flow stop doing weird things at the worst possible time.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-3">
              <a href="#projects" className="interactive hover-scrape border border-accent-dark bg-accent-dark px-6 py-3 text-sm font-black uppercase tracking-widest text-primary-dark">
                show me the hard part
              </a>
              <button
                type="button"
                onClick={() => window.dispatchEvent(new CustomEvent('open-ai-akash'))}
                className="interactive hover-scrape border border-accent-dark bg-primary-dark px-6 py-3 text-sm font-black uppercase tracking-widest text-accent-dark"
              >
                ask the small robot
              </button>
              <a href="/AkashTomy-Resume.pdf" download className="interactive underline-grow px-2 py-3 text-sm font-black uppercase tracking-widest text-accent-dark">
                steal my resume
              </a>
            </div>
          </motion.div>

          <motion.div style={{ y: photoY }} className="relative lg:translate-y-16">
            <div className="hard-panel rotate-[2deg] p-4">
              <img
                src={profilePhoto}
                alt="Akash Tomy"
                className="aspect-[4/5] w-full object-cover grayscale contrast-110 transition duration-500 hover:grayscale-0"
              />
              <div className="mt-4 border-t border-accent-dark/20 pt-4 font-mono text-xs leading-relaxed text-accent-gray">
                {COMMANDS.map(([command, output]) => (
                  <div key={command} className="mb-2">
                    <span className="text-accent-dark">$ {command}</span>
                    <br />
                    <span>{output}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="absolute -bottom-6 -left-6 rotate-[-5deg] border border-accent-dark bg-accent-purple px-4 py-3 text-xs font-black uppercase tracking-widest shadow-[6px_6px_0_#151512]">
              42% fewer queries
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
