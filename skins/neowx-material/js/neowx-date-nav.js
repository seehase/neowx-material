// neowx-date-nav.js
// -----------------------------------------------------------------------------
// Interactive Material Date, Week, Month, and Year navigation pickers for
// NeoWX Material skin.
// Handles dropdown menus, strict date bounds [archive_start_date, archive_stop_date],
// and proactive 404 verification before navigation.
(function ($) {
    'use strict';

    if (!$) return;

    function pad2(n) {
        return (n < 10 ? '0' : '') + n;
    }

    function formatDateIso(d) {
        return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
    }

    function parseDateIso(str) {
        if (!str) return null;
        var parts = str.split('-');
        if (parts.length < 3) return null;
        return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    }

    function getIsoWeekRange(year, week) {
        var simple = new Date(year, 0, 4);
        var dayOfWeek = simple.getDay() || 7;
        var monday = new Date(simple.getTime() + ((week - 1) * 7 + (1 - dayOfWeek)) * 86400000);
        var sunday = new Date(monday.getTime() + 6 * 86400000);
        return { start: monday, end: sunday };
    }

    function getIsoWeeksInYear(year) {
        var d = new Date(Date.UTC(year, 11, 28));
        var dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        var yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }

    function getLocalizedMonthNames() {
        if (typeof moment !== 'undefined' && moment.monthsShort) {
            return moment.monthsShort();
        }
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    }

    function getLocalizedWeekdayNames() {
        if (typeof moment !== 'undefined' && moment.weekdaysMin) {
            var minDays = moment.weekdaysMin(); // Sunday is 0
            // Reorder to Monday-first: Mon (1) to Sun (0)
            return [minDays[1], minDays[2], minDays[3], minDays[4], minDays[5], minDays[6], minDays[0]];
        }
        return ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
    }

    function sanitizeRelativePath(path) {
        if (typeof path !== 'string') return '';
        var cleaned = path.trim();
        // Disallow external schemes, absolute URLs, or protocol-relative paths
        if (/^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|\/\/)/.test(cleaned)) {
            return '';
        }
        // Allow only characters valid in safe relative path segments
        return cleaned.replace(/[^a-zA-Z0-9_\-\.\/]/g, '');
    }

    var RANGE_KEY_PATTERNS = {
        year: /^\d{4}$/,
        month: /^\d{4}-(?:0[1-9]|1[0-2])$/,
        week: /^\d{4}-(?:0[1-9]|[1-4]\d|5[0-3])$/,
        day: /^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$/
    };

    function normalizeRanges(rawList, scale) {
        if (!Array.isArray(rawList)) return null;
        var pat = RANGE_KEY_PATTERNS[scale];
        if (!pat) return null;
        var out = [];
        for (var i = 0; i < rawList.length; i++) {
            var pair = rawList[i];
            if (!Array.isArray(pair) || pair.length !== 2) continue;
            var s = String(pair[0] || '');
            var e = String(pair[1] || '');
            if (pat.test(s) && pat.test(e) && s <= e) {
                out.push([s, e]);
            }
        }
        out.sort(function (a, b) {
            return a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0);
        });
        return out;
    }

    function normalizeArchiveAvailable(raw) {
        if (!raw || typeof raw !== 'object') return null;
        var years = normalizeRanges(raw.years, 'year');
        var months = normalizeRanges(raw.months, 'month');
        var weeks = normalizeRanges(raw.weeks, 'week');
        var days = normalizeRanges(raw.days, 'day');
        if (!years && !months && !weeks && !days) return null;
        return {
            years: years,
            months: months,
            weeks: weeks,
            days: days
        };
    }

    function isKeyInRanges(key, ranges) {
        if (!ranges || !ranges.length) return false;
        for (var i = 0; i < ranges.length; i++) {
            if (key >= ranges[i][0] && key <= ranges[i][1]) return true;
        }
        return false;
    }

    function getAvailableYearsFromRanges(ranges, ensureYear) {
        var yearMap = {};
        if (ranges) {
            for (var i = 0; i < ranges.length; i++) {
                var sy = parseInt(ranges[i][0].slice(0, 4), 10);
                var ey = parseInt(ranges[i][1].slice(0, 4), 10);
                if (!isNaN(sy) && !isNaN(ey)) {
                    for (var y = sy; y <= ey; y++) {
                        yearMap[y] = true;
                    }
                }
            }
        }
        if (typeof ensureYear === 'number' && !isNaN(ensureYear) && ensureYear > 1900) {
            yearMap[ensureYear] = true;
        }
        return Object.keys(yearMap).map(function (k) {
            return parseInt(k, 10);
        }).sort(function (a, b) { return a - b; });
    }

    function hasAnyDayInMonth(year, month, dayRanges) {
        if (!dayRanges || !dayRanges.length) return false;
        var mStr = pad2(month);
        var monthStart = year + '-' + mStr + '-01';
        var daysInMonth = new Date(year, month, 0).getDate();
        var monthEnd = year + '-' + mStr + '-' + pad2(daysInMonth);
        for (var i = 0; i < dayRanges.length; i++) {
            if (dayRanges[i][0] <= monthEnd && dayRanges[i][1] >= monthStart) {
                return true;
            }
        }
        return false;
    }

    function findPrevMonthWithDays(year, month, dayRanges, yearsAsc) {
        for (var i = yearsAsc.length - 1; i >= 0; i--) {
            var y = yearsAsc[i];
            if (y > year) continue;
            var startMo = (y === year) ? (month - 1) : 12;
            for (var m = startMo; m >= 1; m--) {
                if (hasAnyDayInMonth(y, m, dayRanges)) {
                    return { year: y, month: m };
                }
            }
        }
        return null;
    }

    function findNextMonthWithDays(year, month, dayRanges, yearsAsc) {
        for (var i = 0; i < yearsAsc.length; i++) {
            var y = yearsAsc[i];
            if (y < year) continue;
            var startMo = (y === year) ? (month + 1) : 1;
            for (var m = startMo; m <= 12; m++) {
                if (hasAnyDayInMonth(y, m, dayRanges)) {
                    return { year: y, month: m };
                }
            }
        }
        return null;
    }

    function decrementKey(key, scale) {
        if (scale === 'year') {
            return String(parseInt(key, 10) - 1);
        }
        if (scale === 'month') {
            var mp = key.split('-');
            var my = parseInt(mp[0], 10);
            var mm = parseInt(mp[1], 10);
            return (mm > 1 ? my : (my - 1)) + '-' + pad2(mm > 1 ? (mm - 1) : 12);
        }
        if (scale === 'week') {
            var wp = key.split('-');
            return wp[0] + '-' + pad2(parseInt(wp[1], 10) - 1);
        }
        if (scale === 'day') {
            var dp = key.split('-');
            var dt = new Date(parseInt(dp[0], 10), parseInt(dp[1], 10) - 1, parseInt(dp[2], 10) - 1);
            return formatDateIso(dt);
        }
        return null;
    }

    function incrementKey(key, scale) {
        if (scale === 'year') {
            return String(parseInt(key, 10) + 1);
        }
        if (scale === 'month') {
            var mp = key.split('-');
            var my = parseInt(mp[0], 10);
            var mm = parseInt(mp[1], 10);
            return (mm < 12 ? my : (my + 1)) + '-' + pad2(mm < 12 ? (mm + 1) : 1);
        }
        if (scale === 'week') {
            var wp = key.split('-');
            return wp[0] + '-' + pad2(parseInt(wp[1], 10) + 1);
        }
        if (scale === 'day') {
            var dp = key.split('-');
            var dt = new Date(parseInt(dp[0], 10), parseInt(dp[1], 10) - 1, parseInt(dp[2], 10) + 1);
            return formatDateIso(dt);
        }
        return null;
    }

    function findPrevAvailableKey(currentKey, ranges, scale) {
        if (!ranges || !ranges.length) return null;
        for (var i = ranges.length - 1; i >= 0; i--) {
            if (ranges[i][0] < currentKey) {
                if (ranges[i][1] < currentKey) {
                    return ranges[i][1];
                }
                return decrementKey(currentKey, scale);
            }
        }
        return null;
    }

    function findNextAvailableKey(currentKey, ranges, scale) {
        if (!ranges || !ranges.length) return null;
        for (var i = 0; i < ranges.length; i++) {
            if (ranges[i][1] > currentKey) {
                if (ranges[i][0] > currentKey) {
                    return ranges[i][0];
                }
                return incrementKey(currentKey, scale);
            }
        }
        return null;
    }

    function DateNavController() {
        this.$hub = $('#nwm-nav-hub');
        this.$container = $('#nx-picker-container');
        this.$dropdown = $('#nx-picker-dropdown');
        if (!this.$container.length || !this.$dropdown.length) return;

        var rawBasePath = (typeof window.NX_BASE_PATH === 'string')
            ? window.NX_BASE_PATH
            : (this.$hub.attr('data-base-path') || '');
        this.basePath = sanitizeRelativePath(rawBasePath);

        this.page = (this.$hub.attr('data-page') || '').replace(/[^a-zA-Z0-9_\-]/g, '');
        this.activeNav = (this.$hub.attr('data-active-nav') || '').replace(/[^a-zA-Z0-9_\-]/g, '');

        this.contextYear = parseInt(this.$hub.attr('data-context-year') || new Date().getFullYear(), 10);
        this.contextMonth = parseInt(this.$hub.attr('data-context-month') || (new Date().getMonth() + 1), 10);
        this.contextWeek = parseInt(this.$hub.attr('data-context-week') || 1, 10);

        var rawDay = this.$hub.attr('data-context-day') || '';
        this.contextDay = /^\d{4}-\d{2}-\d{2}$/.test(rawDay) ? rawDay : formatDateIso(new Date());

        var rawStart = (typeof window.NX_START_DATE === 'string')
            ? window.NX_START_DATE
            : (this.$hub.attr('data-start-date') || '');
        this.startDateStr = /^\d{4}-\d{2}-\d{2}$/.test(rawStart) ? rawStart : '1970-01-01';

        var rawStop = (typeof window.NX_STOP_DATE === 'string')
            ? window.NX_STOP_DATE
            : (this.$hub.attr('data-stop-date') || '');
        this.stopDateStr = /^\d{4}-\d{2}-\d{2}$/.test(rawStop) ? rawStop : formatDateIso(new Date());

        this.startDate = parseDateIso(this.startDateStr);
        this.stopDate = parseDateIso(this.stopDateStr);

        var rawStartYear = parseInt(this.$hub.attr('data-start-year'), 10);
        this.startYear = this.startDate
            ? this.startDate.getFullYear()
            : ((!isNaN(rawStartYear) && rawStartYear > 1900) ? rawStartYear : 1970);

        var rawStopYear = parseInt(this.$hub.attr('data-stop-year'), 10);
        this.stopYear = this.stopDate
            ? this.stopDate.getFullYear()
            : ((!isNaN(rawStopYear) && rawStopYear > 1900) ? rawStopYear : new Date().getFullYear());

        this.labelPrev = this.$hub.attr('data-label-prev') || 'Previous';
        this.labelNext = this.$hub.attr('data-label-next') || 'Next';
        this.labelNoEarlier = this.$hub.attr('data-label-no-earlier') || 'Earliest available record reached';
        this.labelNoLater = this.$hub.attr('data-label-no-later') || 'Latest available record reached';

        this.available = normalizeArchiveAvailable(window.NX_ARCHIVE_AVAILABLE);
        this.yearPickerTitle = 'Year';

        this.redirectTimer = null;
        this.init();
    }

    DateNavController.prototype.init = function () {
        var self = this;

        // Prevent clicking inside picker controls from accidentally closing the Bootstrap dropdown
        this.$dropdown.on('click', function (e) {
            if ($(e.target).closest('a[href]').length) {
                return; // Let navigation links proceed to interceptor
            }
            e.stopPropagation();
        });

        // Intercept navigation clicks for proactive 404 checking
        $(document).on('click', '.nwm-stepper-group a[href], .nwm-picker-dropdown a[href]', function (e) {
            var $link = $(this);
            var href = $link.attr('href');
            var normalizedHref = (href || '').trim().toLowerCase();
            if (!href || href === '#' ||
                normalizedHref.indexOf('javascript:') === 0 ||
                normalizedHref.indexOf('data:') === 0 ||
                normalizedHref.indexOf('vbscript:') === 0) return;
            if ($link.hasClass('disabled') || $link.is(':disabled')) {
                e.preventDefault();
                return;
            }
            e.preventDefault();
            self.navigateWithCheck(href);
        });

        // Initialize picker type
        if (this.$dropdown.hasClass('nwm-picker-calendar')) {
            this.initDayPicker();
        } else if (this.$dropdown.hasClass('nwm-picker-week')) {
            this.initWeekPicker();
        } else if (this.$dropdown.hasClass('nwm-picker-month')) {
            this.initMonthPicker();
        } else if (this.$dropdown.hasClass('nwm-picker-year')) {
            this.initYearPicker();
        }
        this.syncStepperButtons();

        // Global export for nxJumpDate and external triggers
        window.nxNavigateWithCheck = function (url) {
            self.navigateWithCheck(url);
        };

        // Atomic updater for per-scale disk-backed availability from live.json
        window.nxUpdateArchiveAvailability = function (rawAvailable, newStopDateStr) {
            var normalized = normalizeArchiveAvailable(rawAvailable);
            if (normalized) {
                self.available = normalized;
            }
            if (newStopDateStr && /^\d{4}-\d{2}-\d{2}$/.test(newStopDateStr)) {
                self.stopDateStr = newStopDateStr;
                self.stopDate = parseDateIso(newStopDateStr);
                if (self.stopDate) {
                    self.stopYear = self.stopDate.getFullYear();
                }
            }
            self.reRenderActivePicker();
        };

        // Legacy scalar updaters (fallback for older live.json without archive_available)
        window.nxUpdateStartDate = function (newStartDateStr) {
            if (self.available) return;
            if (!newStartDateStr || !/^\d{4}-\d{2}-\d{2}$/.test(newStartDateStr)) return;
            self.startDateStr = newStartDateStr;
            self.startDate = parseDateIso(newStartDateStr);
            if (self.startDate) {
                self.startYear = self.startDate.getFullYear();
            }
            self.reRenderActivePicker();
        };

        window.nxUpdateStopDate = function (newStopDateStr) {
            if (!newStopDateStr || !/^\d{4}-\d{2}-\d{2}$/.test(newStopDateStr)) return;
            self.stopDateStr = newStopDateStr;
            self.stopDate = parseDateIso(newStopDateStr);
            if (self.stopDate) {
                self.stopYear = self.stopDate.getFullYear();
            }
            self.reRenderActivePicker();
        };
    };

    DateNavController.prototype.getActiveScale = function () {
        if (this.$dropdown.hasClass('nwm-picker-calendar')) return 'day';
        if (this.$dropdown.hasClass('nwm-picker-week')) return 'week';
        if (this.$dropdown.hasClass('nwm-picker-month')) return 'month';
        if (this.$dropdown.hasClass('nwm-picker-year')) return 'year';
        return null;
    };

    DateNavController.prototype.getRangesForScale = function (scale) {
        if (!this.available) return null;
        if (scale === 'day') return this.available.days;
        if (scale === 'week') return this.available.weeks;
        if (scale === 'month') return this.available.months;
        if (scale === 'year') return this.available.years;
        return null;
    };

    DateNavController.prototype.buildUrlForKey = function (key, scale) {
        if (!key) return '';
        if (scale === 'day') {
            var liveDayStr = this.stopDateStr || formatDateIso(new Date());
            if (key === liveDayStr) {
                return this.basePath + 'index.html';
            }
            return this.basePath + 'archive/' + key.slice(0, 4) + '/days/day-' + key + '.html';
        }
        if (scale === 'week') {
            return this.basePath + 'archive/' + key.slice(0, 4) + '/weeks/week-' + key + '.html';
        }
        if (scale === 'month') {
            return this.basePath + 'archive/' + key.slice(0, 4) + '/months/month-' + key + '.html';
        }
        if (scale === 'year') {
            return this.basePath + 'archive/' + key + '/year-' + key + '.html';
        }
        return '';
    };

    DateNavController.prototype.reRenderActivePicker = function () {
        if (this.$dropdown.hasClass('nwm-picker-calendar') && this.viewCalendarYear) {
            this.renderCalendarPicker(this.viewCalendarYear, this.viewCalendarMonth);
        } else if (this.$dropdown.hasClass('nwm-picker-month') && this.viewMonthYear) {
            this.renderMonthPicker(this.viewMonthYear);
        } else if (this.$dropdown.hasClass('nwm-picker-week') && this.viewWeekYear) {
            this.renderWeekPicker(this.viewWeekYear);
        } else if (this.$dropdown.hasClass('nwm-picker-year')) {
            this.renderYearPicker();
        }
        this.syncStepperButtons();
    };

    DateNavController.prototype._replaceStepperSlot = function ($slot, url, direction) {
        if (!$slot || !$slot.length) return;
        var isPrev = (direction === 'prev');
        var iconClass = isPrev ? 'mdi mdi-chevron-left' : 'mdi mdi-chevron-right';

        if (url) {
            if ($slot.is('a') && $slot.attr('href') === url) return;
            var label = isPrev ? this.labelPrev : this.labelNext;
            if ($.fn.tooltip) {
                try { $slot.tooltip('dispose'); } catch (e) {}
            }
            var $link = $('<a>', {
                href: url,
                class: 'nwm-nav-btn',
                'data-toggle': 'tooltip',
                'data-placement': 'bottom',
                title: label,
                'aria-label': label
            }).append($('<i>', { class: iconClass }));
            $slot.replaceWith($link);
            if ($.fn.tooltip) {
                $link.tooltip();
            }
        } else {
            if ($slot.is('button.disabled')) return;
            var disabledLabel = isPrev ? this.labelNoEarlier : this.labelNoLater;
            if ($.fn.tooltip) {
                try { $slot.tooltip('dispose'); } catch (e) {}
            }
            var $btn = $('<button>', {
                type: 'button',
                class: 'nwm-nav-btn disabled',
                disabled: true,
                'data-toggle': 'tooltip',
                'data-placement': 'bottom',
                title: disabledLabel,
                'aria-label': disabledLabel
            }).append($('<i>', { class: iconClass }));
            $slot.replaceWith($btn);
            if ($.fn.tooltip) {
                $btn.tooltip();
            }
        }
    };

    // Dynamically syncs both Previous (<) and Next (>) stepper buttons against
    // per-scale archive_available ranges (or fallback stopDate bounds).
    DateNavController.prototype.syncStepperButtons = function () {
        var scale = this.getActiveScale();
        if (!scale) return;

        var isLivePage = (this.activeNav === 'current' || this.activeNav === 'live' || this.page === 'today');
        var $prevSlot = this.$container.prev('.nwm-nav-btn');
        var $nextSlot = this.$container.next('.nwm-nav-btn');
        var ranges = this.getRangesForScale(scale);

        if (ranges) {
            var currentKey = '';
            if (scale === 'day') {
                currentKey = this.contextDay;
            } else if (scale === 'week') {
                currentKey = this.contextYear + '-' + pad2(this.contextWeek);
            } else if (scale === 'month') {
                currentKey = this.contextYear + '-' + pad2(this.contextMonth);
            } else if (scale === 'year') {
                currentKey = String(this.contextYear);
            }

            var prevKey = findPrevAvailableKey(currentKey, ranges, scale);
            var nextKey = isLivePage ? null : findNextAvailableKey(currentKey, ranges, scale);

            this._replaceStepperSlot($prevSlot, this.buildUrlForKey(prevKey, scale), 'prev');
            this._replaceStepperSlot($nextSlot, this.buildUrlForKey(nextKey, scale), 'next');
            return;
        }

        // Fallback when archive_available is not present (legacy live.json):
        // keep enabling Next (>) on frozen archive pages once stopDate advances.
        if (!this.stopDate || isLivePage) return;
        if (!$nextSlot.length || !$nextSlot.is('button.disabled')) return;

        var nextUrl = '';
        if (scale === 'day') {
            var curDay = parseDateIso(this.contextDay);
            if (curDay) {
                var nextDay = new Date(curDay.getFullYear(), curDay.getMonth(), curDay.getDate() + 1);
                var nextDayIso = formatDateIso(nextDay);
                if (nextDayIso <= this.stopDateStr) {
                    nextUrl = (nextDayIso === this.stopDateStr)
                        ? (this.basePath + 'index.html')
                        : (this.basePath + 'archive/' + nextDay.getFullYear() + '/days/day-' + nextDayIso + '.html');
                }
            }
        } else if (scale === 'week') {
            var curWkRange = getIsoWeekRange(this.contextYear, this.contextWeek);
            var nextWkMon = new Date(curWkRange.start.getFullYear(), curWkRange.start.getMonth(), curWkRange.start.getDate() + 7);
            if (formatDateIso(nextWkMon) <= this.stopDateStr) {
                var d = new Date(Date.UTC(nextWkMon.getFullYear(), nextWkMon.getMonth(), nextWkMon.getDate()));
                var dayNum = d.getUTCDay() || 7;
                d.setUTCDate(d.getUTCDate() + 4 - dayNum);
                var isoYr = d.getUTCFullYear();
                var yearStart = new Date(Date.UTC(isoYr, 0, 1));
                var isoWk = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
                nextUrl = this.basePath + 'archive/' + isoYr + '/weeks/week-' + isoYr + '-' + pad2(isoWk) + '.html';
            }
        } else if (scale === 'month') {
            var nextMoYr = (this.contextMonth < 12) ? this.contextYear : (this.contextYear + 1);
            var nextMo = (this.contextMonth < 12) ? (this.contextMonth + 1) : 1;
            var nextMoFirstIso = nextMoYr + '-' + pad2(nextMo) + '-01';
            if (nextMoFirstIso <= this.stopDateStr) {
                nextUrl = this.basePath + 'archive/' + nextMoYr + '/months/month-' + nextMoYr + '-' + pad2(nextMo) + '.html';
            }
        } else if (scale === 'year') {
            var nextYr = this.contextYear + 1;
            if (nextYr <= this.stopYear) {
                nextUrl = this.basePath + 'archive/' + nextYr + '/year-' + nextYr + '.html';
            }
        }

        if (nextUrl) {
            this._replaceStepperSlot($nextSlot, nextUrl, 'next');
        }
    };

    // -------------------------------------------------------------------------
    // PROACTIVE 404 AVAILABILITY CHECK & NAVIGATION
    // -------------------------------------------------------------------------
    DateNavController.prototype.navigateWithCheck = function (url) {
        var normalizedUrl = (url || '').trim().toLowerCase();
        if (!url || url === '#' ||
            normalizedUrl.indexOf('javascript:') === 0 ||
            normalizedUrl.indexOf('data:') === 0 ||
            normalizedUrl.indexOf('vbscript:') === 0) return;
        var self = this;

        // If navigating to the station's current live date, always route to index.html
        var liveDayStr = this.stopDateStr || formatDateIso(new Date());
        if (liveDayStr && url.indexOf('day-' + liveDayStr + '.html') !== -1) {
            url = this.basePath + 'index.html';
        }

        // Direct navigation if file: protocol (local testing) or already targeting index.html
        if (window.location.protocol === 'file:' || url === (this.basePath + 'index.html') || url === 'index.html') {
            window.location.href = url;
            return;
        }

        // Only probe local paths
        try {
            var resolved = new URL(url, window.location.href);
            if (resolved.origin !== window.location.origin) {
                window.location.href = url;
                return;
            }
        } catch (e) {
            window.location.href = url;
            return;
        }

        // 1200ms timeout probe with AbortController
        var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
        var signal = controller ? controller.signal : undefined;
        var timer = setTimeout(function () {
            if (controller) controller.abort();
        }, 1200);

        fetch(url, { method: 'HEAD', signal: signal, cache: 'no-cache' })
            .then(function (res) {
                clearTimeout(timer);
                if (res.status === 404) {
                    self.showMissingPageModal(url);
                } else {
                    window.location.href = url;
                }
            })
            .catch(function () {
                clearTimeout(timer);
                // On abort, timeout, or network issue, proceed with standard navigation
                window.location.href = url;
            });
    };

    DateNavController.prototype.showMissingPageModal = function () {
        var $modal = $('#nwm-date-missing-modal');
        var basePath = this.basePath;

        if (!$modal.length || !$.fn.modal) {
            // Fallback if modal is not in DOM
            window.location.href = basePath + 'index.html';
            return;
        }

        var countdown = 3;
        var $countdownEl = $('#nwm-redirect-countdown');
        if ($countdownEl.length) {
            $countdownEl.text(countdown + 's');
        }

        if (this.redirectTimer) {
            clearInterval(this.redirectTimer);
            this.redirectTimer = null;
        }

        var self = this;
        this.redirectTimer = setInterval(function () {
            countdown--;
            if ($countdownEl.length) {
                $countdownEl.text(countdown + 's');
            }
            if (countdown <= 0) {
                clearInterval(self.redirectTimer);
                self.redirectTimer = null;
                window.location.href = basePath + 'index.html';
            }
        }, 1000);

        $modal.off('hidden.bs.modal.nx404').on('hidden.bs.modal.nx404', function () {
            if (self.redirectTimer) {
                clearInterval(self.redirectTimer);
                self.redirectTimer = null;
            }
        });

        $('#nwm-redirect-now-btn').attr('href', basePath + 'index.html');
        $modal.modal('show');
    };

    // -------------------------------------------------------------------------
    // YEAR PICKER
    // -------------------------------------------------------------------------
    DateNavController.prototype.initYearPicker = function () {
        var existingTitle = this.$dropdown.find('.nwm-picker-title').first().text().trim();
        if (existingTitle) {
            this.yearPickerTitle = existingTitle;
        }
        // Only re-render immediately if live availability is already present;
        // otherwise keep the server-rendered year grid until live.json arrives.
        if (this.available && this.available.years) {
            this.renderYearPicker();
        }
    };

    DateNavController.prototype.renderYearPicker = function () {
        var yearRanges = this.getRangesForScale('year');
        var yearsAsc;
        if (yearRanges) {
            yearsAsc = getAvailableYearsFromRanges(yearRanges, this.contextYear);
        } else {
            yearsAsc = [];
            for (var y = this.startYear; y <= this.stopYear; y++) {
                yearsAsc.push(y);
            }
            if (yearsAsc.indexOf(this.contextYear) === -1) {
                yearsAsc.push(this.contextYear);
                yearsAsc.sort(function (a, b) { return a - b; });
            }
        }

        var $header = $('<div>', { class: 'nwm-picker-header' })
            .append($('<span>', { class: 'nwm-picker-title', text: this.yearPickerTitle }));

        var $grid = $('<div>', { class: 'nwm-picker-grid-years' });
        for (var i = yearsAsc.length - 1; i >= 0; i--) {
            var yr = yearsAsc[i];
            var yrStr = String(yr);
            var isActive = (yr === this.contextYear);
            var url = this.basePath + 'archive/' + yrStr + '/year-' + yrStr + '.html';
            $grid.append($('<a>', {
                href: url,
                class: 'nwm-picker-cell' + (isActive ? ' active' : ''),
                text: yrStr
            }));
        }

        this.$dropdown.empty().append($header, $grid);
    };

    // -------------------------------------------------------------------------
    // MONTH PICKER
    // -------------------------------------------------------------------------
    DateNavController.prototype.initMonthPicker = function () {
        var self = this;
        this.viewMonthYear = this.contextYear;
        // Normalize picker button label to YYYY-MM even on previously generated archive pages
        $('#nx-picker-label').text(this.contextYear + '-' + pad2(this.contextMonth));
        this.renderMonthPicker(this.viewMonthYear);

        this.$dropdown.on('click', '[data-action="prev-year"]', function (e) {
            e.preventDefault();
            var yearsAsc = self._getMonthPickerYears();
            var idx = yearsAsc.indexOf(self.viewMonthYear);
            if (idx > 0) {
                self.viewMonthYear = yearsAsc[idx - 1];
                self.renderMonthPicker(self.viewMonthYear);
            }
        });

        this.$dropdown.on('click', '[data-action="next-year"]', function (e) {
            e.preventDefault();
            var yearsAsc = self._getMonthPickerYears();
            var idx = yearsAsc.indexOf(self.viewMonthYear);
            if (idx !== -1 && idx < yearsAsc.length - 1) {
                self.viewMonthYear = yearsAsc[idx + 1];
                self.renderMonthPicker(self.viewMonthYear);
            }
        });

        this.$dropdown.on('change', '#nx-mp-year-select', function () {
            self.viewMonthYear = parseInt($(this).val(), 10);
            self.renderMonthPicker(self.viewMonthYear);
        });
    };

    DateNavController.prototype._getMonthPickerYears = function () {
        var monthRanges = this.getRangesForScale('month');
        if (monthRanges) {
            return getAvailableYearsFromRanges(monthRanges, this.contextYear);
        }
        var yearsAsc = [];
        for (var y = this.startYear; y <= this.stopYear; y++) {
            yearsAsc.push(y);
        }
        if (yearsAsc.indexOf(this.contextYear) === -1) {
            yearsAsc.push(this.contextYear);
            yearsAsc.sort(function (a, b) { return a - b; });
        }
        return yearsAsc;
    };

    DateNavController.prototype.renderMonthPicker = function (year) {
        var monthNames = getLocalizedMonthNames();
        var monthRanges = this.getRangesForScale('month');
        var yearsAsc = this._getMonthPickerYears();

        if (yearsAsc.indexOf(year) === -1 && yearsAsc.length) {
            year = yearsAsc[yearsAsc.length - 1];
            this.viewMonthYear = year;
        }
        var yearIdx = yearsAsc.indexOf(year);

        // Header with year navigation
        var $header = $('<div>', { class: 'nwm-picker-header' });

        var $prevBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'prev-year',
            'aria-label': 'Previous year'
        }).append($('<i>', { class: 'mdi mdi-chevron-left' }));
        if (yearIdx <= 0) {
            $prevBtn.prop('disabled', true);
        }

        var $select = $('<select>', {
            class: 'nwm-picker-select',
            id: 'nx-mp-year-select',
            'aria-label': 'Year'
        });
        for (var yi = yearsAsc.length - 1; yi >= 0; yi--) {
            var y = yearsAsc[yi];
            var $opt = $('<option>', { value: y, text: y });
            if (y === year) {
                $opt.prop('selected', true);
            }
            $select.append($opt);
        }

        var $nextBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'next-year',
            'aria-label': 'Next year'
        }).append($('<i>', { class: 'mdi mdi-chevron-right' }));
        if (yearIdx === -1 || yearIdx >= yearsAsc.length - 1) {
            $nextBtn.prop('disabled', true);
        }

        $header.append($prevBtn, $select, $nextBtn);

        // 12 Months Grid
        var minMo = (year === this.startYear && this.startDate) ? (this.startDate.getMonth() + 1) : 1;
        var maxMo = (year === this.stopYear && this.stopDate) ? (this.stopDate.getMonth() + 1) : 12;

        var $grid = $('<div>', { class: 'nwm-picker-grid-months' });
        for (var m = 1; m <= 12; m++) {
            var mStr = pad2(m);
            var mName = monthNames[m - 1] || mStr;
            var monthKey = year + '-' + mStr;
            var isDisabled;

            if (monthRanges) {
                isDisabled = !isKeyInRanges(monthKey, monthRanges);
            } else {
                var firstDayStr = year + '-' + mStr + '-01';
                var daysInMonth = new Date(year, m, 0).getDate();
                var lastDayStr = year + '-' + mStr + '-' + pad2(daysInMonth);
                isDisabled = (m < minMo || m > maxMo) || (lastDayStr < this.startDateStr) || (firstDayStr > this.stopDateStr);
            }
            var isActive = (year === this.contextYear && m === this.contextMonth);

            if (isDisabled) {
                $grid.append($('<span>', {
                    class: 'nwm-picker-cell disabled',
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    title: 'No data',
                    text: mName
                }));
            } else {
                var url = this.basePath + 'archive/' + year + '/months/month-' + monthKey + '.html';
                var $cell = $('<a>', {
                    href: url,
                    class: 'nwm-picker-cell' + (isActive ? ' active' : ''),
                    text: mName
                });
                $grid.append($cell);
            }
        }

        this.$dropdown.empty().append($header, $grid);
        if ($.fn.tooltip) {
            this.$dropdown.find('[data-toggle="tooltip"]').tooltip();
        }
    };

    // -------------------------------------------------------------------------
    // WEEK PICKER
    // -------------------------------------------------------------------------
    DateNavController.prototype.initWeekPicker = function () {
        var self = this;
        this.viewWeekYear = this.contextYear;
        this.weekMonthFilter = 'all'; // 'all' or 1..12
        this.renderWeekPicker(this.viewWeekYear);

        this.$dropdown.on('click', '[data-action="prev-year"]', function (e) {
            e.preventDefault();
            var yearsAsc = self._getWeekPickerYears();
            var idx = yearsAsc.indexOf(self.viewWeekYear);
            if (idx > 0) {
                self.viewWeekYear = yearsAsc[idx - 1];
                self.renderWeekPicker(self.viewWeekYear);
            }
        });

        this.$dropdown.on('click', '[data-action="next-year"]', function (e) {
            e.preventDefault();
            var yearsAsc = self._getWeekPickerYears();
            var idx = yearsAsc.indexOf(self.viewWeekYear);
            if (idx !== -1 && idx < yearsAsc.length - 1) {
                self.viewWeekYear = yearsAsc[idx + 1];
                self.renderWeekPicker(self.viewWeekYear);
            }
        });

        this.$dropdown.on('change', '#nx-wp-year-select', function () {
            self.viewWeekYear = parseInt($(this).val(), 10);
            self.renderWeekPicker(self.viewWeekYear);
        });

        this.$dropdown.on('click', '.nwm-picker-tab', function (e) {
            e.preventDefault();
            if ($(this).hasClass('disabled') || $(this).is(':disabled')) return;
            var filter = $(this).attr('data-month-filter') || 'all';
            self.weekMonthFilter = (filter === 'all' || /^(?:[1-9]|1[0-2])$/.test(filter)) ? filter : 'all';
            self.renderWeekPicker(self.viewWeekYear);
        });
    };

    DateNavController.prototype._getWeekPickerYears = function () {
        var weekRanges = this.getRangesForScale('week');
        if (weekRanges) {
            return getAvailableYearsFromRanges(weekRanges, this.contextYear);
        }
        var yearsAsc = [];
        for (var y = this.startYear; y <= this.stopYear; y++) {
            yearsAsc.push(y);
        }
        if (yearsAsc.indexOf(this.contextYear) === -1) {
            yearsAsc.push(this.contextYear);
            yearsAsc.sort(function (a, b) { return a - b; });
        }
        return yearsAsc;
    };

    DateNavController.prototype.renderWeekPicker = function (year) {
        var monthNames = getLocalizedMonthNames();
        var weekRanges = this.getRangesForScale('week');
        var yearsAsc = this._getWeekPickerYears();

        if (yearsAsc.indexOf(year) === -1 && yearsAsc.length) {
            year = yearsAsc[yearsAsc.length - 1];
            this.viewWeekYear = year;
        }
        var yearIdx = yearsAsc.indexOf(year);
        var totalWeeks = getIsoWeeksInYear(year);

        // Header with year navigation
        var $header = $('<div>', { class: 'nwm-picker-header' });

        var $prevBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'prev-year',
            'aria-label': 'Previous year'
        }).append($('<i>', { class: 'mdi mdi-chevron-left' }));
        if (yearIdx <= 0) {
            $prevBtn.prop('disabled', true);
        }

        var $select = $('<select>', {
            class: 'nwm-picker-select',
            id: 'nx-wp-year-select',
            'aria-label': 'Year'
        });
        for (var yi = yearsAsc.length - 1; yi >= 0; yi--) {
            var y = yearsAsc[yi];
            var $opt = $('<option>', { value: y, text: y });
            if (y === year) {
                $opt.prop('selected', true);
            }
            $select.append($opt);
        }

        var $nextBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'next-year',
            'aria-label': 'Next year'
        }).append($('<i>', { class: 'mdi mdi-chevron-right' }));
        if (yearIdx === -1 || yearIdx >= yearsAsc.length - 1) {
            $nextBtn.prop('disabled', true);
        }

        $header.append($prevBtn, $select, $nextBtn);

        // Precompute week availability and which months have at least one available week
        var weekMeta = [];
        var monthHasWeek = {};
        for (var w = 1; w <= totalWeeks; w++) {
            var wStr = pad2(w);
            var wKey = year + '-' + wStr;
            var range = getIsoWeekRange(year, w);
            var startIso = formatDateIso(range.start);
            var endIso = formatDateIso(range.end);
            var isDisabled = weekRanges
                ? !isKeyInRanges(wKey, weekRanges)
                : ((endIso < this.startDateStr) || (startIso > this.stopDateStr));
            if (!isDisabled) {
                if (range.start.getFullYear() === year) {
                    monthHasWeek[range.start.getMonth() + 1] = true;
                }
                if (range.end.getFullYear() === year) {
                    monthHasWeek[range.end.getMonth() + 1] = true;
                }
            }
            weekMeta.push({
                w: w,
                wStr: wStr,
                range: range,
                isDisabled: isDisabled
            });
        }

        // Month quick filter tabs
        var minMo = (year === this.startYear && this.startDate) ? (this.startDate.getMonth() + 1) : 1;
        var maxMo = (year === this.stopYear && this.stopDate) ? (this.stopDate.getMonth() + 1) : 12;

        if (this.weekMonthFilter !== 'all') {
            var activeMoNum = parseInt(this.weekMonthFilter, 10);
            var activeMoDisabled = weekRanges
                ? !monthHasWeek[activeMoNum]
                : (activeMoNum < minMo || activeMoNum > maxMo);
            if (activeMoDisabled) {
                this.weekMonthFilter = 'all';
            }
        }

        var $tabs = $('<div>', { class: 'nwm-picker-filter-tabs' });
        $tabs.append($('<button>', {
            type: 'button',
            class: 'nwm-picker-tab' + (this.weekMonthFilter === 'all' ? ' active' : ''),
            'data-month-filter': 'all',
            text: 'All'
        }));
        for (var m = 1; m <= 12; m++) {
            var isTabDisabled = weekRanges ? !monthHasWeek[m] : (m < minMo || m > maxMo);
            var $tab = $('<button>', {
                type: 'button',
                class: 'nwm-picker-tab' +
                    (this.weekMonthFilter === String(m) ? ' active' : '') +
                    (isTabDisabled ? ' disabled' : ''),
                'data-month-filter': String(m),
                text: monthNames[m - 1] || String(m)
            });
            if (isTabDisabled) {
                $tab.prop('disabled', true);
            }
            $tabs.append($tab);
        }

        // Weeks Grid
        var $grid = $('<div>', { class: 'nwm-picker-grid-weeks' });
        for (var wi = 0; wi < weekMeta.length; wi++) {
            var meta = weekMeta[wi];
            // Filter check: does week overlap the filtered month?
            if (this.weekMonthFilter !== 'all') {
                var targetMo = parseInt(this.weekMonthFilter, 10) - 1;
                var overlap = (meta.range.start.getMonth() === targetMo || meta.range.end.getMonth() === targetMo);
                if (!overlap) continue;
            }

            var isActive = (year === this.contextYear && meta.w === this.contextWeek);
            var rangeLabel = pad2(meta.range.start.getDate()) + '.' + pad2(meta.range.start.getMonth() + 1) + ' - ' +
                             pad2(meta.range.end.getDate()) + '.' + pad2(meta.range.end.getMonth() + 1);

            if (meta.isDisabled) {
                $grid.append($('<span>', {
                    class: 'nwm-picker-cell disabled',
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    title: 'No data (CW ' + meta.wStr + ')',
                    text: 'CW ' + meta.wStr
                }));
            } else {
                var url = this.basePath + 'archive/' + year + '/weeks/week-' + year + '-' + meta.wStr + '.html';
                $grid.append($('<a>', {
                    href: url,
                    class: 'nwm-picker-cell' + (isActive ? ' active' : ''),
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    title: rangeLabel,
                    text: 'CW ' + meta.wStr
                }));
            }
        }

        this.$dropdown.empty().append($header, $tabs, $grid);
        if ($.fn.tooltip) {
            this.$dropdown.find('[data-toggle="tooltip"]').tooltip();
        }
    };

    // -------------------------------------------------------------------------
    // DAY CALENDAR PICKER
    // -------------------------------------------------------------------------
    DateNavController.prototype.initDayPicker = function () {
        var self = this;
        var parts = this.contextDay.split('-');
        this.viewCalendarYear = parseInt(parts[0], 10) || this.contextYear;
        this.viewCalendarMonth = parseInt(parts[1], 10) || this.contextMonth;

        this.renderCalendarPicker(this.viewCalendarYear, this.viewCalendarMonth);

        this.$dropdown.on('click', '[data-action="prev-month"]', function (e) {
            e.preventDefault();
            var dayRanges = self.getRangesForScale('day');
            if (dayRanges) {
                var yearsAsc = self._getDayPickerYears();
                var prevTarget = findPrevMonthWithDays(self.viewCalendarYear, self.viewCalendarMonth, dayRanges, yearsAsc);
                if (prevTarget) {
                    self.viewCalendarYear = prevTarget.year;
                    self.viewCalendarMonth = prevTarget.month;
                    self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
                }
                return;
            }
            var minMo = (self.viewCalendarYear === self.startYear && self.startDate) ? (self.startDate.getMonth() + 1) : 1;
            if (self.viewCalendarMonth > minMo) {
                self.viewCalendarMonth--;
            } else if (self.viewCalendarYear > self.startYear) {
                self.viewCalendarYear--;
                self.viewCalendarMonth = 12;
            }
            self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
        });

        this.$dropdown.on('click', '[data-action="next-month"]', function (e) {
            e.preventDefault();
            var dayRanges = self.getRangesForScale('day');
            if (dayRanges) {
                var yearsAsc = self._getDayPickerYears();
                var nextTarget = findNextMonthWithDays(self.viewCalendarYear, self.viewCalendarMonth, dayRanges, yearsAsc);
                if (nextTarget) {
                    self.viewCalendarYear = nextTarget.year;
                    self.viewCalendarMonth = nextTarget.month;
                    self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
                }
                return;
            }
            var maxMo = (self.viewCalendarYear === self.stopYear && self.stopDate) ? (self.stopDate.getMonth() + 1) : 12;
            if (self.viewCalendarMonth < maxMo) {
                self.viewCalendarMonth++;
            } else if (self.viewCalendarYear < self.stopYear) {
                self.viewCalendarYear++;
                self.viewCalendarMonth = 1;
            }
            self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
        });

        this.$dropdown.on('change', '#nx-dp-month-select', function () {
            self.viewCalendarMonth = parseInt($(this).val(), 10);
            self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
        });

        this.$dropdown.on('change', '#nx-dp-year-select', function () {
            self.viewCalendarYear = parseInt($(this).val(), 10);
            self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
        });
    };

    DateNavController.prototype._getDayPickerYears = function () {
        var dayRanges = this.getRangesForScale('day');
        var ctxParts = this.contextDay.split('-');
        var ctxYr = parseInt(ctxParts[0], 10) || this.contextYear;
        if (dayRanges) {
            return getAvailableYearsFromRanges(dayRanges, ctxYr);
        }
        var yearsAsc = [];
        for (var y = this.startYear; y <= this.stopYear; y++) {
            yearsAsc.push(y);
        }
        if (yearsAsc.indexOf(ctxYr) === -1) {
            yearsAsc.push(ctxYr);
            yearsAsc.sort(function (a, b) { return a - b; });
        }
        return yearsAsc;
    };

    DateNavController.prototype.renderCalendarPicker = function (year, month) {
        var monthNames = getLocalizedMonthNames();
        var weekdayNames = getLocalizedWeekdayNames();
        var dayRanges = this.getRangesForScale('day');
        var yearsAsc = this._getDayPickerYears();

        if (yearsAsc.indexOf(year) === -1 && yearsAsc.length) {
            year = yearsAsc[yearsAsc.length - 1];
            this.viewCalendarYear = year;
        }

        var minMo = (year === this.startYear && this.startDate) ? (this.startDate.getMonth() + 1) : 1;
        var maxMo = (year === this.stopYear && this.stopDate) ? (this.stopDate.getMonth() + 1) : 12;

        if (dayRanges) {
            if (!hasAnyDayInMonth(year, month, dayRanges)) {
                // Pick nearest month in this year that has available days
                var chosenMo = null;
                for (var cm = 12; cm >= 1; cm--) {
                    if (hasAnyDayInMonth(year, cm, dayRanges)) {
                        chosenMo = cm;
                        break;
                    }
                }
                if (chosenMo !== null) {
                    month = chosenMo;
                }
            }
        } else {
            if (month < minMo) month = minMo;
            if (month > maxMo) month = maxMo;
        }
        this.viewCalendarMonth = month;

        var canGoPrev = dayRanges
            ? !!findPrevMonthWithDays(year, month, dayRanges, yearsAsc)
            : ((year > this.startYear) || (year === this.startYear && month > minMo));
        var canGoNext = dayRanges
            ? !!findNextMonthWithDays(year, month, dayRanges, yearsAsc)
            : ((year < this.stopYear) || (year === this.stopYear && month < maxMo));

        // Header
        var $header = $('<div>', { class: 'nwm-picker-header' });

        var $prevBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'prev-month',
            'aria-label': 'Previous month'
        }).append($('<i>', { class: 'mdi mdi-chevron-left' }));
        if (!canGoPrev) {
            $prevBtn.prop('disabled', true);
        }

        var $selectGroup = $('<div>', {
            class: 'd-flex align-items-center',
            style: 'gap: 0.25rem;'
        });

        // Month dropdown with active boundary disabling
        var $monthSelect = $('<select>', {
            class: 'nwm-picker-select',
            id: 'nx-dp-month-select',
            'aria-label': 'Month'
        });
        for (var m = 1; m <= 12; m++) {
            var isMoDisabled = dayRanges ? !hasAnyDayInMonth(year, m, dayRanges) : (m < minMo || m > maxMo);
            var $mOpt = $('<option>', {
                value: m,
                text: monthNames[m - 1] || String(m)
            });
            if (isMoDisabled) {
                $mOpt.prop('disabled', true);
            }
            if (m === month) {
                $mOpt.prop('selected', true);
            }
            $monthSelect.append($mOpt);
        }

        // Year dropdown strictly from available years
        var $yearSelect = $('<select>', {
            class: 'nwm-picker-select',
            id: 'nx-dp-year-select',
            'aria-label': 'Year'
        });
        for (var yi = yearsAsc.length - 1; yi >= 0; yi--) {
            var y = yearsAsc[yi];
            var $yOpt = $('<option>', { value: y, text: y });
            if (y === year) {
                $yOpt.prop('selected', true);
            }
            $yearSelect.append($yOpt);
        }

        $selectGroup.append($monthSelect, $yearSelect);

        var $nextBtn = $('<button>', {
            type: 'button',
            class: 'nwm-picker-nav-btn',
            'data-action': 'next-month',
            'aria-label': 'Next month'
        }).append($('<i>', { class: 'mdi mdi-chevron-right' }));
        if (!canGoNext) {
            $nextBtn.prop('disabled', true);
        }

        $header.append($prevBtn, $selectGroup, $nextBtn);

        // Weekday header row (Mo..Su)
        var $weekdays = $('<div>', { class: 'nwm-picker-grid-weekdays' });
        for (var wd = 0; wd < 7; wd++) {
            $weekdays.append($('<span>', { text: weekdayNames[wd] }));
        }

        // Days Grid
        var $daysGrid = $('<div>', { class: 'nwm-picker-grid-days' });
        var firstDayIndex = new Date(year, month - 1, 1).getDay(); // 0 is Sun, 1 is Mon
        var leadingBlanks = (firstDayIndex === 0) ? 6 : firstDayIndex - 1; // convert to Mon = 0
        for (var b = 0; b < leadingBlanks; b++) {
            $daysGrid.append($('<span>', { class: 'nwm-picker-empty-cell' }));
        }

        var daysInMonth = new Date(year, month, 0).getDate();
        var todayStr = formatDateIso(new Date());

        for (var d = 1; d <= daysInMonth; d++) {
            var dateStr = year + '-' + pad2(month) + '-' + pad2(d);
            var isDisabled = dayRanges
                ? !isKeyInRanges(dateStr, dayRanges)
                : ((dateStr < this.startDateStr) || (dateStr > this.stopDateStr));
            var isActive = (dateStr === this.contextDay);
            var isToday = (dateStr === todayStr);

            var cellClasses = 'nwm-picker-cell' +
                (isActive ? ' active' : '') +
                (isToday ? ' today' : '');

            if (isDisabled) {
                $daysGrid.append($('<span>', {
                    class: cellClasses + ' disabled',
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    title: 'No data',
                    text: String(d)
                }));
            } else {
                var liveDayStr = this.stopDateStr || todayStr;
                var isCurrentDay = (dateStr === liveDayStr);
                var url = isCurrentDay
                    ? (this.basePath + 'index.html')
                    : (this.basePath + 'archive/' + year + '/days/day-' + dateStr + '.html');
                $daysGrid.append($('<a>', {
                    href: url,
                    class: cellClasses,
                    text: String(d)
                }));
            }
        }

        this.$dropdown.empty().append($header, $weekdays, $daysGrid);
        if ($.fn.tooltip) {
            this.$dropdown.find('[data-toggle="tooltip"]').tooltip();
        }
    };

    // Run immediately if #nwm-nav-hub is already in the DOM (js.inc loads after header.inc),
    // so the month label and picker initialize without waiting for chart scripts to finish.
    if ($('#nwm-nav-hub').length) {
        new DateNavController();
    } else {
        $(function () {
            new DateNavController();
        });
    }

})(window.jQuery);
