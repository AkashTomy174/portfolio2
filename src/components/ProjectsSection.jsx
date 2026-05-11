import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ExternalLinkIcon, GithubIcon, CheckCircleIcon } from './Icons';
import { projects } from '../data/projects';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const IMPACT = [
  ['42%', 'fewer queries after I stopped letting the ORM improvise'],
  ['<300ms', 'order response after moving noisy work to Celery'],
  ['0', 'duplicate payment updates after row-level locking'],
];

const ARCHITECTURE = ['React', 'Django', 'MySQL/RDS', 'Redis', 'Celery', 'Razorpay', 'AWS EC2', 'Nginx'];

const DECISIONS = [
  {
    label: 'Preventing Overselling',
    problem: 'Two customers can try to buy the same limited stock at almost the same time.',
    decision: 'I used transactional row locking with Django ORM so inventory is checked and updated inside one protected database operation.',
    evidence: 'Stock changes stop being a hopeful frontend assumption and become a database-backed state transition.',
  },
  {
    label: 'Payment Integrity',
    problem: 'Payment callbacks can be retried, duplicated, or arrive after the user has already moved on.',
    decision: 'I wrapped payment mutation in a transaction, used select_for_update on the order row, and verified Razorpay webhook signatures.',
    evidence: 'A payment success path can run without creating duplicate transaction updates.',
  },
  {
    label: 'Redis Cache Boundaries',
    problem: 'Caching everything is how stale data quietly wins.',
    decision: 'I cached read-heavy product data, kept order/payment state uncached, and used TTLs where freshness mattered less than speed.',
    evidence: 'The cache helps browsing paths without becoming the source of truth for money or inventory.',
  },
  {
    label: 'N+1 Query Cleanup',
    problem: 'Product/order pages were doing repeated reads that looked harmless until counted.',
    decision: 'I used select_related, prefetch_related, and tighter queryset planning instead of just throwing hardware at it.',
    evidence: 'One optimized path dropped from 36 queries to 21, a 42% reduction.',
  },
  {
    label: 'Async Order Side Effects',
    problem: 'Notifications and other side effects do not need to sit inside the customer-facing response path.',
    decision: 'I moved those jobs to Celery workers and kept the order request focused on the state change.',
    evidence: 'The order response stayed under 300ms while background work continued separately.',
  },
  {
    label: 'Deployment Shape',
    problem: 'A project that only works on localhost has not met reality yet.',
    decision: 'I deployed with EC2, Gunicorn, Nginx, RDS, S3/static handling, GitHub Actions, and environment-based config.',
    evidence: 'Deployment decisions forced me to handle SSL, CORS, media/static files, secrets, process management, and server restarts.',
  },
];

const FLOW = [
  ['Client', 'React storefront and seller/admin dashboards'],
  ['API', 'Django views, auth, validation, permissions'],
  ['Data', 'MySQL/RDS, ORM optimization, row locks'],
  ['Async', 'Celery workers, Redis cache, notifications'],
  ['Edge', 'Nginx, Gunicorn, AWS EC2, S3 assets'],
];

const EngineeringDecisionGrid = () => (
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    {DECISIONS.map(({ label, problem, decision, evidence }) => (
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

const ArchitectureDiagram = () => (
  <div className="rounded-2xl border border-black/8 bg-accent-dark p-5 text-white">
    <div className="text-xs font-bold uppercase tracking-widest text-white/50">Request Lifecycle</div>
    <div className="mt-5 grid gap-3">
      {FLOW.map(([label, body], index) => (
        <div key={label} className="grid grid-cols-[4rem_1fr] items-center gap-3">
          <div className="rounded-xl border border-white/10 bg-white/8 px-3 py-2 text-center text-xs font-black text-white">
            {label}
          </div>
          <div className="relative rounded-xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-white/78">
            {body}
            {index < FLOW.length - 1 && (
              <span className="absolute -bottom-3 left-6 h-3 w-px bg-white/20" aria-hidden="true" />
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

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
              flagship project / not a toy clone
            </span>
            <h3 className="mt-5 text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-8xl">
              {project.title}
            </h3>
            <p className="mt-5 text-base md:text-lg leading-relaxed text-accent-gray">
              {project.description}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {IMPACT.map(([value, label]) => (
              <div key={label} className="border border-accent-dark bg-primary-dark p-4 shadow-[5px_5px_0_rgba(21,21,18,0.16)]">
                <div className="text-3xl font-black text-accent-dark">{value}</div>
                <p className="mt-2 text-xs font-medium leading-relaxed text-accent-gray">{label}</p>
              </div>
            ))}
          </div>

          <div>
            <div className="mb-3 text-xs font-black uppercase tracking-widest text-accent-gray">Tools I used, not decorations</div>
            <div className="flex flex-wrap items-center gap-2">
              {ARCHITECTURE.map((node) => (
                <span key={node} className="rounded-lg border border-black/8 bg-white px-3 py-1.5 text-xs font-semibold text-accent-dark">
                  {node}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <a
              href={project.demo}
            className="interactive hover-scrape inline-flex items-center gap-2 border border-accent-dark bg-accent-dark px-5 py-3 text-sm font-black text-primary-dark"
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLinkIcon className="h-4 w-4" aria-hidden="true" />
              View Live Site
            </a>
            <a
              href={project.github}
              className="interactive inline-flex items-center gap-2 border border-accent-dark bg-primary-dark px-5 py-3 text-sm font-black text-accent-dark transition-all hover:bg-accent-purple"
              target="_blank"
              rel="noopener noreferrer"
            >
              <GithubIcon className="h-4 w-4" aria-hidden="true" />
              Source Code
            </a>
          </div>
        </div>

        <div className="space-y-5">
          <motion.div
            whileHover={reduced ? {} : { scale: 1.015 }}
            transition={{ duration: 0.35 }}
            className="aspect-[16/10] overflow-hidden rounded-2xl border border-black/8 bg-white shadow-lg"
          >
            <img
              src={project.image}
              alt={project.title}
              loading="lazy"
              className="h-full w-full object-cover object-top"
            />
          </motion.div>

          <ArchitectureDiagram />

          <div className="border border-accent-dark bg-primary-dark p-5">
            <h4 className="text-sm font-black uppercase tracking-widest text-accent-dark">What I actually built</h4>
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
              <span key={tech} className="rounded-full border border-black/8 bg-white px-3 py-1 text-xs font-medium text-accent-gray">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-10 border-t border-black/8 pt-8">
        <div className="mb-5">
          <h4 className="text-2xl font-black tracking-tight text-accent-dark">Where I had to think</h4>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-accent-gray">
            This is the section I wish more junior portfolios had. I am showing the constraints, tradeoffs, and boring production choices, because that is where backend work becomes visible.
          </p>
        </div>
        <EngineeringDecisionGrid />
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
        <div key={title} className="rounded-2xl border border-black/8 bg-white/70 p-5">
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
            EasyBuy, with the <span className="text-gradient">mess left in</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: reduced ? 0 : 16 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : 0.25 }}
            className="text-accent-gray mt-3 text-lg max-w-2xl"
          >
            I built this to prove I could handle more than a nice UI. Orders, payments, sellers, admins, caching, workers, deployment: the annoying useful stuff.
          </motion.p>
        </div>

        {projects.map((project) => (
          <ProjectCaseStudy key={project.title} project={project} />
        ))}

        <Principles />
      </div>
    </section>
  );
};

export default ProjectsSection;
