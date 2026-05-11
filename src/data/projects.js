import projectImage from '../assets/project.png';

export const projects = [
  {
    title: 'EasyBuy - Full Stack E-Commerce Platform',
    description:
      'I built EasyBuy because I wanted a real e-commerce project with the messy parts left in: customers, sellers, admins, orders, payments, webhooks, caching, background jobs, and deployment. The interesting work was not the product grid. It was making checkout, order state, and database access behave.',
    tech: ['Python', 'Django', 'React.js', 'Tailwind CSS', 'MySQL', 'AWS EC2/RDS/S3', 'Redis', 'Celery', 'Razorpay', 'Cloudflare Workers', 'OpenAI API', 'GitHub Actions'],
    features: [
      'I guarded payment updates with select_for_update because duplicate success paths are not a fun surprise',
      'I reduced database queries by 42% through Redis caching and ORM cleanup',
      'I moved notifications to Celery so the order response did not wait for side quests',
      'I verified Razorpay webhooks with HMAC signatures instead of trusting happy-path payloads',
      'I added a product-aware AI chatbot using OpenAI API and Cloudflare Workers',
      'I deployed it with GitHub Actions, AWS EC2, Gunicorn, Nginx, RDS, and S3',
    ],
    image: projectImage,
    github: 'https://github.com/AkashTomy174/easybuy',
    demo: 'https://easybuy.akashtomy.com/',
    featured: true,
  },
];
