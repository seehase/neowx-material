// Weewx MQTT Client Script
//
// Version 1.0.1
//
// 1. INIT PAHO CLIENT
// Configuration is injected from index.html.tmpl via window.MQTT_CONFIG
// Only initialize if MQTT is enabled

var client = null;
var options = null;

// Wrap initialization to ensure DOM and dependencies are ready
(function initMQTT() {
    // Check if MQTT is enabled before initialization
    if (window.MQTT_CONFIG && window.MQTT_CONFIG.enabled) {
        debugLog('MQTT enabled - initializing connection');

        client = new Paho.Client(
            window.MQTT_CONFIG.host,
            window.MQTT_CONFIG.port,
            window.MQTT_CONFIG.websocket_path,
            "myclientid_" + parseInt(Math.random() * 100, 10));

        options = {
            useSSL: window.MQTT_CONFIG.use_ssl,
            userName: window.MQTT_CONFIG.username,
            password: window.MQTT_CONFIG.password,
            reconnect: true,
            onSuccess: function () {
                console.log("Connected to MQTT Broker");
                updateMQTTStatusIndicator(true);
                client.subscribe(window.MQTT_CONFIG.topic);
            },
            onFailure: function (e) {
                console.log("MQTT Connection Failed", e);
                updateMQTTStatusIndicator(false);
            }
        };

        client.connect(options);
    } else {
        debugLog('MQTT disabled - skipping connection');
    }
})();

// --- HELPER FUNCTION: Update MQTT status indicator ---
function updateMQTTStatusIndicator(connected) {
    if (window.MQTT_CONFIG && window.MQTT_CONFIG.enabled) {
        console.log('[MQTT INDICATOR] Function called with:', connected);
        var indicator = document.getElementById('mqtt-indicator');

        if (!indicator) {
            console.log('[MQTT INDICATOR] Element NOT found!');
            return;
        }

        console.log('[MQTT INDICATOR] Element found, applying styles...');

        if (connected === true) {
            // Connected - Green (using !important to override CSS inheritance)
            indicator.style.cssText = 'color: #00ff00 !important; vertical-align: middle;';
            console.log('[MQTT INDICATOR] Set color to GREEN');
            if (window.MQTT_CONFIG && window.MQTT_CONFIG.text_connected) {
                indicator.setAttribute('title', window.MQTT_CONFIG.text_connected);
                indicator.setAttribute('data-original-title', window.MQTT_CONFIG.text_connected);
                // Initialize/update Bootstrap tooltip
                if (typeof $ !== 'undefined' && $.fn.tooltip) {
                    $(indicator).tooltip('dispose').tooltip();
                }
                console.log('[MQTT INDICATOR] Set tooltip:', window.MQTT_CONFIG.text_connected);
            }
        } else if (connected === false) {
            // Failed - Red (using !important to override CSS inheritance)
            indicator.style.cssText = 'color: #ff4444 !important; vertical-align: middle;';
            console.log('[MQTT INDICATOR] Set color to RED');
            if (window.MQTT_CONFIG && window.MQTT_CONFIG.text_failed) {
                indicator.setAttribute('title', window.MQTT_CONFIG.text_failed);
                indicator.setAttribute('data-original-title', window.MQTT_CONFIG.text_failed);
                // Initialize/update Bootstrap tooltip
                if (typeof $ !== 'undefined' && $.fn.tooltip) {
                    $(indicator).tooltip('dispose').tooltip();
                }
                console.log('[MQTT INDICATOR] Set tooltip:', window.MQTT_CONFIG.text_failed);
            }
        } else if (connected === null) {
            // Disabled - hide status
            console.log('[MQTT INDICATOR] Hiding indicator (MQTT disabled)');
            var statusContainer = document.getElementById('mqtt-status');
            if (statusContainer) {
                statusContainer.style.display = 'none';
            }
        }
    }
}

// 2. Global Helper Functions
function getCompass(deg) {
    if (deg === undefined || deg === null || isNaN(deg)) return "";
    let val = Math.floor((deg / 22.5) + 0.5);

    // Use language-specific directions passed from skin.conf via MQTT_CONFIG,
    // fall back to English if not available or incomplete (need at least 16 entries)
    const fallbackDirections = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
    let directions = fallbackDirections;
    if (window.MQTT_CONFIG && Array.isArray(window.MQTT_CONFIG.directions) && window.MQTT_CONFIG.directions.length >= 16) {
        directions = window.MQTT_CONFIG.directions;
    }
    return directions[(val % 16)];
}

// 3. MQTT MESSAGE HANDLER
// Only set up handler if client was created (i.e., MQTT is enabled)
if (client) {
    client.onMessageArrived = function (message) {
        try {
            var payload = JSON.parse(message.payloadString);
            debugLog('Message received: ' + JSON.stringify(payload).substring(0, 100) + '...');

            // Check if timestamp is newer, if yes - update page
            var timestampCheck = evaluateMessageTimestamp(payload);
            if (timestampCheck.isNewer) {
                debugLog('Timestamp check passed (isNewer: ' + timestampCheck.isNewer + ', skipped: ' + timestampCheck.skipped + '), updating values');
                updateDateTime(payload, timestampCheck.skipped);
                updatePayloadValues(payload);
                updateTelemetry(payload);
            } else {
                debugLog('Timestamp check failed, no update performed');
            }

        } catch (e) {
            console.log("❌ Sync Error:", e);
        }
    };
}

// --- HELPER FUNCTION 1: Check if payload timestamp is newer ---
// Returns: { isNewer: bool, skipped: bool }
function evaluateMessageTimestamp(payload) {
    // Check if timestamp check should be skipped
    if (window.MQTT_CONFIG && window.MQTT_CONFIG.skip_timestamp_check === true) {
        debugLog('Timestamp check skipped (skip_timestamp_check is enabled)');
        return { isNewer: true, skipped: true };
    }

    // Get the timestamp field name from config (default: dateTime)
    var timestampField = (window.MQTT_CONFIG && window.MQTT_CONFIG.message_timestamp_field)
        ? window.MQTT_CONFIG.message_timestamp_field
        : 'dateTime';

    if (payload[timestampField] === undefined) {
        debugLog('No Timestamp in payload field "' + timestampField + '", and NO timestamp check -> no update performed');
        return { isNewer: false, skipped: false };
    }

    var timeSpan = document.getElementById('current-datetime');
    if (!timeSpan) return { isNewer: false, skipped: false };

    var currentUnixTime = parseInt(timeSpan.getAttribute('data-timestamp'), 10);
    var payloadUnixTime = parseFloat(payload[timestampField]);

    debugLog('Timestamp comparison - Server: ' + currentUnixTime + ', Payload: ' + payloadUnixTime + ' (field: ' + timestampField + ')');

    if (payloadUnixTime > currentUnixTime) {
        debugLog('✓ Payload timestamp is newer');
        return { isNewer: true, skipped: false };
    } else {
        debugLog('⊗ Payload timestamp is not newer, skipping update');
        return { isNewer: false, skipped: false };
    }
}

// --- HELPER FUNCTION 2: Update datetime on page ---
function updateDateTime(payload, skipped) {
    var timeSpan = document.getElementById('current-datetime');
    if (!timeSpan) return;

    var payloadUnixTime;
    var payloadDate;

    // Get the timestamp field name from config (default: dateTime)
    var timestampField = (window.MQTT_CONFIG && window.MQTT_CONFIG.message_timestamp_field)
        ? window.MQTT_CONFIG.message_timestamp_field
        : 'dateTime';

    // Always try to use timestamp from payload
    if (payload[timestampField] !== undefined) {
        payloadUnixTime = parseFloat(payload[timestampField]);
        payloadDate = new Date(payloadUnixTime * 1000);
        debugLog('Using timestamp from payload field "' + timestampField + '": ' + payloadUnixTime +
                 (skipped ? ' (timestamp check was skipped)' : ''));
    } else {
        // Fallback: if timestamp field not in payload, use current time
        payloadDate = new Date();
        payloadUnixTime = payloadDate.getTime() / 1000;
        debugLog('⚠️ Timestamp field "' + timestampField + '" not found in payload, using current time');
    }

    // Initialize DATETIME_CONFIG if not present (safety check)
    if (typeof window.DATETIME_CONFIG === 'undefined') {
        window.DATETIME_CONFIG = {
            weewx_format: '%a %d %H:%M'  // Default fallback
        };
    }

    // Convert WeeWX strftime format to JavaScript-compatible format (only once)
    if (!window.DATETIME_CONFIG.js_format) {
        var strftimeFormat = window.DATETIME_CONFIG.weewx_format || '%a %d %H:%M';
        window.DATETIME_CONFIG.js_format = convertStrftimeToJS(strftimeFormat);
        debugLog('Using WeeWX format: ' + strftimeFormat + ' -> JS format: ' + window.DATETIME_CONFIG.js_format);
    }

    // Format the new datetime using the converted format
    var newDateTime = formatDateTime(payloadDate, window.DATETIME_CONFIG.js_format);

    timeSpan.innerHTML = newDateTime;
    timeSpan.setAttribute('data-timestamp', payloadUnixTime);

    debugLog('✓ Updated datetime to: ' + newDateTime + ' (Unix: ' + payloadUnixTime + ')');

    // Visual feedback - check if flash is enabled
    if (window.MQTT_CONFIG && window.MQTT_CONFIG.flash_on_update !== false) {
        // Get flash color from configuration (default to green if not set)
        var flashColor = (window.MQTT_CONFIG && window.MQTT_CONFIG.flash_color)
            ? window.MQTT_CONFIG.flash_color
            : "#00ff00";

        timeSpan.style.transition = "color 0.5s, text-shadow 0.5s";
        timeSpan.style.color = flashColor;
        timeSpan.style.textShadow = "0 0 8px " + flashColor;
        setTimeout(function () {
            timeSpan.style.color = "";
            timeSpan.style.textShadow = "none";
        }, 1500);
    }
}


// --- HELPER FUNCTION: Convert Python strftime format to JavaScript-compatible format ---
// Takes a Python strftime format string (e.g., "%d.%m.%Y %H:%M") and converts it to a custom format
// that our formatDateTime function can use (e.g., "DD.MM.YYYY HH:mm")
function convertStrftimeToJS(strftimeFormat) {
    if (!strftimeFormat) return 'YYYY-MM-DD HH:mm:ss';

    debugLog('Converting strftime format: ' + strftimeFormat);

    // Map Python strftime codes to our JavaScript format tokens
    var converted = strftimeFormat
        // Date components
        .replace(/%Y/g, 'YYYY')      // 4-digit year
        .replace(/%y/g, 'YY')        // 2-digit year
        .replace(/%m/g, 'MM')        // Month as zero-padded number
        .replace(/%d/g, 'DD')        // Day of month as zero-padded number
        .replace(/%j/g, 'DDD')       // Day of year
        // Time components
        .replace(/%H/g, 'HH')        // Hour (24-hour) zero-padded
        .replace(/%I/g, 'hh')        // Hour (12-hour) zero-padded
        .replace(/%M/g, 'mm')        // Minute zero-padded
        .replace(/%S/g, 'ss')        // Second zero-padded
        .replace(/%p/g, 'A')         // AM/PM
        // Weekday
        .replace(/%A/g, 'dddd')      // Full weekday name
        .replace(/%a/g, 'ddd')       // Abbreviated weekday name
        // Month name
        .replace(/%B/g, 'MMMM')      // Full month name
        .replace(/%b/g, 'MMM')       // Abbreviated month name
        // Special formats
        .replace(/%x/g, 'MM/DD/YYYY') // Locale date representation
        .replace(/%X/g, 'HH:mm:ss')   // Locale time representation
        .replace(/%c/g, 'ddd MMM DD HH:mm:ss YYYY'); // Locale datetime

    debugLog('Converted to JS format: ' + converted);
    return converted;
}

// --- HELPER FUNCTION: Format datetime according to detected format ---
function formatDateTime(date, format) {
    var year = date.getFullYear();
    var yearShort = String(year).substr(2, 2);
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    var dayOfYear = String(Math.ceil((date - new Date(date.getFullYear(), 0, 0)) / 86400000)).padStart(3, '0');
    var hours24 = date.getHours();
    var hours = String(hours24).padStart(2, '0');
    var minutes = String(date.getMinutes()).padStart(2, '0');
    var seconds = String(date.getSeconds()).padStart(2, '0');

    // Day and month names
    var dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    var dayNamesShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    var monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December'];
    var monthNamesShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    var dayName = dayNames[date.getDay()];
    var dayNameShort = dayNamesShort[date.getDay()];
    var monthName = monthNames[date.getMonth()];
    var monthNameShort = monthNamesShort[date.getMonth()];

    // Calculate 12-hour format
    var hours12 = hours24 % 12;
    if (hours12 === 0) hours12 = 12; // 0 becomes 12
    var hours12Str = String(hours12).padStart(2, '0');
    var ampm = hours24 >= 12 ? 'PM' : 'AM';

    // Replace format tokens with actual values
    // Handle longer tokens first to avoid partial replacements (e.g., MMMM before MMM, dddd before ddd)
    var formatted = format
        .replace(/YYYY/g, year)         // 4-digit year
        .replace(/YY/g, yearShort)      // 2-digit year
        .replace(/MMMM/g, monthName)    // Full month name
        .replace(/MMM/g, monthNameShort) // Abbreviated month name
        .replace(/MM/g, month)          // Month as zero-padded number
        .replace(/DDD/g, dayOfYear)     // Day of year
        .replace(/DD/g, day)            // Day of month as zero-padded number
        .replace(/dddd/g, dayName)      // Full weekday name
        .replace(/ddd/g, dayNameShort)  // Abbreviated weekday name
        .replace(/hh/g, hours12Str)     // 12-hour format (must be before HH)
        .replace(/HH/g, hours)          // 24-hour format
        .replace(/mm/g, minutes)        // Minutes
        .replace(/ss/g, seconds)        // Seconds
        .replace(/A/g, ampm);           // AM/PM

    return formatted;
}

// --- HELPER FUNCTION 3: Get mapping of value-card names to payload attributes ---
// This mapping is loaded from skin.conf via window.MQTT_SENSOR_MAPPING
// Configuration: skin.conf [[MQTT]] -> [[[SensorMapping]]]
function getPayloadMapping() {
    // Return the global mapping if available, otherwise return empty object
    return window.MQTT_SENSOR_MAPPING || {};
}

// --- HELPER FUNCTION 4: Update payload values in value-cards ---
function updatePayloadValues(payload) {
    var mapping = getPayloadMapping();
    var valueCards = document.querySelectorAll('.card-value');

    valueCards.forEach(function (card) {
        let cardName = card.getAttribute('data-name');
        let mapEntry = mapping[cardName];

        if (!mapEntry) {
            debugLog('⚠️ No mapping found for card-name: ' + cardName);
            return;
        }

        let payloadValue = payload[mapEntry.payloadAttr];
        if (payloadValue === undefined || payloadValue === null) {
            debugLog('⚠️ Payload missing attribute: ' + mapEntry.payloadAttr);
            return;
        }

        var numValue = parseFloat(payloadValue);
        if (Number.isNaN(numValue)) {
            debugLog('⚠️ Invalid value for ' + mapEntry.payloadAttr + ' : ' + payloadValue);
            return;
        }

        var h4Element = card.querySelector('h4.h2-responsive');

        if (h4Element) {
            // Check if value changed
            let currentText = h4Element.textContent.trim();

            // Detect decimal separator from current text (WeeWX format)
            let decimalSeparator = '.'; // default
            let hasComma = /\d,\d/.test(currentText);
            let hasDot = /\d\.\d/.test(currentText);

            if (hasComma && !hasDot) {
                decimalSeparator = ',';
            }
            debugLog('Detected decimal separator for ' + cardName + ': "' + decimalSeparator + '"');

            // Format value with detected separator
            let formattedValue = numValue.toFixed(mapEntry.decimals);
            if (decimalSeparator === ',') {
                formattedValue = formattedValue.replace('.', ',');
            }
            formattedValue += mapEntry.unit;

            if (cardName === 'windSpeed') {
                let windDirMapEntry = mapping['windDir'];
                let windDirValue = payload[windDirMapEntry ? windDirMapEntry.payloadAttr : null];
                if (windDirValue !== undefined) {
                    formattedValue += ' ' + getCompass(windDirValue);

                    // Update wind direction icon
                    let windIcon = document.getElementById('wind-icon');
                    if (windIcon && (currentText !== formattedValue)) {
                        let deg = Math.round(parseFloat(windDirValue));
                        // Remove existing direction class (wi-wind from-NNN-deg)
                        let existingClasses = windIcon.className.split(' ');
                        existingClasses = existingClasses.filter(function (c) {
                            return !/^from-\d+-deg$/.test(c);
                        });
                        existingClasses.push('from-' + deg + '-deg');
                        windIcon.className = existingClasses.join(' ');
                        windIcon.setAttribute('title', deg + '°');
                        windIcon.setAttribute('data-original-title', deg + '°');
                        if (typeof $ !== 'undefined' && $.fn.tooltip) {
                            $(windIcon).tooltip('dispose').tooltip();
                        }
                        debugLog('✓ Updated wind-icon to: from-' + deg + '-deg');
                    }
                }
            }

            if (currentText !== formattedValue) {
                h4Element.innerHTML = formattedValue;
                debugLog('✓ Updated ' + cardName + ' to: ' + formattedValue);

                // Visual feedback
                applyGreenFlash(h4Element);
            }
        }
    });
}

// --- HELPER FUNCTION 5: Apply visual feedback (green flash) ---
function applyGreenFlash(element) {
    // Check if flash on update is enabled
    if (window.MQTT_CONFIG && window.MQTT_CONFIG.flash_on_update === false) {
        return; // Skip flash effect if disabled
    }

    // Get flash color from configuration (default to green if not set)
    var flashColor = (window.MQTT_CONFIG && window.MQTT_CONFIG.flash_color)
        ? window.MQTT_CONFIG.flash_color
        : "#00ff00";

    element.style.transition = "color 0.5s, text-shadow 0.5s";
    element.style.color = flashColor;
    element.style.textShadow = "0 0 8px " + flashColor;
    setTimeout(function () {
        if (element) {
            element.style.color = "";
            element.style.textShadow = "none";
        }
    }, 1500);
}

// --- HELPER FUNCTION 6: Update telemetry (battery, signal, etc) ---
function updateTelemetry(payload) {
    // Signal strength
    if (payload.rxCheckPercent !== undefined) {
        var el = document.getElementById('mqtt-5in1-sig');
        if (el) el.innerHTML = parseFloat(payload.rxCheckPercent).toFixed(0) + "%";
    }

    // 5in1 Battery status
    if (payload.outTempBatteryStatus !== undefined) {
        var el = document.getElementById('mqtt-5in1-batt');
        if (el) {
            var isLow = (payload.outTempBatteryStatus == 1);
            el.innerHTML = isLow ? "LOW" : "OK";
            el.style.color = isLow ? "#ff4444" : "#00ff00";
            el.style.fontWeight = "bold";
        }
    }

    // Garage battery status
    if (payload.batteryStatus1 !== undefined) {
        var el = document.getElementById('mqtt-garage-batt');
        if (el) {
            var isLow = (payload.batteryStatus1 == 1);
            el.innerHTML = isLow ? "LOW" : "OK";
            el.style.color = isLow ? "#ff4444" : "#00ff00";
            el.style.fontWeight = "bold";
        }
    }
}

// 4. CONNECTION LOST HANDLER
if (client) {
    client.onConnectionLost = function (responseObject) {
        if (responseObject.errorCode !== 0) {
            console.log("Connection Lost: " + responseObject.errorMessage);
            updateMQTTStatusIndicator(false);
            // We don't need a setTimeout here anymore!
            // Paho v1.1.0 handles the 'reconnect: true' automatically.
        }
    };
}

// 5. PHONE WAKE-UP RECONNECT
if (client) {
    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
            debugLog("Tab wake-up detected. Checking connection...");
            // ONLY connect if the status is actually disconnected
            if (!client.isConnected()) {
                debugLog("MQTT not connected. Initiating wake-up connection...");
                client.connect(options);
            } else {
                debugLog("MQTT already reconnected by internal library logic.");
            }
        }
    });
}
