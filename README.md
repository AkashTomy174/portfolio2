# Premium Portfolio Website

A modern, interactive portfolio website built with React, Tailwind CSS, and Framer Motion. Featuring glassmorphism UI, smooth animations, and 60fps performance optimizations.

## 🎨 Features

- ✨ **Smooth Scroll Animations** - Fade-up, scale, and stagger effects on scroll
- 🎭 **Glassmorphism Design** - Modern frosted glass UI with gradient accents
- 🌀 **Animated Background** - Morphing blob animations for visual depth
- 🖱️ **Custom Cursor** - Interactive cursor with trail effects
- 📱 **Fully Responsive** - Optimized for mobile, tablet, and desktop
- ⚡ **High Performance** - 60fps animations, GPU acceleration, lazy loading
- ♿ **Accessible** - Keyboard navigation, ARIA labels, reduced motion support
- 🎯 **Interactive Elements** - Hover effects, 3D tilt, magnetic buttons

## 🛠️ Tech Stack

- **React 19** - Modern UI framework with hooks
- **Tailwind CSS 4** - Utility-first styling
- **Framer Motion 12** - Advanced animation library
- **Vite** - Lightning-fast build tool
- **Lucide React** - Icon library

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 🏗️ Project Structure

```
src/
├── components/
│   ├── HeroSection.jsx          # Hero section with profile
│   ├── AboutSection.jsx         # About & stats section
│   ├── SkillsSection.jsx        # Skills grid with categories
│   ├── ProjectsSection.jsx      # Featured projects showcase
│   ├── ContactSection.jsx       # Contact CTA section
│   ├── CustomCursor.jsx         # Interactive cursor component
│   ├── AnimatedBackground.jsx   # Animated blob background
│   └── Icons.jsx                # SVG icon components
├── hooks/
│   ├── useScrollAnimation.js    # Viewport detection hook
│   ├── useMousePosition.js      # Mouse tracking (throttled)
│   ├── useParallax.js           # Parallax scroll effect
│   ├── useIsMobile.js           # Mobile detection
│   └── index.js                 # Hook exports
├── utils/
│   ├── animationConfig.js       # Animation constants & presets
│   └── utils.js                 # Utility functions (cn, etc)
├── App.jsx                      # Main app component
├── index.css                    # Global styles & keyframes
└── main.jsx                     # Entry point
```

## 🎨 Design System

### Color Palette

- **Primary Dark**: `#0f0f1e` - Main background
- **Surface**: `#1a1a2e` - Card backgrounds
- **Purple Accent**: `#a855f7` - Primary gradient color
- **Pink Accent**: `#ec4899` - Secondary gradient color
- **Blue Accent**: `#3b82f6` - Tertiary gradient color

### Glassmorphism

All cards use the `.glass-card` class for consistent frosted glass effects:
- 60% opacity background
- 24px blur backdrop
- Subtle border and shadow

### Animation Timing

- **Fast**: 300ms
- **Normal**: 500ms
- **Slow**: 800ms
- **Slower**: 1200ms

## 🎬 Animation Components

### Scroll Animations

Elements use `whileInView` for scroll-triggered animations:

```jsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-50px" }}
  transition={{ duration: 0.6 }}
>
  Content
</motion.div>
```

### Stagger Effects

Grid items stagger with sequential delays:

```jsx
{items.map((item, index) => (
  <motion.div
    key={index}
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.1 }}
  >
    {item}
  </motion.div>
))}
```

### Hover Interactions

Cards scale and glow on hover:

```jsx
<motion.div
  whileHover={{ scale: 1.05 }}
  className="glass-card"
>
  Hover me
</motion.div>
```

## 🎯 Customization Guide

### Update Personal Information

Edit component content directly:

1. **HeroSection.jsx** - Update heading, subheading, CTA text
2. **AboutSection.jsx** - Update about text and stats
3. **SkillsSection.jsx** - Modify skill categories and technologies
4. **ProjectsSection.jsx** - Add your projects with details
5. **ContactSection.jsx** - Update email and social links

### Change Colors

Update the color variables in `tailwind.config.js`:

```js
colors: {
  'primary-dark': '#0f0f1e',
  'surface': '#1a1a2e',
  'accent-purple': '#a855f7',
  'accent-pink': '#ec4899',
  'accent-blue': '#3b82f6',
}
```

### Adjust Animation Speed

Modify timing in `utils/animationConfig.js`:

```js
export const DURATIONS = {
  fast: 300,      // Change values here
  normal: 500,
  slow: 800,
};
```

### Add Images

Replace placeholder images:

1. **Profile Image** - HeroSection profile picture URL
2. **Project Images** - ProjectsSection project thumbnails
3. **Background** - AnimatedBackground gradients

## ⚡ Performance Optimizations

### GPU Acceleration

- Animations use `transform` and `opacity` only (no layout shifts)
- `will-change` applied to frequently animated elements
- `backface-visibility: hidden` for smoother transforms

### Throttling & Debouncing

- Mouse tracking throttled to 16ms (60fps)
- Scroll events use `requestAnimationFrame`
- Intersection Observer for viewport detection

### Lazy Loading

- Images use `loading="lazy"`
- Animations trigger only in viewport
- Code splitting ready with Vite

### CSS Optimization

- Custom scrollbar styling
- Minimal CSS with Tailwind
- Noise texture overlay for premium feel

## 📱 Mobile Optimization

- Touch-optimized interactive elements
- Reduced animation complexity on mobile
- Respects `prefers-reduced-motion` setting
- Viewport-based animation triggers

## ♿ Accessibility

- Semantic HTML structure
- ARIA labels on icons
- Keyboard navigation support
- High contrast text
- Focus indicators on interactive elements
- Reduced motion support

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Connect GitHub repo and auto-deploy
# Production build is automatic
```

### Netlify

```bash
npm run build
# Deploy the 'dist' folder
```

### GitHub Pages

```bash
npm run build
# Push dist folder to gh-pages branch
```

## 📊 Core Web Vitals

Target metrics for optimal performance:

- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

## 🐛 Troubleshooting

### Animations not running

- Check browser DevTools for warnings
- Verify Framer Motion is installed: `npm list framer-motion`
- Clear cache: `npm run build && npm run dev`

### Performance issues

- Reduce animation complexity on mobile
- Enable GPU acceleration with `will-change`
- Use Chrome DevTools Performance tab to profile

### Custom cursor not showing

- Custom cursor is disabled on mobile (coarse pointer)
- Check browser cursor CSS settings

## 📝 License

This project is open source and available under the MIT License.

## 💡 Tips & Best Practices

1. **Mobile First** - Test on mobile early in development
2. **Accessibility** - Always include keyboard navigation
3. **Performance** - Monitor Core Web Vitals regularly
4. **Animations** - Keep animations under 600ms for responsiveness
5. **Content** - Keep copy concise and results-oriented

---

Built with ❤️ using React, Tailwind CSS, and Framer Motion
