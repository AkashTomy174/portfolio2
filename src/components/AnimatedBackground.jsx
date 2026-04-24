import { useReducedMotion } from '../contexts/MotionPrefsContext';

const AnimatedBackground = () => {
  const reduced = useReducedMotion();

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <div className={`absolute top-[-15%] left-[-10%] w-[55vw] h-[55vw] rounded-full bg-violet-200/40 blur-[140px] ${!reduced ? 'animate-blob' : ''}`} />
      <div className={`absolute top-[30%] right-[-15%] w-[45vw] h-[45vw] rounded-full bg-blue-200/35 blur-[120px] ${!reduced ? 'animate-blob delay-200' : ''}`} />
      <div className={`absolute bottom-[-10%] left-[25%] w-[40vw] h-[40vw] rounded-full bg-pink-100/30 blur-[100px] ${!reduced ? 'animate-blob delay-400' : ''}`} />

      {/* Fine dot grid */}
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: 'radial-gradient(circle, #c4b5fd 1px, transparent 1px)',
          backgroundSize: '36px 36px',
        }}
      />

      {/* Vignette edges */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_60%,rgba(250,250,250,0.7)_100%)]" />
    </div>
  );
};

export default AnimatedBackground;
