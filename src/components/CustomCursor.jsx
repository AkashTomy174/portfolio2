import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useReducedMotion } from '../contexts/MotionPrefsContext';

const CustomCursor = () => {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [trail, setTrail] = useState([]);
  const [hovering, setHovering] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    let raf;
    let raw = { x: 0, y: 0 };

    const onMove = (event) => {
      raw = { x: event.clientX, y: event.clientY };
      setTrail((items) => [{ ...raw, id: Date.now() }, ...items].slice(0, 5));
    };

    const tick = () => {
      setPos({ ...raw });
      raf = requestAnimationFrame(tick);
    };

    const onOver = (event) => {
      const target = event.target;
      setHovering(Boolean(target.closest('a') || target.closest('button') || target.classList.contains('interactive')));
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

  return (
    <>
      {trail.map((item, index) => (
        <motion.div
          key={item.id}
          className="fixed left-0 top-0 z-[9998] h-2 w-2 rounded-full bg-accent-purple pointer-events-none"
          initial={{ opacity: 0.4, scale: 1 }}
          animate={{ x: item.x - 4, y: item.y - 4, opacity: 0, scale: 0.2 }}
          transition={{ duration: 0.45 + index * 0.04 }}
        />
      ))}
      <motion.div
        className="fixed left-0 top-0 z-[9999] pointer-events-none border border-accent-dark bg-primary-dark"
        style={{ width: 28, height: 28, marginLeft: -14, marginTop: -14 }}
        animate={{
          x: pos.x,
          y: pos.y,
          rotate: hovering ? -10 : 0,
          scale: hovering ? 1.45 : 1,
          backgroundColor: hovering ? '#ccff00' : '#f4f1e8',
        }}
        transition={{ type: 'spring', stiffness: 650, damping: 31, mass: 0.35 }}
      />
    </>
  );
};

export default CustomCursor;
