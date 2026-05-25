# Voltage-Based Battery Gauge Update

## What Changed?

The telemetry page now supports **percentage-based battery gauges** for voltage sensors with dynamic color coding!

### Before:
- Battery gauge always showed 100% green
- No visual indication of actual battery level

### After:
- Battery gauge shows actual percentage based on voltage
- Green when above threshold
- Red when below threshold
- Displays voltage value + percentage

---

## Quick Start Configuration

Add this to your `skin.conf` under `[Extras]` → `[[Telemetry]]` → `[[[BatteryFields]]]`:

```ini
[[Telemetry]]
    allow_zero_values = yes
    chart_days = 1
    
    [[[BatteryFields]]]
        [[[[consBatteryVoltage]]]]
            enabled = yes
            max_voltage = 4.5      # Your battery's max voltage (100%)
            min_voltage = 0.0      # Your battery's min voltage (0%)
            low_threshold = 50     # Below 50%, gauge turns red
```

---

## Configuration Options

### max_voltage (required for voltage sensors)
- **Purpose:** The voltage that represents 100% battery
- **Example:** `max_voltage = 4.5` (for a 4.5V battery)
- **Default:** 100 (treats value as percentage)

### min_voltage (optional)
- **Purpose:** The voltage that represents 0% battery
- **Example:** `min_voltage = 0.0`
- **Default:** 0

### low_threshold (optional)
- **Purpose:** Percentage below which gauge turns red
- **Example:** `low_threshold = 50` (red below 50%)
- **Default:** 20 (red below 20%)

---

## Examples

### Example 1: 4.5V Battery (Your Case)
```ini
[[[[consBatteryVoltage]]]]
    enabled = yes
    max_voltage = 4.5
    min_voltage = 0.0
    low_threshold = 50
```

**Results:**
- 4.5V → 100% green gauge ✅
- 3.6V → 80% green gauge ✅
- 2.0V → 44% red gauge ⚠️ (below 50%)

### Example 2: 12V Battery System
```ini
[[[[battery12v]]]]
    enabled = yes
    max_voltage = 14.4    # Fully charged
    min_voltage = 10.5    # Discharged
    low_threshold = 30
```

**Results:**
- 14.4V → 100% green
- 12.45V → 50% green
- 11.0V → 12% red ⚠️ (below 30%)

### Example 3: 3.3V LiPo Battery
```ini
[[[[lipoBattery]]]]
    enabled = yes
    max_voltage = 4.2
    min_voltage = 3.0
    low_threshold = 25
```

---

## Visual Display

The battery cards now show:

```
┌──────────────────────────────────┐
│   Outside Temperature Battery    │
│                                  │
│  0.0 V        4.5 V        4.5 V │
│  (00:00)                 (14:23) │
│                                  │
│  [████████████████░░]  ← 80%     │
│         80%                      │
└──────────────────────────────────┘
```

- **Top row:** Sensor name
- **Second row:** Min value, Current value, Max value (with timestamps)
- **Third row:** Visual battery gauge (green/red)
- **Bottom:** Percentage display

---

## Color Coding

| Condition | Color | Hex Code |
|-----------|-------|----------|
| Above threshold | Green | #4caf50 |
| Below threshold | Red | #f44336 |

The gauge smoothly transitions width and color.

---

## For Status-Based Sensors

If your sensor reports status codes (0=OK, 1=Low) instead of voltage:
- **Don't** add `max_voltage`, `min_voltage`, or `low_threshold`
- **Do** use the standard text label configuration
- See the main `battery-config-guide.md` for details

---

## Testing

1. Add the configuration to your `skin.conf`
2. Restart weewx:
   ```bash
   sudo systemctl restart weewx
   ```
3. Open the telemetry page
4. Check the battery gauge shows the correct percentage
5. Verify color changes to red when below threshold

---

## Troubleshooting

**Gauge still shows 100%?**
- Make sure `max_voltage` is set correctly
- Check your sensor is actually reporting voltage (not status codes)
- Restart WeeWX after configuration changes: `sudo systemctl restart weewx`
- WeeWX formats values with units - the template now strips these automatically

**Wrong percentage?**
- Verify `max_voltage` matches your battery's actual maximum
- Example: 4.5V max battery needs `max_voltage = 4.5`
- If you see 4.5V = 100% but configured `max_voltage = 10.5`, check you restarted WeeWX

**Charts not showing any values?**
- This was fixed in the latest update
- Make sure you have the latest telemetry.html.tmpl
- For voltage sensors, charts now display raw voltage values
- Restart WeeWX after updating the template

**Values shown with commas (e.g., "4,5 V") causing issues?**
- Fixed! The template now automatically strips units and handles both comma and period decimal separators
- Works with: "4.5 V", "4,5 V", "4.5", "4,5"
- No configuration needed

**Not turning red?**
- Check `low_threshold` value
- Make sure voltage is actually below the threshold

**Want it to turn red earlier?**
- Increase the `low_threshold` value
- Example: `low_threshold = 60` (red below 60%)

---

## Complete Example Configuration

```ini
[Extras]
    [[Telemetry]]
        allow_zero_values = yes
        chart_days = 1
        
        [[[BatteryFields]]]
            # Voltage-based sensors
            [[[[consBatteryVoltage]]]]
                enabled = yes
                max_voltage = 4.5
                min_voltage = 0.0
                low_threshold = 50
            
            [[[[outTempBatteryVoltage]]]]
                enabled = yes
                max_voltage = 4.5
                min_voltage = 0.0
                low_threshold = 30
            
            # Status-based sensors (no voltage settings)
            [[[[batteryStatus1]]]]
                enabled = yes
                0 = Normal
                1 = Low
                chart_position_0 = 1
                chart_position_1 = 0
                max_chart_position = 1
                flip_values = no
```

---

## See Also

- `battery-config-guide.md` - Complete configuration guide
- `skin.conf` - Your main configuration file

