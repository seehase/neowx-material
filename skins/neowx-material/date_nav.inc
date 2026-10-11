#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    date_nav.inc              Date Navigation Toolbar & Scale Switcher   |
## +-------------------------------------------------------------------------+

<div class="col-12 mb-3">
    <div class="card nwm-date-nav shadow-sm">
        <div class="card-body py-2 px-3">
            <div class="row align-items-center">

                <!-- Stepper & Direct Date Picker -->
                <div class="col-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-start mb-2 mb-md-0">
                    #if $page == 'day'
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

                        #if $has_next_day
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
                            <input type="week" id="nx-week-picker"
                                   class="form-control form-control-sm text-center font-weight-bold"
                                   style="max-width: 170px; cursor: pointer;"
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
                            <input type="month" id="nx-month-picker"
                                   class="form-control form-control-sm text-center font-weight-bold"
                                   style="max-width: 160px; cursor: pointer;"
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
                            <select id="nx-year-picker"
                                    class="form-control form-control-sm text-center font-weight-bold"
                                    style="max-width: 110px; cursor: pointer;"
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
                        #if $page == 'day'
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("day")</span>
                            <a href="$context_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week") $context_week
                            </a>
                            <a href="$context_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $context_month_name
                            </a>
                            <a href="$context_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $context_year
                            </a>
                        #else if $page == 'week'
                            <a href="$context_day_url" class="btn btn-sm btn-outline-secondary" title="$gettext('day')">
                                $gettext("day")
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$gettext("week") $context_week</span>
                            <a href="$context_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $context_month_name
                            </a>
                            <a href="$context_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $context_year
                            </a>
                        #else if $page == 'month'
                            <a href="$context_day_url" class="btn btn-sm btn-outline-secondary" title="$gettext('day')">
                                $gettext("day")
                            </a>
                            <a href="$context_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week") $context_week
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$context_month_name</span>
                            <a href="$context_year_url" class="btn btn-sm btn-outline-secondary" title="$gettext('year')">
                                $context_year
                            </a>
                        #else if $page == 'year'
                            <a href="$context_day_url" class="btn btn-sm btn-outline-secondary" title="$gettext('day')">
                                $gettext("day")
                            </a>
                            <a href="$context_week_url" class="btn btn-sm btn-outline-secondary" title="$gettext('week')">
                                $gettext("week") $context_week
                            </a>
                            <a href="$context_month_url" class="btn btn-sm btn-outline-secondary" title="$gettext('month')">
                                $context_month_name
                            </a>
                            <span class="btn btn-sm btn-secondary active font-weight-bold">$context_year</span>
                        #end if
                    </div>

                    #if not $is_current_day
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
            window.location.href = base + 'archive/' + parts[0] + '/month-' + val + '.html';
        }
    } else if (type === 'year') {
        window.location.href = base + 'archive/' + val + '/year-' + val + '.html';
    }
}
</script>
