import { useEffect, useRef, useState } from 'react';

/**
 * Hook to detect when an element enters the viewport and trigger animations
 * Optimized with Intersection Observer for 60fps performance
 */
export const useScrollAnimation = (options = {}) => {
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const currentRef = ref.current;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          // Optional: unobserve after first intersection
          if (options.once) {
            observer.unobserve(entry.target);
          }
        } else if (!options.once) {
          setIsInView(false);
        }
      },
      {
        threshold: options.threshold || 0.1,
        rootMargin: options.rootMargin || '-50px',
      }
    );

    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [options.once, options.threshold, options.rootMargin]);

  return [ref, isInView];
};

export default useScrollAnimation;
