import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ServerIcon, LayoutIcon, DatabaseIcon, LinkIcon, CloudIcon, GitBranchIcon } from './Icons';
import { skillsData } from '../data/skills';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const ICON_MAP = {
  server: ServerIcon,
  layout: LayoutIcon,
  database: DatabaseIcon,
  link: LinkIcon,
  cloud: CloudIcon,
  git: GitBranchIcon,
};

const SkillBar = ({ name, level, dot, inView, reduced }) => (
  <div className="space-y-1.5">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full ${dot} shrink-0`} aria-hidden="true" />
        <span className="text-sm font-medium text-accent-dark">{name}</span>
      </div>
      <span className="text-xs font-semibold text-accent-gray tabular-nums">{level}%</span>
    </div>
    <div className="skill-bar-track" role="progressbar" aria-valuenow={level} aria-valuemin={0} aria-valuemax={100} aria-label={name}>
      <motion.div
        className="skill-bar-fill"
        initial={{ scaleX: 0 }}
        animate={inView ? { scaleX: level / 100 } : { scaleX: 0 }}
        transition={{ duration: reduced ? 0 : 1, ease: [0.16, 1, 0.3, 1], delay: reduced ? 0 : 0.1 }}
      />
    </div>
  </div>
);

const SkillCard = ({ item, index }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });
  const reduced = useReducedMotion();
  const Icon = ICON_MAP[item.iconKey];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: reduced ? 0 : 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: reduced ? 0 : 0.6, ease: [0.16, 1, 0.3, 1], delay: reduced ? 0 : index * 0.08 }}
      whileHover={reduced ? {} : { y: -6, boxShadow: '0 24px 48px rgba(0,0,0,0.1)' }}
      className="glass-card-elevated rounded-2xl p-6 group transition-all duration-300"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className={`p-2.5 rounded-xl bg-gradient-to-br ${item.colorClass} text-white shadow-sm`} aria-hidden="true">
          {Icon && <Icon className="w-5 h-5" />}
        </div>
        <div>
          <h3 className="text-sm font-bold text-accent-dark tracking-wide">{item.category}</h3>
          <div className={`mt-0.5 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${item.accent} inline-block`}>
            {item.skills.length} skills
          </div>
        </div>
        <motion.div
          className={`ml-auto h-0.5 bg-gradient-to-r ${item.colorClass} rounded-full`}
          initial={{ width: 0 }}
          animate={inView ? { width: 32 } : { width: 0 }}
          transition={{ duration: reduced ? 0 : 0.8, delay: reduced ? 0 : index * 0.08 + 0.3 }}
          aria-hidden="true"
        />
      </div>

      <div className="space-y-3.5">
        {item.skills.map((skill) => (
          <SkillBar key={skill.name} {...skill} dot={item.dot} inView={inView} reduced={reduced} />
        ))}
      </div>
    </motion.div>
  );
};

const SkillsSection = () => {
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true });
  const reduced = useReducedMotion();

  return (
    <section id="skills" className="py-28 relative z-10">
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
            Technical <span className="text-gradient">Arsenal</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.25 }}
            className="text-accent-gray mt-3 text-lg max-w-xl"
          >
            Full-stack toolset optimised for scalable, high-traffic platforms.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {skillsData.map((item, index) => (
            <SkillCard key={item.category} item={item} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default SkillsSection;
