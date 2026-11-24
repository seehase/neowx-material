#
# Copyright (c) 2026 NeowxArchiveGenerator Extension for NeoWX Material
#
# Distributed under the terms of the GNU GENERAL PUBLIC LICENSE
#

"""Provides advanced archive generation with ISO week spans, nested directory routing,
cutoff limits (archive_start_date), granularity controls (archive_history), two-pass
live-first incremental backfill, and contextual navigation variables for NeoWX Material.

To use, configure [Generators] in skin.conf:

[Generators]
    generator_list = weewx.reportengine.CopyGenerator, user.neowx_archive.NeowxArchiveGenerator
"""

import datetime
import json
import logging
import os
import re
import time

try:
    import Cheetah.Filters
    import Cheetah.Parser
    import Cheetah.Template
    import unicodedata
    import weeutil.logger
    import weewx.cheetahgenerator
    import weewx.reportengine
    from weeutil.weeutil import TimeSpan, to_bool, to_int, timestamp_to_string, getFileName
except ImportError:
    # Fallback for standalone/linting environments
    class _DummyBase:
        generator_dict = {}
        format_dict = {}
        def __init__(self, *args, **kwargs):
            self.outputted_dict = {}
    class _DummyModule:
        CheetahGenerator = _DummyBase
        ReportGenerator = _DummyBase
    class TimeSpan:
        def __init__(self, start, stop):
            self.start = start
            self.stop = stop
        def includesArchiveTime(self, ts):
            return self.start < ts <= self.stop
    weewx = type('weewx', (), {'cheetahgenerator': _DummyModule, 'reportengine': _DummyModule})()
    to_bool = lambda v: str(v).lower() in ('true', 'yes', '1')
    to_int = lambda v: int(v) if v is not None else None
    timestamp_to_string = lambda ts: str(ts)

    def getFileName(template, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp)
        filename = os.path.basename(template).replace('.tmpl', '')
        filename = filename.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d').replace('WW', '%V')
        return dt.strftime(filename)

VERSION = "1.2.2"

log = logging.getLogger(__name__)


def genWeekSpans(start_ts, stop_ts):
    """Generator function that yields Monday-to-Monday ISO week TimeSpans
    in an inclusive range.

    Args:
        start_ts (float): Start timestamp.
        stop_ts (float): Stop timestamp.

    Yields:
        TimeSpan: A sequence of TimeSpans starting on Monday 00:00:00 and
                  stopping on next Monday 00:00:00.
    """
    if None in (start_ts, stop_ts):
        return

    start_dt = datetime.datetime.fromtimestamp(start_ts)
    stop_dt = datetime.datetime.fromtimestamp(stop_ts)

    start_date = start_dt.date()
    stop_date = stop_dt.date()

    # Find the Monday of the starting week
    start_monday = start_date - datetime.timedelta(days=start_date.weekday())
    # Find the Monday of the ending week
    stop_monday = stop_date - datetime.timedelta(days=stop_date.weekday())

    # If stop_ts falls exactly on Monday midnight and spans multiple days, exclude the next week
    if (stop_dt.weekday(), stop_dt.hour, stop_dt.minute, stop_dt.second) == (0, 0, 0, 0) and stop_ts > start_ts:
        stop_monday -= datetime.timedelta(days=7)

    curr_monday = start_monday
    while curr_monday <= stop_monday:
        next_monday = curr_monday + datetime.timedelta(days=7)
        s_ts = int(time.mktime((curr_monday.year, curr_monday.month, curr_monday.day, 0, 0, 0, 0, 0, -1)))
        e_ts = int(time.mktime((next_monday.year, next_monday.month, next_monday.day, 0, 0, 0, 0, 0, -1)))
        yield TimeSpan(s_ts, e_ts)
        curr_monday = next_monday


class NeowxArchiveGenerator(weewx.cheetahgenerator.CheetahGenerator):
    """Cheetah Generator extension supporting SummaryByWeek, dynamic directory routing,
    archive_start_date bounds, and rich template navigation context.
    """

    # Extended generator dict including SummaryByWeek
    generator_dict = dict(weewx.cheetahgenerator.CheetahGenerator.generator_dict)
    generator_dict['SummaryByWeek'] = genWeekSpans

    format_dict = dict(weewx.cheetahgenerator.CheetahGenerator.format_dict)
    format_dict['SummaryByWeek'] = "%Y-%V"

    # Priority ordering for SummaryBy* sections (coarse-to-fine)
    SUMMARY_PRIORITY = ('SummaryByYear', 'SummaryByMonth', 'SummaryByWeek', 'SummaryByDay')

    # Minimum skin version required per archive summary type.
    # Bump a specific key here when a release modifies that template's markup/layout
    # so existing historical HTML files with a lower embedded version are automatically
    # refreshed in the background during Pass 2 ('history').
    MIN_ARCHIVE_VERSION = {
        'SummaryByYear':  '2.2.0',
        'SummaryByMonth': '2.2.0',
        'SummaryByWeek':  '2.2.0',
        'SummaryByDay':   '2.0.0',
    }

    _VERSION_META_RE = re.compile(
        rb'(?:<meta\s+name=["\']neowx-version["\']\s+content=["\']v?([^"\']+)["\']'
        rb'|<!--\s*NeoWX Material skin v([^\s-]+)\s*-->)',
        re.IGNORECASE
    )

    _YEAR_DIR_RE = re.compile(r'^(\d{4})$')
    _YEAR_FILE_RE = re.compile(r'^year-(\d{4})\.html$')
    _MONTH_FILE_RE = re.compile(r'^month-(\d{4})-(\d{2})\.html$')
    _WEEK_FILE_RE = re.compile(r'^week-(\d{4})-(\d{2})\.html$')
    _DAY_FILE_RE = re.compile(r'^day-(\d{4})-(\d{2})-(\d{2})\.html$')

    @classmethod
    def _scan_existing_archives(cls, html_root, stop_dt):
        """Scans HTML_ROOT/archive/ once to discover all actually existing HTML archive
        pages per scale, always including the active current period for stop_dt.
        """
        years = set()
        months = set()
        weeks = set()
        days = set()

        stop_date = stop_dt.date()
        stop_monday = stop_date - datetime.timedelta(days=stop_date.weekday())
        stop_wk_yr = stop_monday.year
        stop_wk_num = stop_monday.isocalendar()[1]

        archive_dir = os.path.join(html_root, 'archive')
        if os.path.isdir(archive_dir):
            try:
                year_entries = list(os.scandir(archive_dir))
            except OSError:
                year_entries = []

            for yr_entry in year_entries:
                m_dir = cls._YEAR_DIR_RE.match(yr_entry.name)
                if not m_dir:
                    continue
                try:
                    if not yr_entry.is_dir():
                        continue
                except OSError:
                    continue

                dir_yr = int(m_dir.group(1))
                if dir_yr > stop_dt.year:
                    continue

                yr_path = yr_entry.path
                yr_file = os.path.join(yr_path, f"year-{dir_yr:04d}.html")
                if os.path.isfile(yr_file):
                    years.add(dir_yr)

                # Months: archive/<YYYY>/months/month-<YYYY>-<MM>.html
                months_dir = os.path.join(yr_path, 'months')
                if os.path.isdir(months_dir):
                    try:
                        for entry in os.scandir(months_dir):
                            m = cls._MONTH_FILE_RE.match(entry.name)
                            if not m:
                                continue
                            y, mo = int(m.group(1)), int(m.group(2))
                            if y == dir_yr and 1 <= mo <= 12 and (y, mo) <= (stop_dt.year, stop_dt.month):
                                months.add((y, mo))
                    except OSError:
                        pass

                # Weeks: archive/<YYYY>/weeks/week-<YYYY>-<WW>.html
                weeks_dir = os.path.join(yr_path, 'weeks')
                if os.path.isdir(weeks_dir):
                    try:
                        for entry in os.scandir(weeks_dir):
                            m = cls._WEEK_FILE_RE.match(entry.name)
                            if not m:
                                continue
                            y, wk = int(m.group(1)), int(m.group(2))
                            if y != dir_yr or not (1 <= wk <= 53):
                                continue
                            if y < stop_wk_yr:
                                weeks.add((y, wk))
                            elif y == stop_wk_yr:
                                # Allow normal <= stop_wk_num; also allow year-end ISO week 01 if stop_monday is in Dec
                                if wk <= stop_wk_num or (stop_monday.month == 12 and stop_wk_num == 1):
                                    weeks.add((y, wk))
                    except OSError:
                        pass

                # Days: archive/<YYYY>/days/day-<YYYY>-<MM>-<DD>.html
                days_dir = os.path.join(yr_path, 'days')
                if os.path.isdir(days_dir):
                    try:
                        for entry in os.scandir(days_dir):
                            m = cls._DAY_FILE_RE.match(entry.name)
                            if not m:
                                continue
                            y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
                            if y != dir_yr:
                                continue
                            try:
                                d = datetime.date(y, mo, dd)
                            except ValueError:
                                continue
                            if d <= stop_date:
                                days.add(d)
                    except OSError:
                        pass

        # Current active period is always guaranteed by Pass 1 (index.html + current summaries)
        years.add(stop_dt.year)
        months.add((stop_dt.year, stop_dt.month))
        weeks.add((stop_wk_yr, stop_wk_num))
        days.add(stop_date)

        return {
            'years': years,
            'months': months,
            'weeks': weeks,
            'days': days,
        }

    @staticmethod
    def _compress_ranges(sorted_items, is_consecutive_fn, format_fn):
        """Compresses sorted items into compact contiguous [start, end] string pairs."""
        if not sorted_items:
            return []
        ranges = []
        run_start = sorted_items[0]
        run_prev = sorted_items[0]
        for item in sorted_items[1:]:
            if is_consecutive_fn(run_prev, item):
                run_prev = item
            else:
                ranges.append([format_fn(run_start), format_fn(run_prev)])
                run_start = item
                run_prev = item
        ranges.append([format_fn(run_start), format_fn(run_prev)])
        return ranges

    @classmethod
    def _serialize_archive_available(cls, avail):
        """Serializes the per-scale availability sets into a compact JSON string."""
        if not avail:
            return ''

        year_ranges = cls._compress_ranges(
            sorted(avail.get('years', ())),
            lambda a, b: b == a + 1,
            lambda y: f"{y:04d}"
        )
        month_ranges = cls._compress_ranges(
            sorted(avail.get('months', ())),
            lambda a, b: b == ((a[0], a[1] + 1) if a[1] < 12 else (a[0] + 1, 1)),
            lambda ym: f"{ym[0]:04d}-{ym[1]:02d}"
        )
        # Compress week ranges only within the same calendar year so 52/53-week
        # ISO boundaries never require cross-year arithmetic on the client.
        week_ranges = cls._compress_ranges(
            sorted(avail.get('weeks', ())),
            lambda a, b: a[0] == b[0] and b[1] == a[1] + 1,
            lambda yw: f"{yw[0]:04d}-{yw[1]:02d}"
        )
        day_ranges = cls._compress_ranges(
            sorted(avail.get('days', ())),
            lambda a, b: b == a + datetime.timedelta(days=1),
            lambda d: d.strftime('%Y-%m-%d')
        )

        return json.dumps({
            'years': year_ranges,
            'months': month_ranges,
            'weeks': week_ranges,
            'days': day_ranges,
        }, separators=(',', ':'))

    def _record_generated_archive(self, summarize_by, ref_dt, fullname):
        """Updates the in-memory availability sets when a summary HTML file is written."""
        if self._available_archives is None or not fullname.lower().endswith('.html'):
            return
        added = False
        if summarize_by == 'SummaryByYear':
            key = ref_dt.year
            if key not in self._available_archives['years']:
                self._available_archives['years'].add(key)
                added = True
        elif summarize_by == 'SummaryByMonth':
            key = (ref_dt.year, ref_dt.month)
            if key not in self._available_archives['months']:
                self._available_archives['months'].add(key)
                added = True
        elif summarize_by == 'SummaryByWeek':
            key = (ref_dt.year, ref_dt.isocalendar()[1])
            if key not in self._available_archives['weeks']:
                self._available_archives['weeks'].add(key)
                added = True
        elif summarize_by == 'SummaryByDay':
            key = ref_dt.date()
            if key not in self._available_archives['days']:
                self._available_archives['days'].add(key)
                added = True
        if added:
            self._available_archives_changed = True

    @staticmethod
    def _needs_finalization(filepath, timespan, stop_ts):
        """Returns True if an existing past summary file was last written before its
        period ended (mtime < timespan.stop), meaning it needs one final rebuild
        after midnight/week/month/year rollover.
        """
        if stop_ts <= timespan.stop:
            return False
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            return False
        return mtime < timespan.stop

    @staticmethod
    def _parse_version_tuple(ver_str):
        """Parses a version string like '2.0.3' or 'v2.0.3' into a comparable int tuple (2, 0, 3)."""
        if not ver_str:
            return (0, 0, 0)
        cleaned = str(ver_str).strip().lstrip('vV')
        if not cleaned:
            return (0, 0, 0)
        parts = []
        for token in re.split(r'[._-]', cleaned):
            m = re.match(r'^(\d+)', token)
            if m:
                parts.append(int(m.group(1)))
            else:
                break
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    @classmethod
    def _extract_file_version(cls, filepath):
        """Reads the first 1 KB of an HTML file and extracts its embedded skin version tuple."""
        try:
            with open(filepath, 'rb') as fd:
                head = fd.read(1024)
        except OSError:
            return (0, 0, 0)
        m = cls._VERSION_META_RE.search(head)
        if not m:
            return (0, 0, 0)
        raw_ver = (m.group(1) or m.group(2) or b'').decode('ascii', errors='ignore')
        return cls._parse_version_tuple(raw_ver)

    @classmethod
    def _get_min_required_version(cls, summarize_by, report_dict):
        """Returns the effective minimum required version tuple for summarize_by,
        combining MIN_ARCHIVE_VERSION in code with optional skin.conf overrides.
        """
        code_min = cls._parse_version_tuple(cls.MIN_ARCHIVE_VERSION.get(summarize_by, '0.0.0'))
        conf_global = cls._parse_version_tuple(report_dict.get('min_archive_version', ''))
        per_type_key = {
            'SummaryByYear': 'min_year_version',
            'SummaryByMonth': 'min_month_version',
            'SummaryByWeek': 'min_week_version',
            'SummaryByDay': 'min_day_version',
        }.get(summarize_by)
        conf_type = cls._parse_version_tuple(report_dict.get(per_type_key, '')) if per_type_key else (0, 0, 0)
        return max(code_min, conf_global, conf_type)

    @classmethod
    def _needs_version_refresh(cls, filepath, summarize_by, report_dict):
        """Returns True if an existing HTML archive file has a lower embedded skin version
        than the minimum required version for its summary type.
        """
        if not filepath.lower().endswith('.html'):
            return False
        min_req = cls._get_min_required_version(summarize_by, report_dict)
        if min_req <= (0, 0, 0):
            return False
        file_ver = cls._extract_file_version(filepath)
        return file_ver < min_req

    def __init__(self, config_dict, skin_dict, *args, **kwargs):
        super(NeowxArchiveGenerator, self).__init__(config_dict, skin_dict, *args, **kwargs)
        log.info("NeowxArchiveGenerator version %s", VERSION)
        self._run_start_time = None
        self._backfill_count = 0
        self._backfill_limit_logged = False
        self._available_archives = None
        self._available_archives_changed = False
        self._scan_html_root = None
        self._live_data_targets = []
        # ISO-8601 week spans (genWeekSpans / %V) always start on Monday (0).
        # Ensure stn_info.week_start is 0 so WeeWX's TimeBinder ($week) queries
        # the exact same Monday-to-Monday span regardless of weewx.conf week_start.
        if hasattr(self, 'stn_info') and self.stn_info is not None:
            try:
                self.stn_info.week_start = 0
            except Exception:
                pass
        # Ensure outputted_dict tracks all generator keys
        for k in self.generator_dict:
            if k not in self.outputted_dict:
                self.outputted_dict[k] = []

    def _getSearchList(self, encoding, timespan, default_binding, section_name, file_name):
        """Builds the Cheetah search list and enforces Monday (0) week_start on
        TimeBinder instances so $week aligns with genWeekSpans ISO weeks.
        """
        search_list = super(NeowxArchiveGenerator, self)._getSearchList(
            encoding, timespan, default_binding, section_name, file_name
        )
        for entry in search_list:
            opt_dict = getattr(entry, 'option_dict', None)
            if isinstance(opt_dict, dict):
                opt_dict['week_start'] = 0
        return search_list

    @staticmethod
    def _resolve_archive_start_date(raw_val, first_good_ts, stop_ts):
        """Resolves archive_start_date (YYYY-MM-DD or keyword: all, current_year,
        current_month, current/today/none) into (start_ts, cutoff_ts).
        """
        raw_str = str(raw_val if raw_val is not None else '1970-01-01').strip()
        raw_lower = raw_str.lower()
        stop_dt = datetime.datetime.fromtimestamp(stop_ts)
        cutoff_ts = 0

        if raw_lower in ('', 'all', '1970-01-01'):
            cutoff_ts = 0
        elif raw_lower == 'current_year':
            cutoff_ts = int(time.mktime((stop_dt.year, 1, 1, 0, 0, 0, 0, 0, -1)))
        elif raw_lower == 'current_month':
            cutoff_ts = int(time.mktime((stop_dt.year, stop_dt.month, 1, 0, 0, 0, 0, 0, -1)))
        elif raw_lower in ('current', 'today', 'none'):
            cutoff_ts = int(time.mktime((stop_dt.year, stop_dt.month, stop_dt.day, 0, 0, 0, 0, 0, -1)))
        else:
            try:
                cutoff_tt = time.strptime(raw_str, "%Y-%m-%d")
                cutoff_ts = int(time.mktime(cutoff_tt))
            except (ValueError, TypeError):
                cutoff_ts = 0

        start_ts = max(first_good_ts, cutoff_ts) if cutoff_ts > 0 else first_good_ts
        return (start_ts, cutoff_ts)

    @classmethod
    def _parse_archive_history(cls, raw_val, raw_start_date=''):
        """Parses archive_history setting into a set of enabled SummaryBy* keys.
        Supports presets ('all', 'months_years', 'years', 'none') or comma/underscore
        lists of granularities ('years, months, weeks, days').
        """
        all_keys = set(cls.SUMMARY_PRIORITY)
        start_lower = str(raw_start_date or '').strip().lower()
        if start_lower in ('current', 'today', 'none'):
            return set()

        if raw_val is None:
            return all_keys

        if isinstance(raw_val, (list, tuple)):
            raw_str = ','.join(str(x) for x in raw_val)
        else:
            raw_str = str(raw_val)

        tokens = [t for t in re.split(r'[,\s_]+', raw_str.strip().lower()) if t]
        if not tokens or 'all' in tokens or 'true' in tokens or 'yes' in tokens:
            return all_keys
        if any(t in ('none', 'current', 'current_only', 'false', 'no') for t in tokens):
            return set()

        mapping = {
            'year': 'SummaryByYear',
            'years': 'SummaryByYear',
            'summarybyyear': 'SummaryByYear',
            'month': 'SummaryByMonth',
            'months': 'SummaryByMonth',
            'summarybymonth': 'SummaryByMonth',
            'week': 'SummaryByWeek',
            'weeks': 'SummaryByWeek',
            'summarybyweek': 'SummaryByWeek',
            'day': 'SummaryByDay',
            'days': 'SummaryByDay',
            'summarybyday': 'SummaryByDay',
        }
        enabled = set()
        for token in tokens:
            if token in mapping:
                enabled.add(mapping[token])
        return enabled

    def _order_subsections(self, section, _pass):
        """Orders subsections so non-summary sections (LiveData, Global, ToDate) run
        first in Pass 1 ('current'), followed by SummaryByYear -> Month -> Week -> Day.
        In Pass 2 ('history'), only SummaryBy* sections are visited in coarse-to-fine order.
        """
        # If this section is already a SummaryBy* container (e.g. [[SummaryByMonth]]),
        # all of its child subsections (e.g. [[[month_summary]]], [[[month_NOAA]]])
        # inherit summarize_by and should be visited in declaration order in both passes.
        if section.get('summarize_by') in self.generator_dict:
            return list(section.sections)

        non_summary = []
        summary_by_key = {k: [] for k in self.SUMMARY_PRIORITY}
        other_summary = []

        for sub in section.sections:
            sub_sec = section[sub]
            sum_by = sub_sec.get('summarize_by') or (sub if sub in self.generator_dict else None)
            if sum_by in summary_by_key:
                summary_by_key[sum_by].append(sub)
            elif sum_by in self.generator_dict:
                other_summary.append(sub)
            else:
                non_summary.append(sub)

        ordered_summaries = []
        for k in self.SUMMARY_PRIORITY:
            ordered_summaries.extend(summary_by_key[k])
        ordered_summaries.extend(other_summary)

        if _pass == 'history':
            return ordered_summaries
        return non_summary + ordered_summaries

    @staticmethod
    def _getFileName(template, time_val):
        """Helper to get destination filename from template and timestamp or time tuple."""
        ts = time_val if isinstance(time_val, (int, float)) else time.mktime(time_val)
        try:
            return getFileName(template, ts)
        except Exception:
            dt = datetime.datetime.fromtimestamp(ts)
            filename = os.path.basename(template).replace('.tmpl', '')
            filename = filename.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d').replace('WW', '%V')
            return dt.strftime(filename)

    def _prepGen(self, report_dict):
        """Locates template (with skin root fallback) and base destination directory."""
        skin_dir = os.path.join(
            self.config_dict['WEEWX_ROOT'],
            self.config_dict['StdReport']['SKIN_ROOT'],
            report_dict['skin']
        )
        template_rel = report_dict['template']
        template = os.path.join(skin_dir, template_rel)

        # If the template path does not exist directly (e.g. if configured as archive/%Y/days/day.tmpl
        # but stored flat as day-%Y-%m-%d.html.tmpl), resolve to the template file in skin_dir.
        if not os.path.exists(template):
            basename = os.path.basename(template_rel)
            flat_path = os.path.join(skin_dir, basename)
            if os.path.exists(flat_path):
                template = flat_path
            else:
                archive_flat = os.path.join(skin_dir, 'archive', basename)
                if os.path.exists(archive_flat):
                    template = archive_flat
                elif 'week' in basename:
                    alt_name = basename.replace('%V', '%W') if '%V' in basename else basename.replace('%W', '%V')
                    alt_path = os.path.join(skin_dir, alt_name)
                    if os.path.exists(alt_path):
                        template = alt_path

        # Destination directory: either explicitly configured via destination_dir or derived from template
        custom_dest = report_dict.get('destination_dir')
        if custom_dest:
            destination_dir = os.path.join(
                self.config_dict['WEEWX_ROOT'],
                report_dict['HTML_ROOT'],
                custom_dest
            )
        else:
            destination_dir = os.path.join(
                self.config_dict['WEEWX_ROOT'],
                report_dict['HTML_ROOT'],
                os.path.dirname(template_rel)
            )

        encoding = report_dict.get('encoding', 'utf8').strip().lower()
        if encoding == 'utf-8':
            encoding = 'utf8'

        default_binding = report_dict['data_binding']
        return (template, destination_dir, encoding, default_binding)

    def generate(self, section, section_name, gen_ts, _pass=None):
        """Generate reports for the indicated section in two passes:
        Pass 1 ('current'): ToDate/LiveData/Global templates and the current active
                            span of each SummaryBy* section (always generated immediately).
        Pass 2 ('history'): Missing historical SummaryBy* spans in reverse chronological
                            order (newest -> oldest), bounded by archive_history,
                            archive_batch_size, and archive_max_run_time.
        """
        if _pass is None:
            self._run_start_time = time.time()
            self._backfill_count = 0
            self._backfill_limit_logged = False
            self._available_archives = None
            self._available_archives_changed = False
            self._scan_html_root = None
            self._live_data_targets = []
            ngen = self.generate(section, section_name, gen_ts, _pass='current')
            ngen += self.generate(section, section_name, gen_ts, _pass='history')
            if self._available_archives_changed and self._live_data_targets:
                self._available_archives_changed = False
                for live_sec, live_name in self._live_data_targets:
                    ngen += self.generate(live_sec, live_name, gen_ts, _pass='refresh_live')
            return ngen

        ngen = 0
        for subsection in self._order_subsections(section, _pass):
            if 'summarize_by' not in section[subsection]:
                if subsection in self.generator_dict:
                    section[subsection]['summarize_by'] = subsection
            ngen += self.generate(section[subsection], subsection, gen_ts, _pass=_pass)

        if 'template' not in section:
            return ngen

        report_dict = weewx.cheetahgenerator.accumulateLeaves(section)
        summarize_by = report_dict.get('summarize_by')
        is_summary = summarize_by in self.generator_dict

        # Non-summary templates (ToDate, Global, LiveData) only run in Pass 1 ('current')
        if _pass == 'history' and not is_summary:
            return ngen

        generate_once = to_bool(report_dict.get('generate_once', False))
        if generate_once and not self.first_run:
            return ngen

        (template, dest_dir_pattern, encoding, default_binding) = self._prepGen(report_dict)

        default_archive = self.db_binder.get_manager(default_binding)
        first_good_ts = default_archive.firstGoodStamp()
        if not first_good_ts:
            if _pass == 'current':
                log.info("Skipping template %s: cannot find start time", section['template'])
            return ngen

        if gen_ts:
            record = default_archive.getRecord(gen_ts, max_delta=to_int(report_dict.get('max_delta')))
            if record:
                stop_ts = record['dateTime']
            else:
                if _pass == 'current':
                    log.info("Skipping template %s: generate time %s not in database",
                             section['template'], timestamp_to_string(gen_ts))
                return ngen
        else:
            stop_ts = default_archive.lastGoodStamp()

        # Resolve archive_start_date (YYYY-MM-DD or keyword: all, current_year, current_month, current/today/none)
        archive_start_date_raw = report_dict.get('archive_start_date', '1970-01-01')
        archive_start_date_str = str(archive_start_date_raw).strip()
        start_ts, cutoff_ts = self._resolve_archive_start_date(
            archive_start_date_raw, first_good_ts, stop_ts
        )

        if stop_ts < start_ts:
            return ngen

        # Resolve enabled historical granularities (archive_history)
        enabled_history = self._parse_archive_history(
            report_dict.get('archive_history', 'all'), archive_start_date_raw
        )

        # In Pass 2 ('history'), disabled granularities do not backfill new historical
        # files, but still check the immediately preceding span to finalize an
        # already-existing file once after period rollover (e.g. yesterday's day page
        # or last week's page whose mtime < timespan.stop).
        finalize_only = (_pass == 'history' and summarize_by not in enabled_history)

        if is_summary:
            _spangen = self.generator_dict[summarize_by]
            all_spans = list(_spangen(start_ts, stop_ts))
            if _pass == 'current':
                spans_to_process = [ts for ts in all_spans if ts.includesArchiveTime(stop_ts)]
                if not spans_to_process and all_spans:
                    spans_to_process = [all_spans[-1]]
            elif finalize_only:
                spans_to_process = [ts for ts in reversed(all_spans) if not ts.includesArchiveTime(stop_ts)][:1]
            else:
                # Pass 2 ('history'): reverse chronological (newest -> oldest)
                spans_to_process = [ts for ts in reversed(all_spans) if not ts.includesArchiveTime(stop_ts)]
        else:
            spans_to_process = [TimeSpan(start_ts, stop_ts)]

        batch_size = to_int(report_dict.get('archive_batch_size', 50))
        max_run_time = to_int(report_dict.get('archive_max_run_time', 240))

        html_root = os.path.join(self.config_dict['WEEWX_ROOT'], report_dict['HTML_ROOT'])
        stop_dt_for_scan = datetime.datetime.fromtimestamp(stop_ts)
        if self._available_archives is None or self._scan_html_root != html_root:
            self._available_archives = self._scan_existing_archives(html_root, stop_dt_for_scan)
            self._scan_html_root = html_root

        is_live_data = (not is_summary and os.path.basename(report_dict['template']) == 'live.json.tmpl')
        if _pass == 'current' and is_live_data:
            if not any(existing_sec is section for existing_sec, _ in self._live_data_targets):
                self._live_data_targets.append((section, section_name))

        for timespan in spans_to_process:
            if hasattr(self, 'stop_event') and self.stop_event and self.stop_event.is_set():
                log.debug("Stop event set. Stopping template '%s'", template)
                return ngen

            start_tt = time.localtime(timespan.start)
            stop_tt = time.localtime(timespan.stop)
            ref_dt = datetime.datetime.fromtimestamp(timespan.start)

            if summarize_by in self.format_dict:
                date_str = time.strftime(self.format_dict[summarize_by], start_tt)
                if not finalize_only and date_str not in self.outputted_dict[summarize_by]:
                    self.outputted_dict[summarize_by].append(date_str)
                _filename = self._getFileName(template, timespan.start)
            else:
                _filename = self._getFileName(template, timespan.stop)

            # Evaluate strftime codes in destination directory (e.g. archive/%Y/days -> archive/2026/days)
            eval_dest_dir = dest_dir_pattern
            if '%' in eval_dest_dir or 'YYYY' in eval_dest_dir or 'MM' in eval_dest_dir:
                eval_dest_dir = eval_dest_dir.replace('YYYY', '%Y').replace('MM', '%m')
                eval_dest_dir = ref_dt.strftime(eval_dest_dir)

            _fullname = os.path.join(eval_dest_dir, _filename)

            # Skip summary files outside the active timespan that already exist on disk,
            # unless their embedded skin version is older than the minimum required version
            # or they were last written before their period ended (rollover finalization).
            file_exists = os.path.exists(_fullname)
            needs_finalization = (
                is_summary
                and file_exists
                and not timespan.includesArchiveTime(stop_ts)
                and self._needs_finalization(_fullname, timespan, stop_ts)
            )
            if finalize_only:
                if not (file_exists and needs_finalization):
                    continue
                needs_refresh = False
            else:
                needs_refresh = (
                    is_summary
                    and file_exists
                    and self._needs_version_refresh(_fullname, summarize_by, report_dict)
                )
            if is_summary \
                    and file_exists \
                    and not timespan.includesArchiveTime(stop_ts) \
                    and not needs_refresh \
                    and not needs_finalization:
                continue

            # Staleness check (bypassed for version upgrade refresh, rollover finalization, or live refresh)
            stale = to_int(report_dict.get('stale_age'))
            if stale is not None and not needs_refresh and not needs_finalization and _pass != 'refresh_live':
                t_now = time.time()
                try:
                    last_mod = os.path.getmtime(_fullname)
                    if t_now - last_mod < stale:
                        continue
                except os.error:
                    pass

            # In Pass 2 ('history'), enforce per-cycle backfill batch size & time budget
            # (always allow finalizing a single rolled-over file)
            if _pass == 'history' and not needs_finalization:
                elapsed = time.time() - (self._run_start_time or time.time())
                batch_exceeded = batch_size is not None and batch_size > 0 and self._backfill_count >= batch_size
                time_exceeded = max_run_time is not None and max_run_time > 0 and elapsed >= max_run_time
                if batch_exceeded or time_exceeded:
                    if not self._backfill_limit_logged:
                        log.info(
                            "NeowxArchiveGenerator: Backfill batch limit reached "
                            "(generated %d historical files in %.1fs); "
                            "remaining historical archives will continue on next cycle.",
                            self._backfill_count, elapsed
                        )
                        self._backfill_limit_logged = True
                    return ngen

            # Calculate relative base_path from destination to HTML_ROOT
            rel_dir = os.path.relpath(os.path.dirname(_fullname), html_root)
            if rel_dir == '.':
                base_path = ''
            else:
                depth = len(rel_dir.replace('\\', '/').strip('/').split('/'))
                base_path = '../' * depth

            # Build navigation context
            nav_context = self._build_nav_context(
                timespan, start_ts, stop_ts, cutoff_ts, base_path,
                archive_start_date_str, summarize_by, enabled_history,
                is_live_data=is_live_data
            )

            # Ensure parent directories exist
            try:
                os.makedirs(os.path.dirname(_fullname), exist_ok=True)
            except OSError:
                pass

            # Prepare search list
            searchList = self._getSearchList(
                encoding, timespan, default_binding, section_name,
                os.path.join(os.path.dirname(report_dict['template']), _filename)
            )
            # Inject navigation context as top search list dictionary
            searchList.insert(0, nav_context)

            # Compile template
            t1 = time.time()
            try:
                compiled_template = Cheetah.Template.Template(
                    file=template,
                    searchList=searchList,
                    filter='AssureUnicode',
                    filtersLib=weewx.cheetahgenerator
                )
            except Exception as e:
                log.error("Compilation of template %s failed with exception '%s'", template, type(e))
                weeutil.logger.log_traceback(log.error, "****  ")
                continue

            # Evaluate template
            try:
                unicode_string = compiled_template.respond()
            except Exception as e:
                log.error("Evaluation of template %s failed with exception '%s'", template, type(e))
                weeutil.logger.log_traceback(log.error, "****  ")
                continue

            # Encode string
            if encoding == 'html_entities':
                byte_string = unicode_string.encode('ascii', 'xmlcharrefreplace')
            elif encoding == 'strict_ascii':
                byte_string = unicode_string.encode('ascii', 'ignore')
            elif encoding == 'normalized_ascii':
                normalized = unicodedata.normalize('NFD', unicode_string)
                byte_string = normalized.encode('ascii', 'ignore')
            else:
                byte_string = unicode_string.encode(encoding)

            # Write file atomically
            try:
                tmpname = _fullname + '.tmp'
                with open(tmpname, mode='wb') as fd:
                    fd.write(byte_string)
                os.replace(tmpname, _fullname)
                ngen += 1
                if is_summary:
                    self._record_generated_archive(summarize_by, ref_dt, _fullname)
                if _pass == 'history' and not needs_finalization:
                    self._backfill_count += 1
            except Exception as e:
                log.error("Failed writing output file %s: %s", _fullname, e)
                try:
                    os.unlink(tmpname)
                except OSError:
                    pass

        return ngen

    def _build_nav_context(self, timespan, start_ts, stop_ts, cutoff_ts, base_path,
                           archive_start_date_str, summarize_by, enabled_history=None,
                           is_live_data=False):
        """Constructs rich navigation and URL helpers for templates."""
        if summarize_by in ('SummaryByDay', 'SummaryByWeek', 'SummaryByMonth', 'SummaryByYear'):
            ref_dt = datetime.datetime.fromtimestamp(timespan.start)
        else:
            ref_dt = datetime.datetime.fromtimestamp(stop_ts)
        start_dt = datetime.datetime.fromtimestamp(start_ts)
        stop_dt = datetime.datetime.fromtimestamp(stop_ts)

        days_enabled = enabled_history is None or ('SummaryByDay' in enabled_history)
        weeks_enabled = enabled_history is None or ('SummaryByWeek' in enabled_history)
        months_enabled = enabled_history is None or ('SummaryByMonth' in enabled_history)
        years_enabled = enabled_history is None or ('SummaryByYear' in enabled_history)

        yr = ref_dt.year
        mo = ref_dt.month
        day = ref_dt.day
        iso_yr, iso_wk, _ = ref_dt.isocalendar()

        # Latest/current timestamps for direct navigation
        stop_yr = stop_dt.year
        stop_mo = stop_dt.month
        stop_day = stop_dt.day
        stop_monday = stop_dt.date() - datetime.timedelta(days=stop_dt.weekday())
        stop_wk_yr = stop_monday.year
        stop_wk_num = stop_monday.isocalendar()[1]

        avail = self._available_archives
        avail_years = set(avail['years']) if avail else {stop_yr}
        avail_months = set(avail['months']) if avail else {(stop_yr, stop_mo)}
        avail_weeks = set(avail['weeks']) if avail else {(stop_wk_yr, stop_wk_num)}
        avail_days = set(avail['days']) if avail else {stop_dt.date()}

        # Day navigation (disk-aware even when days history backfill is disabled)
        prev_day_dt = ref_dt - datetime.timedelta(days=1)
        next_day_dt = ref_dt + datetime.timedelta(days=1)
        if days_enabled:
            prev_day_date = prev_day_dt.date() if prev_day_dt.date() >= start_dt.date() else max((d for d in avail_days if d < ref_dt.date()), default=None)
            next_day_date = next_day_dt.date() if next_day_dt.date() <= stop_dt.date() else None
        else:
            prev_day_date = max((d for d in avail_days if d < ref_dt.date()), default=None)
            next_day_date = min((d for d in avail_days if d > ref_dt.date()), default=None)
        has_prev_day = prev_day_date is not None
        has_next_day = next_day_date is not None

        # Week navigation (disk-aware even when weeks history backfill is disabled)
        ref_monday = ref_dt.date() - datetime.timedelta(days=ref_dt.weekday())
        cur_wk_key = (ref_monday.year, ref_monday.isocalendar()[1])
        prev_wk_monday = ref_monday - datetime.timedelta(days=7)
        prev_wk_sunday = prev_wk_monday + datetime.timedelta(days=6)
        next_wk_monday = ref_monday + datetime.timedelta(days=7)
        if weeks_enabled:
            prev_wk_key = (prev_wk_monday.year, prev_wk_monday.isocalendar()[1]) if prev_wk_sunday >= start_dt.date() else max((w for w in avail_weeks if w < cur_wk_key), default=None)
            next_wk_key = (next_wk_monday.year, next_wk_monday.isocalendar()[1]) if next_wk_monday <= stop_dt.date() else None
        else:
            prev_wk_key = max((w for w in avail_weeks if w < cur_wk_key), default=None)
            next_wk_key = min((w for w in avail_weeks if w > cur_wk_key), default=None)
        has_prev_week = prev_wk_key is not None
        has_next_week = next_wk_key is not None

        # Month navigation (disk-aware even when months history backfill is disabled)
        cur_mo_key = (yr, mo)
        prev_mo_yr = yr if mo > 1 else yr - 1
        prev_mo = mo - 1 if mo > 1 else 12
        next_mo_yr = yr if mo < 12 else yr + 1
        next_mo = mo + 1 if mo < 12 else 1
        if months_enabled:
            prev_mo_key = (prev_mo_yr, prev_mo) if datetime.date(prev_mo_yr, prev_mo, 1) >= datetime.date(start_dt.year, start_dt.month, 1) else max((m for m in avail_months if m < cur_mo_key), default=None)
            next_mo_key = (next_mo_yr, next_mo) if datetime.date(next_mo_yr, next_mo, 1) <= datetime.date(stop_dt.year, stop_dt.month, 1) else None
        else:
            prev_mo_key = max((m for m in avail_months if m < cur_mo_key), default=None)
            next_mo_key = min((m for m in avail_months if m > cur_mo_key), default=None)
        has_prev_month = prev_mo_key is not None
        has_next_month = next_mo_key is not None

        # Year navigation (disk-aware even when years history backfill is disabled)
        if years_enabled:
            year_list = sorted(avail_years | set(range(start_dt.year, stop_dt.year + 1)))
            prev_yr_val = (yr - 1) if (yr - 1) >= start_dt.year else max((y for y in avail_years if y < yr), default=None)
            next_yr_val = (yr + 1) if (yr + 1) <= stop_dt.year else None
        else:
            year_list = sorted(avail_years) if avail_years else [stop_yr]
            prev_yr_val = max((y for y in avail_years if y < yr), default=None)
            next_yr_val = min((y for y in avail_years if y > yr), default=None)
        has_prev_year = prev_yr_val is not None
        has_next_year = next_yr_val is not None

        # Check if viewing current day / week / month / year
        is_current_day = ref_dt.date() == stop_dt.date()
        is_current_week = iso_yr == stop_dt.isocalendar()[0] and iso_wk == stop_dt.isocalendar()[1]
        is_current_month = yr == stop_dt.year and mo == stop_dt.month
        is_current_year = yr == stop_dt.year

        context_year_str = f"{yr:04d}"
        context_month_str = f"{mo:02d}"
        context_week_str = f"{iso_wk:02d}"
        context_day_str = f"{yr:04d}-{mo:02d}-{day:02d}"

        # Effective start date for the current page's header picker (or global start for live.json)
        if is_live_data:
            picker_start_dt = start_dt
        elif summarize_by == 'SummaryByYear':
            picker_start_dt = datetime.datetime(year_list[0], 1, 1)
        elif summarize_by == 'SummaryByMonth':
            min_mo = min(avail_months) if avail_months else (stop_yr, stop_mo)
            if months_enabled:
                min_mo = min(min_mo, (start_dt.year, start_dt.month))
            picker_start_dt = datetime.datetime(min_mo[0], min_mo[1], 1)
        elif summarize_by == 'SummaryByWeek':
            if weeks_enabled:
                picker_start_dt = start_dt
            else:
                min_wk = min(avail_weeks) if avail_weeks else (stop_wk_yr, stop_wk_num)
                try:
                    wk_mon = datetime.date.fromisocalendar(min_wk[0], min_wk[1], 1)
                except ValueError:
                    wk_mon = datetime.date(min_wk[0], 1, 1)
                picker_start_dt = datetime.datetime.combine(wk_mon, datetime.time.min)
        else:
            min_day = min(avail_days) if avail_days else stop_dt.date()
            if days_enabled:
                min_day = min(min_day, start_dt.date())
            picker_start_dt = datetime.datetime.combine(min_day, datetime.time.min)

        archive_years = [f"{y:04d}" for y in year_list]
        archive_years_reversed = [f"{y:04d}" for y in reversed(year_list)]

        current_live_url = f"{base_path}index.html"
        current_day_url = f"{base_path}index.html"
        current_week_url = f"{base_path}archive/{stop_wk_yr:04d}/weeks/week-{stop_wk_yr:04d}-{stop_wk_num:02d}.html"
        current_month_url = f"{base_path}archive/{stop_yr:04d}/months/month-{stop_yr:04d}-{stop_mo:02d}.html"
        current_year_url = f"{base_path}archive/{stop_yr:04d}/year-{stop_yr:04d}.html"

        # Context-dependent URLs when viewing different scales
        if summarize_by == 'SummaryByYear':
            target_mo = stop_mo if is_current_year else 12
            target_mo_key = (yr, target_mo)
            ctx_month_str = f"{target_mo:02d}"
            context_month_link = f"{base_path}archive/{context_year_str}/months/month-{context_year_str}-{ctx_month_str}.html"
            if is_current_year:
                target_wk_key = (stop_wk_yr, stop_wk_num)
                context_week_link = current_week_url
            else:
                jan1 = datetime.date(yr, 1, 1)
                first_monday_yr = jan1 if jan1.weekday() == 0 else jan1 + datetime.timedelta(days=(7 - jan1.weekday()))
                if first_monday_yr < start_dt.date() and start_dt.year == yr:
                    first_monday_yr = start_dt.date() - datetime.timedelta(days=start_dt.date().weekday())
                yr_wk_yr = first_monday_yr.year
                yr_wk_num = first_monday_yr.isocalendar()[1]
                target_wk_key = (yr_wk_yr, yr_wk_num)
                context_week_link = f"{base_path}archive/{yr_wk_yr:04d}/weeks/week-{yr_wk_yr:04d}-{yr_wk_num:02d}.html"
            target_day_date = stop_dt.date() if is_current_year else datetime.date(yr, 1, 1)
            target_day_str = target_day_date.strftime('%Y-%m-%d')
            context_day_link = f"{base_path}index.html" if is_current_year else f"{base_path}archive/{context_year_str}/days/day-{target_day_str}.html"
        elif summarize_by == 'SummaryByMonth':
            target_mo_key = (yr, mo)
            context_month_link = f"{base_path}archive/{context_year_str}/months/month-{context_year_str}-{context_month_str}.html"
            if is_current_month:
                target_wk_key = (stop_wk_yr, stop_wk_num)
                context_week_link = current_week_url
            else:
                first_day_mo = datetime.date(yr, mo, 1)
                first_monday_mo = first_day_mo if first_day_mo.weekday() == 0 else first_day_mo + datetime.timedelta(days=(7 - first_day_mo.weekday()))
                if first_monday_mo < start_dt.date() and (start_dt.year, start_dt.month) == (yr, mo):
                    first_monday_mo = start_dt.date() - datetime.timedelta(days=start_dt.date().weekday())
                elif first_monday_mo > stop_dt.date():
                    first_monday_mo = stop_monday
                mo_wk_yr = first_monday_mo.year
                mo_wk_num = first_monday_mo.isocalendar()[1]
                target_wk_key = (mo_wk_yr, mo_wk_num)
                context_week_link = f"{base_path}archive/{mo_wk_yr:04d}/weeks/week-{mo_wk_yr:04d}-{mo_wk_num:02d}.html"
            target_day = stop_day if is_current_month else 1
            target_day_date = datetime.date(yr, mo, target_day)
            context_day_link = f"{base_path}index.html" if is_current_month else f"{base_path}archive/{context_year_str}/days/day-{context_year_str}-{context_month_str}-{target_day:02d}.html"
        elif summarize_by == 'SummaryByWeek':
            target_mo_key = (yr, mo)
            target_wk_key = cur_wk_key
            target_day_date = stop_dt.date() if is_current_week else ref_dt.date()
            context_month_link = f"{base_path}archive/{context_year_str}/months/month-{context_year_str}-{context_month_str}.html"
            context_week_link = f"{base_path}archive/{ref_monday.year:04d}/weeks/week-{ref_monday.year:04d}-{ref_monday.isocalendar()[1]:02d}.html"
            context_day_link = f"{base_path}index.html" if is_current_week else f"{base_path}archive/{context_year_str}/days/day-{context_day_str}.html"
        else:
            target_mo_key = (yr, mo)
            target_wk_key = cur_wk_key
            target_day_date = ref_dt.date()
            context_month_link = f"{base_path}archive/{context_year_str}/months/month-{context_year_str}-{context_month_str}.html"
            context_week_link = f"{base_path}archive/{ref_monday.year:04d}/weeks/week-{ref_monday.year:04d}-{ref_monday.isocalendar()[1]:02d}.html"
            today_iso = stop_dt.strftime('%Y-%m-%d')
            context_day_link = f"{base_path}index.html" if (is_current_day or context_day_str == today_iso) else f"{base_path}archive/{context_year_str}/days/day-{context_day_str}.html"

        # If a historical granularity is disabled via archive_history and the target
        # page does not exist on disk, point navbar scale links to the active page.
        if not days_enabled and target_day_date not in avail_days:
            context_day_link = current_day_url
        if not weeks_enabled and target_wk_key not in avail_weeks:
            context_week_link = current_week_url
        if not months_enabled and target_mo_key not in avail_months:
            context_month_link = current_month_url
        context_year_link = (
            f"{base_path}archive/{context_year_str}/year-{context_year_str}.html"
            if (years_enabled or yr in avail_years)
            else current_year_url
        )

        # Fallback card_datetime if accessed before inc/card_datetime.inc
        card_dt_fallback = self.skin_dict.get('Extras', {}).get('Formatting', {}).get('datetime', '%Y-%m-%d %H:%M')
        if summarize_by == 'SummaryByDay':
            card_dt_fallback = self.skin_dict.get('Extras', {}).get('Formatting', {}).get('datetime_today', '%H:%M')

        archive_available_json = self._serialize_archive_available(self._available_archives) if is_live_data else ''

        return {
            'base_path': base_path,
            'card_datetime': card_dt_fallback,
            'archive_start_date': picker_start_dt.strftime('%Y-%m-%d'),
            'archive_stop_date': stop_dt.strftime('%Y-%m-%d'),
            'archive_start_year': picker_start_dt.year,
            'archive_stop_year': stop_dt.year,
            'archive_years': archive_years,
            'archive_years_reversed': archive_years_reversed,
            'archive_available_json': archive_available_json,
            'context_year': context_year_str,
            'context_month': context_month_str,
            'context_month_name': ref_dt.strftime("%B"),
            'context_week': context_week_str,
            'context_day': context_day_str,
            'context_day_num': f"{day:02d}",

            # Current URLs for navbar/switcher links
            'current_live_url': current_live_url,
            'current_day_url': current_day_url,
            'current_week_url': current_week_url,
            'current_month_url': current_month_url,
            'current_year_url': current_year_url,

            # URLs for scale switching from current context
            'context_live_url': f"{base_path}index.html",
            'context_day_url': context_day_link,
            'context_week_url': context_week_link,
            'context_month_url': context_month_link,
            'context_year_url': context_year_link,
            'context_noaa_year_url': f"{base_path}archive/NOAA/NOAA-{context_year_str}.txt",
            'context_noaa_month_url': f"{base_path}archive/NOAA/NOAA-{context_year_str}-{context_month_str}.txt",

            # Stepper URLs and state
            'is_current_day': is_current_day,
            'is_current_week': is_current_week,
            'is_current_month': is_current_month,
            'is_current_year': is_current_year,

            'has_prev_day': has_prev_day,
            'has_next_day': has_next_day,
            'prev_day_url': f"{base_path}archive/{prev_day_date.year:04d}/days/day-{prev_day_date.strftime('%Y-%m-%d')}.html" if has_prev_day else '#',
            'next_day_url': (f"{base_path}index.html" if next_day_date >= stop_dt.date() else f"{base_path}archive/{next_day_date.year:04d}/days/day-{next_day_date.strftime('%Y-%m-%d')}.html") if has_next_day else '#',

            'has_prev_week': has_prev_week,
            'has_next_week': has_next_week,
            'prev_week_url': f"{base_path}archive/{prev_wk_key[0]:04d}/weeks/week-{prev_wk_key[0]:04d}-{prev_wk_key[1]:02d}.html" if has_prev_week else '#',
            'next_week_url': f"{base_path}archive/{next_wk_key[0]:04d}/weeks/week-{next_wk_key[0]:04d}-{next_wk_key[1]:02d}.html" if has_next_week else '#',

            'has_prev_month': has_prev_month,
            'has_next_month': has_next_month,
            'prev_month_url': f"{base_path}archive/{prev_mo_key[0]:04d}/months/month-{prev_mo_key[0]:04d}-{prev_mo_key[1]:02d}.html" if has_prev_month else '#',
            'next_month_url': f"{base_path}archive/{next_mo_key[0]:04d}/months/month-{next_mo_key[0]:04d}-{next_mo_key[1]:02d}.html" if has_next_month else '#',

            'has_prev_year': has_prev_year,
            'has_next_year': has_next_year,
            'prev_year_url': f"{base_path}archive/{prev_yr_val:04d}/year-{prev_yr_val:04d}.html" if has_prev_year else '#',
            'next_year_url': f"{base_path}archive/{next_yr_val:04d}/year-{next_yr_val:04d}.html" if has_next_year else '#',
        }
