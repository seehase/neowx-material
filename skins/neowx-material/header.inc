#encoding UTF-8
#import time
## +-------------------------------------------------------------------------+
## |    header.inc                 Header section (nav) for all templates    |
## +-------------------------------------------------------------------------+

## Add google tag manager if enabled
#if $Extras.Header.google_tagmanager_enable == "yes"
    <!-- Google Tag Manager (noscript) -->
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=$Extras.Header.google_tagmanager_id"
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        <!-- End Google Tag Manager (noscript) -->
    #end if

    #if $active_nav != 'current'
        ## Anti-flash guard (non-current pages): hide the fields that neowx-live.js
        ## replaces from live.json, so this page's stale build-time values (e.g. an
        ## old date / sun-moon times on a day-old archive page) don't flash before
        ## the fetch resolves. JS-gated via the nx-live-pending class, so no-JS
        ## visitors still see the server-rendered fallback. visibility:hidden keeps
        ## the layout from shifting. The inline setTimeout is a safety net: if
        ## neowx-live.js never runs (e.g. fails to load), the fields still reveal.
        <script>
            document.documentElement.classList.add('nx-live-pending');
            setTimeout(function () {
                document.documentElement.classList.remove('nx-live-pending');
            }, 5000);
        </script>
        <style>
            .nx-live-pending #header-date,
            .nx-live-pending #alm-sun-rise, .nx-live-pending #alm-sun-set,
            .nx-live-pending #alm-sunrise, .nx-live-pending #alm-sunset,
            .nx-live-pending #alm-moon-rise, .nx-live-pending #alm-moon-set,
            .nx-live-pending #alm-moon-icon, .nx-live-pending #alm-moon-fullness,
            .nx-live-pending #footer-year,
            .nx-live-pending #footer-weewx-version, .nx-live-pending #footer-skin-version,
            .nx-live-pending #footer-station-uptime, .nx-live-pending #footer-server-uptime {
                visibility: hidden;
            }
        </style>
    #end if

    <header>

        <nav class="navbar navbar-expand-lg navbar-dark $Extras.color" style="padding: 0.4rem 1rem; min-height: 5.2rem;">

            <!-- ===== COLUMN 1: Brand / Station Info ===== -->
            <!-- Fixed height = guarantees logo + station name never move between pages -->
            <div class="d-flex align-items-center flex-shrink-0 mr-3" style="height: 4.5rem;">

                <!-- Sub-col A: Weather icon / logo (vertically centered within fixed height) -->
                #if $Extras.Header.show_logo == "yes"
                    <a class="mr-3" href="index.html" style="display:flex; align-items:center; height:100%; flex-shrink:0;">
                        #if $Extras.Header.custom_logo_url != ""
                            <img src="$Extras.Header.custom_logo_url" style="width: 4rem">
                        #else
                            <img src="img/icon-alpha-1x.png" srcset="img/icon-alpha-1x.png 1x, img/icon-alpha-2x.png 2x" style="width: 4rem">
                        #end if
                    </a>
                #end if

                <!-- Sub-col B: flex-column, centered in fixed height so every row is always at the same Y -->
                <div style="display:flex; flex-direction:column; justify-content:center; height:100%; line-height:1.2;">

                    <!-- Row 1: Station name -->
                    <div style="font-size:20px; font-weight:700; color:#fff; white-space:nowrap; margin-bottom:0.3rem;">$station.location</div>

                    <!-- Row 2: Date + icons (icons column always rendered, empty on non-current pages) -->
                    <div style="display:flex; align-items:center; gap:0.4rem;">
                        #set $date_format = $Extras.Formatting.get('date', '%x')
                        #if $active_nav == 'current'
                            <div id="current-date" style="white-space:nowrap; font-size:0.95rem; color:#fff;">$current.dateTime.format($date_format)</div>
                        #else
                            <!-- Server value is the page's build date (fallback); neowx-live.js overwrites it with today's date from live.json -->
                            <div id="header-date" style="white-space:nowrap; font-size:0.95rem; color:#fff;">$time.strftime($date_format)</div>
                        #end if
                        <!-- Icon container: position:relative so OFFLINE badge can float below without affecting row height -->
                        <div style="position:relative; display:flex; flex-direction:column; gap:0.1rem;">
                            <!-- Icons row -->
                            <div style="display:flex; align-items:center; gap:0.25rem; font-size:1.1rem;">
                                #if $active_nav == 'current'
                                    #if ($Extras.MQTT.enabled == "true" or $Extras.MQTT.enabled == True)
                                        <div id="mqtt-status" class="text-white">
                                            <span id="mqtt-indicator" class="mdi mdi-resistor-nodes"
                                                  data-toggle="tooltip" data-placement="bottom"
                                                  style="vertical-align:middle;" title=""></span>
                                        </div>
                                    #end if
                                    #if $varExists('onlinecheck')
                                        #set $online_check = $onlinecheck.get_status()
                                    #else
                                        #set $online_check = {'offline': False}
                                    #end if
                                    #if $online_check.offline
                                        <div id="online-status" class="text-white">
                                            <span class="mdi mdi-wifi-strength-alert-outline"
                                                  data-toggle="tooltip" data-placement="bottom"
                                                  style="vertical-align:middle;" title="$gettext('System is offline')"></span>
                                        </div>
                                    #elif $Extras.OnlineCheck.get('always_show_status', False)
                                        <div id="online-status" class="text-white">
                                            <span class="mdi mdi-wifi"
                                                  data-toggle="tooltip" data-placement="bottom"
                                                  style="vertical-align:middle;" title="$gettext('System is online')"></span>
                                        </div>
                                    #end if
                                #else
                                    <!-- Calendar icon: hidden by default; neowx-live.js reveals it when this
                                         page's build date (data-generated-date) differs from today. The title
                                         shows when the page content was generated. -->
                                    <div id="generated-status" class="text-white" style="display:none;"
                                         data-generated-ts="$time.time()"
                                         data-old-threshold="$Extras.Header.get('old_page_threshold_minutes', '1440')">
                                        <span class="mdi mdi-calendar-clock"
                                              data-toggle="tooltip" data-placement="bottom"
                                              style="vertical-align:middle;"
                                              title="$time.strftime($Extras.Formatting.get('datetime_generated', '%d.%m.%Y %H:%M'))"></span>
                                    </div>
                                    <!-- Transparent spacer — keeps icon-column height identical to current page -->
                                    <span style="font-size:1.1rem; color:transparent;" aria-hidden="true">&#9632;</span>
                                #end if
                            </div>
                            <!-- OFFLINE badge: absolutely positioned below icons, left-aligned with MQTT icon.
                                 position:absolute means it does NOT affect the flex-row height — no layout shift. -->
                            <span id="status-label"
                                  style="display:none; position:absolute; top:100%; left:0; margin-top:3px;
                                         font-size:0.65rem; font-weight:700; line-height:1.4;
                                         color:#ffffff; background-color:#f44336;
                                         padding:1px 4px; border-radius:2px; white-space:nowrap;"></span>
                        </div>
                    </div>

                    <!-- Row 3: Time only -->
                    #if $active_nav == 'current'
                        <div id="current-time" style="white-space:nowrap; font-size:0.95rem; color:#fff;">$current.dateTime.format($Extras.Formatting.time)</div>
                        <span id="current-datetime" data-timestamp="$current.dateTime.raw" style="display:none;"></span>
                    #else
                        <div style="white-space:nowrap; font-size:0.95rem; color:transparent;" aria-hidden="true">00:00:00</div>
                    #end if
                </div>


            </div><!-- end column 1 -->

            <!-- Mobile toggle button -->
            <button class="navbar-toggler ml-auto" type="button" data-toggle="collapse"
                    data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent"
                    aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <!-- ===== COLUMN 2: Navigation (centered, grows to fill space) ===== -->
            <div class="collapse navbar-collapse justify-content-center" id="navbarSupportedContent" style="flex: 1 1 auto;">
                <ul class="navbar-nav">

                    #if $Extras.Header.current_nav_link == "yes"
                        #if $active_nav == 'current'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="index.html">$gettext("current")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="index.html">$gettext("current")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.yesterday_nav_link == "yes"
                        #if $active_nav == 'yesterday'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="yesterday.html">$gettext("yesterday")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="yesterday.html">$gettext("yesterday")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.week_nav_link == "yes"
                        #if $active_nav == 'week'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="week.html">$gettext("week")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="week.html">$gettext("week")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.month_nav_link == "yes"
                        #if $active_nav == 'month'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="month.html">$gettext("month")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="month.html">$gettext("month")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.year_nav_link == "yes"
                        #if $active_nav == 'year'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="year.html">$gettext("year")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="year.html">$gettext("year")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.archive_nav_link == "yes"
                        #if $active_nav == 'archive'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="archive.html">$gettext("archive")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="archive.html">$gettext("archive")</a>
                            </li>
                        #end if
                    #end if

                    #if $active_nav == 'history'
                        <li class="nav-item active mr-3">
                            <a class="nav-link" href="history.html">$gettext("history")</a>
                        </li>
                    #else
                        <li class="nav-item mr-3">
                            <a class="nav-link" href="history.html">$gettext("history")</a>
                        </li>
                    #end if

                    #if $Extras.Header.almanac_nav_link == "yes"
                        #if $active_nav == 'almanac'
                            <li class="nav-item active mr-3">
                                <a class="nav-link" href="almanac.html">$gettext("almanac")</a>
                            </li>
                        #else
                            <li class="nav-item mr-3">
                                <a class="nav-link" href="almanac.html">$gettext("almanac")</a>
                            </li>
                        #end if
                    #end if

                    #if $Extras.Header.custom1_url != ""
                        <li class="nav-item mr-3">
                            <a class="nav-link" href="$Extras.Header.custom1_url">$Extras.Header.custom1_label</a>
                        </li>
                    #end if

                    #if $Extras.Header.custom2_url != ""
                        <li class="nav-item mr-3">
                            <a class="nav-link" href="$Extras.Header.custom2_url">$Extras.Header.custom2_label</a>
                        </li>
                    #end if

                </ul>
            </div><!-- end column 2 -->

            <!-- ===== COLUMN 3: Almanac ===== -->
            #if $Extras.Header.show_almanac == "yes"
                #if $almanac.hasExtras
                    <ul class="navbar-nav nav-flex-icons flex-shrink-0 ml-3" style="line-height: 1.5; padding-top: .25rem;">
                        <li class="nav-item mr-4 text-white">
                            <i class="wi wi-sunrise mr-1" style="opacity: .75"></i> <span id="alm-sun-rise">$almanac.sun.rise</span> <br>
                            <i class="wi wi-sunset mr-1" style="opacity: .75"></i> <span id="alm-sun-set">$almanac.sun.set</span>
                        </li>
                        <li class="nav-item mr-4 text-white" style="line-height: 1.5">
                            <i class="wi wi-moonrise mr-1" style="opacity: .75"></i> <span id="alm-moon-rise">$almanac.moon.rise</span> <br>
                            <i class="wi wi-moonset mr-1" style="opacity: .75"></i> <span id="alm-moon-set">$almanac.moon.set</span>
                        </li>
                        <li class="nav-item mr-2 text-white text-center" style="line-height: 1.5">
                            <span id="alm-moon-phase" title="$almanac.moon_phase" data-toggle="tooltip" data-html="true">
                                <span id="alm-moon-icon">
                                #if $almanac.moon_index == 0
                                    <i class="wi wi-moon-new mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 1
                                    <i class="wi wi-moon-waxing-crescent-4 mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 2
                                    <i class="wi wi-moon-first-quarter mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 3
                                    <i class="wi wi-moon-waxing-gibbous-4 mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 4
                                    <i class="wi wi-moon-full mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 5
                                    <i class="wi wi-moon-waning-gibbous-4 mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 6
                                    <i class="wi wi-moon-third-quarter mr-1" style="opacity: .75"></i>
                                #else if $almanac.moon_index == 7
                                    <i class="wi wi-moon-waning-crescent-4 mr-1" style="opacity: .75"></i>
                                #else
                                    <i class="wi wi-moon-waning-crescent-3 mr-1" style="opacity: .75"></i>
                                #end if
                                </span>
                                <span id="alm-moon-fullness">$almanac.moon_fullness</span>%
                            </span><br>
                            <a href="almanac.html" class="text-white" style="opacity: .6">
                                $gettext("more")
                            </a>
                        </li>
                    </ul>
                #else
                    <ul class="navbar-nav nav-flex-icons flex-shrink-0 ml-3" style="line-height: 1.5; padding-top: .25rem;">
                        <li class="nav-item mr-4 text-white">
                            <i class="wi wi-sunrise mr-1" style="opacity: .75"></i> <span id="alm-sunrise">$almanac.sunrise</span> <br>
                            <i class="wi wi-sunset mr-1" style="opacity: .75"></i> <span id="alm-sunset">$almanac.sunset</span>
                        </li>
                    </ul>
                #end if
            #end if
            ## end column 3

        </nav>

    </header>
