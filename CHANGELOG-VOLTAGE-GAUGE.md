# Changelog: Voltage-Based Battery Gauge Feature

## Date: May 25, 2026

## Summary
Added support for **voltage-based battery percentage gauges** with dynamic color coding on the telemetry page. Previously, battery gauges always showed 100% green regardless of actual voltage. Now they display accurate percentages with red/green color coding based on configurable thresholds.

---

## Changes Made

### 1. Modified Files

#### `skins/neowx-material/telemetry.html.tmpl`

**New Functions Added:**

1. **`calculateBatteryPercentage($name, $value)`**
   - Calculates actual battery percentage based on voltage
   - Uses `max_voltage` and `min_voltage` from configuration
   - Returns value clamped between 0-100%
   - Formula: `((current - min) / (max - min)) * 100`

2. **`getBatteryColor($name, $percentage)`**
   - Determines gauge color based on threshold
   - Returns green (#4caf50) when above threshold
   - Returns red (#f44336) when below threshold
   - Uses `low_threshold` from configuration (default: 20%)

**Modified Function:**

3. **`batteryCard($name)`**
   - Now calculates actual battery percentage
   - Applies dynamic color to gauge based on threshold
   - Displays percentage below the gauge
   - Shows voltage value as main display (e.g., "4.5 V")
   - Gauge width now reflects actual battery level

**Visual Changes:**
```diff
- Fixed 100% green gauge
- Fixed percentage display

+ Dynamic width based on actual percentage
+ Color changes from green to red below threshold
+ Percentage displayed below gauge
+ Smooth transitions for width and color changes
```

---

### 2. Documentation Updates

#### `battery-config-guide.md`

**Added Sections:**
- "Voltage-Based Battery Gauge (For Voltage Sensors)"
- Complete explanation of new configuration options
- Example configurations for different voltage ranges
- Troubleshooting for voltage-based sensors

**New Configuration Options Documented:**
- `max_voltage` - Maximum voltage representing 100%
- `min_voltage` - Minimum voltage representing 0%
- `low_threshold` - Percentage threshold for red color

**New Examples:**
- Console Battery (0-4.5V)
- 12V Battery System (10.5-14.4V)
- 3.3V LiPo Battery (3.0-4.2V)
- Mixed configuration (status + voltage sensors)

---

### 3. New Documentation Files

#### `VOLTAGE-BATTERY-GAUGE-UPDATE.md`
- Quick start guide for new feature
- Configuration examples
- Visual display explanation
- Troubleshooting guide
- Complete example configurations

---

## Configuration Examples

### Basic Voltage Sensor (4.5V Battery)
```ini
[[[[consBatteryVoltage]]]]
    enabled = yes
    max_voltage = 4.5
    min_voltage = 0.0
    low_threshold = 50
```

### Result:
- **4.5V** → 100% green gauge
- **3.6V** → 80% green gauge
- **2.0V** → 44% red gauge (below 50% threshold)

---

## Technical Details

### Percentage Calculation
```python
percentage = ((current_voltage - min_voltage) / (max_voltage - min_voltage)) * 100
percentage = max(0, min(100, percentage))  # Clamp to 0-100
```

### Color Determination
```python
if percentage < low_threshold:
    color = "#f44336"  # Red
else:
    color = "#4caf50"  # Green
```

### CSS Transitions
- Width transition: 0.3s ease
- Color transition: 0.3s ease
- Smooth visual feedback

---

## Backward Compatibility

✅ **Fully backward compatible**
- Existing status-based sensors (0=OK, 1=Low) continue to work
- Old configurations don't need any changes
- New voltage options are optional
- Falls back to 100% if voltage settings not configured

---

## Testing Checklist

- [x] Template syntax validation (no errors)
- [x] Percentage calculation logic
- [x] Color threshold logic
- [x] Integration with existing battery mapping
- [x] CSS transitions for smooth animation
- [x] Documentation completeness
- [x] Example configurations
- [x] Troubleshooting guide

---

## Migration Guide

### For Existing Users with Status Sensors
**No action required!** Your existing configuration continues to work.

### For Users with Voltage Sensors
Add these three lines to each voltage sensor:

```ini
max_voltage = 4.5      # Your battery's max voltage
min_voltage = 0.0      # Usually 0
low_threshold = 50     # Adjust to your preference
```

---

## Configuration Reference

### New Options (All Optional)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_voltage` | float | 100 | Maximum voltage (100%) |
| `min_voltage` | float | 0 | Minimum voltage (0%) |
| `low_threshold` | float | 20 | Red color threshold (%) |

### When to Use
- **Voltage sensors** (e.g., 0-5V, 0-12V) → Use new options
- **Status sensors** (e.g., 0=OK, 1=Low) → Don't use new options

---

## Future Enhancements (Possible)

- [ ] Configurable colors (not just green/red)
- [ ] Multiple color thresholds (green/yellow/orange/red)
- [ ] Warning threshold in addition to critical threshold
- [ ] Different gauge styles (circular, vertical, etc.)
- [ ] Battery percentage in card title
- [ ] History of battery changes overview

---

## Support

For issues or questions:
1. Check `battery-config-guide.md` for detailed documentation
2. Check `VOLTAGE-BATTERY-GAUGE-UPDATE.md` for quick reference
3. Verify configuration syntax in `skin.conf`
4. Check troubleshooting section in documentation

---

## Files Modified Summary

```
Modified:
  ✏️  skins/neowx-material/telemetry.html.tmpl
  ✏️  battery-config-guide.md

Created:
  ✨  VOLTAGE-BATTERY-GAUGE-UPDATE.md
  ✨  CHANGELOG-VOLTAGE-GAUGE.md
```

---

## Example Before/After

### Before Update
```
┌──────────────────────────────────┐
│   Console Battery                │
│  4.5 V                           │
│  [████████████████████]  ← 100%  │  Always 100% green
└──────────────────────────────────┘
```

### After Update (with 3.6V actual voltage)
```
┌──────────────────────────────────┐
│   Console Battery                │
│                                  │
│  0.0 V        4.5 V        4.5 V │
│  (00:00)                 (14:23) │
│                                  │
│  [████████████████░░]  ← 80%     │  Actual 80% green
│         80%                      │
└──────────────────────────────────┘
```

### After Update (with 2.0V actual voltage - below threshold)
```
┌──────────────────────────────────┐
│   Console Battery                │
│                                  │
│  0.0 V        2.0 V        4.5 V │
│  (00:00)                 (14:23) │
│                                  │
│  [████████░░░░░░░░░░░]  ← 44%    │  Red below 50%
│         44%                      │
└──────────────────────────────────┘
```

