import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ExternalLinkIcon, GithubIcon, CheckCircleIcon } from './Icons';
import { projects } from '../data/projects';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const ProjectCard = ({ project, index }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduced = useReducedMotion();
  const isEven = index % 2 === 0;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: reduced ? 0 : 60 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: reduced ? 0 : 0.8, ease: [0.16, 1, 0.3, 1] }}
      className={`flex flex-col ${isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'} gap-10 items-center`}
    >
      <motion.div
        whileHover={reduced ? {} : { scale: 1.02 }}
        transition={{ duration: 0.4 }}
        className="w-full lg:w-1/2 aspect-[16/10] rounded-2xl overflow-hidden glass-card relative group shadow-lg bg-white"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-violet-500/20 to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 z-10" aria-hidden="true" />
        <img
          src={project.image}
          alt={project.title}
          loading="lazy"
          className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-700"
        />
      </motion.div>

      <div className="w-full lg:w-1/2 space-y-5">
        {project.featured && (
          <span className="inline-block text-xs font-bold tracking-widest uppercase text-violet-600 bg-violet-50 border border-violet-200 px-3 py-1 rounded-full">
            Featured Project
          </span>
        )}
        <h3 className="text-2xl md:text-3xl font-black text-accent-dark tracking-tight">{project.title}</h3>

        <div className="glass-card rounded-xl p-5">
          <p className="text-accent-gray text-sm leading-relaxed">{project.description}</p>
        </div>

        {/* Architecture flow */}
        <div className="flex items-center gap-2 flex-wrap">
          {['React', 'Django', 'MySQL', 'Redis', 'AWS EC2'].map((node, i, arr) => (
            <span key={node} className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-accent-dark bg-white border border-black/10 px-2.5 py-1 rounded-md">{node}</span>
              {i < arr.length - 1 && <span className="text-accent-gray/40 text-xs">→</span>}
            </span>
          ))}
        </div>

        <ul className="space-y-2">
          {project.features.map((f) => (
            <li key={f} className="flex items-start gap-2.5 text-sm text-accent-gray">
              <CheckCircleIcon className="w-4 h-4 text-violet-500 shrink-0 mt-0.5" aria-hidden="true" />
              {f}
            </li>
          ))}
        </ul>

        <div className="flex flex-wrap gap-2">
          {project.tech.map((t) => (
            <span key={t} className="text-xs font-medium text-accent-gray bg-white border border-black/8 px-3 py-1 rounded-full">
              {t}
            </span>
          ))}
        </div>

        <div className="flex gap-3 pt-1">
          <a
            href={project.demo}
            className="interactive flex items-center gap-2 text-sm font-semibold text-white bg-accent-dark px-5 py-2.5 rounded-lg hover:bg-accent-purple transition-colors shadow-sm"
            aria-label={`View live demo for ${project.title}`}
            target="_blank" rel="noopener noreferrer"
          >
            <ExternalLinkIcon className="w-4 h-4" aria-hidden="true" /> View Live Site
          </a>
          <a
            href={project.github}
            className="interactive flex items-center gap-2 text-sm font-medium text-accent-dark bg-white border border-black/10 px-5 py-2.5 rounded-lg hover:border-violet-400 hover:text-violet-600 transition-all"
            aria-label={`View source code for ${project.title}`}
            target="_blank" rel="noopener noreferrer"
          >
            <GithubIcon className="w-4 h-4" aria-hidden="true" /> Source Code
          </a>
        </div>
      </div>
    </motion.div>
  );
};

const ProjectsSection = () => {
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true });
  const reduced = useReducedMotion();

  return (
    <section id="projects" className="py-28 relative z-10">
      <div className="container mx-auto px-6 max-w-6xl">
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
            className="text-4xl md:text-5xl font-black text-accent-dark tracking-tight"
          >
            Featured <span className="text-gradient">Projects</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.25 }}
            className="text-accent-gray mt-3 text-lg max-w-xl"
          >
            Production-ready applications demonstrating scale and performance.
          </motion.p>
        </div>

        <div className="space-y-24">
          {projects.map((p, i) => <ProjectCard key={p.title} project={p} index={i} />)}
        </div>
      </div>
    </section>
  );
};

export default ProjectsSection;
