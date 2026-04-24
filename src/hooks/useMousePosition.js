import { useEffect, useState } from 'react';

/**
 * Hook to track mouse position with throttling for smooth cursor effects
 * Throttled at 60fps (16ms intervals) to maintain performance
 */
export const useMousePosition = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    let lastTime = 0;
    const THROTTLE_MS = 16; // ~60fps

    const updateMousePosition = (e) => {
      const now = performance.now();
      if (now - lastTime >= THROTTLE_MS) {
        setMousePosition({ x: e.clientX, y: e.clientY });
        lastTime = now;
      }
    };

    window.addEventListener('mousemove', updateMousePosition);

    return () => {
      window.removeEventListener('mousemove', updateMousePosition);
    };
  }, []);

  return mousePosition;
};

export default useMousePosition;
