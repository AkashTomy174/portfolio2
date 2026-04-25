import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { useRef, useState, useEffect, useCallback } from 'react';
import { useReducedMotion } from '../contexts/MotionPrefsContext';
import profilePhoto from '../assets/portfolioimage.jpeg';

const ROLES = ['Full-Stack Developer', 'Django Architect', 'React Engineer', 'E-Commerce Builder'];

const useTypewriter = (words) => {
  const [display, setDisplay] = useState('');
  const [wordIdx, setWordIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);
  // Keep words stable via ref so the effect never needs it as a dep
  const wordsRef = useRef(words);

  useEffect(() => {
    const current = wordsRef.current[wordIdx];
    const speed = 80;
    const pause = 1800;
    const delay = deleting ? speed / 2 : charIdx === current.length ? pause : speed;

    const t = setTimeout(() => {
      if (!deleting && charIdx < current.length) {
        setDisplay(current.slice(0, charIdx + 1));
        setCharIdx((c) => c + 1);
      } else if (!deleting && charIdx === current.length) {
        setDeleting(true);
      } else if (deleting && charIdx > 0) {
        setDisplay(current.slice(0, charIdx - 1));
        setCharIdx((c) => c - 1);
      } else {
        setDeleting(false);
        setWordIdx((i) => (i + 1) % wordsRef.current.length);
      }
    }, delay);

    return () => clearTimeout(t);
  }, [charIdx, deleting, wordIdx]);

  return display;
};

const HeroSection = () => {
  const ref = useRef(null);
  const role = useTypewriter(ROLES);
  const prefersReducedMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });
  const rawY = useTransform(scrollYProgress, [0, 1], [0, prefersReducedMotion ? 0 : 120]);
  const parallaxY = useSpring(rawY, { stiffness: 80, damping: 20 });
  const rawOpacity = useTransform(scrollYProgress, [0, 0.6], [1, prefersReducedMotion ? 1 : 0]);
  const fadeOut = useSpring(rawOpacity, { stiffness: 80, damping: 20 });
  const imgRawY = useTransform(scrollYProgress, [0, 1], [0, prefersReducedMotion ? 0 : -60]);
  const imgY = useSpring(imgRawY, { stiffness: 80, damping: 20 });

  const dur = useCallback((ms) => (prefersReducedMotion ? 0 : ms), [prefersReducedMotion]);

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: prefersReducedMotion ? 0 : 0.12, delayChildren: prefersReducedMotion ? 0 : 0.2 } },
  };
  const item = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 40 },
    show: { opacity: 1, y: 0, transition: { duration: dur(0.7), ease: [0.16, 1, 0.3, 1] } },
  };

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      <div className="container mx-auto px-6 max-w-6xl relative z-10">
        <div className="flex flex-col-reverse lg:flex-row items-center justify-between gap-16">

          {/* Text */}
          <motion.div style={{ y: parallaxY, opacity: fadeOut }} className="flex-1 text-center lg:text-left">
            <motion.div variants={container} initial="hidden" animate="show">

              <motion.div variants={item} className="inline-flex items-center gap-2 mb-8">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
                <span className="text-xs font-semibold tracking-[0.2em] text-accent-gray uppercase glass-card px-4 py-2 rounded-full">
                  Available for new projects
                </span>
              </motion.div>

              <motion.h1
                variants={item}
                className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[0.95] mb-6 text-accent-dark"
              >
                Building
                <br />
                <span className="text-gradient">Scalable</span>
                <br />
                Platforms.
              </motion.h1>

              <motion.div variants={item} className="flex items-center gap-3 justify-center lg:justify-start mb-8 h-8">
                <span className="w-6 h-px bg-accent-dark/30" aria-hidden="true" />
                <span className="text-base md:text-lg font-medium text-accent-gray tracking-wide" aria-live="polite">
                  {role}
                  <span className="cursor-blink ml-0.5 text-accent-purple" aria-hidden="true">|</span>
                </span>
              </motion.div>

              <motion.p variants={item} className="text-base md:text-lg text-accent-gray leading-relaxed mb-10 max-w-xl mx-auto lg:mx-0">
                Backend-focused developer specializing in Django and scalable system design. Built and deployed a production-grade e-commerce platform on AWS — 42% DB query reduction, concurrent-safe payments, and sub-300ms order responses.
              </motion.p>

              <motion.div variants={item} className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
                <motion.a
                  href="#projects"
                  whileHover={prefersReducedMotion ? {} : { scale: 1.04, y: -2 }}
                  whileTap={prefersReducedMotion ? {} : { scale: 0.97 }}
                  className="interactive group relative px-8 py-4 rounded-full bg-accent-dark text-white font-semibold text-sm tracking-wide overflow-hidden shadow-[0_4px_24px_rgba(17,17,17,0.18)] hover:shadow-[0_8px_32px_rgba(17,17,17,0.28)] transition-shadow"
                >
                  <span className="relative z-10">View My Work</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-accent-purple to-accent-blue opacity-0 group-hover:opacity-100 transition-opacity duration-300" aria-hidden="true" />
                </motion.a>
                <motion.a
                  href="#contact"
                  whileHover={prefersReducedMotion ? {} : { scale: 1.04, y: -2 }}
                  whileTap={prefersReducedMotion ? {} : { scale: 0.97 }}
                  className="interactive px-8 py-4 rounded-full glass-card text-accent-dark font-semibold text-sm tracking-wide hover:shadow-[0_8px_32px_rgba(109,40,217,0.15)] transition-all"
                >
                  Start a Conversation →
                </motion.a>
              </motion.div>

              <motion.div variants={item} className="flex items-center gap-8 mt-14 justify-center lg:justify-start">
                {[['42%', 'DB Query Reduction'], ['300ms', 'Order Response'], ['3', 'User Roles']].map(([num, label]) => (
                  <div key={label} className="text-center lg:text-left">
                    <div className="text-2xl font-black text-accent-dark">{num}</div>
                    <div className="text-xs text-accent-gray tracking-wider uppercase mt-0.5">{label}</div>
                  </div>
                ))}
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Image */}
          <motion.div
            style={{ y: imgY }}
            initial={{ opacity: 0, scale: prefersReducedMotion ? 1 : 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: dur(1.1), ease: [0.16, 1, 0.3, 1], delay: dur(0.3) }}
            className="flex-1 flex justify-center lg:justify-end"
          >
            <div className="relative w-64 h-64 md:w-80 md:h-80 lg:w-96 lg:h-96">
              {!prefersReducedMotion && (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-[-16px] rounded-full border border-dashed border-violet-300/60 hidden md:block"
                    aria-hidden="true"
                  />
                  <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ duration: 36, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-[-32px] rounded-full border border-blue-200/40 hidden md:block"
                    aria-hidden="true"
                  />
                </>
              )}

              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-violet-300/40 to-blue-200/30 blur-2xl scale-110" aria-hidden="true" />

              <motion.div
                animate={prefersReducedMotion ? {} : { y: [-8, 8, -8] }}
                transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                className="relative w-full h-full rounded-full overflow-hidden border-4 border-white/80 shadow-[0_20px_60px_rgba(109,40,217,0.2),0_4px_16px_rgba(0,0,0,0.1)]"
              >
                <img
                  src={profilePhoto}
                  alt="Akash Tomy — Full-Stack Developer"
                  className="w-full h-full object-cover scale-105 hover:scale-110 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-tr from-violet-500/10 to-transparent" aria-hidden="true" />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: dur(1.2), duration: dur(0.6) }}
                className="absolute -bottom-4 -right-4 glass-card-elevated rounded-2xl px-4 py-3 shadow-lg"
              >
                <div className="text-xs font-bold text-accent-dark">Django + React</div>
                <div className="text-[10px] text-accent-gray mt-0.5">Full-Stack Expert</div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: dur(2), duration: dur(1) }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        aria-hidden="true"
      >
        <span className="text-[10px] text-accent-gray/60 uppercase tracking-[0.25em]">Scroll</span>
        <div className="w-px h-12 bg-gradient-to-b from-accent-dark/20 to-transparent relative overflow-hidden">
          {!prefersReducedMotion && (
            <motion.div
              animate={{ y: [-48, 48] }}
              transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute top-0 w-full h-1/2 bg-gradient-to-b from-accent-purple to-transparent"
            />
          )}
        </div>
      </motion.div>
    </section>
  );
};

export default HeroSection;
