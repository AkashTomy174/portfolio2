const NotFoundPage = () => (
  <main className="relative z-10 flex min-h-screen items-center justify-center px-6">
    <div className="hard-panel max-w-xl rotate-[-1deg] bg-primary-dark p-8">
      <div className="inline-block bg-accent-purple px-3 py-1 font-mono text-xs font-black uppercase tracking-widest text-accent-dark">
        404 / misplaced route
      </div>
      <h1 className="mt-6 text-5xl font-extralight leading-none tracking-tight text-accent-dark md:text-7xl">
        I did not build this page.
        <span className="font-black"> Yet.</span>
      </h1>
      <p className="mt-6 text-base leading-relaxed text-accent-gray">
        Either the URL wandered off, or I forgot to make this part. Both are believable.
      </p>
      <a href="/" className="interactive hover-scrape mt-8 inline-block border border-accent-dark bg-accent-dark px-5 py-3 text-sm font-black uppercase tracking-widest text-primary-dark">
        back to the useful page
      </a>
    </div>
  </main>
);

export default NotFoundPage;
