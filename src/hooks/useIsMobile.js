import { useEffect, useState } from 'react';

/**
 * Hook to detect if device is mobile and prefers reduced motion
 * Used to simplify animations on mobile and respect user preferences
 */
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if mobile
    const checkMobile = () => {
      const isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;
      const isTouchDevice = () => {
        return (
          (typeof window !== 'undefined' &&
            ((navigator.maxTouchPoints > 0) ||
              (navigator.msMaxTouchPoints > 0)))
        );
      };
      setIsMobile(isCoarsePointer || isTouchDevice());
    };

    // Check for reduced motion preference
    const checkReducedMotion = () => {
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      setPrefersReducedMotion(prefersReduced);
    };

    checkMobile();
    checkReducedMotion();

    // Listen for media query changes
    const mobileMediaQuery = window.matchMedia('(pointer: coarse)');
    const motionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleMobileChange = (e) => setIsMobile(e.matches);
    const handleMotionChange = (e) => setPrefersReducedMotion(e.matches);

    mobileMediaQuery.addEventListener('change', handleMobileChange);
    motionMediaQuery.addEventListener('change', handleMotionChange);

    return () => {
      mobileMediaQuery.removeEventListener('change', handleMobileChange);
      motionMediaQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  return { isMobile, prefersReducedMotion };
};

export default useIsMobile;
