import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const CustomCursor = () => {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [hovering, setHovering] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    let raf;
    let raw = { x: 0, y: 0 };

    const onMove = (e) => { raw = { x: e.clientX, y: e.clientY }; };
    const tick = () => { setPos({ ...raw }); raf = requestAnimationFrame(tick); };

    const onOver = (e) => {
      const t = e.target;
      setHovering(!!(t.closest('a') || t.closest('button') || t.classList.contains('interactive')));
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('mouseover', onOver, { passive: true });
    raf = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseover', onOver);
      cancelAnimationFrame(raf);
    };
  }, []);

  const isCoarse = typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches;
  if (isCoarse || prefersReducedMotion) return null;

  const ringStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: 32,
    height: 32,
    marginLeft: -16,
    marginTop: -16,
    borderRadius: '50%',
    border: '1.5px solid rgba(17,17,17,0.35)',
    pointerEvents: 'none',
    zIndex: 9999,
  };

  const dotStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: 5,
    height: 5,
    marginLeft: -2.5,
    marginTop: -2.5,
    borderRadius: '50%',
    backgroundColor: '#111111',
    pointerEvents: 'none',
    zIndex: 9999,
  };

  return (
    <>
      <motion.div
        style={ringStyle}
        animate={{
          x: pos.x,
          y: pos.y,
          scale: hovering ? 1.6 : 1,
          borderColor: hovering ? 'rgba(109,40,217,0.7)' : 'rgba(17,17,17,0.35)',
          backgroundColor: hovering ? 'rgba(109,40,217,0.08)' : 'transparent',
        }}
        transition={{ type: 'spring', stiffness: 600, damping: 32, mass: 0.4 }}
      />
      <motion.div
        style={dotStyle}
        animate={{ x: pos.x, y: pos.y, scale: hovering ? 0 : 1 }}
        transition={{ type: 'spring', stiffness: 800, damping: 28, mass: 0.2 }}
      />
    </>
  );
};

export default CustomCursor;
