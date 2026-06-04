#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    js.inc                   Common javascript code for all templates    |
## +-------------------------------------------------------------------------+

## jQuery
<script type="text/javascript" src="js/jquery.min.js"></script>
## Bootstrap tooltips / JS
<script type="text/javascript" src="js/popper.min.js"></script>
<script type="text/javascript" src="js/bootstrap.min.js"></script>
## MDB core JavaScript
<script type="text/javascript" src="js/mdb.min.js"></script>
## Vendor JS
#if $lang == "en"
    <script src="js/vendor/moment.min.js"></script>
#else
    <script src="js/vendor/moment-with-locales.min.js"></script>
    <script type="text/javascript">moment.locale('$lang')</script>
#end if
<script src="js/vendor/apexcharts/apexcharts.min.js"></script>
## NeoWX Material chart helpers (shared date formatter)
<script type="text/javascript" src="js/neowx-date-format.js"></script>
## NeoWX Material App
<script type="text/javascript" src="js/app.js"></script>

<script type="text/javascript">
    // Show/update status label only if configured threshold > 0 in skin.conf
    const showOfflineLabel = "$active_nav" === "current"; // Show offline-state only on current page
    if (showOfflineLabel && $Extras.Header.offline_threshold_minutes > 0) {
        let lastUpdateTimestampString = '$current.dateTime.raw';
        if (lastUpdateTimestampString === "" ) {
            lastUpdateTimestampString = "4891363200"; // Fallback to 01.01.2125 if not available
        }
        const lastUpdateTimestamp =  Number(lastUpdateTimestampString) ;  // in seconds
        const nowTimestamp = new Date() / 1000;             // now in seconds
        const diffMinutes = (nowTimestamp - lastUpdateTimestamp) / 60; // Difference in minutes

        const statusLabel = document.getElementById("status-label");
        if (statusLabel && diffMinutes > $Extras.Header.offline_threshold_minutes) {
            statusLabel.textContent = "$gettext('OFFLINE')";
            statusLabel.style.display = 'inline-block';
        }
    }
</script>

#set $allowMouseWheelZoom = "false"
#if $Extras.Appearance.get('allowMouseWheelZoom') == "true"
    #set $allowMouseWheelZoom = "true"
#end if

#set $defaultChartBehavior = "zoom"
#if $Extras.Appearance.get('defaultChartBehavior') == "pan"
    #set $defaultChartBehavior = "pan"
#end if

## Global apexcharts config
<script type="text/javascript">
    // Charts drawn in "align" mode (the only ones with xaxis.min+max set) keep
    // their calendar alignment through a zoom: record their original aligned
    // axis at mount, re-snap on zoom, and restore the original on reset zoom.
    // fixed/auto charts are left alone. Granularity follows the zoom width,
    // same as graph_align_axis.inc server-side: hour tier (<=2 days), day tier
    // (<=62 days), else even spacing.
    var NEOWX_ALIGNED = {};
    function neowxMountedHandler(chartContext) {
        try {
            var x = chartContext.w.config.xaxis;
            if (x && x.min != null && x.max != null) {
                NEOWX_ALIGNED[chartContext.w.globals.chartID] =
                    { min: x.min, max: x.max, tickAmount: x.tickAmount };
            }
        } catch (e) {}
    }
    function neowxAlignAxis(minMs, maxMs) {
        var secs = (maxMs - minMs) / 1000;
        if (secs < 3600) { secs = 3600; }
        if (secs <= 172800) {
            var hours = Math.ceil(secs / 3600);
            var hs = Math.max(1, Math.round(hours / 6));
            var ht = Math.ceil(hours / hs);
            var h0 = moment(minMs).startOf('hour');
            return { min: h0.valueOf(), max: h0.clone().add(ht * hs, 'hours').valueOf(), tickAmount: ht };
        }
        var days = Math.ceil(secs / 86400);
        if (days <= 62) {
            var ds = Math.max(1, Math.round(days / 12));
            var dt = Math.ceil(days / ds);
            var d0 = moment(minMs).startOf('day');
            return { min: d0.valueOf(), max: d0.clone().add(dt * ds, 'days').valueOf(), tickAmount: dt };
        }
        return { min: minMs, max: maxMs, tickAmount: 12 };
    }
    var _neowxZooming = false;
    var _neowxResetting = false;
    function neowxZoomHandler(chartContext, opts) {
        if (_neowxZooming || _neowxResetting) { return; }
        try { if (!NEOWX_ALIGNED[chartContext.w.globals.chartID]) { return; } } catch (e) { return; }
        if (!opts || !opts.xaxis || opts.xaxis.min == null || opts.xaxis.max == null) { return; }
        var a = neowxAlignAxis(opts.xaxis.min, opts.xaxis.max);
        _neowxZooming = true;
        try {
            var p = chartContext.updateOptions(
                { xaxis: { min: a.min, max: a.max, tickAmount: a.tickAmount } }, false, false);
            if (p && p.then) { p.then(function(){ _neowxZooming = false; }, function(){ _neowxZooming = false; }); }
            else { _neowxZooming = false; }
        } catch (e) { _neowxZooming = false; }
    }
    function neowxResetDone() { _neowxZooming = false; _neowxResetting = false; }
    function neowxBeforeResetHandler(chartContext) {
        // Restore the ORIGINAL aligned min/max/tickAmount captured at mount. beforeResetZoom only
        // positions min/max, so re-apply the exact tickAmount right after via updateOptions.
        try {
            var o = NEOWX_ALIGNED[chartContext.w.globals.chartID];
            if (!o) { return; }
            _neowxResetting = true;
            setTimeout(function() {
                try {
                    _neowxZooming = true;
                    var p = chartContext.updateOptions(
                        { xaxis: { min: o.min, max: o.max, tickAmount: o.tickAmount } }, false, false);
                    if (p && p.then) { p.then(neowxResetDone, neowxResetDone); }
                    else { neowxResetDone(); }
                } catch (e) { neowxResetDone(); }
            }, 0);
            return { xaxis: { min: o.min, max: o.max } };
        } catch (e) {}
    }

    var config_mode = '${Extras.Appearance.mode}';
    var theme_mode = 'light';
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        theme_mode = 'dark';
    }
    // Override mode by config
    if(config_mode != "auto") {
        theme_mode = config_mode;
    }

    window.Apex = {
        theme: {
            mode: theme_mode,
            palette: '$Extras.Charts.palette'
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: '$Extras.Charts.stroke_curve',
            width: $Extras.Charts.stroke_width
        },
        markers: {
            size: $Extras.Charts.markers_size,
        },
        chart: {
            height: $Extras.Charts.height,
            stacked: false,
            background: theme_mode === 'dark' ? '#444' : '#ffffff',
            zoom: {
                type: 'x',
                enabled: true,
                autoScaleYaxis: true,
                allowMouseWheelZoom: $allowMouseWheelZoom,
            },
            toolbar: {
                autoSelected: '$defaultChartBehavior',
                export: {
                    csv: {
                        headerCategory: 'DateTime',
                        dateFormatter(timestamp) {
                            return moment(timestamp).toISOString()
                        }
                    }
                }
            },
            locales: [
                #include raw "js/vendor/apexcharts/locales/" + $lang + ".json"
            ],
            defaultLocale: '$lang',
            animations: {
                enabled: false
            },
            events: {
                mounted: neowxMountedHandler,
                zoomed: neowxZoomHandler,
                beforeResetZoom: neowxBeforeResetHandler
            },
        },
    }

    ## Ordinals conversion for W0CHP's custom WindDir Charts:
    function getOrdinalDirection(degrees) {
        var sectors = [
            '$Extras.hemispheres[0]',
            '$Extras.hemispheres[1]',
            '$Extras.hemispheres[2]',
            '$Extras.hemispheres[3]',
            '$Extras.hemispheres[4]',
            '$Extras.hemispheres[5]',
            '$Extras.hemispheres[6]',
            '$Extras.hemispheres[7]'
        ];
        var index = Math.round(degrees / (360 / sectors.length));
        return sectors[index % sectors.length];
    }
</script>
