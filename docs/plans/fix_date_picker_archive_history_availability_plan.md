# Plan: Disk-Backed Archive Availability & Date Picker Fix for `archive_history`

## 1. Problem Summary & Root Cause Analysis

When running WeeWX with partial archive history such as:
```ini
[CheetahGenerator]
    archive_history = months_years
```
all expected HTML files are generated on disk (historical years & months, plus the active current week and day), **but the interactive date picker and steppers behave incorrectly**:

### Root Cause 1: Single `archive_start_date` in `live.json` Clobbers All Scales
- In `bin/user/neowx_archive.py` (`_build_nav_context`, lines 698–710), `picker_start_dt` is computed per template.
- When generating `live.json.tmpl` (`[[LiveData]]`), `summarize_by` is `None`. Because `days` is not in `archive_history = months_years`, execution falls into:
  ```python
  elif summarize_by not in ('SummaryByYear', 'SummaryByMonth', 'SummaryByWeek') and not days_enabled:
      picker_start_dt = stop_dt
  ```
- As a result, `live.json` is written with `"archive_start_date": "<today>"` (e.g. `"2026-11-24"`).
- On every non-current page (`month-2026-09.html`, `year-2023.html`, etc.), `skins/neowx-material/js/neowx-live.js` fetches `live.json` and calls `window.nxUpdateStartDate(data.archive_start_date)`.
- `skins/neowx-material/js/neowx-date-nav.js` overwrites the page's picker bounds to `[2026-11-24, 2026-11-24]`, collapsing the Month picker's year selector to `2026` and disabling every month except `Nov` — even while viewing `month-2026-09.html`.

### Root Cause 2: Year Picker Has No Client-Side Dynamic Rendering
- `neowx-date-nav.js` initializes Day (`.nwm-picker-calendar`), Week (`.nwm-picker-week`), and Month (`.nwm-picker-month`) pickers, but has **no `initYearPicker()` / `renderYearPicker()`**.
- Static/frozen `year-YYYY.html` pages only show the server-baked `#for $yr in $archive_years_reversed` from build time (and `year_summary` has `stale_age = 86400`), so they cannot dynamically reflect newly available years or config changes from `live.json`.

### Root Cause 3: Config-Only Bounds Ignore Accumulated Files on Disk
- `_build_nav_context()` previously checked `days_enabled` / `weeks_enabled` strictly from `archive_history`.
- When WeeWX runs continuously with `archive_history = months_years`, Pass 1 generates today's `day-YYYY-MM-DD.html` and the current `week-YYYY-WW.html` and **never deletes them** after midnight or week rollover.
- Tomorrow (`2026-11-25`), `day-2026-11-24.html` still exists on disk; next week (CW 49), `week-2026-48.html` still exists on disk. Likewise, if historical files were previously generated or partially backfilled, those files remain on disk.
- Config-only bounds hid those existing files from the date picker and disabled the `<` stepper chevron.

### Root Cause 4: Yesterday's `day-YYYY-MM-DD.html` Retains Active-Day Redirect After Midnight
- In `skins/neowx-material/day-%Y-%m-%d.html.tmpl` (lines 416–419), when today's `day-YYYY-MM-DD.html` is generated with `is_current_day = True`, it bakes an unconditional `<script>window.location.replace('.../index.html');</script>` and `<meta http-equiv="refresh" content="0; url=.../index.html">` into the file.
- After midnight, `NeowxArchiveGenerator` skips `day-2026-11-24.html` because `file_exists` is already `True` (and under `archive_history = months_years`, `SummaryByDay` is skipped in Pass 2).
- Without finalizing rolled-over files and making the redirect date-aware, clicking yesterday in the date picker would immediately bounce the user back to `index.html` and miss the final records before midnight.

---

## 2. Proposed Architecture & Design

### A. Disk-Backed Archive Availability Index (`bin/user/neowx_archive.py`)
Instead of guessing availability solely from `archive_history` config or emitting a single scalar `archive_start_date`, `NeowxArchiveGenerator` will build an exact, lightweight inventory of **actually existing HTML archive files on disk**:

1. **Fast Single-Pass Filesystem Scan (`_scan_existing_archives(html_root, stop_dt)`)**:
   - Runs once at the beginning of `NeowxArchiveGenerator.generate()` (`_pass is None`) using `os.scandir()` across `HTML_ROOT/archive/`:
     - `archive/<YYYY>/year-<YYYY>.html` → `years: set[int]`
     - `archive/<YYYY>/months/month-<YYYY>-<MM>.html` → `months: set[tuple[int, int]]`
     - `archive/<YYYY>/weeks/week-<YYYY>-<WW>.html` → `weeks: set[tuple[int, int]]`
     - `archive/<YYYY>/days/day-<YYYY>-<MM>-<DD>.html` → `days: set[datetime.date]`
   - Validates parsed dates/ranges and excludes any future entries beyond `stop_dt`.
   - Always unions in the current active period (`stop_dt`'s year, month, week Monday `(wk_yr, wk_num)`, and `stop_dt.date()`), since Pass 1 guarantees today (`index.html`) and current week/month/year exist.
   - Performance: Only reads directory names via `os.scandir()` (no file opens, no extra stat calls) — typically <10 ms for 10 years of archives.

2. **In-Memory Tracking & Post-Pass-2 `live.json` Refresh**:
   - Whenever Pass 1 or Pass 2 writes a new summary HTML file, its key is immediately added to the in-memory availability sets.
   - Because Pass 1 generates `live.json` first (live-first behavior) and Pass 2 may backfill additional historical pages afterward, if Pass 2 added any newly generated HTML files, `[[LiveData]]` (`live.json`) is re-rendered once at the end of `generate()` so `live.json` immediately reflects the full set of files on disk.

3. **Compact Contiguous Range Encoding in `live.json`**:
   - Compress each scale's sorted available keys into contiguous `[start, end]` pairs:
     - `years`: consecutive integers (`y + 1`) → `[["2017", "2026"]]`
     - `months`: consecutive `(y, m)` across year boundaries → `[["2017-01", "2026-11"]]`
     - `weeks`: consecutive `(y, w)` within the same year (`y1 == y2 and w2 == w1 + 1`) → e.g. `[["2025-01", "2025-52"], ["2026-01", "2026-48"]]` (avoids 52/53-week ISO boundary assumptions completely)
     - `days`: consecutive calendar dates (`d + timedelta(days=1)`) → e.g. `[["2026-11-24", "2026-11-25"]]`
   - Example payload added to `live.json` (~150–400 bytes even for 10 years of data, and 100% exact even when gaps exist):
     ```json
     "archive_start_date": "2017-01-01",
     "archive_stop_date": "2026-11-24",
     "archive_available": {
         "years": [["2017", "2026"]],
         "months": [["2017-01", "2026-11"]],
         "weeks": [["2026-48", "2026-48"]],
         "days": [["2026-11-24", "2026-11-25"]]
     }
     ```
   - `archive_start_date` in `live.json` is fixed to always hold the true global earliest date (`start_dt`, e.g. `"2017-01-01"`) rather than `stop_dt`, preserving backward compatibility for legacy consumers.

---

### B. Rollover Finalization & Safe Active-Day Redirect
1. **Finalize Rolled-Over Existing Archive Files (`bin/user/neowx_archive.py`)**:
   - Add `_needs_finalization(filepath, timespan, stop_ts)`: returns `True` when an existing past summary file (`file_exists` and `not timespan.includesArchiveTime(stop_ts)`) has `os.path.getmtime(filepath) < timespan.stop` (meaning it was last written *before* its period ended).
   - For the immediately preceding span (e.g. yesterday's `day-YYYY-MM-DD.html`, last week's `week-YYYY-WW.html`, last month's `month-YYYY-MM.html`, last year's `year-YYYY.html`), if that file already exists on disk and `_needs_finalization` is `True`, regenerate it **once** (bypassing `stale_age`), even if its granularity is not in `archive_history` (it never creates *new* historical files for disabled granularities — it only finalizes files that already exist on disk!).
   - Once regenerated after `timespan.stop`, `mtime >= timespan.stop`, so it stays frozen permanently.

2. **Date-Aware Redirect Guard (`skins/neowx-material/day-%Y-%m-%d.html.tmpl`)**:
   - Remove the static `<meta http-equiv="refresh" content="0; url=${base_path}index.html">` and unconditional `window.location.replace`.
   - Replace with a lightweight inline script (emitted when `$is_current_day` is `True`) that checks the station's current day via the pre-warmed `window.NX_LIVE_DATA` (`data.today`, falling back to browser local date if unavailable) and **only** redirects to `${base_path}index.html` if `pageDay === today`.
   - Guarantees yesterday's day page NEVER traps a visitor in a redirect loop even if opened right after midnight before the next report cycle finishes.

---

### C. Per-Scale Navigation Context (`bin/user/neowx_archive.py` & `skins/neowx-material/inc/header.inc`)
1. **Accurate Server-Side Context (`_build_nav_context`)**:
   - Compute per-scale start/stop bounds and prev/next availability from the disk inventory (unioned with expected spans for granularities enabled in `archive_history`, so pages generated mid-backfill in Pass 2 get sensible initial static links while `live.json` drives live client-side truth):
     - **Day (`index.html`, `day-*.html`)**: Uses available days on disk (so tomorrow on `index.html`, `<` links directly to yesterday's `day-2026-11-24.html` even under `archive_history = months_years`).
     - **Week (`week-*.html`)**: Uses available weeks on disk (so next week, `<` links directly to `week-2026-48.html`).
     - **Month (`month-*.html`)**: Uses available months (`2017-01..2026-11`).
     - **Year (`year-*.html`)**: Uses available years (`2017..2026`), populating `archive_years` / `archive_years_reversed` with only actually available years.
     - **LiveData (`live.json.tmpl`)**: Uses global `start_dt` for `archive_start_date` and injects `archive_available_json`.
   - Navbar scale-switch links (`context_day_url`, `context_week_url`, `context_month_url`, `context_year_url`): Link to the contextual period if it exists in the available inventory (or is enabled for backfill), otherwise fall back cleanly to the current active period (`current_*_url`).
2. **Localized Stepper Labels in `inc/header.inc`**:
   - Add `data-label-prev`, `data-label-next`, `data-label-no-earlier`, `data-label-no-later` attributes (populated via `$gettext(...)`) on `#nwm-nav-hub` so client-side stepper updates preserve the active skin language instead of hardcoding English `"Next"`.

---

### D. Client-Side Picker & Stepper Overhaul (`neowx-live.js` & `neowx-date-nav.js`)
1. **`skins/neowx-material/js/neowx-live.js`**:
   - Allow `live.json` sync to run on ALL pages with `#nwm-nav-hub` (including `index.html`, where `head.inc` already pre-warms `window.NX_LIVE_DATA`), while keeping header date / almanac / footer chrome updates scoped to non-current pages as before.
   - When `data.archive_available` is present:
     - Store `window.NX_ARCHIVE_AVAILABLE = data.archive_available` and `window.NX_STOP_DATE = data.today`.
     - Call `window.nxUpdateArchiveAvailability(data.archive_available, data.today)` (single atomic update + single re-render).
     - Do **not** overwrite the picker's `startDate` with a single global scalar when `data.archive_available` is provided (retain `nxUpdateStartDate` only as a backward-compatible fallback when `data.archive_available` is absent).

2. **`skins/neowx-material/js/neowx-date-nav.js`**:
   - **Range Helper Utilities**:
     - `isKeyInRanges(key, ranges)` — exact membership check for `YYYY`, `YYYY-MM`, `YYYY-WW`, `YYYY-MM-DD`.
     - `getAvailableYears(ranges)` — sorted list of years containing ≥1 available entry.
     - `hasAvailableInMonth(year, month, dayRanges)` — checks whether a calendar month overlaps any available day range.
     - `findPrevAvailableKey(key, ranges, scale)` / `findNextAvailableKey(key, ranges, scale)` — finds the exact previous/next available key across contiguous ranges and gaps.
   - **Add Dynamic Year Picker (`initYearPicker()` / `renderYearPicker()`)**:
     - Dynamically populates `.nwm-picker-grid-years` from `archive_available.years` (descending), preserving the localized `.nwm-picker-title` and highlighting `contextYear`.
     - Ensures frozen `year-YYYY.html` pages always display newly added years and current availability.
   - **Update Month Picker (`renderMonthPicker`)**:
     - Populates year `<select>` and `<`/`>` year arrows strictly from years present in `archive_available.months` (always keeping the currently viewed `contextYear` reachable).
     - Enables each month `1..12` iff `isKeyInRanges(YYYY-MM, archive_available.months)`.
   - **Update Week Picker (`renderWeekPicker`)**:
     - Populates year `<select>` and `<`/`>` year arrows from years present in `archive_available.weeks`.
     - Enables each `CW WW` iff `isKeyInRanges(YYYY-WW, archive_available.weeks)`.
     - Disables month quick-filter tabs that contain zero available weeks in the selected year.
   - **Update Day Calendar Picker (`renderCalendarPicker`)**:
     - Populates year `<select>` from years present in `archive_available.days`.
     - Disables months in `#nx-dp-month-select` with zero available days (`!hasAvailableInMonth(...)`).
     - Steps `<` / `>` month arrows directly to the previous/next month that has available days (skipping empty gap months).
     - Enables each day cell iff `isKeyInRanges(YYYY-MM-DD, archive_available.days)`, routing `stopDateStr` / today to `index.html`.
   - **Upgrade `syncNextStepperButton()` → `syncStepperButtons()`**:
     - Dynamically syncs **both** Previous (`<`) and Next (`>`) stepper controls on every page (including `<` on `index.html` when yesterday exists, and `<`/`>` on frozen archive pages when new periods accumulate or backfill progresses).
     - Uses the localized labels from `#nwm-nav-hub`'s `data-label-*` attributes.
   - **Race-Free Initialization**:
     - Reads `window.NX_ARCHIVE_AVAILABLE` in `DateNavController` constructor if `live.json` resolved before `neowx-date-nav.js` ran, and exposes `window.nxUpdateArchiveAvailability` for when `live.json` resolves afterward.

---

## 3. Files to Modify

1. **[`bin/user/neowx_archive.py`](../../bin/user/neowx_archive.py)**
   - Bump `VERSION` (`"1.2.1"` → `"1.2.2"`).
   - Add `_scan_existing_archives()`, `_compress_ranges()`, `_serialize_archive_available()`, and `_needs_finalization()`.
   - Track newly written summary HTML files in memory during Pass 1 & Pass 2; refresh `live.json` at end of `generate()` if Pass 2 added new archive files.
   - Finalize already-existing immediately-preceding rolled-over files (`mtime < timespan.stop`) even when their granularity is disabled in `archive_history`.
   - Update `_build_nav_context()` to compute per-scale bounds, steppers, and `archive_available_json` from the disk inventory, and pass global `start_dt` for `live.json.tmpl`.
2. **[`skins/neowx-material/live.json.tmpl`](../../skins/neowx-material/live.json.tmpl)**
   - Emit `"archive_available": $archive_available_json` (guarded with `#if $varExists('archive_available_json')`) alongside accurate global `"archive_start_date"` and `"archive_stop_date"`.
3. **[`skins/neowx-material/inc/header.inc`](../../skins/neowx-material/inc/header.inc)**
   - Add `data-label-prev`, `data-label-next`, `data-label-no-earlier`, and `data-label-no-later` attributes on `#nwm-nav-hub`.
4. **[`skins/neowx-material/day-%Y-%m-%d.html.tmpl`](../../skins/neowx-material/day-%Y-%m-%d.html.tmpl)** *(preserve CRLF line endings)*
   - Replace static `<meta http-equiv="refresh">` + unconditional `window.location.replace` with a date-aware redirect script checking `window.NX_LIVE_DATA` (`data.today`) with local-date fallback.
5. **[`skins/neowx-material/js/neowx-live.js`](../../skins/neowx-material/js/neowx-live.js)**
   - Run `live.json` availability sync on all pages containing `#nwm-nav-hub` (including `index.html`).
   - Pass `data.archive_available` and `data.today` to `window.nxUpdateArchiveAvailability(...)`; only fall back to `nxUpdateStartDate` when `archive_available` is absent.
6. **[`skins/neowx-material/js/neowx-date-nav.js`](../../skins/neowx-material/js/neowx-date-nav.js)**
   - Add range helper utilities (`isKeyInRanges`, `getAvailableYears`, `hasAvailableInMonth`, `findPrevAvailableKey`, `findNextAvailableKey`).
   - Add `initYearPicker()` / `renderYearPicker()`.
   - Update `renderMonthPicker()`, `renderWeekPicker()`, and `renderCalendarPicker()` to use per-scale `archive_available` ranges (with fallback to `startDate`/`stopDate`).
   - Replace `syncNextStepperButton()` with bidirectional `syncStepperButtons()` covering both `<` and `>` across all 4 scales.

*(No new files added to `skins/neowx-material/`, so `install.py` requires no manifest changes, and no SCSS changes are required.)*

---

## 4. Verification Plan

1. **Python Unit & Integration Verification**:
   - Run targeted Python verification scripts against `NeowxArchiveGenerator` simulating a temporary `HTML_ROOT` with:
     - `archive_history = months_years` on Day 1 (`2026-11-24`: years `2017..2026`, months `2017-01..2026-11`, week `2026-48`, day `2026-11-24`).
     - Day 2 rollover (`2026-11-25`): verify `day-2026-11-24.html` is finalized once (`mtime >= timespan.stop`), remains visible in `archive_available.days` (`[["2026-11-24", "2026-11-25"]]`), and `has_prev_day` is `True` on `index.html`.
     - Week rollover (CW 49): verify `week-2026-48.html` is finalized and `archive_available.weeks` is `[["2026-48", "2026-49"]]`.
     - Gapped disk archives (e.g., `2025-01-01..2025-01-31` + `2026-11-24..2026-11-25`): verify range compression produces exact disjoint ranges and `live.json` is valid JSON.
     - `archive_history = all`, `years`, `none`, and `archive_start_date = current_year`.
2. **JavaScript Unit Verification (Node.js)**:
   - Verify range lookup, year/month extraction, prev/next key navigation across contiguous ranges and gaps, and picker rendering behavior for all 4 scales (Day, Week, Month, Year) including `month-2026-09.html` with `archive_history = months_years`.
3. **Syntax & Line-Ending Checks**:
   - `python3 -m py_compile bin/user/neowx_archive.py`
   - `node --check skins/neowx-material/js/neowx-live.js skins/neowx-material/js/neowx-date-nav.js`
   - Verify `day-%Y-%m-%d.html.tmpl` preserves CRLF and `git diff` stays clean and minimal.
