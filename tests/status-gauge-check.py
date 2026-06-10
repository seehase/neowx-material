#!/usr/bin/env python3
"""Behavior checks for the status-battery gauge helpers in telemetry.html.tmpl.

Requires the CT3 (Cheetah) package: pip install CT3
Run: python tests/status-gauge-check.py
Prints PASS and exits 0 when all assertions hold.

NOTE: expected to FAIL (missing helpers) until the feature is implemented.
"""
import os
import sys

from Cheetah.Template import Template

TMPL = os.path.join(os.path.dirname(__file__), '..',
                    'skins', 'neowx-material', 'telemetry.html.tmpl')

CFG = {'Extras': {'Telemetry': {'BatteryFields': {
    # 2-state: 0=OK(top), 1=Low(bottom); red at/above raw 1
    'twoState': {'enabled': 'yes', '0': 'OK', '1': 'Low',
                 'chart_position_0': '1', 'chart_position_1': '0',
                 'max_chart_position': '1',
                 'low_state': '1', 'low_when': 'at_or_above'},
    # Ecowitt: 0=Normal, 9=Low; red at/above raw 9 (low_when defaults)
    'ecowitt': {'enabled': 'yes', '0': 'Normal', '9': 'Low',
                'chart_position_0': '1', 'chart_position_9': '0',
                'max_chart_position': '1',
                'low_state': '9'},
    # Inverted 2-state: 1=OK, 0=Low; red at/below raw 0
    'inverted': {'enabled': 'yes', '0': 'Low', '1': 'OK',
                 'chart_position_0': '0', 'chart_position_1': '1',
                 'max_chart_position': '1',
                 'low_state': '0', 'low_when': 'at_or_below'},
    # 5-state, red at/above raw 3 (Low and Critical states)
    'fiveState': {'enabled': 'yes',
                  '0': 'Full', '1': 'Good', '2': 'Fair',
                  '3': 'Low', '4': 'Critical',
                  'chart_position_0': '4', 'chart_position_1': '3',
                  'chart_position_2': '2', 'chart_position_3': '1',
                  'chart_position_4': '0', 'max_chart_position': '4',
                  'low_state': '3'},
    # Good state at LOW position numbers, fixed by flip_values
    'flipped': {'enabled': 'yes', '0': 'OK', '1': 'Low',
                'chart_position_0': '0', 'chart_position_1': '1',
                'max_chart_position': '1', 'flip_values': 'yes',
                'low_state': '1'},
    # No threshold configured: never red
    'noThreshold': {'enabled': 'yes', '0': 'OK', '1': 'Low',
                    'chart_position_0': '1', 'chart_position_1': '0',
                    'max_chart_position': '1'},
    # Voltage regression field (no chart positions)
    'volt': {'enabled': 'yes', 'max_voltage': '4.5', 'min_voltage': '0',
             'low_threshold': '50'},
}}}}

failures = []


def check(label, got, expected):
    got_s = str(got).strip()
    exp_s = str(expected)
    if got_s != exp_s:
        failures.append('%s: got %r, expected %r' % (label, got_s, exp_s))


def main():
    klass = Template.compile(file=TMPL)
    t = klass(searchList=[CFG])

    # --- calculateStatePercentage: (pos+1)/(max+1)*100, flip honored ---
    check('2-state OK pct', t.calculateStatePercentage('twoState', '0'), '100')
    check('2-state Low pct', t.calculateStatePercentage('twoState', '1'), '50')
    check('ecowitt Normal pct', t.calculateStatePercentage('ecowitt', '0'), '100')
    check('ecowitt Low pct (9.0 raw)', t.calculateStatePercentage('ecowitt', '9.0'), '50')
    check('5-state Full pct', t.calculateStatePercentage('fiveState', '0'), '100')
    check('5-state Good pct', t.calculateStatePercentage('fiveState', '1'), '80')
    check('5-state Fair pct', t.calculateStatePercentage('fiveState', '2'), '60')
    check('5-state Low pct', t.calculateStatePercentage('fiveState', '3'), '40')
    check('5-state Critical pct', t.calculateStatePercentage('fiveState', '4'), '20')
    check('flipped OK pct', t.calculateStatePercentage('flipped', '0'), '100')
    check('flipped Low pct', t.calculateStatePercentage('flipped', '1'), '50')
    check('unmapped raw -> None', t.calculateStatePercentage('twoState', '7'), 'None')
    check('no positions -> None', t.calculateStatePercentage('volt', '3.6'), 'None')

    # --- isLowState: raw-value threshold per low_when ---
    check('2-state OK not low', t.isLowState('twoState', '0'), 'False')
    check('2-state Low is low', t.isLowState('twoState', '1'), 'True')
    check('ecowitt 9 is low', t.isLowState('ecowitt', '9'), 'True')
    check('ecowitt 0 not low', t.isLowState('ecowitt', '0'), 'False')
    check('inverted 0 low (at_or_below)', t.isLowState('inverted', '0'), 'True')
    check('inverted 1 not low', t.isLowState('inverted', '1'), 'False')
    check('5-state 3 is low', t.isLowState('fiveState', '3'), 'True')
    check('5-state 4 is low', t.isLowState('fiveState', '4'), 'True')
    check('5-state 2 not low', t.isLowState('fiveState', '2'), 'False')
    check('no threshold never low', t.isLowState('noThreshold', '1'), 'False')
    # flip affects positions/percentage only; the threshold still compares raw
    check('flipped 1 is low', t.isLowState('flipped', '1'), 'True')
    check('flipped 0 not low', t.isLowState('flipped', '0'), 'False')

    # --- getStateFillWidth: 2-state low -> full bar, else proportional ---
    check('2-state low -> full red bar', t.getStateFillWidth('twoState', 50, True), '100')
    check('2-state ok -> pct', t.getStateFillWidth('twoState', 100, False), '100')
    check('flipped 2-state low -> full red bar', t.getStateFillWidth('flipped', 50, True), '100')
    check('5-state low -> proportional', t.getStateFillWidth('fiveState', 40, True), '40')
    check('5-state critical -> proportional', t.getStateFillWidth('fiveState', 20, True), '20')
    check('5-state ok -> pct', t.getStateFillWidth('fiveState', 60, False), '60')

    # --- safe defaults on unparseable values ---
    check('unparseable pct -> None', t.calculateStatePercentage('twoState', 'n/a'), 'None')
    check('unparseable low -> False', t.isLowState('twoState', 'n/a'), 'False')

    # --- regressions: voltage/status behavior unchanged ---
    check('voltage pct', t.calculateBatteryPercentage('volt', '3.6 V'), '80')
    check('voltage color below threshold', t.getBatteryColor('volt', 44), '#f44336')
    check('voltage color above threshold', t.getBatteryColor('volt', 80), '#4caf50')
    check('status label mapping', t.mapBatteryValue('twoState', '0'), 'OK')
    check('status chart position', t.getBatteryChartValue('twoState', '0'), '1')

    if failures:
        print('FAIL (%d)' % len(failures))
        for f in failures:
            print('  - ' + f)
        sys.exit(1)
    print('PASS')


if __name__ == '__main__':
    main()
