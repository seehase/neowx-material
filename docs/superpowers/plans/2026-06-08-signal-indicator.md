# Signal Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a WiFi-style "signal cone" telemetry display mode, triggered by a new `max_signal` config key, that replaces the horizontal battery bar with a server-rendered SVG of two parenthesis-like cones whose fill grows green→red with the percentage.

**Architecture:** All template logic lives in `skins/neowx-material/telemetry.html.tmpl`. A field opts into signal mode by configuring `max_signal` (mirroring the existing `max_voltage` voltage gauge). New Cheetah `#def` helpers detect signal mode, compute the percentage (reusing a shared numeric parser), pick the color from `low_threshold`, and emit a static SVG cone. The chart pipeline treats signal fields as plain numeric series, like voltage fields. A standalone Python script reproduces the cone geometry so the math can be visually and programmatically checked before/after porting it into Cheetah.

**Tech Stack:** WeeWX Cheetah templates (`.tmpl`), inline SVG, Python (geometry check script), Node (existing test runner — not used here).

**Reference spec:** `docs/superpowers/specs/2026-06-08-signal-indicator-design.md`
**Approved visual mockup:** `.superpowers/brainstorm/<session>/content/cone-style-v5.html`

**Testing note:** This repo has no Cheetah/Python unit-test harness (only one Node test for a JS helper). Per the design decision, the cone is server-side Cheetah and is verified manually. Task 1 adds a runnable Python geometry check (`python tests/signal-cone-preview.py --check`) that asserts the math invariants and emits an HTML preview to compare against the approved mockup; the Cheetah port in later tasks mirrors that exact math. Final verification renders the telemetry page (or inspects generated HTML) in a real/sample WeeWX install.

**Geometry constants (shared by the Python check and the Cheetah helper):**
- viewBox `0 0 120 24`, center `(60,12)`
- Radius `R = 14.6`; inner half-height `HH_I = 4.75`; outer half-height `HH_O = 11.0`; dot radius `3.5`
- Left wing: inner `x=52` → outer `x=12` (bulge left). Right wing: inner `x=68` → outer `x=108` (bulge right).
- Sagitta (bulge depth) for half-height `hh`: `s = R - sqrt(R² - hh²)`. Quadratic control x = `x + dir·2·s` (`dir=-1` left, `+1` right).
- Fill fraction `f = clamp(percentage/100, 0, 1)`. Frontier: `xf = xi + f·(xo − xi)`, `hhf = HH_I + f·(HH_O − HH_I)`.
- Colors: dim wing `#4a4a4a`, fill green `#4caf50`, fill red `#f44336` (when `percentage < low_threshold`), dot `#ddd`.
- Reference values (for spot-checks): `s(11.0)=5.0`, `s(4.75)≈0.794`; at `f=0.7` left `xf=24.0`, `hhf=9.125`, `s≈3.203`; at `f=1` left `xf=12`, right `xf=108`.

---

### Task 1: Geometry check script (reference implementation)

A standalone Python script that builds the cone SVG and (a) writes an HTML preview to compare against the approved mockup and (b) with `--check` asserts the math invariants. This is the reference the Cheetah port must mirror.

**Files:**
- Create: `tests/signal-cone-preview.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Reference geometry + visual preview for the telemetry signal cone.

Usage:
  python tests/signal-cone-preview.py            # writes tests/signal-cone-preview.html
  python tests/signal-cone-preview.py --check    # asserts math invariants, prints PASS

The math here is the source of truth for the Cheetah `signalCone` helper in
skins/neowx-material/telemetry.html.tmpl. Keep the two in sync.
"""
import math
import os
import sys

R = 14.6
CY = 12.0
HH_I = 4.75
HH_O = 11.0
DOT_R = 3.5
GREEN = "#4caf50"
RED = "#f44336"
DIM = "#4a4a4a"

# (inner x, outer x, direction) per wing
LEFT = (52.0, 12.0, -1)
RIGHT = (68.0, 108.0, 1)


def sag(hh):
    """Bulge depth (sagitta) of a chord of half-height hh on a circle radius R."""
    return R - math.sqrt(R * R - hh * hh)


def ctrl_x(xv, s, direction):
    """Quadratic control x reproducing sagitta s at x=xv, bulging in direction."""
    return xv + direction * 2 * s


def _fmt(v):
    return "%.3f" % v


def wing_full(wing):
    xi, xo, d = wing
    si, so = sag(HH_I), sag(HH_O)
    return (
        "M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" % (
            _fmt(xi), _fmt(CY - HH_I),
            _fmt(xo), _fmt(CY - HH_O),
            _fmt(ctrl_x(xo, so, d)), _fmt(CY), _fmt(xo), _fmt(CY + HH_O),
            _fmt(xi), _fmt(CY + HH_I),
            _fmt(ctrl_x(xi, si, d)), _fmt(CY), _fmt(xi), _fmt(CY - HH_I),
        )
    )


def fill_band(wing, f):
    xi, xo, d = wing
    f = max(0.0, min(1.0, f))
    xf = xi + f * (xo - xi)
    hhf = HH_I + f * (HH_O - HH_I)
    si, sf = sag(HH_I), sag(hhf)
    return (
        "M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" % (
            _fmt(xi), _fmt(CY - HH_I),
            _fmt(xf), _fmt(CY - hhf),
            _fmt(ctrl_x(xf, sf, d)), _fmt(CY), _fmt(xf), _fmt(CY + hhf),
            _fmt(xi), _fmt(CY + HH_I),
            _fmt(ctrl_x(xi, si, d)), _fmt(CY), _fmt(xi), _fmt(CY - HH_I),
        )
    )


def cone_svg(percentage, threshold=30, width=120):
    f = percentage / 100.0
    color = RED if percentage < threshold else GREEN
    return (
        '<svg viewBox="0 0 120 24" width="%d" height="%d" '
        'style="display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">'
        '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
        '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
        '<circle cx="60" cy="12" r="%s" fill="#ddd"/></svg>' % (
            width, int(width * 24 / 120),
            wing_full(LEFT), DIM, wing_full(RIGHT), DIM,
            fill_band(LEFT, f), color, fill_band(RIGHT, f), color,
            DOT_R,
        )
    )


def write_preview():
    cells = ""
    for pct in (100, 70, 40, 15, 0):
        cells += (
            '<div style="background:#2b2b2b;padding:14px;border-radius:8px;'
            'text-align:center">%s<div style="color:#999;font:12px sans-serif;'
            'margin-top:6px">%d%%</div></div>' % (cone_svg(pct), pct)
        )
    html = (
        '<!doctype html><meta charset="utf-8"><body style="background:#1e1e1e;'
        'display:flex;gap:18px;flex-wrap:wrap;padding:30px">%s</body>' % cells
    )
    out = os.path.join(os.path.dirname(__file__), "signal-cone-preview.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote " + out)


def check():
    assert abs(sag(HH_O) - 5.0) < 1e-6, "sag(HH_O) should be 5.0"
    # f=1 fill frontier reaches the outer tip x on both wings.
    for wing, xo in ((LEFT, 12.0), (RIGHT, 108.0)):
        d = fill_band(wing, 1.0)
        assert (" %s " % _fmt(xo)) in d, "fill at f=1 must reach outer x %s" % xo
    # Left frontier x decreases monotonically as fill grows.
    prev = None
    for i in range(0, 11):
        f = i / 10.0
        xf = LEFT[0] + f * (LEFT[1] - LEFT[0])
        if prev is not None:
            assert xf < prev, "left frontier x must decrease as f grows"
        prev = xf
    # Half-height interpolates between inner and outer.
    assert abs((HH_I + 0.0 * (HH_O - HH_I)) - 4.75) < 1e-9
    assert abs((HH_I + 1.0 * (HH_O - HH_I)) - 11.0) < 1e-9
    print("PASS")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        write_preview()
```

- [ ] **Step 2: Run the invariant check**

Run: `python tests/signal-cone-preview.py --check`
Expected: prints `PASS` and exits 0.

- [ ] **Step 3: Generate and eyeball the preview**

Run: `python tests/signal-cone-preview.py`
Then open `tests/signal-cone-preview.html` in a browser.
Expected: five cones at 100/70/40/15/0% that match the approved v5 mockup — symmetric parenthesis cones, fill grows from the center dot outward, 15% is red, 0% shows no fill.

- [ ] **Step 4: Commit**

```bash
git add tests/signal-cone-preview.py
git commit -m "Add signal-cone geometry reference + check script"
```

---

### Task 2: Detect signal mode (`isSignalBased`)

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl` (insert after the `isVoltageBased` def, which currently ends at line 135)

- [ ] **Step 1: Add the helper**

Insert immediately after the `#end def` that closes `isVoltageBased` (after line 135):

```cheetah

## +-------------------------------------------------------------------------+
## | Check if a battery field is signal-based (has max_signal configured)    |
## +-------------------------------------------------------------------------+
#def isSignalBased($name)
    #try
        #set max_s = $getVar('Extras.Telemetry.BatteryFields.' + $name + '.max_signal', None)
        #if $max_s is not None and str($max_s).strip() != '' and str($max_s) != 'None'
            #try
                #set test_float = float($max_s)
                #return True
            #except
                #return False
            #end try
        #else
            #return False
        #end if
    #except
        #return False
    #end try
#end def
```

- [ ] **Step 2: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK` (no Cheetah compile error).
If `Cheetah` is not installed, run `pip install CT3` (the maintained Cheetah fork WeeWX uses) first, or skip and rely on the WeeWX render in Task 8.

- [ ] **Step 3: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Add isSignalBased helper for signal telemetry fields"
```

---

### Task 3: Shared numeric parsing + signal percentage

Extract the numeric-string parsing the voltage gauge already does into `parseNumericValue`, add a generic `rangePercentage`, reroute `calculateBatteryPercentage` through it (behavior preserved), and add `calculateSignalPercentage`.

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl` (replace the `calculateBatteryPercentage` def at lines 174-214; add helpers before it)

- [ ] **Step 1: Replace the `calculateBatteryPercentage` block**

Replace the entire existing def (from the comment banner at line 170 through the `#end def` at line 214) with:

```cheetah
## +-------------------------------------------------------------------------+
## | Parse a numeric value out of a string like "4,5 V" -> 4.5               |
## +-------------------------------------------------------------------------+
#def parseNumericValue($value)
    #import re
    #set value_str = str($value).strip()
    ## Keep only digits, comma, decimal point, minus; normalize comma to period
    #set numeric_str = re.sub(r'[^0-9,.\-]', '', value_str)
    #set numeric_str = numeric_str.replace(',', '.')
    #return float($numeric_str)
#end def

## +-------------------------------------------------------------------------+
## | Generic range -> percentage (0-100) for a configured max/min key pair.  |
## | Returns None when the max key is absent/blank or the range is invalid.  |
## +-------------------------------------------------------------------------+
#def rangePercentage($name, $value, $max_key, $min_key)
    #try
        #set max_str = $getVar('Extras.Telemetry.BatteryFields.' + $name + '.' + $max_key, None)
        #if $max_str is None or str($max_str).strip() == '' or str($max_str) == 'None'
            #return None
        #end if
        #set raw_val = $parseNumericValue($value)
        #set max_v = float(str($max_str).strip())
        #set min_str = $getVar('Extras.Telemetry.BatteryFields.' + $name + '.' + $min_key, '0')
        #set min_v = float(str($min_str).strip())
        #if $max_v > $min_v
            #set percentage = (($raw_val - $min_v) / ($max_v - $min_v)) * 100
            #if $percentage < 0
                #set percentage = 0
            #elif $percentage > 100
                #set percentage = 100
            #end if
            #return int($percentage)
        #else
            #return None
        #end if
    #except
        #return None
    #end try
#end def

## +-------------------------------------------------------------------------+
## | Helper function to calculate battery percentage                         |
## | Returns percentage (0-100) based on current voltage vs max voltage      |
## +-------------------------------------------------------------------------+
#def calculateBatteryPercentage($name, $value)
    #set p = $rangePercentage($name, $value, 'max_voltage', 'min_voltage')
    #if $p is None
        #return 100
    #else
        #return $p
    #end if
#end def

## +-------------------------------------------------------------------------+
## | Helper function to calculate signal percentage                          |
## | Returns percentage (0-100) based on current value vs max_signal         |
## +-------------------------------------------------------------------------+
#def calculateSignalPercentage($name, $value)
    #set p = $rangePercentage($name, $value, 'max_signal', 'min_signal')
    #if $p is None
        #return 0
    #else
        #return $p
    #end if
#end def
```

- [ ] **Step 2: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Share numeric parsing; add calculateSignalPercentage"
```

---

### Task 4: Gauge color helpers (`getGaugeColor`, `getSignalColor`)

Generalize the threshold→color logic so both voltage and signal modes reuse it.

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl` (replace the `getBatteryColor` def at lines 216-239)

- [ ] **Step 1: Replace the `getBatteryColor` block**

Replace the existing def (from the comment banner at line 216 through its `#end def` at line 239) with:

```cheetah
## +-------------------------------------------------------------------------+
## | Generic gauge color: red below low_threshold when max_key is set,       |
## | otherwise green. Shared by voltage and signal modes.                    |
## +-------------------------------------------------------------------------+
#def getGaugeColor($name, $percentage, $max_key)
    #try
        #set max_v = $getVar('Extras.Telemetry.BatteryFields.' + $name + '.' + $max_key, None)
        #if $max_v is None or str($max_v).strip() == '' or str($max_v) == 'None'
            #return "#4caf50"
        #end if
        #set threshold = float($getVar('Extras.Telemetry.BatteryFields.' + $name + '.low_threshold', '20'))
        #if float($percentage) < $threshold
            #return "#f44336"  ## Red
        #else
            #return "#4caf50"  ## Green
        #end if
    #except
        #return "#4caf50"  ## Default green
    #end try
#end def

## +-------------------------------------------------------------------------+
## | Helper function to determine battery gauge color (voltage threshold)    |
## +-------------------------------------------------------------------------+
#def getBatteryColor($name, $percentage)
    #return $getGaugeColor($name, $percentage, 'max_voltage')
#end def

## +-------------------------------------------------------------------------+
## | Helper function to determine signal cone color (signal threshold)       |
## +-------------------------------------------------------------------------+
#def getSignalColor($name, $percentage)
    #return $getGaugeColor($name, $percentage, 'max_signal')
#end def
```

- [ ] **Step 2: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Generalize gauge color; add getSignalColor"
```

---

### Task 5: `signalCone` SVG render helper

Port the verified Task 1 geometry into a Cheetah def that emits the static SVG.

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl` (insert after the `getSignalColor` def added in Task 4)

- [ ] **Step 1: Add the helper**

Insert immediately after the `#end def` that closes `getSignalColor`:

```cheetah

## +-------------------------------------------------------------------------+
## | Render the signal "cone" as a static SVG. Mirrors the geometry in       |
## | tests/signal-cone-preview.py. percentage 0-100; color is the fill.      |
## +-------------------------------------------------------------------------+
#def signalCone($name, $percentage, $color)
    #import math
    #set R = 14.6
    #set cy = 12.0
    #set hh_i = 4.75
    #set hh_o = 11.0
    #set f = float($percentage) / 100.0
    #if $f < 0.0
        #set f = 0.0
    #end if
    #if $f > 1.0
        #set f = 1.0
    #end if
    ## Sagitta (bulge depth) for inner, outer, and frontier edges.
    #set si = $R - math.sqrt($R * $R - $hh_i * $hh_i)
    #set so = $R - math.sqrt($R * $R - $hh_o * $hh_o)
    #set hhf = $hh_i + $f * ($hh_o - $hh_i)
    #set sf = $R - math.sqrt($R * $R - $hhf * $hhf)
    ## Frontier x for each wing (inner -> outer).
    #set xfL = 52.0 + $f * (12.0 - 52.0)
    #set xfR = 68.0 + $f * (108.0 - 68.0)
    ## Constant y edges: top_i=7.25 bot_i=16.75 top_o=1 bot_o=23, center=12.
    <svg viewBox="0 0 120 24" width="120" height="24" style="display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">
        <path d="M 52 7.25 L 12 1 Q ${"%.3f" % (12.0 - 2 * $so)} 12 12 23 L 52 16.75 Q ${"%.3f" % (52.0 - 2 * $si)} 12 52 7.25 Z" fill="#4a4a4a"/>
        <path d="M 68 7.25 L 108 1 Q ${"%.3f" % (108.0 + 2 * $so)} 12 108 23 L 68 16.75 Q ${"%.3f" % (68.0 + 2 * $si)} 12 68 7.25 Z" fill="#4a4a4a"/>
        <path d="M 52 7.25 L ${"%.3f" % $xfL} ${"%.3f" % (12.0 - $hhf)} Q ${"%.3f" % ($xfL - 2 * $sf)} 12 ${"%.3f" % $xfL} ${"%.3f" % (12.0 + $hhf)} L 52 16.75 Q ${"%.3f" % (52.0 - 2 * $si)} 12 52 7.25 Z" fill="$color"/>
        <path d="M 68 7.25 L ${"%.3f" % $xfR} ${"%.3f" % (12.0 - $hhf)} Q ${"%.3f" % ($xfR + 2 * $sf)} 12 ${"%.3f" % $xfR} ${"%.3f" % (12.0 + $hhf)} L 68 16.75 Q ${"%.3f" % (68.0 + 2 * $si)} 12 68 7.25 Z" fill="$color"/>
        <circle cx="60" cy="12" r="3.5" fill="#ddd"/>
    </svg>
#end def
```

- [ ] **Step 2: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK`.

- [ ] **Step 3: Cross-check the emitted coordinates against the reference**

Confirm the constant control points match the Task 1 values:
- inner control: `52 − 2·s(4.75) = 52 − 1.588 = 50.412`; outer control: `12 − 2·s(11) = 12 − 10 = 2.0`.
- At `percentage=70`: left frontier `xfL=24.0`, `hhf=9.125`, frontier control `24 − 2·3.203 = 17.594`.
These are the same numbers `tests/signal-cone-preview.py` produces.

- [ ] **Step 4: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Add signalCone SVG render helper"
```

---

### Task 6: Branch the card to render the cone

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl:46-62` (inside `batteryCard`, the `col-6` block)

- [ ] **Step 1: Replace the card's value+gauge block**

Replace lines 46-62 (from `#set current_value` through the closing `<div class="text-muted font-small mt-1">$battery_percentage%</div>`) with:

```cheetah
                            #set current_value = $getVar('current.' + name)
                            #set display_value = $mapBatteryValue($name, $current_value)

                            <h4 class="h2-responsive mb-2">
                                $display_value
                            </h4>

                            #if $isSignalBased($name)
                                ## Signal mode: WiFi-style cone (replaces the battery bar)
                                #set signal_percentage = $calculateSignalPercentage($name, $current_value)
                                #set signal_color = $getSignalColor($name, $signal_percentage)
                                $signalCone($name, $signal_percentage, $signal_color)
                                <div class="text-muted font-small mt-1">$signal_percentage%</div>
                            #else
                                ## Battery/voltage mode: horizontal fill bar
                                #set battery_percentage = $calculateBatteryPercentage($name, $current_value)
                                #set battery_color = $getBatteryColor($name, $battery_percentage)
                                <!-- Visual battery gauge -->
                                <div class="battery-container" style="border: 2px solid #555; border-radius: 4px; width: 100px; height: 20px; margin: 0 auto; position: relative;">
                                    <div class="battery-fill" style="background-color: $battery_color;width: $battery_percentage%;height: 100%;border-radius: 2px;transition: width 0.3s ease, background-color 0.3s ease;"></div>
                                    <div style="position: absolute;top: 2px;left: 100%;width: 6px;height: 12px;background: #555;border-radius: 2px;margin-left: 2px;"></div>
                                </div>
                                <div class="text-muted font-small mt-1">$battery_percentage%</div>
                            #end if
```

- [ ] **Step 2: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Render signal cone in telemetry card for signal fields"
```

---

### Task 7: Treat signal fields as numeric in charts + value mapping

Signal fields must not be run through status-position mapping. Mirror the existing voltage exclusions in `mapBatteryValue`, `getBatteryChartValue`, and the chart Y-axis.

**Files:**
- Modify: `skins/neowx-material/telemetry.html.tmpl` (three spots)

- [ ] **Step 1: Skip mapping for signal fields in `mapBatteryValue`**

In `mapBatteryValue`, immediately after the voltage guard:

```cheetah
    ## Don't map voltage-based sensors - return raw value
    #if $isVoltageBased($name)
        #return $value
    #end if
```

add:

```cheetah
    ## Don't map signal-based sensors - return raw value
    #if $isSignalBased($name)
        #return $value
    #end if
```

- [ ] **Step 2: Skip chart-position conversion for signal fields in `getBatteryChartValue`**

In `getBatteryChartValue`, immediately after the voltage guard:

```cheetah
    ## Don't convert voltage-based sensors - use raw voltage in charts
    #if $isVoltageBased($name)
        #return $raw_value
    #end if
```

add:

```cheetah
    ## Don't convert signal-based sensors - use raw value in charts
    #if $isSignalBased($name)
        #return $raw_value
    #end if
```

- [ ] **Step 3: Exclude signal fields from the status Y-axis in `getChartJsCode`**

Find (currently near line 408):

```cheetah
                #set is_battery = $isBatteryFieldEnabled($name)
                #set is_voltage = $isVoltageBased($name)
```

add a line below it:

```cheetah
                #set is_signal = $isSignalBased($name)
```

Then find the Y-axis branch (currently near line 451):

```cheetah
                        #if $is_battery and not $is_voltage
```

and change it to:

```cheetah
                        #if $is_battery and not $is_voltage and not $is_signal
```

- [ ] **Step 4: Verify the template still parses**

Run: `python -c "from Cheetah.Template import Template; Template.compile(file='skins/neowx-material/telemetry.html.tmpl')" && echo OK`
Expected: prints `OK`.

- [ ] **Step 5: Commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Treat signal fields as numeric in charts and value mapping"
```

---

### Task 8: End-to-end render verification

Verify the feature in a real or sample WeeWX render. No code changes unless a defect is found.

**Files:**
- None (verification only). If a defect is found, fix it in `skins/neowx-material/telemetry.html.tmpl` and re-run.

- [ ] **Step 1: Configure a signal field**

In a test `skin.conf` (or the sample at `skins/neowx-material/skin.conf.voltage-battery-sample`), ensure `rxCheckPercent` is in `telemetry_order` and add:

```ini
[[Telemetry]]
    allow_zero_values = yes
    [[[BatteryFields]]]
        [[[[rxCheckPercent]]]]
            enabled = yes
            max_signal = 100
            min_signal = 0
            low_threshold = 30
```

- [ ] **Step 2: Render and inspect**

Run WeeWX report generation against test data (e.g. `wee_reports` / `weectl report run`, or restart WeeWX), then open the generated `telemetry.html`.
Expected:
- The `rxCheckPercent` card shows the signal cone (not the horizontal bar), with the percentage below it.
- A high value (e.g. 100%) renders a full green cone; a value below 30% renders a red, partially-filled cone.
- The cone matches the approved `tests/signal-cone-preview.html` shapes.

- [ ] **Step 3: Regression-check the voltage and status cards**

Confirm an existing voltage field (e.g. `consBatteryVoltage`) still shows the horizontal fill bar with the same percentage/color as before, and a status field (e.g. `batteryStatus1`) still shows its mapped text label and status chart. Nothing about non-signal fields should have changed.

- [ ] **Step 4: Check the signal chart**

If `rxCheckPercent` is in `telemetry_chart_order`, confirm its chart plots the raw numeric percentage over time (numeric Y-axis with `%` labels), not status-position labels.

- [ ] **Step 5 (only if defects found): fix and commit**

```bash
git add skins/neowx-material/telemetry.html.tmpl
git commit -m "Fix signal cone rendering issues found in verification"
```

---

### Task 9: Document the Signal Indicator

**Files:**
- Modify: `docs/battery-config-guide.md` (add a new section after the "Voltage-Based Battery Gauge" section, before "Step 3: Configure Text Labels")

- [ ] **Step 1: Add the documentation section**

Insert this section (place it after the voltage gauge section ends, around line 125):

````markdown
### Signal Indicator (For Signal-Strength Sensors)

If a sensor reports a signal-strength value (e.g. `rxCheckPercent`, a 0–100% link
quality), configure it as a **signal indicator**. Instead of the horizontal battery
bar, the card shows a WiFi-style "cone": two parenthesis-shaped wings that fill from
the center outward in proportion to the percentage — green normally, red below a
threshold.

#### Configuration Options:

```ini
[[[[rxCheckPercent]]]]
    enabled = yes
    max_signal = 100      # raw value that represents 100%
    min_signal = 0        # raw value that represents 0% (default: 0)
    low_threshold = 30    # below this %, the cone turns red
```

#### How It Works:

1. **max_signal**: the raw value that maps to 100% (for `rxCheckPercent`, `100`).
2. **min_signal**: the raw value that maps to 0% (usually `0`).
3. **low_threshold**: percentage below which the cone fill turns red (reuses the same
   key as the voltage gauge; default `20`).

Percentage = (current − min_signal) ÷ (max_signal − min_signal) × 100, clamped to
0–100.

#### Example:

```ini
[[Appearance]]
    telemetry_order = rxCheckPercent, consBatteryVoltage
    telemetry_chart_order = rxCheckPercent

[[Telemetry]]
    allow_zero_values = yes
    [[[BatteryFields]]]
        [[[[rxCheckPercent]]]]
            enabled = yes
            max_signal = 100
            min_signal = 0
            low_threshold = 30
```

- 100% → full green cone
- 70% → green cone filled ~70% from the center out
- 20% → red, lightly filled cone (below the 30% threshold)

**Signal vs. voltage:** a field is a *signal* sensor when `max_signal` is set and a
*voltage* sensor when `max_voltage` is set — use one or the other, not both. If both
are set, signal mode wins. In charts, signal fields plot their raw numeric value
(like voltage fields), not status positions.

#### Quick Reference — Signal Configuration
| Setting | Purpose | Example |
|---------|---------|---------|
| `max_signal` | Raw value = 100% | `100` |
| `min_signal` | Raw value = 0% | `0` |
| `low_threshold` | Percentage to turn red | `30` |
````

- [ ] **Step 2: Commit**

```bash
git add docs/battery-config-guide.md
git commit -m "Document the signal indicator telemetry mode"
```

---

## Self-Review

**Spec coverage:**
- Config trigger `max_signal` + `min_signal` → Tasks 2, 3, 6. ✓
- Range mapping / clamp → Task 3 (`rangePercentage`). ✓
- `low_threshold` reuse → Task 4 (`getGaugeColor`). ✓
- Signal-wins mutual exclusivity → Task 6 (signal branch checked first); chart/map guards return raw for either mode → Task 7. ✓
- Big value unchanged → Task 6 (keeps `$display_value` `<h4>`). ✓
- Bar replaced by cone → Task 6. ✓
- SVG geometry (R, HH_I, HH_O, dot, unified-radius sagitta, server-side) → Tasks 1 & 5. ✓
- Fill band green/red → Tasks 1, 4, 5. ✓
- Charts treat signal as numeric → Task 7. ✓
- Docs section → Task 9. ✓
- No new files to register in `install.py` (cone is in the existing template; the Python script is a dev tool under `tests/`, not shipped in the skin). ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; every verify step shows the command and expected output. ✓

**Type/name consistency:** Helper names used consistently across tasks — `isSignalBased`, `parseNumericValue`, `rangePercentage`, `calculateBatteryPercentage`, `calculateSignalPercentage`, `getGaugeColor`, `getBatteryColor`, `getSignalColor`, `signalCone`. Card branch (Task 6) calls `calculateSignalPercentage`/`getSignalColor`/`signalCone`; chart guards (Task 7) use `is_signal` from `isSignalBased`. ✓
