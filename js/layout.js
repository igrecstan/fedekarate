(function () {
    function getPartialsBase() {
        var b =
            document.body.getAttribute('data-partials-base') ||
            document.documentElement.getAttribute('data-partials-base') ||
            '';
        if (!b) return '';
        if (b.slice(-1) !== '/') b += '/';
        return b;
    }

    function rewriteRelativeLinks(container, base) {
        if (!base || !container) return;
        container.querySelectorAll('a[href]').forEach(function (a) {
            var h = a.getAttribute('href');
            if (!h || h.indexOf('://') !== -1 || h.startsWith('mailto:') || h.startsWith('tel:')) return;
            if (h.charAt(0) === '/') return;
            if (h.indexOf('../') === 0) return;
            a.setAttribute('href', base + h);
        });
    }

    function loadPartial(url, containerId) {
        return fetch(url)
            .then(function (r) {
                if (!r.ok) throw new Error(url + ' : ' + r.status);
                return r.text();
            })
            .then(function (html) {
                var el = document.getElementById(containerId);
                if (el) el.innerHTML = html;
            });
    }

    function initNav() {
        var mobileBtn = document.getElementById('mobileMenu');
        var navLinks = document.getElementById('navLinks');
        if (mobileBtn && navLinks) {
            mobileBtn.addEventListener('click', function () {
                navLinks.classList.toggle('active');
            });
        }
        document.querySelectorAll('.nav-links a').forEach(function (link) {
            link.addEventListener('click', function () {
                if (navLinks) navLinks.classList.remove('active');
            });
        });
        var path = window.location.pathname.replace(/\\/g, '/').toLowerCase();
        document.querySelectorAll('.nav-links a[aria-current="page"]').forEach(function (a) {
            a.removeAttribute('aria-current');
        });
        if (path.indexOf('espace-club') !== -1) {
            var espace = document.querySelector('.nav-links a[href*="espace-club"]');
            if (espace) espace.setAttribute('aria-current', 'page');
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var base = getPartialsBase();
        var hUrl = base + 'header.html';
        var fUrl = base + 'footer.html';
        Promise.all([loadPartial(hUrl, 'site-header'), loadPartial(fUrl, 'site-footer')])
            .then(function () {
                rewriteRelativeLinks(document.getElementById('site-header'), base);
            })
            .then(initNav)
            .catch(function (err) {
                console.error('Chargement header/footer :', err);
            });
    });
})();
