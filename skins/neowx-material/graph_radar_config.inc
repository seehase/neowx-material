#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    graph_radar_config.inc         JS config for default radar charts    |
## +-------------------------------------------------------------------------+

chart: {
    type: 'radar',
},
fill: {
    opacity: 0.1
},
xaxis: {
    categories: [
        '$Extras.hemispheres[0]',
        '$Extras.hemispheres[1]',
        '$Extras.hemispheres[2]',
        '$Extras.hemispheres[3]',
        '$Extras.hemispheres[4]',
        '$Extras.hemispheres[5]',
        '$Extras.hemispheres[6]',
        '$Extras.hemispheres[7]'
    ]
},
tooltip: {
    x: {
        formatter: function(value, { series, seriesIndex, dataPointIndex, w }) {
            ## per-page key for $page (datetime_graph_tooltip_<page>), else the base key
            #set $_tipval = $Extras.Formatting.get('datetime_graph_tooltip_' + $page, $Extras.Formatting.get('datetime_graph_tooltip', ''))
            #set $_tipval = ', '.join($_tipval) if isinstance($_tipval, list) else $_tipval
            ## resolve as a named [[Formatting]] constant; if not a known name, use the value literally
            #set $_tipfmt = $Extras.Formatting.get($_tipval, $_tipval)
            #set $_tipfmt = ', '.join($_tipfmt) if isinstance($_tipfmt, list) else $_tipfmt
            var fmt = "$_tipfmt";
            fmt = fmt.replace(/:MM/g, ':mm');
            // the first argument is 'value' (timestamp), use that
            return moment.unix(value).format(fmt);
        }
    }
},
