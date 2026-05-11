import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ExternalLinkIcon, GithubIcon, CheckCircleIcon } from './Icons';
import { projects } from '../data/projects';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const EngineeringDecisionGrid = ({ decisions }) => (
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    {decisions.map(({ label, problem, decision, evidence }) => (
      <div key={label} className="hard-panel bg-primary-dark p-5">
        <div className="text-xs font-black uppercase tracking-widest text-accent-dark">{label}</div>
        <div className="mt-4 space-y-4">
          <div>
            <div className="text-[10px] font-black uppercase tracking-widest text-accent-gray/55">Problem</div>
            <p className="mt-1 text-sm leading-relaxed text-accent-gray">{problem}</p>
          </div>
          <div>
            <div className="text-[10px] font-black uppercase tracking-widest text-accent-gray/55">Decision</div>
            <p className="mt-1 text-sm leading-relaxed text-accent-gray">{decision}</p>
          </div>
          <div>
            <div className="text-[10px] font-black uppercase tracking-widest text-accent-gray/55">Evidence</div>
            <p className="mt-1 text-sm font-semibold leading-relaxed text-accent-dark">{evidence}</p>
          </div>
        </div>
      </div>
    ))}
  </div>
);

const ArchitectureDiagram = ({ flow }) => (
  <div className="border border-accent-dark bg-accent-dark p-5 text-primary-dark">
    <div className="text-xs font-bold uppercase tracking-widest text-primary-dark/50">System path</div>
    <div className="mt-5 grid gap-3">
      {flow.map(([label, body], index) => (
        <div key={label} className="grid grid-cols-[4.5rem_1fr] items-center gap-3">
          <div className="border border-primary-dark/20 bg-primary-dark/8 px-3 py-2 text-center text-xs font-black text-primary-dark">
            {label}
          </div>
          <div className="relative border border-primary-dark/20 bg-primary-dark/6 px-4 py-3 text-sm text-primary-dark/78">
            {body}
            {index < flow.length - 1 && (
              <span className="absolute -bottom-3 left-6 h-3 w-px bg-primary-dark/20" aria-hidden="true" />
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const ProjectVisual = ({ project, reduced }) => {
  if (project.visual === 'terminal') {
    return (
      <motion.div
        whileHover={reduced ? {} : { rotate: -1, y: -4 }}
        transition={{ duration: 0.28 }}
        className="terminal-scan border border-accent-dark bg-accent-dark p-5 font-mono text-xs leading-relaxed text-primary-dark shadow-[10px_10px_0_#ccff00]"
      >
        <div className="text-accent-purple">ai-project-judge pipeline</div>
        <div className="mt-4 text-primary-dark/70">$ ingest https://github.com/team/project</div>
        <div className="mt-2 text-primary-dark/70">language: python + javascript</div>
        <div className="text-primary-dark/70">kept: entry points, source, tests, config, README</div>
        <div className="text-primary-dark/70">ignored: node_modules, dist, binaries, lock noise</div>
        <div className="mt-4 text-primary-dark/70">$ run deterministic layer</div>
        <div className="text-primary-dark/70">coverage: 23% / lint: 14 / cves: 2 critical / complexity: high</div>
        <div className="mt-4 text-primary-dark/70">$ ask ai layer with metrics injected</div>
        <div className="text-primary-dark/70">score: evidence-backed, not vibes-backed</div>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={reduced ? {} : { scale: 1.015 }}
      transition={{ duration: 0.35 }}
      className="aspect-[16/10] overflow-hidden border border-accent-dark bg-white shadow-[10px_10px_0_rgba(21,21,18,0.16)]"
    >
      <img
        src={project.image}
        alt={project.title}
        loading="lazy"
        className="h-full w-full object-cover object-top"
      />
    </motion.div>
  );
};

const ProjectCaseStudy = ({ project }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();

  return (
    <motion.article
      ref={ref}
      initial={{ opacity: 0, y: reduced ? 0 : 48 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: reduced ? 0 : 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="hard-panel bg-primary-dark p-5 md:p-8"
    >
      <div className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="space-y-8">
          <div>
            <span className="inline-block rotate-[-2deg] border border-accent-dark bg-accent-purple px-3 py-1 text-xs font-black uppercase tracking-widest text-accent-dark shadow-[4px_4px_0_#151512]">
              {project.badge}
            </span>
            <h3 className="mt-5 text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl">
              {project.title}
            </h3>
            <div className="mt-4 inline-block border border-accent-dark/25 px-3 py-1 font-mono text-xs font-black uppercase tracking-widest text-accent-gray">
              {project.status}
            </div>
            <p className="mt-5 text-base leading-relaxed text-accent-gray md:text-lg">
              {project.description}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {project.impact.map(([value, label]) => (
              <div key={label} className="border border-accent-dark bg-primary-dark p-4 shadow-[5px_5px_0_rgba(21,21,18,0.16)]">
                <div className="text-3xl font-black text-accent-dark">{value}</div>
                <p className="mt-2 text-xs font-medium leading-relaxed text-accent-gray">{label}</p>
              </div>
            ))}
          </div>

          <div>
            <div className="mb-3 text-xs font-black uppercase tracking-widest text-accent-gray">Tools I used, not decorations</div>
            <div className="flex flex-wrap items-center gap-2">
              {project.architecture.map((node) => (
                <span key={node} className="border border-accent-dark/20 bg-primary-dark px-3 py-1.5 text-xs font-semibold text-accent-dark">
                  {node}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <a
              href={project.demo}
              className="interactive hover-scrape inline-flex items-center gap-2 border border-accent-dark bg-accent-dark px-5 py-3 text-sm font-black text-primary-dark"
              target={project.demo.startsWith('#') ? undefined : '_blank'}
              rel={project.demo.startsWith('#') ? undefined : 'noopener noreferrer'}
            >
              <ExternalLinkIcon className="h-4 w-4" aria-hidden="true" />
              {project.demo.startsWith('#') ? 'Ask me about it' : 'View Live Site'}
            </a>
            <a
              href={project.github}
              className="interactive inline-flex items-center gap-2 border border-accent-dark bg-primary-dark px-5 py-3 text-sm font-black text-accent-dark transition-all hover:bg-accent-purple"
              target={project.github.startsWith('#') ? undefined : '_blank'}
              rel={project.github.startsWith('#') ? undefined : 'noopener noreferrer'}
            >
              <GithubIcon className="h-4 w-4" aria-hidden="true" />
              {project.github.startsWith('#') ? 'Not public yet' : 'Source Code'}
            </a>
          </div>
        </div>

        <div className="space-y-5">
          <ProjectVisual project={project} reduced={reduced} />
          <ArchitectureDiagram flow={project.flow} />

          <div className="border border-accent-dark bg-primary-dark p-5">
            <h4 className="text-sm font-black uppercase tracking-widest text-accent-dark">What I actually built / designed</h4>
            <ul className="mt-4 space-y-3">
              {project.features.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-sm leading-relaxed text-accent-gray">
                  <CheckCircleIcon className="mt-0.5 h-4 w-4 shrink-0 text-accent-dark" aria-hidden="true" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-wrap gap-2">
            {project.tech.map((tech) => (
              <span key={tech} className="border border-accent-dark/20 bg-primary-dark px-3 py-1 text-xs font-medium text-accent-gray">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-10 border-t border-accent-dark/20 pt-8">
        <div className="mb-5">
          <h4 className="text-2xl font-black tracking-tight text-accent-dark">Where I had to think</h4>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-accent-gray">
            This is the section I wish more junior portfolios had. I am showing the constraints, tradeoffs, and boring production choices, because that is where backend work becomes visible.
          </p>
        </div>
        <EngineeringDecisionGrid decisions={project.decisions} />
      </div>
    </motion.article>
  );
};

const Principles = () => {
  const principles = [
    ['Lock before celebrating', 'If money is involved, I want the database to agree before the UI smiles.'],
    ['Count before guessing', 'I like query counts because they make performance arguments less hand-wavy.'],
    ['Move chores out of the path', 'Notifications belong in workers, not in the user waiting room.'],
    ['Deploy early enough to hurt', 'EC2, Nginx, env vars, CORS, and SSL reveal problems localhost politely hides.'],
  ];

  return (
    <div className="mt-16 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {principles.map(([title, body], index) => (
        <div key={title} className="border border-accent-dark/20 bg-primary-dark p-5">
          <div className="text-xs font-black text-accent-dark">{String(index + 1).padStart(2, '0')}</div>
          <h4 className="mt-3 text-base font-black text-accent-dark">{title}</h4>
          <p className="mt-2 text-sm leading-relaxed text-accent-gray">{body}</p>
        </div>
      ))}
    </div>
  );
};

const ProjectsSection = () => {
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true });
  const reduced = useReducedMotion();

  return (
    <section id="projects" className="relative z-10 py-28">
      <div className="container mx-auto max-w-6xl px-6">
        <div ref={headRef} className="mb-16">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={headInView ? { scaleX: 1 } : {}}
            transition={{ duration: reduced ? 0 : 0.7, ease: [0.16, 1, 0.3, 1] }}
            style={{ transformOrigin: 'left' }}
            className="section-line"
            aria-hidden="true"
          />
          <motion.h2
            initial={{ opacity: 0, y: reduced ? 0 : 24 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.15 }}
            className="text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl"
          >
            Projects, with the <span className="font-black">system parts exposed.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.25 }}
            className="mt-5 max-w-2xl text-lg leading-relaxed text-accent-gray"
          >
            I am not trying to show every button I built. I am trying to show the constraints I noticed and the decisions I made.
          </motion.p>
        </div>

        <div className="space-y-20">
          {projects.map((project) => (
            <ProjectCaseStudy key={project.title} project={project} />
          ))}
        </div>

        <Principles />
      </div>
    </section>
  );
};

export default ProjectsSection;
