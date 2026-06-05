// neowx-live.js
// -----------------------------------------------------------------------------
// Keeps the header/footer "chrome" current on NON-current pages (yesterday,
// week, month, year, archive, and the frozen month-YYYY-MM / year-YYYY summary
// pages). Those pages are static HTML that weewx may never rebuild, so their
// server-rendered date / almanac / versions would otherwise stay frozen at
// build time.
//
// On load we fetch live.json (regenerated every report cycle) and overwrite the
// id'd nodes. If the fetch fails, the server-rendered values simply remain as a
// graceful fallback.
//
// Gate: #header-date only exists on non-current pages (the current page uses
// #current-date), so its presence is our "this is a non-current page" signal.
(function () {
    'use strict';

    var dateNode = document.getElementById('header-date');
    if (!dateNode) {
        return; // current page (or header not present) — nothing to do
    }

    var MOON_ICONS = [
        'wi-moon-new',                 // 0
        'wi-moon-waxing-crescent-4',   // 1
        'wi-moon-first-quarter',       // 2
        'wi-moon-waxing-gibbous-4',    // 3
        'wi-moon-full',                // 4
        'wi-moon-waning-gibbous-4',    // 5
        'wi-moon-third-quarter',       // 6
        'wi-moon-waning-crescent-4'    // 7
    ];
    var MOON_ICON_DEFAULT = 'wi-moon-waning-crescent-3';

    function setText(id, value) {
        if (value === undefined || value === null) { return; }
        var el = document.getElementById(id);
        if (el) { el.textContent = value; }
    }

    function revealGeneratedIcon(today) {
        // Show the calendar icon only when this page was built on a different
        // day than "today". The tooltip (build datetime) is baked server-side.
        var status = document.getElementById('generated-status');
        if (!status) { return; }
        var built = status.getAttribute('data-generated-date');
        if (built && today && built !== today) {
            status.style.display = '';
        }
    }

    function applyAlmanac(alm) {
        if (!alm) { return; }

        // Sun: pyephem (hasExtras) layout uses #alm-sun-rise/#alm-sun-set;
        // the basic layout uses #alm-sunrise/#alm-sunset. Fill whichever exists.
        if (document.getElementById('alm-sun-rise') && alm.sun) {
            setText('alm-sun-rise', alm.sun.rise);
            setText('alm-sun-set', alm.sun.set);
        } else {
            setText('alm-sunrise', alm.sunrise);
            setText('alm-sunset', alm.sunset);
        }

        // Moon (pyephem only)
        if (alm.moon) {
            setText('alm-moon-rise', alm.moon.rise);
            setText('alm-moon-set', alm.moon.set);
        }
        setText('alm-moon-fullness', alm.moon_fullness);

        if (alm.moon_index !== undefined && alm.moon_index !== null) {
            var iconHost = document.getElementById('alm-moon-icon');
            if (iconHost) {
                var cls = MOON_ICONS[alm.moon_index] || MOON_ICON_DEFAULT;
                // Build via DOM methods (cls is from a fixed allowlist) — no innerHTML.
                var icon = document.createElement('i');
                icon.className = 'wi ' + cls + ' mr-1';
                icon.style.opacity = '.75';
                iconHost.textContent = '';
                iconHost.appendChild(icon);
            }
        }

        if (alm.moon_phase) {
            var phaseHost = document.getElementById('alm-moon-phase');
            if (phaseHost) {
                // Bootstrap moves the original title into data-original-title
                // once the tooltip is initialised, so update both.
                phaseHost.setAttribute('title', alm.moon_phase);
                phaseHost.setAttribute('data-original-title', alm.moon_phase);
            }
        }
    }

    function apply(data) {
        setText('header-date', data.date);
        setText('footer-year', data.year);
        if (data.versions) {
            setText('footer-weewx-version', data.versions.weewx);
            setText('footer-skin-version', data.versions.skin);
        }
        applyAlmanac(data.almanac);
        revealGeneratedIcon(data.today);
    }

    function todayBrowserLocal() {
        // Fallback for the calendar icon when live.json can't be fetched.
        var d = new Date();
        function pad(n) { return (n < 10 ? '0' : '') + n; }
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }

    function run() {
        fetch('live.json?_=' + new Date().getTime(), { cache: 'no-store' })
            .then(function (resp) {
                if (!resp.ok) { throw new Error('live.json HTTP ' + resp.status); }
                return resp.json();
            })
            .then(apply)
            .catch(function () {
                // Keep server-rendered fallbacks; still flag a stale build date
                // using the browser's local date as a best effort.
                revealGeneratedIcon(todayBrowserLocal());
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
})();
