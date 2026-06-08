# Signal Indicator — Design Spec

**Date:** 2026-06-08
**Status:** Approved, pending implementation plan

## Summary

Add a third telemetry display mode — a WiFi-style **signal indicator** — alongside
the existing status-label and voltage-gauge modes. A field opts in via a new
`max_signal` config key (mirroring `max_voltage`). Instead of the horizontal
battery fill bar, the card renders an inline SVG of two symmetric parenthesis-like
"cone" wings flanking a center dot, filled from the inner edge outward in
proportion to the percentage. The fill is green normally and red when the
percentage drops below `low_threshold`.

The primary use case is `rxCheckPercent` (signal quality), which already reports a
0–100% value.

## Motivation

The skin already converts voltage telemetry into a percentage gauge. Percentage-
style signal fields (e.g. `rxCheckPercent`) currently fall through to the same
horizontal battery bar, which does not read as "signal strength." A dedicated
signal indicator communicates signal quality at a glance and visually distinguishes
signal fields from battery fields.

## Configuration

A field enters signal mode when a numeric `max_signal` is present under its
`[[[[fieldName]]]]` block in `[[[BatteryFields]]]`:

```ini
[[[[rxCheckPercent]]]]
    enabled = yes
    max_signal = 100      # raw value that maps to 100%
    min_signal = 0        # raw value that maps to 0% (default: 0)
    low_threshold = 30    # below this %, the fill turns red (reuses existing key)
```

### Rules

- **Trigger:** presence of a parseable numeric `max_signal` activates signal mode,
  exactly as `max_voltage` activates voltage mode.
- **Range mapping:** `percentage = (raw - min_signal) / (max_signal - min_signal) * 100`,
  clamped to 0–100. For `rxCheckPercent`, `max_signal = 100` / `min_signal = 0`
  yields a 1:1 mapping.
- **Threshold:** reuses the existing `low_threshold` key (percentage below which the
  fill turns red). Default behavior matches the voltage gauge default.
- **Mutual exclusivity:** `max_signal` and `max_voltage` are not meant to coexist on
  one field. If both are set, **signal mode wins** (documented behavior).
- **Big value display:** the large value at the top of the card continues to show the
  mapped/raw value (e.g. `100%` for `rxCheckPercent`), unchanged from current behavior.

## Visual Design

The signal indicator **replaces** the horizontal battery fill bar on the card (the
big value above and the small `%` line below are unchanged). It is a small inline
**SVG** rendered as two symmetric "cone" wings flanking a center dot — each wing
reads like a parenthesis that flares from a short inner edge (near the dot) out to
the full gauge height at the curved outer tip:

```
 (((  ·  )))
```

The shape was finalized interactively; the reference mockup is
`.superpowers/brainstorm/<session>/content/cone-style-v5.html`.

### Geometry (viewBox `0 0 120 24`, center `(60,12)`)

- **Two wings.** Left wing spans inner `x=52` → outer `x=12`; right wing is the
  mirror (`x=68` → `x=108`).
- **Taper.** Each wing's half-height grows from `HH_I = 4.75` at the inner edge to
  `HH_O = 11` at the outer tip (so it flares from just taller than the dot out to
  full gauge height).
- **Center dot.** A filled circle at `(60,12)`, radius `DOT_R = 3.5`, with a small
  gap before each wing's inner edge.
- **Unified-radius curves.** Every curved vertical end — the outer tip, the wing's
  inner edge, and both ends of the fill — is an arc of one shared radius
  `R = 14.6`. Each curve's bulge depth (sagitta) is derived from `R` and that
  edge's half-height: `s(hh) = R - sqrt(R² - hh²)`. Curves are drawn as quadratic
  Béziers whose control point reproduces that sagitta
  (`control_x = x ± 2·s`, sign per side). Taller edges (outer tip) bulge most; the
  short inner edge is nearly flat — the intended consequence of a single radius.

### Fill

- The colored fill is a **band** from the wing's inner edge out to a frontier at
  fraction `f = percentage / 100`. The frontier's `x` and half-height are linearly
  interpolated between the inner and outer values; its curved end uses the same
  shared radius `R`, so a partial fill reads as a nested parenthesis.
- The full wing outline is drawn dim (`#4a4a4a`); the fill band is drawn on top in
  green (`#4caf50`), or red (`#f44336`) when `percentage < low_threshold`. The dot
  is always drawn.
- The SVG is rendered **server-side**: the template computes `f` from the known
  percentage and emits the path `d` strings (no client-side JavaScript), matching
  how the existing gauge renders.

## Implementation

All changes are in `skins/neowx-material/telemetry.html.tmpl` (plus docs).

1. **`isSignalBased($name)`** — new helper, parallel to `isVoltageBased`, returning
   `True` when a numeric `max_signal` is configured for the field.

2. **Shared percentage calculation** — generalize the existing voltage parser so the
   string-cleaning logic (strip units, normalize comma/period decimals, clamp) is
   shared between voltage and signal modes rather than duplicated. The signal path
   reads `max_signal` / `min_signal` (the latter defaulting to `0`); the voltage path
   keeps reading `max_voltage` / `min_voltage`. Existing voltage behavior must be
   preserved exactly.

3. **`signalCone($name, $percentage, $color)`** — new render helper that emits the
   inline SVG described in *Visual Design*: two dim wing outlines, two colored fill
   bands sized to `f = percentage / 100`, and the center dot. The helper computes the
   sagitta-derived quadratic control points and the interpolated frontier server-side
   (likely via `#import math` for `sqrt`), so the output is static SVG markup.

4. **`batteryCard()`** — branch the gauge block: when `isSignalBased($name)` render the
   signal cone; otherwise render the existing horizontal fill bar. The big value and
   the `%` line remain in place for both modes.

5. **Chart handling** — extend the `is_battery and not is_voltage` conditions in
   `getBatteryChartValue`, the `getChartJsCode` y-axis block, and `getChartData` so
   signal fields are also excluded from status-position mapping. Signal fields plot
   their **raw numeric value** on the chart, the same way voltage fields do.

## Documentation

Add a "Signal Indicator" section to `docs/battery-config-guide.md`, mirroring the
existing voltage-gauge section: a config table (`max_signal`, `min_signal`,
`low_threshold`), an example using `rxCheckPercent`, and a note on signal/voltage
mutual exclusivity.

## Out of Scope (YAGNI)

- Custom cone/threshold colors.
- Configurable cone geometry (radius, heights, dot size) — fixed in the template.
- Separate chart styling for signal fields (they reuse the numeric chart path).
- Auto-detection of percentage fields without explicit `max_signal` config.
