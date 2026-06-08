# Signal Indicator — Design Spec

**Date:** 2026-06-08
**Status:** Approved, pending implementation plan

## Summary

Add a third telemetry display mode — a WiFi-style **signal indicator** — alongside
the existing status-label and voltage-gauge modes. A field opts in via a new
`max_signal` config key (mirroring `max_voltage`). Instead of the horizontal
battery fill bar, the card renders symmetric arcs around a center dot
(`( ( ( ( ( · ) ) ) ) )`), where each glyph represents 10%. The arcs are green
normally and red when the percentage drops below `low_threshold`.

The primary use case is `rxCheckPercent` (signal quality), which already reports a
0–100% value.

## Motivation

The skin already converts voltage telemetry into a percentage gauge. Percentage-
style signal fields (e.g. `rxCheckPercent`) currently fall through to the same
horizontal battery bar, which does not read as "signal strength." A dedicated
arc indicator communicates signal quality at a glance and visually distinguishes
signal fields from battery fields.

## Configuration

A field enters signal mode when a numeric `max_signal` is present under its
`[[[[fieldName]]]]` block in `[[[BatteryFields]]]`:

```ini
[[[[rxCheckPercent]]]]
    enabled = yes
    max_signal = 100      # raw value that maps to 100%
    min_signal = 0        # raw value that maps to 0% (default: 0)
    low_threshold = 30    # below this %, arcs turn red (reuses existing key)
```

### Rules

- **Trigger:** presence of a parseable numeric `max_signal` activates signal mode,
  exactly as `max_voltage` activates voltage mode.
- **Range mapping:** `percentage = (raw - min_signal) / (max_signal - min_signal) * 100`,
  clamped to 0–100. For `rxCheckPercent`, `max_signal = 100` / `min_signal = 0`
  yields a 1:1 mapping.
- **Threshold:** reuses the existing `low_threshold` key (percentage below which the
  filled arcs turn red). Default behavior matches the voltage gauge default.
- **Mutual exclusivity:** `max_signal` and `max_voltage` are not meant to coexist on
  one field. If both are set, **signal mode wins** (documented behavior).
- **Big value display:** the large value at the top of the card continues to show the
  mapped/raw value (e.g. `100%` for `rxCheckPercent`), unchanged from current behavior.

## Visual Design

The signal indicator **replaces** the horizontal battery fill bar on the card (the
big value above and the small `%` line below are unchanged).

```
( ( ( ( ( · ) ) ) ) )
```

- **10 glyphs total** — 5 `(` on the left, 5 `)` on the right — plus a static center
  dot (`·`). Each glyph represents 10%.
- **Fill order:** center-outward and symmetric. The percentage is rounded to the
  nearest glyph (`round(pct / 10)` glyphs filled); the innermost arcs fill first,
  growing outward on both sides.
- **Color:** filled glyphs are green (`#4caf50`), or red (`#f44336`) when
  `percentage < low_threshold`. Empty glyphs are muted/dim.
- Glyph count is fixed at 10 (not configurable).

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

3. **`signalArcs($name, $percentage, $color)`** — new render helper that emits the
   11-character arc row (10 colored glyphs + center dot) as styled `<span>` elements,
   applying the fill color to filled glyphs and the muted style to empty glyphs.

4. **`batteryCard()`** — branch the gauge block: when `isSignalBased($name)` render the
   arc indicator; otherwise render the existing horizontal fill bar. The big value and
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

- Custom arc/threshold colors.
- Configurable glyph count.
- Separate chart styling for signal fields (they reuse the numeric chart path).
- Auto-detection of percentage fields without explicit `max_signal` config.
