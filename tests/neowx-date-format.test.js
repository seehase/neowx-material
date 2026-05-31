// Unit test for the neowxDateFormatter chart-date helper.
// Run: node tests/neowx-date-format.test.js
const assert = require('assert');
const path = require('path');

// Load the exact vendored moment build the skin ships and expose it as the
// global the helper reads (mirrors the browser, where moment is a global).
global.moment = require(
    path.join(__dirname, '..', 'skins', 'neowx-material', 'js', 'vendor', 'moment.min.js')
);

const neowxDateFormatter = require(
    path.join(__dirname, '..', 'skins', 'neowx-material', 'js', 'neowx-date-format.js')
);

// Arbitrary fixed unix timestamp. Assertions compare the helper against a direct
// moment call with the SAME timestamp, so the absolute value is irrelevant and
// the test is timezone-independent.
const TS = 1767322445;

// 1. Axis-style call: ApexCharts passes (value, timestamp); format the timestamp.
assert.strictEqual(
    neowxDateFormatter('DD.MM.YYYY')(null, TS),
    moment.unix(TS).format('DD.MM.YYYY'),
    'axis-style call should format the timestamp arg'
);

// 2. Tooltip-style call: ApexCharts passes only (value); format that value.
assert.strictEqual(
    neowxDateFormatter('DD.MM.YYYY')(TS),
    moment.unix(TS).format('DD.MM.YYYY'),
    'tooltip-style call should fall back to the first arg'
);

// 3. The ":MM" minutes mistake is converted to moment's ":mm".
const out = neowxDateFormatter('HH:MM')(null, TS);
assert.strictEqual(out, moment.unix(TS).format('HH:mm'), '":MM" should become ":mm"');
assert.ok(/^\d{2}:\d{2}$/.test(out), 'expected HH:mm shape, got ' + out);

// 4. Month token "MM" (not preceded by ":") is left untouched.
assert.strictEqual(
    neowxDateFormatter('DD.MM')(null, TS),
    moment.unix(TS).format('DD.MM'),
    'month MM must not be turned into minutes'
);

// 5. Tooltip-style call where ApexCharts passes an options OBJECT as the 2nd arg.
//    Must format the first arg (the timestamp), NOT moment.unix(object) -> "Invalid date".
const tipOut = neowxDateFormatter('DD.MM.YYYY')(TS, { series: [], seriesIndex: 0, w: {} });
assert.strictEqual(
    tipOut,
    moment.unix(TS).format('DD.MM.YYYY'),
    'tooltip call with an opts object as 2nd arg must format the first arg'
);

console.log('neowx-date-format: all tests passed');
