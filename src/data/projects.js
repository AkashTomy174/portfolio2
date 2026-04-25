export const projects = [
  {
    title: 'EasyBuy — Full Stack E-Commerce Platform',
    description:
      'Multi-role e-commerce platform (Customer, Seller, Admin) deployed on AWS. Built with a focus on payment consistency, concurrency safety, and performance — cutting DB queries by 42% and keeping order responses under 300ms.',
    tech: ['Python', 'Django', 'React.js', 'Tailwind CSS', 'MySQL', 'AWS EC2/RDS/S3', 'Redis', 'Celery', 'Razorpay', 'Cloudflare Workers', 'OpenAI API', 'GitHub Actions'],
    features: [
      'Concurrent-safe payments using select_for_update — zero duplicate transactions',
      'Cut DB queries by 42% (36 → 21) via Redis caching + ORM optimisation',
      'Celery async workers for notifications keeping order responses under 300ms',
      'Razorpay integration with HMAC webhook signature verification',
      'Product-aware AI chatbot using OpenAI API + Cloudflare Workers',
      'Zero-downtime CI/CD via GitHub Actions → AWS EC2 with Gunicorn + Nginx',
    ],
    image:
      'https://images.unsplash.com/photo-1557821552-17105176677c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80',
    github: 'https://github.com/AkashTomy174/easybuy',
    demo: 'https://easybuy.akashtomy.com/',
    featured: true,
  },
];
