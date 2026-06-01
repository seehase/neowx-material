#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    graph_area_config.inc           JS config for default area charts    |
## +-------------------------------------------------------------------------+

chart: {
    type: 'area'
},
fill: {
    type: 'gradient',
    gradient: {
        shadeIntensity: 1,
        inverseColors: false,
        opacityFrom: 0.6,
        opacityTo: 0,
        stops: [0, 75, 100]
    },
},
xaxis: {
    type: 'datetime',
    hideOverlappingLabels: true,
    tickAmount: 8,
    labels: {
        formatter: function(val, timestamp) {
            ## per-page key for $page (datetime_graph_label_<page>), else the base key
            #set $_lblval = $Extras.Formatting.get('datetime_graph_label_' + $page, $Extras.Formatting.get('datetime_graph_label', ''))
            #set $_lblval = ', '.join($_lblval) if isinstance($_lblval, list) else $_lblval
            ## resolve as a named [[Formatting]] constant; if not a known name, use the value literally
            #set $_lblfmt = $Extras.Formatting.get($_lblval, $_lblval)
            #set $_lblfmt = ', '.join($_lblfmt) if isinstance($_lblfmt, list) else $_lblfmt
            var fmt = "$_lblfmt";
            // If the format uses uppercase MM for minutes (common mistake), convert
            // only occurrences of ":MM" to Moment's minutes token ":mm" so we don't
            // change months (MM) to minutes.
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(timestamp).format(fmt);
        }
    }
},
tooltip: {
    x: {
        formatter: function(val) {
            ## per-page key for $page (datetime_graph_tooltip_<page>), else the base key
            #set $_tipval = $Extras.Formatting.get('datetime_graph_tooltip_' + $page, $Extras.Formatting.get('datetime_graph_tooltip', ''))
            #set $_tipval = ', '.join($_tipval) if isinstance($_tipval, list) else $_tipval
            ## resolve as a named [[Formatting]] constant; if not a known name, use the value literally
            #set $_tipfmt = $Extras.Formatting.get($_tipval, $_tipval)
            #set $_tipfmt = ', '.join($_tipfmt) if isinstance($_tipfmt, list) else $_tipfmt
            var fmt = "$_tipfmt";
            // convert minute token if needed (':MM' -> ':mm')
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(val).format(fmt);
        }
    }
},
