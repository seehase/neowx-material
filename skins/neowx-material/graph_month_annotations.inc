#encoding UTF-8
## ---------------------------------------------------------------------------
## Emit ApexCharts `annotations: { xaxis: [...] }` with a labeled marker on the
## 1st of each month (for the year page's align:month mode). Requires the global
## $month_marks: a list of [ts_milliseconds, label] built by the page from its
## day records. Pair this with hiding the regular x-axis labels in the chart's
## xaxis override (the page does that, since it needs $type).
## ---------------------------------------------------------------------------
annotations: {
    xaxis: [
        #for $_mk in $month_marks
            {
                x: $_mk[0],
                borderColor: '#888',
                strokeDashArray: 3,
                label: {
                    text: '$_mk[1]',
                    position: 'bottom',
                    orientation: 'horizontal',
                    style: { fontSize: '11px', background: 'transparent', color: '#888' }
                }
            },
        #end for
    ]
},
