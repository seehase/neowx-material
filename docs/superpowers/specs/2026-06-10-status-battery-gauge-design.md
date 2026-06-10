# Status-Battery Gauge — Design Spec

**Date:** 2026-06-10
**Status:** Approved, pending implementation plan

## Summary

Give status-based battery fields (discrete states like 0=OK / 9=Low) a meaningful
battery gauge. Today these fields always render a 100% green bar. With this change,
the gauge percentage is derived automatically from the field's existing
`chart_position_X` state map, and an optional raw-value threshold (`low_state` +
`low_when`) turns the fill red when the battery is in a low state. Two-state fields
fill the entire bar red when low; fields with three or more states show their
proportional fill in red.

## Motivation

The skin renders percentage gauges for voltage fields (`max_voltage`) and signal
fields (`max_signal`), but status-based fields — the most common battery sensors —
always show a full green bar regardless of state. A "Low" transmitter battery looks
identical to an "OK" one at a glance. The state map needed to compute a percentage
(`chart_position_X`, `max_chart_position`) is already required configuration for
these fields, so the gauge can improve with no new config; the red threshold is the
only new opt-in.

## Configuration

All keys live under the field's existing `[[[[fieldName]]]]` block in
`[[[BatteryFields]]]`:

```ini
[[[[txBatteryStatus]]]]
    enabled = yes
    0 = OK
    1 = Low
    chart_position_0 = 1
    chart_position_1 = 0
    max_chart_position = 1
    # NEW — optional red threshold:
    low_state = 1             # raw station value to compare against
    low_when = at_or_above    # at_or_above (default) | at_or_below
```

### Rules

- **Percentage (automatic, no new config).** For every enabled status-based field
  (not voltage, not signal):
  `percentage = (position + 1) ÷ (max_chart_position + 1) × 100`,
  where `position` is the field's `chart_position_<rawValue>`.
  - 2-state example: OK (pos 1) → 100%, Low (pos 0) → 50%.
  - 5-state example: 100 / 80 / 60 / 40 / 20%.
  - `flip_values = yes` inverts the position before the math (same rule the chart
    uses via `getBatteryChartValue`), so gauge and chart can never disagree.
  - Truncation uses the same epsilon guard as `rangePercentage` so integral results
    don't come out one short.
- **Low threshold (opt-in).** Only evaluated when `low_state` is present:
  - `low_when = at_or_above` (default): LOW when `rawValue >= low_state`.
  - `low_when = at_or_below`: LOW when `rawValue <= low_state`.
  - Comparison is numeric, against the RAW station value (not the chart position),
    because raw scales differ by vendor (Ecowitt: 9 = low; simple: 1 = low;
    inverted: 0 = low).
- **Precedence.** Signal and voltage modes are detected first and unchanged. A
  `low_state` key on a voltage- or signal-based field is ignored (documented).

## Rendering

- **Color:** LOW → red `#f44336`; otherwise green `#4caf50` (same constants as the
  voltage/signal gauges).
- **Fill width:**
  - 2-state fields (`max_chart_position = 1`): LOW fills the bar **100% red** — an
    at-a-glance alarm.
  - Fields with 3+ states: LOW keeps the computed proportional width, colored red.
  - Not low: proportional width, green.
- **Percentage text:** the small `%` line under the bar always shows the computed
  percentage (a 2-state Low reads "50%" under a full red bar — this was an explicit
  choice).
- **Fallbacks (preserve today's behavior exactly):** raw value missing from the
  position map, unparseable value, or any error → 100% green, as now. The big
  mapped label (`OK` / `Low`) above the gauge is unchanged.

## Implementation

All changes in `skins/neowx-material/telemetry.html.tmpl` (plus docs).

1. **`calculateStatePercentage($name, $value)`** — new helper. Resolves the raw
   value to its integer key (same `str(int(float(raw) + 0.000001))` idiom as
   `mapBatteryValue`), looks up `chart_position_<key>`, applies `flip_values` the
   way `getBatteryChartValue` does, then returns
   `int((pos + 1) / (max_pos + 1) * 100 + epsilon)`. Returns `None` when the field
   isn't an enabled status field, the position is missing, or anything fails.

2. **`isLowState($name, $value)`** — new helper. Returns `False` when `low_state`
   is absent/blank; otherwise numerically compares the raw value per `low_when`
   (default `at_or_above`). Broad try/except → `False`, per house style.

3. **`batteryCard()`** — restructure the existing `#else` (battery-bar) arm:
   - `isVoltageBased` → existing `calculateBatteryPercentage` / `getBatteryColor`,
     unchanged.
   - else, if `calculateStatePercentage` returns a value → use it, with color from
     `isLowState` and a separate `fill_width` (100 when low and
     `max_chart_position == 1`, else the percentage).
   - else → today's fallback (100% green).
   The bar markup gains a `fill_width` variable distinct from the displayed
   percentage; for voltage and fallback paths `fill_width = percentage`.

4. **Charts — no changes.** Status charts already plot positions with text labels.

## Documentation

In `docs/battery-config-guide.md`:
- New subsection "Low Threshold for Status Batteries" covering `low_state`,
  `low_when`, the automatic percentage formula, the 2-state full-red rule, and the
  voltage/signal precedence note.
- Correct any text implying status gauges always show 100%.

## Out of Scope (YAGNI)

- Custom or per-state colors.
- Chart rendering changes (thresholds, coloring).
- Multiple thresholds (e.g. a yellow warning band).
- Opt-out of the automatic percentage (it replaces a meaningless constant 100%).
