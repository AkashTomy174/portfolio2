# Deployment Guide

## Quick Start

Choose your preferred deployment platform and follow the steps below.

---

## 🚀 **Vercel** (Recommended)

### Setup

1. Push your project to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Select your GitHub repository
5. Vercel auto-detects Vite configuration
6. Click "Deploy"

### Configuration (Automatic)

Vercel automatically:
- Detects Vite build configuration
- Sets build command to `npm run build`
- Sets output directory to `dist`
- Enables auto-deployment on git push

### Custom Domain

1. In Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Update your domain registrar's DNS to point to Vercel

---

## 🌐 **Netlify**

### Setup via Git

1. Push to GitHub
2. Go to [netlify.com](https://netlify.com)
3. Click "New site from Git"
4. Connect GitHub account
5. Select repository
6. Netlify auto-detects Vite settings
7. Click "Deploy"

### Setup via Manual Upload

```bash
# Build locally
npm run build

# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

### Configuration File

Create `netlify.toml` in project root:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[dev]
  command = "npm run dev"
  port = 3000

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## 📦 **GitHub Pages**

### Setup

1. Create a GitHub repository named `yourname.github.io`
2. Clone and cd into it
3. Copy your portfolio files
4. Create `vite.config.js` entry if missing

### Update Base URL

In `vite.config.js`:

```js
export default {
  base: '/yourname.github.io/', // or '/' if custom domain
  // ... rest of config
}
```

### Deploy

```bash
# Build
npm run build

# Initialize git (if needed)
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourname/yourname.github.io.git
git push -u origin main

# Push dist folder to gh-pages branch
git push origin main
# Create gh-pages branch if needed
git checkout -b gh-pages
git push -u origin gh-pages
```

### Or use gh-pages package:

```bash
npm install --save-dev gh-pages
```

Add to `package.json`:

```json
"scripts": {
  "deploy": "npm run build && gh-pages -d dist"
}
```

Run: `npm run deploy`

---

## 🐳 **Docker** (Self-Hosted)

### Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine
RUN npm install -g serve
WORKDIR /app
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Build and Run

```bash
# Build image
docker build -t portfolio .

# Run container
docker run -p 3000:3000 portfolio
```

---

## 📋 **Pre-Deployment Checklist**

- [ ] Update personal information (name, email, links)
- [ ] Replace placeholder images with real photos/logos
- [ ] Update project descriptions and links
- [ ] Test all links (internal and external)
- [ ] Verify animations on target devices
- [ ] Check mobile responsiveness
- [ ] Optimize images for web
- [ ] Update social media links
- [ ] Test form submissions (if applicable)
- [ ] Verify Google Analytics setup (if using)
- [ ] Test SEO meta tags
- [ ] Run Lighthouse audit

---

## 🔍 **SEO Optimization**

### Meta Tags

Update `index.html`:

```html
<meta name="description" content="Full-Stack Developer specializing in Django & React">
<meta name="keywords" content="developer, portfolio, react, django, ecommerce">
<meta name="author" content="Your Name">
<meta property="og:title" content="Your Name - Developer">
<meta property="og:description" content="Your tagline">
<meta property="og:image" content="https://yoursite.com/og-image.png">
```

### Sitemap

Create `public/sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yoursite.com/</loc>
    <lastmod>2024-01-15</lastmod>
  </url>
</urlset>
```

### robots.txt

Create `public/robots.txt`:

```
User-agent: *
Allow: /
Sitemap: https://yoursite.com/sitemap.xml
```

---

## 📊 **Analytics Setup**

### Google Analytics

Add to `index.html` in `<head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
```

---

## 🔒 **Security Headers**

### For Vercel

Add `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

---

## 🧪 **Testing Before Deploy**

```bash
# Check build
npm run build

# Preview build locally
npm run preview

# Run linter
npm run lint

# Check TypeScript (if using)
npm run type-check
```

---

## ⚡ **Performance Tips**

1. **Optimize Images** - Use tools like TinyPNG or ImageOptim
2. **Enable Compression** - Most platforms do this automatically
3. **Minimize Bundle** - Check with `npm run build` output
4. **Cache Headers** - Configure on your hosting platform
5. **CDN** - Use platform's built-in CDN (Vercel, Netlify)

---

## 🆘 **Troubleshooting**

### Build fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Asset paths broken

- Check `vite.config.js` `base` setting
- Verify relative paths in imports
- Check public folder assets

### Custom domain not working

- Wait 24-48 hours for DNS propagation
- Check domain registrar DNS settings
- Verify CNAME record points to hosting provider

---

## 📞 **Support**

- **Vercel**: [vercel.com/support](https://vercel.com/support)
- **Netlify**: [docs.netlify.com](https://docs.netlify.com)
- **GitHub**: [docs.github.com/pages](https://docs.github.com/pages)

---

Happy deploying! 🎉
