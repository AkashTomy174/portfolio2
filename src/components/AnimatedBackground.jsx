const AnimatedBackground = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none z-0" aria-hidden="true">
    <div className="absolute left-0 top-24 h-px w-full bg-accent-dark/10" />
    <div className="absolute left-8 top-0 h-full w-px bg-accent-dark/10" />
    <div className="absolute bottom-10 right-8 rotate-[-8deg] border border-accent-dark/20 bg-primary-dark px-4 py-2 text-[10px] font-black uppercase tracking-[0.35em] text-accent-dark/35">
      inspect the boring parts
    </div>
  </div>
);

export default AnimatedBackground;
