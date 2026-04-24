/**
 * Animation Timing and Easing Configuration
 * Centralized constants for consistent animation behavior across the portfolio
 */

// Animation Duration Constants (in milliseconds)
export const DURATIONS = {
  fast: 300,
  normal: 500,
  slow: 800,
  slower: 1200,
};

// Easing Functions (cubic-bezier values)
export const EASINGS = {
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  smoothOut: 'cubic-bezier(0.3, 0, 0.1, 1)',
  easeOut: 'cubic-bezier(0.16, 1, 0.3, 1)',
  easeInOut: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
};

// Transition Presets
export const TRANSITIONS = {
  fast: {
    duration: DURATIONS.fast,
    ease: EASINGS.smooth,
  },
  normal: {
    duration: DURATIONS.normal,
    ease: EASINGS.smooth,
  },
  slow: {
    duration: DURATIONS.slow,
    ease: EASINGS.smooth,
  },
  smooth: {
    type: 'spring',
    stiffness: 100,
    damping: 15,
  },
};

// Common Animation Variants for Framer Motion
export const ANIMATION_VARIANTS = {
  // Fade and scale animations
  fadeInScale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },

  // Slide up animations
  slideUp: {
    initial: { opacity: 0, y: 40 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 40 },
  },

  // Bounce in animation
  bounceIn: {
    initial: { opacity: 0, scale: 0.3 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.3 },
  },

  // Stagger container
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  },

  // Stagger items
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
  },
};

// Hover and tap effects
export const INTERACTION_VARIANTS = {
  hover: {
    scale: 1.02,
    transition: { duration: DURATIONS.fast / 1000 },
  },
  tap: {
    scale: 0.98,
  },
};

// Pattern for button interactions
export const buttonVariants = {
  initial: { scale: 1 },
  hover: { scale: 1.05 },
  tap: { scale: 0.95 },
};

// Pattern for card interactions
export const cardVariants = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  hover: { scale: 1.02, y: -5 },
};
