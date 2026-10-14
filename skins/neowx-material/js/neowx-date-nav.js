// neowx-date-nav.js
// -----------------------------------------------------------------------------
// Interactive Material Date, Week, Month, and Year navigation pickers for
// NeoWX Material skin.
// Handles dropdown menus, range limits [archive_start_date, archive_stop_date],
// and safe jumping without premature form/input events.
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

    function DateNavController() {
        this.$hub = $('#nwm-nav-hub');
        this.$container = $('#nx-picker-container');
        this.$dropdown = $('#nx-picker-dropdown');
        if (!this.$container.length || !this.$dropdown.length) return;

        this.basePath = this.$hub.attr('data-base-path') || '';
        this.page = this.$hub.attr('data-page') || '';
        this.activeNav = this.$hub.attr('data-active-nav') || '';

        this.contextYear = parseInt(this.$hub.attr('data-context-year') || new Date().getFullYear(), 10);
        this.contextMonth = parseInt(this.$hub.attr('data-context-month') || (new Date().getMonth() + 1), 10);
        this.contextWeek = parseInt(this.$hub.attr('data-context-week') || 1, 10);
        this.contextDay = this.$hub.attr('data-context-day') || formatDateIso(new Date());

        this.startDateStr = this.$hub.attr('data-start-date') || '1970-01-01';
        this.stopDateStr = window.NX_STOP_DATE || this.$hub.attr('data-stop-date') || formatDateIso(new Date());

        this.startDate = parseDateIso(this.startDateStr);
        this.stopDate = parseDateIso(this.stopDateStr);

        this.startYear = this.startDate ? this.startDate.getFullYear() : 1970;
        this.stopYear = this.stopDate ? this.stopDate.getFullYear() : new Date().getFullYear();

        this.init();
    }

    DateNavController.prototype.init = function () {
        var self = this;

        // Prevent clicking inside picker controls from accidentally closing the Bootstrap dropdown
        this.$dropdown.on('click', function (e) {
            if ($(e.target).closest('a[href]').length) {
                return; // Let navigation links proceed
            }
            e.stopPropagation();
        });

        // Initialize picker type
        if (this.$dropdown.hasClass('nwm-picker-calendar')) {
            this.initDayPicker();
        } else if (this.$dropdown.hasClass('nwm-picker-week')) {
            this.initWeekPicker();
        } else if (this.$dropdown.hasClass('nwm-picker-month')) {
            this.initMonthPicker();
        }

        // Expose global updater so live.json can refresh stopDate if needed
        window.nxUpdateStopDate = function (newStopDateStr) {
            if (!newStopDateStr) return;
            self.stopDateStr = newStopDateStr;
            self.stopDate = parseDateIso(newStopDateStr);
            if (self.stopDate) {
                self.stopYear = self.stopDate.getFullYear();
            }
            if (self.$dropdown.hasClass('nwm-picker-calendar') && self.viewCalendarYear) {
                self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
            } else if (self.$dropdown.hasClass('nwm-picker-month') && self.viewMonthYear) {
                self.renderMonthPicker(self.viewMonthYear);
            } else if (self.$dropdown.hasClass('nwm-picker-week') && self.viewWeekYear) {
                self.renderWeekPicker(self.viewWeekYear);
            }
        };
    };

    // -------------------------------------------------------------------------
    // MONTH PICKER
    // -------------------------------------------------------------------------
    DateNavController.prototype.initMonthPicker = function () {
        var self = this;
        this.viewMonthYear = this.contextYear;
        this.renderMonthPicker(this.viewMonthYear);

        this.$dropdown.on('click', '[data-action="prev-year"]', function (e) {
            e.preventDefault();
            if (self.viewMonthYear > self.startYear) {
                self.viewMonthYear--;
                self.renderMonthPicker(self.viewMonthYear);
            }
        });

        this.$dropdown.on('click', '[data-action="next-year"]', function (e) {
            e.preventDefault();
            if (self.viewMonthYear < self.stopYear) {
                self.viewMonthYear++;
                self.renderMonthPicker(self.viewMonthYear);
            }
        });

        this.$dropdown.on('change', '#nx-mp-year-select', function () {
            self.viewMonthYear = parseInt($(this).val(), 10);
            self.renderMonthPicker(self.viewMonthYear);
        });
    };

    DateNavController.prototype.renderMonthPicker = function (year) {
        var monthNames = getLocalizedMonthNames();
        var html = '';

        // Header with year navigation
        html += '<div class="nwm-picker-header">';
        html += '<button type="button" class="nwm-picker-nav-btn" data-action="prev-year"' +
                (year <= this.startYear ? ' disabled' : '') + ' aria-label="Previous year"><i class="mdi mdi-chevron-left"></i></button>';

        html += '<select class="nwm-picker-select" id="nx-mp-year-select" aria-label="Year">';
        for (var y = this.stopYear; y >= this.startYear; y--) {
            html += '<option value="' + y + '"' + (y === year ? ' selected' : '') + '>' + y + '</option>';
        }
        html += '</select>';

        html += '<button type="button" class="nwm-picker-nav-btn" data-action="next-year"' +
                (year >= this.stopYear ? ' disabled' : '') + ' aria-label="Next year"><i class="mdi mdi-chevron-right"></i></button>';
        html += '</div>';

        // 12 Months Grid
        html += '<div class="nwm-picker-grid-months">';
        for (var m = 1; m <= 12; m++) {
            var mStr = pad2(m);
            var mName = monthNames[m - 1] || mStr;

            var firstDayStr = year + '-' + mStr + '-01';
            var daysInMonth = new Date(year, m, 0).getDate();
            var lastDayStr = year + '-' + mStr + '-' + pad2(daysInMonth);

            var isDisabled = (lastDayStr < this.startDateStr) || (firstDayStr > this.stopDateStr);
            var isActive = (year === this.contextYear && m === this.contextMonth);

            if (isDisabled) {
                html += '<span class="nwm-picker-cell disabled" data-toggle="tooltip" data-placement="top" title="No data">' + mName + '</span>';
            } else {
                var url = this.basePath + 'archive/' + year + '/months/month-' + year + '-' + mStr + '.html';
                html += '<a href="' + url + '" class="nwm-picker-cell' + (isActive ? ' active' : '') + '">' + mName + '</a>';
            }
        }
        html += '</div>';

        this.$dropdown.html(html);
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
            if (self.viewWeekYear > self.startYear) {
                self.viewWeekYear--;
                self.renderWeekPicker(self.viewWeekYear);
            }
        });

        this.$dropdown.on('click', '[data-action="next-year"]', function (e) {
            e.preventDefault();
            if (self.viewWeekYear < self.stopYear) {
                self.viewWeekYear++;
                self.renderWeekPicker(self.viewWeekYear);
            }
        });

        this.$dropdown.on('change', '#nx-wp-year-select', function () {
            self.viewWeekYear = parseInt($(this).val(), 10);
            self.renderWeekPicker(self.viewWeekYear);
        });

        this.$dropdown.on('click', '.nwm-picker-tab', function (e) {
            e.preventDefault();
            self.weekMonthFilter = $(this).attr('data-month-filter');
            self.renderWeekPicker(self.viewWeekYear);
        });
    };

    DateNavController.prototype.renderWeekPicker = function (year) {
        var monthNames = getLocalizedMonthNames();
        var totalWeeks = getIsoWeeksInYear(year);
        var html = '';

        // Header with year navigation
        html += '<div class="nwm-picker-header">';
        html += '<button type="button" class="nwm-picker-nav-btn" data-action="prev-year"' +
                (year <= this.startYear ? ' disabled' : '') + ' aria-label="Previous year"><i class="mdi mdi-chevron-left"></i></button>';

        html += '<select class="nwm-picker-select" id="nx-wp-year-select" aria-label="Year">';
        for (var y = this.stopYear; y >= this.startYear; y--) {
            html += '<option value="' + y + '"' + (y === year ? ' selected' : '') + '>' + y + '</option>';
        }
        html += '</select>';

        html += '<button type="button" class="nwm-picker-nav-btn" data-action="next-year"' +
                (year >= this.stopYear ? ' disabled' : '') + ' aria-label="Next year"><i class="mdi mdi-chevron-right"></i></button>';
        html += '</div>';

        // Month quick filter tabs
        html += '<div class="nwm-picker-filter-tabs">';
        html += '<button type="button" class="nwm-picker-tab' + (this.weekMonthFilter === 'all' ? ' active' : '') + '" data-month-filter="all">All</button>';
        for (var m = 1; m <= 12; m++) {
            html += '<button type="button" class="nwm-picker-tab' + (this.weekMonthFilter === String(m) ? ' active' : '') + '" data-month-filter="' + m + '">' + (monthNames[m - 1] || m) + '</button>';
        }
        html += '</div>';

        // Weeks Grid
        html += '<div class="nwm-picker-grid-weeks">';
        for (var w = 1; w <= totalWeeks; w++) {
            var wStr = pad2(w);
            var range = getIsoWeekRange(year, w);
            var startIso = formatDateIso(range.start);
            var endIso = formatDateIso(range.end);

            // Filter check: does week overlap the filtered month?
            if (this.weekMonthFilter !== 'all') {
                var targetMo = parseInt(this.weekMonthFilter, 10) - 1;
                var overlap = (range.start.getMonth() === targetMo || range.end.getMonth() === targetMo);
                if (!overlap) continue;
            }

            var isDisabled = (endIso < this.startDateStr) || (startIso > this.stopDateStr);
            var isActive = (year === this.contextYear && w === this.contextWeek);

            var rangeLabel = pad2(range.start.getDate()) + '.' + pad2(range.start.getMonth() + 1) + ' - ' +
                             pad2(range.end.getDate()) + '.' + pad2(range.end.getMonth() + 1);

            if (isDisabled) {
                html += '<span class="nwm-picker-cell disabled" data-toggle="tooltip" data-placement="top" title="No data (CW ' + wStr + ')">CW ' + wStr + '</span>';
            } else {
                var url = this.basePath + 'archive/' + year + '/weeks/week-' + year + '-' + wStr + '.html';
                html += '<a href="' + url + '" class="nwm-picker-cell' + (isActive ? ' active' : '') + '" data-toggle="tooltip" data-placement="top" title="' + rangeLabel + '">CW ' + wStr + '</a>';
            }
        }
        html += '</div>';

        this.$dropdown.html(html);
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
            if (self.viewCalendarMonth > 1) {
                self.viewCalendarMonth--;
            } else if (self.viewCalendarYear > self.startYear) {
                self.viewCalendarYear--;
                self.viewCalendarMonth = 12;
            }
            self.renderCalendarPicker(self.viewCalendarYear, self.viewCalendarMonth);
        });

        this.$dropdown.on('click', '[data-action="next-month"]', function (e) {
            e.preventDefault();
            if (self.viewCalendarMonth < 12) {
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

    DateNavController.prototype.renderCalendarPicker = function (year, month) {
        var monthNames = getLocalizedMonthNames();
        var weekdayNames = getLocalizedWeekdayNames();
        var html = '';

        var canGoPrev = (year > this.startYear) || (year === this.startYear && month > (this.startDate ? this.startDate.getMonth() + 1 : 1));
        var canGoNext = (year < this.stopYear) || (year === this.stopYear && month < (this.stopDate ? this.stopDate.getMonth() + 1 : 12));

        // Header
        html += '<div class="nwm-picker-header">';
        html += '<button type="button" class="nwm-picker-nav-btn" data-action="prev-month"' +
                (!canGoPrev ? ' disabled' : '') + ' aria-label="Previous month"><i class="mdi mdi-chevron-left"></i></button>';

        html += '<div class="d-flex align-items-center" style="gap: 0.25rem;">';
        // Month dropdown
        html += '<select class="nwm-picker-select" id="nx-dp-month-select" aria-label="Month">';
        for (var m = 1; m <= 12; m++) {
            html += '<option value="' + m + '"' + (m === month ? ' selected' : '') + '>' + (monthNames[m - 1] || m) + '</option>';
        }
        html += '</select>';

        // Year dropdown
        html += '<select class="nwm-picker-select" id="nx-dp-year-select" aria-label="Year">';
        for (var y = this.stopYear; y >= this.startYear; y--) {
            html += '<option value="' + y + '"' + (y === year ? ' selected' : '') + '>' + y + '</option>';
        }
        html += '</select>';
        html += '</div>';

        html += '<button type="button" class="nwm-picker-nav-btn" data-action="next-month"' +
                (!canGoNext ? ' disabled' : '') + ' aria-label="Next month"><i class="mdi mdi-chevron-right"></i></button>';
        html += '</div>';

        // Weekday header row (Mo..Su)
        html += '<div class="nwm-picker-grid-weekdays">';
        for (var wd = 0; wd < 7; wd++) {
            html += '<span>' + weekdayNames[wd] + '</span>';
        }
        html += '</div>';

        // Days Grid
        html += '<div class="nwm-picker-grid-days">';
        var firstDayIndex = new Date(year, month - 1, 1).getDay(); // 0 is Sun, 1 is Mon
        var leadingBlanks = (firstDayIndex === 0) ? 6 : firstDayIndex - 1; // convert to Mon = 0
        for (var b = 0; b < leadingBlanks; b++) {
            html += '<span class="nwm-picker-empty-cell"></span>';
        }

        var daysInMonth = new Date(year, month, 0).getDate();
        var todayStr = formatDateIso(new Date());

        for (var d = 1; d <= daysInMonth; d++) {
            var dateStr = year + '-' + pad2(month) + '-' + pad2(d);
            var isDisabled = (dateStr < this.startDateStr) || (dateStr > this.stopDateStr);
            var isActive = (dateStr === this.contextDay);
            var isToday = (dateStr === todayStr);

            var cellClasses = 'nwm-picker-cell' +
                (isActive ? ' active' : '') +
                (isToday ? ' today' : '');

            if (isDisabled) {
                html += '<span class="' + cellClasses + ' disabled" data-toggle="tooltip" data-placement="top" title="No data">' + d + '</span>';
            } else {
                var url = this.basePath + 'archive/' + year + '/days/day-' + dateStr + '.html';
                html += '<a href="' + url + '" class="' + cellClasses + '">' + d + '</a>';
            }
        }
        html += '</div>';

        this.$dropdown.html(html);
        if ($.fn.tooltip) {
            this.$dropdown.find('[data-toggle="tooltip"]').tooltip();
        }
    };

    $(function () {
        new DateNavController();
    });

})(window.jQuery);
