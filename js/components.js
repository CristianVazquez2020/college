(function () {
    const script = document.currentScript;
    const base = script ? (script.getAttribute('data-base') || '') : '';

    const isHome = window.location.pathname.endsWith('index.html')
                || window.location.pathname.endsWith('/');

    const header = `
        <header>
            <div class="header-inner">
                <a class="site-title" href="${base}index.html">
                    COURSE <span class="accent">CONTENT</span>
                </a>
                <p class="site-subtitle"> by Cristian Vazquez </p> <!-- &mdash; Personal Reference Site</p>-->
            </div>
        </header>
        <nav>
            <div class="nav-inner">
                <a href="${base}index.html"${isHome ? ' class="active"' : ''}>Home</a>
            </div>
        </nav>
        <div class="disclaimer-bar">
            <strong>Note:</strong> This is a personal reference site and is not affiliated with or endorsed by Allan Hancock College.
        </div>
    `;

    const footer = `
        <footer>
            <p>&copy; 2026 Cristian Vazquez </p> <!-- &mdash; Personal Reference Site</p> -->
        </footer>
    `;

    const headerEl = document.getElementById('site-header');
    const footerEl = document.getElementById('site-footer');

    if (headerEl) headerEl.outerHTML = header;
    if (footerEl) footerEl.outerHTML = footer;
})();
