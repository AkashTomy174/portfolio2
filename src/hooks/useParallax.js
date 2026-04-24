import { useEffect, useRef, useState } from 'react';

/**
 * Hook to create parallax effect based on scroll position
 * Elements move at a fraction of the scroll speed for depth effect
 */
export const useParallax = (speed = 0.5) => {
  const ref = useRef(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    let animationFrameId = null;

    const handleScroll = () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }

      animationFrameId = requestAnimationFrame(() => {
        const scrollY = window.scrollY;
        const elementTop = ref.current?.offsetTop || 0;
        const relativeScroll = scrollY - elementTop;
        
        // Only apply parallax when element is in view
        if (relativeScroll > -window.innerHeight && relativeScroll < window.innerHeight) {
          setOffset(relativeScroll * speed);
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [speed]);

  return [ref, offset];
};

export default useParallax;
