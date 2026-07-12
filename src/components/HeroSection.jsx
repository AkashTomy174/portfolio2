import { GithubIcon, LinkedinIcon, MailIcon } from './Icons';
import { SITE } from '../siteConfig';

const PROFILE_AVIF_SRCSET = '/images/portfolioimage-384.avif 384w, /images/portfolioimage-640.avif 640w, /images/portfolioimage-960.avif 960w';
const PROFILE_WEBP_SRCSET = '/images/portfolioimage-384.webp 384w, /images/portfolioimage-640.webp 640w, /images/portfolioimage-960.webp 960w';
const PROFILE_SIZES = '(min-width: 1024px) 350px, (min-width: 768px) 45vw, calc(100vw - 4rem)';

const COMMANDS = [
  ['identity', 'backend systems + AI evaluation pipelines'],
  ['flagship', 'AI Project Judge: deterministic metrics + LLM interpretation'],
  ['proof', 'EasyBuy: payments, locks, Redis, Celery, AWS'],
];

const HeroSection = () => {
  return (
    <section className="relative min-h-screen overflow-hidden pt-24">
      <div className="container relative z-10 mx-auto max-w-6xl px-6">
        <div className="grid min-h-[calc(100vh-6rem)] grid-cols-1 items-center gap-10 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="relative">
            <div className="mb-8 inline-block rotate-[-2deg] border border-accent-dark bg-accent-purple px-4 py-2 text-xs font-black uppercase tracking-[0.28em] shadow-[5px_5px_0_#151512]">
              Full Stack Developer / Django / DRF / React / AWS
            </div>

            <h1 className="max-w-5xl text-6xl font-extralight leading-[0.88] tracking-tight text-accent-dark md:text-8xl lg:text-9xl">
              Akash Tomy
              <br />
              <span className="font-black">builds backend systems</span>
              <br />
              that can be
              <br />
              <span className="font-black">audited.</span>
            </h1>

            <p className="mt-8 max-w-2xl text-lg leading-relaxed text-accent-gray md:text-xl">
              Full Stack Developer with production-ready backend judgment across Django, DRF, React, AWS, payments, queues, Redis, Celery, and AI evaluation systems.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-3">
              <a href="#architecture" className="interactive hover-scrape border border-accent-dark bg-accent-dark px-6 py-3 text-sm font-black uppercase tracking-widest text-primary-dark">
                show the pipeline
              </a>
              <a href="#projects" className="interactive hover-scrape border border-accent-dark bg-primary-dark px-6 py-3 text-sm font-black uppercase tracking-widest text-accent-dark">
                read the deep dive
              </a>
              <a href="/AkashTomy-Resume.pdf" download className="interactive underline-grow px-2 py-3 text-sm font-black uppercase tracking-widest text-accent-dark">
                grab resume
              </a>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <a href={SITE.github} target="_blank" rel="noopener noreferrer" className="interactive inline-flex items-center gap-2 border border-accent-dark bg-primary-dark px-4 py-2 text-xs font-black uppercase tracking-widest text-accent-dark transition hover:bg-accent-purple">
                <GithubIcon className="h-4 w-4" aria-hidden="true" />
                GitHub
              </a>
              <a href={SITE.linkedin} target="_blank" rel="noopener noreferrer" className="interactive inline-flex items-center gap-2 border border-accent-dark bg-primary-dark px-4 py-2 text-xs font-black uppercase tracking-widest text-accent-dark transition hover:bg-accent-purple">
                <LinkedinIcon className="h-4 w-4" aria-hidden="true" />
                LinkedIn
              </a>
              <a href={`mailto:${SITE.email}`} className="interactive inline-flex items-center gap-2 border border-accent-dark bg-primary-dark px-4 py-2 text-xs font-black uppercase tracking-widest text-accent-dark transition hover:bg-accent-purple">
                <MailIcon className="h-4 w-4" aria-hidden="true" />
                Contact
              </a>
            </div>
          </div>

          <div className="relative lg:translate-y-16">
            <div className="hard-panel rotate-[2deg] p-4">
              <picture>
                <source
                  type="image/avif"
                  srcSet={PROFILE_AVIF_SRCSET}
                  sizes={PROFILE_SIZES}
                />
                <source
                  type="image/webp"
                  srcSet={PROFILE_WEBP_SRCSET}
                  sizes={PROFILE_SIZES}
                />
                <img
                  src="/images/portfolioimage-640.webp"
                  alt="Akash Tomy"
                  width="1114"
                  height="1412"
                  fetchPriority="high"
                  decoding="async"
                  className="aspect-[4/5] w-full object-cover grayscale contrast-110 transition duration-500 hover:grayscale-0"
                />
              </picture>
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
              flagship: ai judge
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
