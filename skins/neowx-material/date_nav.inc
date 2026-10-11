#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    date_nav.inc              Date Navigation Toolbar & Scale Switcher   |
## +-------------------------------------------------------------------------+

#import datetime
#import time
#if not $varExists('base_path')
    #set $base_path = ''
#end if
#if not $varExists('context_year')
    #set $context_year = $time.strftime('%Y')
#end if
#if not $varExists('context_month')
    #set $context_month = $time.strftime('%m')
#end if
#if not $varExists('context_month_name')
    #set $context_month_name = $time.strftime('%B')
#end if
#if not $varExists('context_week')
    #set $context_week = $time.strftime('%W')
#end if
#if not $varExists('context_day')
    #set $context_day = $time.strftime('%Y-%m-%d')
#end if
#if not $varExists('archive_start_date')
    #set $archive_start_date = '1970-01-01'
#end if
#if not $varExists('current_live_url')
    #set $current_live_url = $base_path + 'index.html'
#end if
#if not $varExists('current_day_url')
    #set $current_day_url = $base_path + 'archive/' + $context_year + '/days/day-' + $context_day + '.html'
#end if
#if not $varExists('current_week_url')
    #set $current_week_url = $base_path + 'archive/' + $context_year + '/weeks/week-' + $context_year + '-' + $context_week + '.html'
#end if
#if not $varExists('current_month_url')
    #set $current_month_url = $base_path + 'archive/' + $context_year + '/months/month-' + $context_year + '-' + $context_month + '.html'
#end if
#if not $varExists('current_year_url')
    #set $current_year_url = $base_path + 'archive/' + $context_year + '/year-' + $context_year + '.html'
#end if
#if not $varExists('is_current_day')
    #set $is_current_day = ($page == 'today')
#end if
#if not $varExists('has_prev_day')
    #set $has_prev_day = True
#end if
#if not $varExists('has_next_day')
    #set $has_next_day = False
#end if
#if not $varExists('prev_day_url')
    #set $yest_dt = datetime.datetime.fromtimestamp($time.time()) - datetime.timedelta(days=1)
    #set $prev_day_url = $base_path + 'archive/' + $yest_dt.strftime('%Y') + '/days/day-' + $yest_dt.strftime('%Y-%m-%d') + '.html'
#end if
#if not $varExists('next_day_url')
    #set $next_day_url = '#'
#end if
#if not $varExists('has_prev_week')
    #set $has_prev_week = True
#end if
#if not $varExists('has_next_week')
    #set $has_next_week = False
#end if
#if not $varExists('prev_week_url')
    #set $prev_week_url = '#'
#end if
#if not $varExists('next_week_url')
    #set $next_week_url = '#'
#end if
#if not $varExists('has_prev_month')
    #set $has_prev_month = True
#end if
#if not $varExists('has_next_month')
    #set $has_next_month = False
#end if
#if not $varExists('prev_month_url')
    #set $prev_month_url = '#'
#end if
#if not $varExists('next_month_url')
    #set $next_month_url = '#'
#end if
#if not $varExists('has_prev_year')
    #set $has_prev_year = True
#end if
#if not $varExists('has_next_year')
    #set $has_next_year = False
#end if
#if not $varExists('prev_year_url')
    #set $prev_year_url = '#'
#end if
#if not $varExists('next_year_url')
    #set $next_year_url = '#'
#end if
#if not $varExists('context_noaa_month_url')
    #set $context_noaa_month_url = $base_path + 'archive/NOAA/NOAA-' + $context_year + '-' + $context_month + '.txt'
#end if
#if not $varExists('context_noaa_year_url')
    #set $context_noaa_year_url = $base_path + 'archive/NOAA/NOAA-' + $context_year + '.txt'
#end if

<style>
.nwm-date-nav {
    border-radius: 0.5rem;
    font-family: inherit;
}
.nwm-date-nav .nwm-date-title {
    font-size: 1.05rem;
    font-family: inherit;
}
.nwm-date-nav input,
.nwm-date-nav select,
.nwm-date-nav .btn {
    font-family: inherit;
}
.dark-theme .nwm-date-nav {
    background-color: #2b2b2b;
    border-color: #3f3f3f;
    color: #f0f0f0;
}
.dark-theme .nwm-date-nav input,
.dark-theme .nwm-date-nav select {
    background-color: #383838;
    border-color: #4a4a4a;
    color: #ffffff;
}
.dark-theme .nwm-date-nav .nwm-date-title {
    color: #ffffff;
}
</style>

<div class="col-12 mb-3">
    <div class="card nwm-date-nav shadow-sm">
        <div class="card-body py-2 px-3">
            <div class="row align-items-center">

                <!-- Stepper & Direct Date Picker -->
                <div class="col-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-start mb-2 mb-md-0">
                    #if $page in ('day', 'today')
                        #if $has_prev_day
                            <a href="$prev_day_url" class="btn btn-sm btn-outline-secondary mr-2" title="$gettext('previous')">
                                <i class="mdi mdi-chevron-left"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary mr-2" disabled>
                                <i class="mdi mdi-chevron-left"></i>
                            </button>
                        #end if

                        <div class="d-inline-flex align-items-center position-relative">
                            <input type="date" id="nx-date-picker"
                                   class="form-control form-control-sm text-center font-weight-bold"
                                   style="max-width: 155px; cursor: pointer;"
                                   value="$context_day"
                                   min="$archive_start_date"
                                   onchange="nxJumpDate('day', this.value)">
                        </div>

                        #if $page != 'today' and $has_next_day
                            <a href="$next_day_url" class="btn btn-sm btn-outline-secondary ml-2" title="$gettext('next')">
                                <i class="mdi mdi-chevron-right"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary ml-2" disabled>
                                <i class="mdi mdi-chevron-right"></i>
                            </button>
                        #end if

                    #else if $page == 'week'
                        #if $has_prev_week
                            <a href="$prev_week_url" class="btn btn-sm btn-outline-secondary mr-2" title="$gettext('previous')">
                                <i class="mdi mdi-chevron-left"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary mr-2" disabled>
                                <i class="mdi mdi-chevron-left"></i>
                            </button>
                        #end if

                        <div class="d-inline-flex align-items-center">
                            <span class="font-weight-bold px-2 nwm-date-title" style="white-space: nowrap;">${context_year} - $gettext("CW") ${context_week}</span>
                            <input type="week" id="nx-week-picker"
                                   class="form-control form-control-sm text-center font-weight-bold ml-1"
                                   style="width: 42px; padding: 0 2px; cursor: pointer;"
                                   title="$gettext('week')"
                                   value="${context_year}-W${context_week}"
                                   onchange="nxJumpDate('week', this.value)">
                        </div>

                        #if $has_next_week
                            <a href="$next_week_url" class="btn btn-sm btn-outline-secondary ml-2" title="$gettext('next')">
                                <i class="mdi mdi-chevron-right"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary ml-2" disabled>
                                <i class="mdi mdi-chevron-right"></i>
                            </button>
                        #end if

                    #else if $page == 'month'
                        #if $has_prev_month
                            <a href="$prev_month_url" class="btn btn-sm btn-outline-secondary mr-2" title="$gettext('previous')">
                                <i class="mdi mdi-chevron-left"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary mr-2" disabled>
                                <i class="mdi mdi-chevron-left"></i>
                            </button>
                        #end if

                        <div class="d-inline-flex align-items-center">
                            <span class="font-weight-bold px-2 nwm-date-title" style="white-space: nowrap;">$context_month_name ${context_year}</span>
                            <input type="month" id="nx-month-picker"
                                   class="form-control form-control-sm text-center font-weight-bold ml-1"
                                   style="width: 42px; padding: 0 2px; cursor: pointer;"
                                   title="$gettext('month')"
                                   value="${context_year}-${context_month}"
                                   onchange="nxJumpDate('month', this.value)">
                        </div>

                        #if $has_next_month
                            <a href="$next_month_url" class="btn btn-sm btn-outline-secondary ml-2" title="$gettext('next')">
                                <i class="mdi mdi-chevron-right"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary ml-2" disabled>
                                <i class="mdi mdi-chevron-right"></i>
                            </button>
                        #end if

                    #else if $page == 'year'
                        #if $has_prev_year
                            <a href="$prev_year_url" class="btn btn-sm btn-outline-secondary mr-2" title="$gettext('previous')">
                                <i class="mdi mdi-chevron-left"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary mr-2" disabled>
                                <i class="mdi mdi-chevron-left"></i>
                            </button>
                        #end if

                        <div class="d-inline-flex align-items-center">
                            <span class="font-weight-bold px-2 nwm-date-title" style="white-space: nowrap;">${context_year}</span>
                            <select id="nx-year-picker"
                                    class="form-control form-control-sm text-center font-weight-bold ml-1"
                                    style="max-width: 90px; cursor: pointer;"
                                    onchange="nxJumpDate('year', this.value)">
                                #set $avail_years = $getVar('archive_years', $getVar('SummaryByYear', []))
                                #for $yr in $avail_years
                                    <option value="$yr"#if str($yr) == str($context_year)# selected#end if#>$yr</option>
                                #end for
                            </select>
                        </div>

                        #if $has_next_year
                            <a href="$next_year_url" class="btn btn-sm btn-outline-secondary ml-2" title="$gettext('next')">
                                <i class="mdi mdi-chevron-right"></i>
                            </a>
                        #else
                            <button class="btn btn-sm btn-outline-secondary ml-2" disabled>
                                <i class="mdi mdi-chevron-right"></i>
                            </button>
                        #end if
                    #end if

                    #if $page == 'month'
                        <a href="$context_noaa_month_url" target="_blank" class="btn btn-sm btn-outline-info ml-2" title="NOAA Report">
                            <i class="mdi mdi-file-document-outline mr-1"></i>NOAA
                        </a>
                    #else if $page == 'year'
                        <a href="$context_noaa_year_url" target="_blank" class="btn btn-sm btn-outline-info ml-2" title="NOAA Report">
                            <i class="mdi mdi-file-document-outline mr-1"></i>NOAA
                        </a>
                    #end if
                </div>

                <!-- Multi-Scale Switcher: Day -> Week -> Month -> Year -->
                <div class="col-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-end">
                    <div class="btn-group btn-group-sm flex-wrap" role="group" aria-label="Time Scale Navigation">
                        #if $page in ('day', 'today')
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("Day")</span>
                            <a href="$current_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week")
                            </a>
                            <a href="$current_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $gettext("month")
                            </a>
                            <a href="$current_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $gettext("year")
                            </a>
                        #else if $page == 'week'
                            <a href="$current_live_url" class="btn btn-sm btn-outline-secondary" title="$gettext('Day')">
                                $gettext("Day")
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("week")</span>
                            <a href="$current_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $gettext("month")
                            </a>
                            <a href="$current_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $gettext("year")
                            </a>
                        #else if $page == 'month'
                            <a href="$current_live_url" class="btn btn-sm btn-outline-secondary" title="$gettext('Day')">
                                $gettext("Day")
                            </a>
                            <a href="$current_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week")
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("month")</span>
                            <a href="$current_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $gettext("year")
                            </a>
                        #else if $page == 'year'
                            <a href="$current_live_url" class="btn btn-sm btn-outline-secondary" title="$gettext('Day')">
                                $gettext("Day")
                            </a>
                            <a href="$current_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week")
                            </a>
                            <a href="$current_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $gettext("month")
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("year")</span>
                        #end if
                    </div>

                    #if $page != 'today' and not $is_current_day
                        <a href="${base_path}index.html" class="btn btn-sm btn-primary ml-2 d-none d-sm-inline-block" title="$gettext('current')">
                            <i class="mdi mdi-flash mr-1"></i>$gettext("current")
                        </a>
                    #end if
                </div>

            </div>
        </div>
    </div>
</div>

<script>
function nxJumpDate(type, val) {
    if (!val) return;
    var base = '${base_path}';
    if (type === 'day') {
        var parts = val.split('-');
        if (parts.length === 3) {
            window.location.href = base + 'archive/' + parts[0] + '/days/day-' + val + '.html';
        }
    } else if (type === 'week') {
        var parts = val.split('-W');
        if (parts.length === 2) {
            window.location.href = base + 'archive/' + parts[0] + '/weeks/week-' + parts[0] + '-' + parts[1] + '.html';
        }
    } else if (type === 'month') {
        var parts = val.split('-');
        if (parts.length === 2) {
            window.location.href = base + 'archive/' + parts[0] + '/months/month-' + val + '.html';
        }
    } else if (type === 'year') {
        window.location.href = base + 'archive/' + val + '/year-' + val + '.html';
    }
}
</script>
