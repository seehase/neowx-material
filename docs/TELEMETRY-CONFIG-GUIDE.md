# Telemetry Configuration Guide

## Overview

The telemetry page shows cards and charts for battery and sensor fields reported
by your weather station. Each field is configured in a single block under
`[[Telemetry]]` in `skin.conf`. A `sensor_type` key picks the gauge style; without
one the field shows its raw value with no gauge.

Which fields appear is controlled by `Extras.Appearance.telemetry_order` (cards)
and `telemetry_chart_order` (charts). Only fields listed there are displayed —
the per-field config blocks are just configuration, not opt-in.

| sensor_type | What renders | Typical sensor |
|---|---|---|
| `none` (default) | Raw value, no gauge | Any numeric reading |
| `voltage` | Horizontal battery bar filled from voltage range | 4.5 V, 12.6 V, … |
| `signal` | WiFi-style cone filled by signal percentage | 0–100 link quality |
| `percent` | Horizontal battery bar filled from 0–100 value | % battery |
| `status` | Mapped status bar (OK / Low / …) | 0, 1, 9 state codes |

---

## Migration from the old config (breaking change)

The previous config split field settings across two sub-sections:
`[[[BatteryFields]]]` (gauge keys) and `[[[FieldConfiguration]]]` (chart keys).
Both are gone. Every field now has a single block directly under `[[Telemetry]]`.

**What you need to do for each field:**

1. Move the field's keys out of `[[[BatteryFields]]]` / `[[[FieldConfiguration]]]`
   and into a `[[Telemetry]] [[[<fieldname>]]]` block.
2. Add `sensor_type` to every gauge field. Anything left without `sensor_type`
   now defaults to `none` — a plain raw-value display with no gauge. Voltage,
   signal, percent, and status fields all need to declare themselves.
3. Delete the `enabled` lines. Being listed in `telemetry_order` is what opts a
   field in.
4. Delete any `show_value = pad` lines. Bottom spacing is now automatic; `pad`
   is gone. Use `show_value = no` if you want to hide the value.

**Before (old format):**

```ini
[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1

    [[[BatteryFields]]]
        [[[[outTempBatteryStatus]]]]
            enabled = yes
            0 = OK
            1 = Low
            chart_position_0 = 1
            chart_position_1 = 0
            max_chart_position = 1
            low_state = 1
            low_when = at_or_above

        [[[[consBatteryVoltage]]]]
            enabled = yes
            max_voltage = 4.5
            min_voltage = 0.0
            low_threshold = 50

    [[[FieldConfiguration]]]
        [[[[outTempBatteryStatus]]]]
            chart_interval = 3600
            colors = palette1:3
```

**After (new format):**

```ini
[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    value_position = bottom         # global default (bottom | left | right)

    [[[outTempBatteryStatus]]]
        sensor_type = status
        0 = OK
        1 = Low
        chart_position_0 = 1
        chart_position_1 = 0
        max_chart_position = 1
        low_state = 1
        low_when = at_or_above
        chart_interval = 3600
        colors = palette1:3

    [[[consBatteryVoltage]]]
        sensor_type = voltage
        max_voltage = 4.5
        min_voltage = 0.0
        low_threshold = 50
```

---

## How fields get configured

### Field discovery

Fields are shown only when they appear in `telemetry_order` (cards) or
`telemetry_chart_order` (charts) under `[[Appearance]]`. The skin does not walk
`[[Telemetry]]` sub-sections looking for fields, so the per-field blocks sit
alongside scalar settings like `chart_days` without confusion.

```ini
[[Appearance]]
    telemetry_order = consBatteryVoltage, outTempBatteryStatus, rxCheckPercent
    telemetry_chart_order = consBatteryVoltage, outTempBatteryStatus
```

### Per-field block structure

```ini
[[Telemetry]]
    [[[<fieldname>]]]
        sensor_type = voltage       # none | voltage | signal | percent | status

        # --- type-specific keys (see sections below) ---
        max_voltage = 4.5
        min_voltage = 0.0
        low_threshold = 20

        # --- value display (override the [[Telemetry]] default) ---
        value_position = bottom     # bottom | left | right
        show_value = yes            # yes | no

        # --- chart settings ---
        chart_interval = 300        # seconds between chart data points
        colors = palette1:3         # chart color override
```

`chart_interval` and `colors` used to live in `[[[FieldConfiguration]]]`; they
now live in the same per-field block as everything else.

When a field has no `chart_interval`, the global `default_interval` set directly
under `[[Telemetry]]` is used. If that is also absent, the skin falls back to
`300` seconds.

---

## Sensor types

### `sensor_type = voltage`

Draws a horizontal battery bar filled from the configured voltage range. The bar
turns red below `low_threshold` percent.

```ini
[[[consBatteryVoltage]]]
    sensor_type = voltage
    max_voltage = 4.5       # voltage that represents 100%
    min_voltage = 0.0       # voltage that represents 0%
    low_threshold = 20      # optional; below this % the bar turns red (default: 20)
    chart_interval = 300
```

Percentage = (current − min_voltage) ÷ (max_voltage − min_voltage) × 100,
clamped to 0–100. The displayed value is the raw voltage (e.g. `3.6 V`).

**Example: 12V battery system**

```ini
[[[batteryVoltage12v]]]
    sensor_type = voltage
    max_voltage = 14.4      # fully charged
    min_voltage = 10.5      # discharged
    low_threshold = 30
```

- 14.4 V → 100% green bar
- 12.45 V → 50% green bar
- 11.0 V → 12% red bar (below 30%)

**Required keys:** `max_voltage`, `min_voltage`
**Optional key:** `low_threshold` (default: `20`)

---

### `sensor_type = signal`

Draws a WiFi-style cone that fills from the center outward in proportion to the
signal percentage. The cone turns red below `low_threshold` percent.

```ini
[[[rxCheckPercent]]]
    sensor_type = signal
    max_signal = 100        # raw value that maps to 100%
    min_signal = 0          # raw value that maps to 0% (default: 0)
    low_threshold = 30      # percentage below which the cone turns red
```

```
   signal = 100%        signal = 70%        signal = 20% (below threshold)

     (((|)))              ( (|) )                 (|)
      green                green                  red
```

Percentage = (current − min_signal) ÷ (max_signal − min_signal) × 100, clamped
to 0–100. If `max_signal` and `min_signal` are not set, the raw value is taken
directly as a percentage. The displayed value reads `X%`.

**Optional keys:** `max_signal`, `min_signal` (if omitted, raw value is used as %),
`low_threshold` (default: `20`)

---

### `sensor_type = percent`

Draws a horizontal battery bar filled directly from the field value (treated as
0–100%). Uses the same `low_threshold` coloring as the voltage bar.

```ini
[[[extraBattery7]]]
    sensor_type = percent
    low_threshold = 20      # optional; below this % the bar turns red (default: 20)
```

The displayed value reads `X%` (clamped to 0–100, no decimals).

**Optional key:** `low_threshold` (default: `20`)

---

### `sensor_type = status`

Draws a mapped status bar driven by chart positions. Each raw station value is
given a text label and a chart position.

```ini
[[[outTempBatteryStatus]]]
    sensor_type = status

    # 1. Text labels: map each raw value to display text
    0 = OK
    1 = Low

    # 2. Chart positions: where each raw value appears on the chart
    #    Higher numbers = top of chart (good); lower = bottom (bad)
    chart_position_0 = 1
    chart_position_1 = 0

    # 3. Chart range
    max_chart_position = 1

    # 4. Optional: turn the bar red on the low state
    low_state = 1               # raw value to compare against
    low_when = at_or_above      # at_or_above (default) | at_or_below

    # 5. Optional: flip the chart (if bad states are coming out at the top)
    flip_values = no

    chart_interval = 3600
```

The gauge fill percentage comes from the chart position:
`(chart_position + 1) ÷ (max_chart_position + 1) × 100`

- Two states (0/1): OK → 100%, Low → 50%
- Five states (0–4): top → 100%, second → 80%, …, bottom → 20%

The displayed value is the mapped label (e.g. `OK`). If the station's current
value has no matching `0 =` / `1 =` / … label, the raw value is shown as-is.

**Optional keys for the low/red threshold:**

- `low_state` — the raw station value to compare against (e.g. `1` or `9`).
  Without this the bar never turns red.
- `low_when` — `at_or_above` (default): bar is red when raw value ≥ `low_state`.
  Use this when a higher number means a weaker battery (e.g. Ecowitt: `0 = Normal`,
  `9 = Low`, set `low_state = 9`). `at_or_below`: bar is red when raw value ≤
  `low_state` (for stations where `0` means low and `1` means OK).
- `flip_values` — `yes` inverts the chart. Use when the chart renders
  upside-down (bad states at the top).

**Two-state fields fill the whole bar red when low** (an at-a-glance alarm).
Fields with three or more states keep their proportional fill, colored red.

**Common mistake — using sequential numbers instead of raw values:**

```ini
# WRONG: station doesn't report value "1" — it reports "9"
chart_position_1 = 0

# CORRECT: use the actual raw value
chart_position_9 = 0
```

**Ecowitt example (0 = Normal, 9 = Low):**

```ini
[[[batteryStatus1]]]
    sensor_type = status
    0 = Normal
    9 = Low
    chart_position_0 = 1
    chart_position_9 = 0
    max_chart_position = 1
    low_state = 9
    low_when = at_or_above
    chart_interval = 3600
```

**Multi-level example (0–4):**

```ini
[[[extraBatteryStatus1]]]
    sensor_type = status
    0 = Full
    1 = Good
    2 = Fair
    3 = Low
    4 = Critical
    chart_position_0 = 4
    chart_position_1 = 3
    chart_position_2 = 2
    chart_position_3 = 1
    chart_position_4 = 0
    max_chart_position = 4
    low_state = 3               # Low (3) and Critical (4) show in red
    low_when = at_or_above
```

**Required keys:** `0 =` / `1 =` / … labels; `chart_position_X` for each value;
`max_chart_position`
**Optional keys:** `low_state`, `low_when`, `flip_values`

---

### `sensor_type = none`

Shows the raw field value with no gauge. The title and the min/max columns still
appear. When `value_position = bottom` (the default), the card reserves the same
vertical space as a gauge card so it lines up neatly next to its neighbours. With
`value_position = left` or `right` no space is reserved, so a `none` card will be
shorter than gauge cards in the same row. `show_value` has no visible effect on a
`none` card — the raw value is always shown in the card heading.

```ini
[[[supplyVoltage]]]
    sensor_type = none
```

This is also the default — a field with no `sensor_type` key behaves as `none`.

---

## Value display

### `value_position` — where the value sits relative to the gauge

Set a global default directly under `[[Telemetry]]`, then override per field:

```ini
[[Telemetry]]
    value_position = bottom     # global default: bottom | left | right | none

    [[[consBatteryVoltage]]]
        value_position = right  # this field overrides the global default
```

Resolution order: field's own `value_position` → `[[Telemetry]]` default →
`bottom`.

Set `value_position = none` (typically as the global default under
`[[Telemetry]]`) to hide the value line for **every** sensor — the gauges still
render, just without the value text. When `value_position = none`, `show_value`
has no effect. You can also set it on a single field to hide just that value.

```
   value_position = bottom        value_position = left      value_position = right
   (default)

        OK                              OK                         OK
     [####____]                    47 [####____]              [####____] 47
        47
```

`left`/`right` place the value beside the gauge. `bottom` places it on its own
line beneath. With `bottom`, the line's space is always reserved so cards in
the same row stay the same height even if some have values hidden.

### `show_value` — whether the value line is shown

```ini
show_value = yes    # default: show the value
show_value = no     # hide the value entirely
```

- `yes` — value is shown at the chosen `value_position`.
- `no` — value is hidden. With `value_position = bottom` the reserved space is
  kept so the card height stays consistent with its neighbours.
- Has no effect when `value_position = none` (the value line is already hidden).

**Note:** The old `show_value = pad` option is removed. Bottom spacing is now
automatic; delete any `pad` lines from your config.

---

## Complete examples

### Example 1: Mixed sensors (status + voltage + signal)

```ini
[[Appearance]]
    telemetry_order = consBatteryVoltage, outTempBatteryStatus, rxCheckPercent
    telemetry_chart_order = consBatteryVoltage, outTempBatteryStatus

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    value_position = bottom

    [[[consBatteryVoltage]]]
        sensor_type = voltage
        max_voltage = 4.5
        min_voltage = 0.0
        low_threshold = 50
        chart_interval = 300

    [[[outTempBatteryStatus]]]
        sensor_type = status
        0 = OK
        1 = Low
        chart_position_0 = 1
        chart_position_1 = 0
        max_chart_position = 1
        low_state = 1
        low_when = at_or_above
        chart_interval = 3600

    [[[rxCheckPercent]]]
        sensor_type = signal
        max_signal = 100
        min_signal = 0
        low_threshold = 30
```

### Example 2: Percentage battery + raw value field

```ini
[[Appearance]]
    telemetry_order = extraBattery7, supplyVoltage

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 7

    [[[extraBattery7]]]
        sensor_type = percent
        low_threshold = 20

    [[[supplyVoltage]]]
        sensor_type = none
```

### Example 3: Value display customisation

```ini
[[Telemetry]]
    value_position = bottom     # default for all fields

    # Show voltage to the right of the bar
    [[[consBatteryVoltage]]]
        sensor_type = voltage
        max_voltage = 4.5
        min_voltage = 0.0
        value_position = right

    # Hide the OK/Low label under the status bar
    [[[outTempBatteryStatus]]]
        sensor_type = status
        0 = OK
        1 = Low
        chart_position_0 = 1
        chart_position_1 = 0
        max_chart_position = 1
        show_value = no
```

---

## Organizing telemetry display

### `telemetry_order` (cards)

Controls the order of telemetry value cards on the left side of the telemetry
page. Only fields listed here are shown.

```ini
[[Appearance]]
    telemetry_order = rxCheckPercent, txBatteryStatus, windBatteryStatus, rainBatteryStatus, outTempBatteryStatus, inTempBatteryStatus, consBatteryVoltage, heatingVoltage, supplyVoltage
```

### `telemetry_chart_order` (charts)

Controls the order of historical charts. Only fields listed here get a chart.

```ini
[[Appearance]]
    telemetry_chart_order = outTempBatteryStatus, inTempBatteryStatus, consBatteryVoltage, supplyVoltage
```

**Usage tips:**
- List fields in the order you want them to appear
- Only fields listed in `telemetry_order` / `telemetry_chart_order` are shown
- Separate field names with commas

---

## Quick reference

### `[[Telemetry]]` global keys

| Key | Purpose | Default |
|---|---|---|
| `allow_zero_values` | Show fields whose value is 0 | `no` |
| `chart_days` | Days of history in charts | `30` |
| `default_interval` | Default chart data-point interval (seconds) | `300` |
| `value_position` | Default value line placement for all cards (`none` hides all values) | `bottom` |

### Per-field keys — all sensor types

| Key | Purpose | Values |
|---|---|---|
| `sensor_type` | Gauge style | `none` \| `voltage` \| `signal` \| `percent` \| `status` |
| `value_position` | Override global placement (`none` hides the value) | `bottom` \| `left` \| `right` \| `none` |
| `show_value` | Show or hide the value | `yes` \| `no` |
| `chart_interval` | Chart data-point interval for this field | seconds |
| `colors` | Chart color override | e.g. `palette1:3` |

### `voltage` keys

| Key | Purpose | Required |
|---|---|---|
| `max_voltage` | Voltage = 100% | yes |
| `min_voltage` | Voltage = 0% | yes |
| `low_threshold` | % below which bar turns red | no (default: 20) |

### `signal` keys

| Key | Purpose | Required |
|---|---|---|
| `max_signal` | Raw value = 100% | no (if omitted, raw value is used as %) |
| `min_signal` | Raw value = 0% | no |
| `low_threshold` | % below which cone turns red | no (default: 20) |

### `percent` keys

| Key | Purpose | Required |
|---|---|---|
| `low_threshold` | % below which bar turns red | no (default: 20) |

### `status` keys

| Key | Purpose | Required |
|---|---|---|
| `0 = Text`, `1 = Text`, … | Labels for each raw value | yes |
| `chart_position_X` | Chart Y-position for raw value X | yes |
| `max_chart_position` | Highest position number used | yes |
| `low_state` | Raw value threshold for red | no |
| `low_when` | `at_or_above` (default) or `at_or_below` | no |
| `flip_values` | Invert chart (`yes` / `no`) | no |

---

## Troubleshooting

**Problem:** A field is not showing on the telemetry page
- Check it is listed in `telemetry_order` under `[[Appearance]]`
- If the sensor can report 0, set `allow_zero_values = yes`

**Problem:** A gauge field shows as a plain number with no gauge
- Add `sensor_type = voltage` / `signal` / `percent` / `status` to the field block

**Problem:** Chart shows numbers instead of labels (status fields)
- Check `chart_position_X` uses the actual raw values your station reports, not
  sequential numbers

**Problem:** Chart looks upside-down (bad status at top)
- Set `flip_values = yes` in the field block

**Problem:** Status bar stays green even when the station reports Low
- Add `low_state` (and `low_when` if needed) to the field block
- Example: `low_state = 1` with `low_when = at_or_above` turns red when the
  station reports `1`
- If a reported value has no matching `chart_position_<value>`, the card shows the
  raw value with no gauge (instead of a green bar) so the gap is visible

**Problem:** Voltage gauge shows 100% green regardless of voltage
- Check `max_voltage` and `min_voltage` are set correctly for your battery range.
  If neither is set the card shows the raw value with no gauge (instead of a full
  bar), so a missing range is obvious

**Problem:** Voltage gauge doesn't turn red when low
- Adjust `low_threshold` (default is 20%). Example: `low_threshold = 50` turns
  red below 50%

**Problem:** Cards in the same row are different heights
- Make sure all cards use `value_position = bottom` (the default). Cards using
  `left` or `right` are a little shorter because the value sits beside the gauge
  rather than on its own line. A `sensor_type = none` card with `left` or `right`
  is also shorter — switch it to `bottom` to match gauge cards

**Problem:** Config from before the overhaul stopped working
- See the **Migration** section at the top of this guide
