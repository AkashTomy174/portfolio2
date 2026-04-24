export const projects = [
  {
    title: 'EasyBuy — Multi-Vendor Marketplace',
    description:
      'Complete e-commerce platform with seller onboarding, real-time inventory, dynamic pricing, and coupon system. Production deployment on AWS with MySQL, Redis caching, and AI-powered chatbot.',
    tech: ['Django 6.0', 'React', 'Tailwind CSS', 'MySQL', 'Redis', 'Razorpay', 'Twilio', 'OpenAI'],
    features: [
      'Multi-vendor marketplace with inventory management',
      'Payment gateway (12+ payment methods)',
      'AI shopping assistant (GPT-4 with persistence)',
      'Notification system (Email, WhatsApp, In-app)',
      'Admin dashboard with analytics',
    ],
    image:
      'https://images.unsplash.com/photo-1557821552-17105176677c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80',
    github: '#',
    demo: 'https://easybuy.akashtomy.com/',
    featured: true,
  },
  {
    title: 'Django Performance Suite',
    description:
      'Internal optimization suite managing Redis caching architectures, database query profiling, and high-throughput signal-driven events across production Django applications.',
    tech: ['Python', 'Django', 'Redis', 'Celery', 'MySQL'],
    features: [
      'Namespace versioning for cache invalidation',
      'Query optimization & profiling tools',
      'Asynchronous background task workers',
    ],
    image:
      'https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80',
    github: '#',
    demo: '#',
    featured: false,
  },
  {
    title: 'Redis Caching Architecture',
    description:
      'Sophisticated caching layer with namespace versioning, TTL management, and connection pooling for high-traffic Django applications serving 10K+ active users.',
    tech: ['Redis', 'Python', 'Django', 'Cloudflare'],
    features: [
      'Namespace-based cache versioning',
      'Connection pooling & TTL strategies',
      'Performance monitoring dashboard',
    ],
    image:
      'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80',
    github: '#',
    demo: '#',
    featured: false,
  },
];
