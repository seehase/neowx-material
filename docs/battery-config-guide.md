# Battery Field Mapping Configuration Guide

## Overview
This feature allows you to convert numeric battery status values (like 0, 1, 9) 
into human-readable custom text (like "OK", "Low", "Critical") and display them with custom charts.

---

## Step-by-Step Configuration

### Step 1: Find Your Station's Battery Values

First, you need to know what numeric values your weather station reports for battery status. 
If you know your station has a "battery sensor" but it's not showing under the Telemetry page edit the skin.conf 
to allow_zero_values = yes to plot it.
Or check your weewx database or reports to see what values appear.

**Common examples:**
- Simple stations: `0` and `1` 
- Ecowitt stations: `0` (Normal) and `9` (Low)
- Advanced stations: `0`, `1`, `2`, `3`, `4` (multiple levels)

---

### Step 2: Understanding the Configuration Structure

For each battery sensor, you need to configure 4 things:

```ini
[[Telemetry]]
allow_zero_values = yes #needed if the sensor output might be equal to 0
chart_days = 1
    [[[BatteryFields]]]
        [[[[sensorName]]]]
            enabled = yes
            
            # 1. TEXT LABELS: What text to display for each raw value
            0 = Normal
            9 = Low
            
            # 2. CHART POSITIONS: Where each value appears on the chart
            chart_position_0 = 1
            chart_position_9 = 0
            
            # 3. MAX POSITION: The highest position number used
            max_chart_position = 1
            
            # 4. FLIP: Whether to flip the chart upside-down
            flip_values = no
            
            # 5. VOLTAGE-BASED GAUGE (Optional): For voltage sensors (e.g., 0-5V)
            max_voltage = 4.5      # Maximum voltage (100%)
            min_voltage = 0.0      # Minimum voltage (0%)
            low_threshold = 50     # Below this percentage, gauge turns red
```

---

### Voltage-Based Battery Gauge (For Voltage Sensors)

If your battery sensor reports actual voltage values (e.g., 4.5V, 3.6V, 2.0V) instead of status codes, you can configure the battery gauge to show a **percentage-based visual indicator** with color coding:

#### Configuration Options:

```ini
[[[[consBatteryVoltage]]]]
    enabled = yes
    
    # Voltage range configuration
    max_voltage = 4.5      # Full battery voltage (100%)
    min_voltage = 0.0      # Empty battery voltage (0%)
    low_threshold = 50     # Below 50%, gauge turns red
```

#### How It Works:

1. **max_voltage**: The voltage that represents 100% battery
2. **min_voltage**: The voltage that represents 0% battery (usually 0)
3. **low_threshold**: Percentage below which the gauge turns red (default: 20%)

#### Example Scenarios:

**Scenario 1: Console Battery (0V to 4.5V)**
```ini
[[[[consBatteryVoltage]]]]
    enabled = yes
    max_voltage = 4.5
    min_voltage = 0.0
    low_threshold = 50
```
- Current: 4.5V → Shows 100% (green)
- Current: 3.6V → Shows 80% (green)
- Current: 2.0V → Shows 44% (red, below threshold)

**Scenario 2: 12V Battery System**
```ini
[[[[batteryVoltage12v]]]]
    enabled = yes
    max_voltage = 14.4     # Fully charged 12V battery
    min_voltage = 10.5     # Discharged 12V battery
    low_threshold = 30
```
- Current: 14.4V → Shows 100% (green)
- Current: 12.45V → Shows 50% (green)
- Current: 11.0V → Shows 12% (red, below 30%)

**Scenario 3: 3.3V LiPo Battery**
```ini
[[[[lipoBattery]]]]
    enabled = yes
    max_voltage = 4.2      # Fully charged LiPo
    min_voltage = 3.0      # Minimum safe voltage
    low_threshold = 25
```

#### Visual Display:

The battery gauge will:
- Display the actual voltage value (e.g., "3.6 V")
- Show a visual gauge filled to the calculated percentage
- Change from **green** to **red** when below the threshold
- Display the percentage below the gauge (e.g., "80%")

**Note:** For status-based sensors (0=OK, 9=Low), leave out the voltage options and use the standard text label configuration instead.

---

### Step 3: Configure Text Labels

**Rule:** The number must match what your station reports.

```ini
# Your station reports these raw values → Display this text
0 = Normal
9 = Low
```

**Examples:**

**Two-level battery (0 and 1):**
```ini
0 = OK
1 = Low
```

**Three-level battery (0, 1, and 2):**
```ini
0 = Good
1 = Fair  
2 = Low
```

**Five-level battery (0 through 4):**
```ini
0 = Full
1 = Good
2 = Fair
3 = Low
4 = Critical
```

---

### Step 4: Configure Chart Positions

**Rule:** `chart_position_X` where X is the RAW VALUE your station reports.

The position number controls where it appears on the chart:
- **Higher numbers = Top of chart** (good status)
- **Lower numbers = Bottom of chart** (bad status)

#### Example 1: Ecowitt (values 0 and 9)

```ini
# Station reports 0 for Normal → Show at top (position 1)
chart_position_0 = 1

# Station reports 9 for Low → Show at bottom (position 0)
chart_position_9 = 0

# Chart range is 0 to 1
max_chart_position = 1
```

**Visual result:**
```
Chart Y-axis:
1 (top)    ← Normal (green/good)
0 (bottom) ← Low (red/warning)
```

#### Example 2: Simple Battery (values 0 and 1)

```ini
# Station reports 0 for OK → Show at top (position 1)
chart_position_0 = 1

# Station reports 1 for Low → Show at bottom (position 0)
chart_position_1 = 0

# Chart range is 0 to 1
max_chart_position = 1
```

#### Example 3: Three-Level Battery (values 0, 1, and 2)

```ini
# Station reports 0 for Good → Show at top (position 2)
chart_position_0 = 2

# Station reports 1 for Fair → Show in middle (position 1)
chart_position_1 = 1

# Station reports 2 for Low → Show at bottom (position 0)
chart_position_2 = 0

# Chart range is 0 to 2
max_chart_position = 2
```

**Visual result:**
```
Chart Y-axis:
2 (top)    ← Good
1 (middle) ← Fair
0 (bottom) ← Low
```

---

### Step 5: Set Maximum Chart Position

**Rule:** Set this to the highest position number you used.

```ini
# If your positions are 0 and 1
max_chart_position = 1

# If your positions are 0, 1, and 2
max_chart_position = 2

# If your positions are 0, 1, 2, 3, and 4
max_chart_position = 4
```

---

### Step 6: Flip Values (Optional)

If your chart looks upside-down (bad status at top, good at bottom), use flip:

```ini
# Normal display (good at top)
flip_values = no

# Flipped display (inverts the chart)
flip_values = yes
```

---

## Common Mistakes

### ❌ WRONG: Using sequential numbers instead of raw values
```ini
0 = Normal
9 = Low
chart_position_0 = 1
chart_position_1 = 0  # WRONG! Station doesn't report value "1"
```

### ✅ CORRECT: Using the actual raw values
```ini
0 = Normal
9 = Low
chart_position_0 = 1
chart_position_9 = 0  # CORRECT! Matches the raw value "9"
```

---

## Complete Examples

### Example 1: Ecowitt Battery (0=Normal, 9=Low)

```ini
[[Appearance]]
    # Card display order
    telemetry_order = batteryStatus1, rxCheckPercent
    # Chart display order (only sensors you want to track historically)
    telemetry_chart_order = batteryStatus1

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    
    [[[BatteryFields]]]
        [[[[batteryStatus1]]]]
            enabled = yes
            0 = Normal
            9 = Low
            chart_position_0 = 1
            chart_position_9 = 0
            max_chart_position = 1
            flip_values = no
```

### Example 2: Simple Battery (0=OK, 1=Change)

```ini
[[Appearance]]
    telemetry_order = outTempBatteryStatus, rxCheckPercent
    telemetry_chart_order = outTempBatteryStatus

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    
    [[[BatteryFields]]]
        [[[[outTempBatteryStatus]]]]
            enabled = yes
            0 = OK
            1 = Change
            chart_position_0 = 1
            chart_position_1 = 0
            max_chart_position = 1
            flip_values = no
```

### Example 3: Multi-Level Battery (0-4)

```ini
[[Appearance]]
    telemetry_order = extraBatteryStatus1, rxCheckPercent
    telemetry_chart_order = extraBatteryStatus1

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 7
    
    [[[BatteryFields]]]
        [[[[extraBatteryStatus1]]]]
            enabled = yes
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
            flip_values = no
```

### Example 4: Voltage-Based Battery (0V to 4.5V with percentage gauge)

```ini
[[Appearance]]
    telemetry_order = consBatteryVoltage, outTempBatteryVoltage, rxCheckPercent
    telemetry_chart_order = consBatteryVoltage, outTempBatteryVoltage

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    
    [[[BatteryFields]]]
        [[[[consBatteryVoltage]]]]
            enabled = yes
            # Voltage range for percentage calculation
            max_voltage = 4.5
            min_voltage = 0.0
            low_threshold = 50
        
        [[[[outTempBatteryVoltage]]]]
            enabled = yes
            max_voltage = 4.5
            min_voltage = 0.0
            low_threshold = 30
```

**Result:**
- When voltage = 4.5V → Displays "4.5 V" with 100% green gauge
- When voltage = 3.6V → Displays "3.6 V" with 80% green gauge
- When voltage = 2.0V → Displays "2.0 V" with 44% red gauge (below 50% threshold)

### Example 5: Mixed Configuration (Status + Voltage sensors)

```ini
[[Appearance]]
    # Display voltage sensor first, then status sensor
    telemetry_order = consBatteryVoltage, batteryStatus1, rxCheckPercent
    # Show both in charts
    telemetry_chart_order = consBatteryVoltage, batteryStatus1

[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    
    [[[BatteryFields]]]
        # Status-based sensor (0=OK, 1=Low)
        [[[[batteryStatus1]]]]
            enabled = yes
            0 = Normal
            1 = Low
            chart_position_0 = 1
            chart_position_1 = 0
            max_chart_position = 1
            flip_values = no
        
        # Voltage-based sensor
        [[[[consBatteryVoltage]]]]
            enabled = yes
            max_voltage = 4.5
            min_voltage = 0.0
            low_threshold = 50
```

---

## Organizing Telemetry Display

You can control the display order of both telemetry **cards** and **charts** on the telemetry page using two configuration options in `skin.conf`:

### telemetry_order (Cards)
Controls the order of telemetry value cards displayed on the left side of the telemetry page. These show current sensor values.

```ini
[[Appearance]]
    telemetry_order = rxCheckPercent, txBatteryStatus, windBatteryStatus, rainBatteryStatus, outTempBatteryStatus, inTempBatteryStatus, consBatteryVoltage, heatingVoltage, supplyVoltage, referenceVoltage, extraBattery1, extraBattery2, extraBattery3, extraBattery4, extraBattery5, extraBattery6, extraBattery7, extraBattery8
```

### telemetry_chart_order (Charts)
Controls the order of telemetry historical charts. These show battery trends over time (configurable via `chart_days`).

```ini
[[Appearance]]
    telemetry_chart_order = outTempBatteryStatus, inTempBatteryStatus, consBatteryVoltage, supplyVoltage, referenceVoltage
```

**Usage tips:**
- List sensors in the order you want them to appear
- Only configured and enabled sensors will be displayed
- Sensors not in the list won't be shown
- Separate sensor names with commas

**Example:**
If you want to prioritize voltage sensors, you can reorder them:

```ini
[[Appearance]]
    # Show voltage sensors first in cards
    telemetry_order = consBatteryVoltage, supplyVoltage, referenceVoltage, outTempBatteryStatus, inTempBatteryStatus, rxCheckPercent
    
    # Show only critical voltage charts
    telemetry_chart_order = consBatteryVoltage, supplyVoltage
```

---

## Quick Reference

### Text-Based Status Configuration
| Setting | Purpose | Example |
|---------|---------|---------|
| `enabled` | Turn mapping on/off | `yes` or `no` |
| `0 = Text` | Label for raw value 0 | `0 = Normal` |
| `chart_position_X` | Y-axis position for value X | `chart_position_0 = 1` |
| `max_chart_position` | Highest position used | `1` for 2 levels, `2` for 3 levels, etc. |
| `flip_values` | Invert chart display | `yes` or `no` |

### Voltage-Based Percentage Configuration
| Setting | Purpose | Example |
|---------|---------|---------|
| `max_voltage` | Maximum voltage (100%) | `4.5` (for 4.5V max) |
| `min_voltage` | Minimum voltage (0%) | `0.0` (typically 0) |
| `low_threshold` | Percentage to turn red | `50` (below 50% = red) |

### Telemetry Display Order
| Setting | Purpose | Location in skin.conf |
|---------|---------|---------------------|
| `telemetry_order` | Order of value cards | `[[Appearance]]` section |
| `telemetry_chart_order` | Order of historical charts | `[[Appearance]]` section |
| `chart_days` | Days of history to show in charts | `[[Telemetry]]` section (default: 30) |

**Note:** For voltage-based sensors, you don't need text labels or chart positions. The gauge automatically calculates the percentage and applies color coding.

---

## Troubleshooting
**Problem:** The sensor is not even showing under telemetry
- **Check:** Make sure `allow_zero_values = yes` so the sensor gets plotted even if is reporting 0

**Problem:** Chart shows numbers instead of text labels
- **Check:** Make sure `chart_position_X` uses the actual raw values your station reports

**Problem:** Chart looks upside-down (bad at top, good at bottom)
- **Solution:** Set `flip_values = yes`

**Problem:** Values show as "1", "2" instead of your labels
- **Check:** Your `chart_position_X` numbers must match the raw values from your station

**Problem:** Page breaks when sensor doesn't exist
- **Solution:** Only configure sensors that actually exist, or set `enabled = no`

**Problem:** Battery gauge always shows 100% green (voltage sensors)
- **Solution:** Configure `max_voltage` and `min_voltage` for voltage-based sensors
- **Example:** For a 4.5V battery, set `max_voltage = 4.5` and `min_voltage = 0.0`
- **Note:** The template automatically strips units (" V") and handles both comma and period decimal separators
- **Restart WeeWX** after configuration changes

**Problem:** Battery gauge doesn't turn red when voltage is low
- **Solution:** Adjust the `low_threshold` value (default is 20%)
- **Example:** To turn red below 50%, set `low_threshold = 50`

**Problem:** Battery percentage seems incorrect
- **Check:** Make sure `max_voltage` matches your actual maximum battery voltage
- **Check:** Verify your sensor is reporting voltage values, not status codes
- **Example:** If your battery is 3.7V LiPo (max 4.2V), use `max_voltage = 4.2`
- **Calculation:** Percentage = (current - min) ÷ (max - min) × 100

**Problem:** Values appear with comma (e.g., "4,5 V") and gauge shows 100%
- **Fixed!** The template now automatically handles European decimal format
- **No action needed** - just restart WeeWX to apply template updates

---

## Testing Your Configuration

1. Add the configuration to `skin.conf`
2. Restart weewx: `sudo systemctl restart weewx`
3. Check the telemetry page
4. Look at the chart - "good" status should be at the top
5. If upside-down, set `flip_values = yes`
