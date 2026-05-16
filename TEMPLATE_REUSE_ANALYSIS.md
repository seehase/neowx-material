# Cheetah Template Reuse Analysis

_Date: 2026-05-16_

## What the Documentation Actually Says

**`#include`** — confirmed NOT suitable for method sharing:
> *"Cheetah wraps each chunk of `#include` text inside a nested Template object. Each nested template has a copy of the main template's searchList."*

A nested template gets the WeeWX search list (day/week/obs/etc.) but NOT parent template's `#def` methods — those are methods on the parent's Python class, not in the search list. This is a hard constraint.

**`#extends`** — IS the correct mechanism, documented precisely for this use case:
> *"It's possible for a template to subclass another template or a pure Python class. `#extends` specifies the parent class. Cheetah imports the class mentioned automatically: `#extends Superclass` implicitly does `#from Superclass import Superclass`."*
> *"Because `#def` is handled at compile time… if a superclass placeholder calls a method that's overridden in a subclass, it's the subclass method that will be called."*

**`#block`** — designed for overriding specific sections in child templates:
> *"The `#block` directive allows you to mark a section of your template that can be selectively reimplemented in a subclass without copy-pasting the entire thing."*

**`ImportHooks`** — the documented solution for importing `.tmpl` files at runtime:
> *"Subvert Python import to make Cheetah import directly from `*.tmpl` files using import hooks: `from Cheetah import ImportHooks; ImportHooks.install(); sys.path.insert(0, 'path/to/template_dir')`"*

---

## Why Previous `#extends` Attempt Failed

WeeWX compiles templates via:
```python
Cheetah.Template.Template(file=template, searchList=searchList)
```
It never adds the skin directory to `sys.path`. So when the generated Python code executes
`import _chart_methods`, Python cannot find the file even though it is sitting right there
in the skin folder.

**The fix is documented**: A WeeWX SearchList Extension runs **before** template compilation
(`init_extensions` is called before `generate`). A tiny extension that calls
`ImportHooks.install()` and `sys.path.insert(0, skin_dir)` is all that's needed — it
installs before Cheetah ever touches a template.

---

## What Can and Cannot Be Shared

| Method | Shareable? | Reason |
|---|---|---|
| `getChartJsCode` | ✅ YES — all 7 templates | Only difference: series `has_data` check prefix (`'week.'`, `'month.'`, etc.) → replace with `$period_prefix` variable |
| `chartCard` | ✅ YES — 6 of 7 templates | Only difference: `has_data` check prefix → same fix. `index.html.tmpl` has a slightly different signature (no `$id` arg) |
| `valuesCard` | ✅ YES — 6 of 7 templates | Uses period-specific WeeWX objects (`$week.wind.avg` etc.) but ALL are reachable via `$getVar(pp + '.wind.avg')`. `index.html.tmpl` must stay unique (shows live current value + trend arrows, fundamentally different) |
| `getChartData` | ✅ PARTIALLY — see details below | Group B (week/yesterday/month/year) identical structure, shareable via global vars. Group C (month-%Y-%m, year-%Y) override base. index sets unique `period_data_span`. |

---

## Implementation Plan

### Step 1: `bin/user/chart_methods_loader.py` — fix the import issue (~15 lines)

A WeeWX SearchList Extension that runs once before any template is compiled. It:
1. Installs Cheetah's `ImportHooks` so Python can auto-compile and import `.tmpl` files
2. Inserts the skin directory onto `sys.path`

Registered in `skin.conf` under `[CheetahGenerator] → search_list_extensions`.

### Step 2: `skins/neowx-material/_chart_methods.tmpl` — the shared base

Contains the three shareable `#def` methods, all using `$period_prefix` as the period key:
- `#def valuesCard($name)` — uses `$getVar(pp + '.wind.avg')` etc., with `$period_datetime_fmt` for date formatting
- `#def chartCard($name, $id, $name2="XX")` — uses `$getVar(pp + '.' + name + '.has_data')`
- `#def getChartJsCode(...)` — uses `$getVar(pp + '.' + seriesN + '.has_data')` for all series checks

### Step 3: Update 6 page templates (not `index.html.tmpl`)

Each template gets a header block replacing their `#def` sections:
```cheetah
#encoding UTF-8
#extends _chart_methods

#set global $period_prefix  = "week"
#set global $period_datetime_fmt = $Extras.Formatting.datetime
```

Each template then contains only:
- `#attr $active_nav`
- `#def getChartData(...)` (if not shareable)
- The HTML layout
- The `$getChartJsCode(...)` call list

`index.html.tmpl` keeps its own `valuesCard` (fundamentally different) but can still
inherit `chartCard` and `getChartJsCode` from the base.

---

## Estimated Line Reduction

| What gets removed | Lines each | Templates | Saved |
|---|---|---|---|
| `getChartJsCode` body | ~100 | 6 | ~600 |
| `chartCard` body | ~15 | 6 | ~90 |
| `valuesCard` body (if shared) | ~110 | 6 | ~660 |
| **Total saved** | | | **~1,350 lines** |
| **New files** (`_chart_methods.tmpl` + loader) | | | +~145 |
| **Net reduction** | | | **~−1,200 lines** |

---

## Open Questions

1. **Is `getChartData()` shareable?** — **YES, partially.** See full analysis below.
2. **Include `valuesCard` in shared base?** (+660 lines saved, but all `$week.wind.avg`
   style references become `$getVar(pp + '.wind.avg')` — less readable but works)
3. **Import approach choice:**
   - **ImportHooks** (auto-compiles `_chart_methods.tmpl`, one SearchList Extension required)
   - **Pre-compile** (run `cheetah compile` once, put `_chart_methods.py` in `bin/user/`,
     no runtime extension needed — but requires recompiling when the base changes)

---

## Period-Specific Variables Per Template

| Template | `period_prefix` | `period_datetime_fmt` | Notes |
|---|---|---|---|
| `index.html.tmpl` | `"day"` | `datetime_today` | `valuesCard` unique — shows current reading |
| `week.html.tmpl` | `"week"` | `datetime` | |
| `yesterday.html.tmpl` | `"yesterday"` | `datetime_today` | data-slicing splice logic unique |
| `month.html.tmpl` | `"month"` | `datetime` | has `temperatureThresholdDays` block |
| `month-%Y-%m.html.tmpl` | `"month"` | `datetime` | has `temperatureThresholdDays` block |
| `year.html.tmpl` | `"year"` | `datetime_archive` | has `temperatureThresholdDays` block |
| `year-%Y.html.tmpl` | `"year"` | `datetime_archive` | has `temperatureThresholdDays` block |

---

## `getChartData()` Deep Analysis

### Three distinct implementation groups

**Group A — Sub-day interval, unique span: `index.html.tmpl`**
```
span($time_delta=$custom_time_delta)   ← rolling window aligned to last full hour
default interval : current_timespan
rain + ET combined: current_rain_timespan
windrun          : (none — windrun not on current page)
```

**Group B — Sub-day interval, standard pattern: `week`, `yesterday`, `month`, `year`**

Body structure is **100% identical**. Only the config key prefix and `$span()` call differ:

| Template | `$span()` call | default interval key | rain key | ET key | windrun key |
|---|---|---|---|---|---|
| `yesterday` | `$span($day_delta=1,$boundary='midnight')` | `current_timespan` | `current_rain_timespan` | (combined with rain) | (none) |
| `week` | `$span($week_delta=1,$boundary='midnight')` | `week_timespan` | `week_rain_timespan` | `week_ET_timespan` | `week_windrun_timespan` |
| `month` | `$span($day_delta=31,$boundary='midnight')` | `month_timespan` | `month_rain_timespan` | `month_ET_timespan` | `month_windrun_timespan` |
| `year` | `$span($year_delta=1,$boundary='midnight')` | `year_timespan` | `year_rain_timespan` | `year_ET_timespan` | `year_windrun_timespan` |

**Group C — Calendar day iteration: `month-%Y-%m`, `year-%Y`**
```
list($month.days) / list($year.days)   ← one data point per exact calendar day
No config interval keys needed at all.
```

### Verdict: ALL differences are intentional

| Difference | Reason |
|---|---|
| `index` uses `$time_delta=$custom_time_delta` | Rolling window aligned to last full hour — unique to live page |
| `yesterday` reuses `current_*` config keys | Same 24-hour resolution as today; no separate `yesterday_timespan` needed |
| `week/month/year` have separate `ET_timespan` | Longer periods need independently configurable ET resolution |
| `week/month/year` have `windrun_timespan` | Windrun only shown on those pages, needs its own resolution |
| `month-%Y-%m`, `year-%Y` use `.days` iterator | Archive pages need exact calendar alignment, not a rolling window |

### Can `getChartData` be shared?

**Group B — YES** (4 templates): set 4–5 global variables at top of each template,
use a single shared `getChartData` body in the base template:

```cheetah
## Set at top of week.html.tmpl (example):
#set global $period_default_interval  = int($Extras.Charts.week_timespan)
#set global $period_rain_interval     = int($Extras.Charts.week_rain_timespan)
#set global $period_ET_interval       = int($Extras.Charts.week_ET_timespan)
#set global $period_windrun_interval  = int($Extras.Charts.week_windrun_timespan)
#set global $period_data_span         = $span($week_delta=1, $boundary='midnight')
```

**Group A — YES** with one extra variable (`$period_data_span = $span($time_delta=$custom_time_delta)`).

**Group C — OVERRIDE** (`month-%Y-%m`, `year-%Y` define their own `#def getChartData`
in the child template, overriding the base — exactly what `#extends` + `#def` override is for).

### Revised line savings including `getChartData`

| What gets removed | Lines each | Templates | Saved |
|---|---|---|---|
| `getChartJsCode` body | ~100 | 6 | ~600 |
| `chartCard` body | ~15 | 6 | ~90 |
| `valuesCard` body (if shared) | ~110 | 6 | ~660 |
| `getChartData` body (Group B + A) | ~15 | 5 | ~75 |
| **Total saved** | | | **~1,425 lines** |
| **New files** (`_chart_methods.tmpl` + loader) | | | +~160 |
| **Net reduction** | | | **~−1,265 lines** |

---

## Group B — Concrete Implementation Outcome

### Shared `getChartData` body — goes into `_chart_methods.tmpl`

Replace the four individual `#def getChartData` blocks with a single definition that reads
the period-specific values from global variables set by each child template:

```cheetah
## +-------------------------------------------------------------------------+
## | Get data array for a chart                                              |
## |                                                                         |
## | string  $name    the name of the database field  (e.g. outTemp)         |
## | string  $column  the column of the display value (e.g. min, max, avg)   |
## |                                                                         |
## | Relies on per-template globals (set with #set global at the top of      |
## | each child template):                                                   |
## |   $period_default_interval   — default resolution from config           |
## |   $period_rain_interval      — rain / ET resolution from config         |
## |   $period_ET_interval        — ET-specific resolution from config       |
## |   $period_windrun_interval   — windrun resolution from config           |
## |   $period_data_span          — the $span(…) call for this period        |
## +-------------------------------------------------------------------------+

#def getChartData($name, $column)
    #set current_interval = $period_default_interval
    #if $name == "rain"
        #set current_interval = $period_rain_interval
    #end if
    #if $name == "ET"
        #set current_interval = $period_ET_interval
    #end if
    #if $name == "windrun"
        #set current_interval = $period_windrun_interval
    #end if

    #set $records = list($period_data_span.spans(interval=current_interval))
    #for idx, record in enumerate($records)
        #try
            #set val = $getattr($record, $name)
            #set data = $getattr($val, $column).format(add_label=False, localize=False, None_string="null")
            #if $data != "null" or $idx == 0 or $idx == len($records) - 1
                [$record.start.raw, $data],
            #end if
        #except

        #end try
    #end for
#end def
```

### Per-template global variable blocks

Each Group B template removes its `#def getChartData` body and instead declares these
globals near the top (after `#extends _chart_methods` and `#attr $active_nav`):

**`week.html.tmpl`**
```cheetah
#set global $period_default_interval  = int($Extras.Charts.week_timespan)
#set global $period_rain_interval     = int($Extras.Charts.week_rain_timespan)
#set global $period_ET_interval       = int($Extras.Charts.week_ET_timespan)
#set global $period_windrun_interval  = int($Extras.Charts.week_windrun_timespan)
#set global $period_data_span         = $span($week_delta=1, $boundary='midnight')
```

**`yesterday.html.tmpl`**
> `yesterday` combines rain + ET into one config key (`current_rain_timespan`) and has no
> windrun chart, so `period_ET_interval` and `period_windrun_interval` reuse the rain key.

```cheetah
#set global $period_default_interval  = int($Extras.Charts.current_timespan)
#set global $period_rain_interval     = int($Extras.Charts.current_rain_timespan)
#set global $period_ET_interval       = int($Extras.Charts.current_rain_timespan)
#set global $period_windrun_interval  = int($Extras.Charts.current_rain_timespan)
#set global $period_data_span         = $span($day_delta=1, $boundary='midnight')
```

**`month.html.tmpl`**
```cheetah
#set global $period_default_interval  = int($Extras.Charts.month_timespan)
#set global $period_rain_interval     = int($Extras.Charts.month_rain_timespan)
#set global $period_ET_interval       = int($Extras.Charts.month_ET_timespan)
#set global $period_windrun_interval  = int($Extras.Charts.month_windrun_timespan)
#set global $period_data_span         = $span($day_delta=31, $boundary='midnight')
```

**`year.html.tmpl`**
```cheetah
#set global $period_default_interval  = int($Extras.Charts.year_timespan)
#set global $period_rain_interval     = int($Extras.Charts.year_rain_timespan)
#set global $period_ET_interval       = int($Extras.Charts.year_ET_timespan)
#set global $period_windrun_interval  = int($Extras.Charts.year_windrun_timespan)
#set global $period_data_span         = $span($year_delta=1, $boundary='midnight')
```

### Net effect for Group B

| Template | Lines removed | Lines added |
|---|---|---|
| `week.html.tmpl` | 25 (`#def getChartData` block) | 5 (global vars) |
| `yesterday.html.tmpl` | 19 (`#def getChartData` block) | 5 (global vars) |
| `month.html.tmpl` | 25 (`#def getChartData` block) | 5 (global vars) |
| `year.html.tmpl` | 25 (`#def getChartData` block) | 5 (global vars) |
| `_chart_methods.tmpl` | — | +35 (shared def, once) |
| **Net** | **−94** | **+55 → −39 lines** |

The ~39-line net saving is modest on its own, but this completes the shared-base
contract so that `_chart_methods.tmpl` owns **all** reusable logic for Group B.

---

## Bug Fixes Already Applied (branch: `fix/template_inconsistencies`)

| # | Bug | Files | Fix |
|---|---|---|---|
| 1 | Wrong `'day.'` prefix for series5–8 in `getChartJsCode` | week, month, month-%Y-%m, year, year-%Y | `'day.'` → correct period prefix |
| 2 | Hardcoded `Min`/`Max` strings (not translated) | month-%Y-%m | `"Min"` → `$gettext("min")` etc. |
| 3 | Missing outTemp min+max special branch | month | Added `#if $series1 == "outTemp"` block |
| 4 | Wrong `leafTemp` name arg (`"leafTemp"` vs `"leafTemp1"`) | week | `"leafTemp"` → `"leafTemp1"` |
| 5 | Wrong `leafTemp` chart id (`"leafTempchart"` vs `"leafTemp1chart"`) | index, yesterday | `"leafTempchart"` → `"leafTemp1chart"` |

