# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.48.0] - 2025-08-22

### CHANGED

- manifest file read station name from configuration "station.location"
- manifest file backgrount and theme color fonfigurable from skin.conf
- added PM2.5, CO2, modified windrun
- added configurable timespan for ET and Windrun for week, month, year for better readability
- improved Slovak localization

## [1.47.0] - 2025-08-22

### CHANGED

- Added possibility to display Tropical Days, Summer Days, Tropical nights, Arktic Days. Configurable in skin by setting temperatureThresholdDays in values_order section

## [1.46.2] - 2025-08-22

### CHANGED

- fixed error Element nof found when data for chart are not present

## [1.46.1] - 2025-08-22

### CHANGED

- updated install.py script, removed non necessary files and added new languages missing in script

## [1.35] - 2025-01-12

### CHANGED

- restructured files to be compliant to weewx extensions (https://weewx.com/docs/5.1/custom/extensions/) 


## [1.34] - 2025-01-11

### CHANGED

- reworked translation using gettext()
- added languages

## [1.12] 

### Added

- history generator

## [1.11] - 2021-03-30

### Added

- The theme mode (auto / light / dark) can now be changed
  in the settings
  
### Fixed

- Month page will get generated again. The timespan
  "1 month" didn't work due to missing Feb 29th this year.
  Now the month page shows a timespan of 31 days.


## [1.10] - 2021-03-27

### Added

- Cloudbase chart
- Chart titles can be changed
- Better error handling if data isn't available for a chart

### Fixed

- Empty appTemp card isn't shown anymore


## [1.9] - 2021-03-24

### Added

- Charts now support up to 4 sensors / series
- Apptemp is shown on windchill / heat index chart if it's enabled
- Min / Max texts can be translated as well

### Fixed

- ET chart is shown correctly again


## [1.8] - 2021-03-23

### Added

- The low / high values on cards can now have a custom color
  which you can set in the skin.conf (appearance section)
- Telemetry link in the footer can be hidden
- Telemetry values order can be changed in the skin.conf
- Telemetry page shows 24h charts for all available values
- Support for sensors: appTemp, snowDepth, leafTemp1-2, 
  soilTemp1-4, soilMoist1-4
- More chart settings
- Footer "about" table can be hidden
- Translation for hemispheres on radar chart (wind vector)
- Trend arrows can be shown at any value on the "current" page
- Coordinates can now be hidden on NOAA TXT reports

### Changed

- The credits in the footer (powered by weewx + skin) can
  optionally be hidden if you don't want to support these projects
- The weewx + skin version can be hidden in the footer
- Hidden charts won't get any JS code created - better performance

### Fixed

- The monthly archive TXT report does now have the correct template
- Wind speed value does now have the same size as all other values
- ET chart is displayed again correctly on yesterday page


## [1.7] - 2021-03-21

### Added

- Almanac in the header can be disabled
- Almanac can also be shown as link in navigation menu
- All navigation menu links can be enabled / disabled
- Up to two custom links can be defined in the navigation menu in skin.conf
- Catalan translation
- Missing battery status values to telemetry page
- The order of all cards (values and charts) can be changed in skin.conf
- Cards (values and charts) can easily be hidden in skin.conf
- Missing values and charts are now displayed if data is available
  (extraTemp4-8, extraHumid1-8, inTemp, inHumidity)

### Changed

- font-small text is now slightly smaller (0.85rem)
  to fix the full HD layout
- Better year archive layout with improved overview on Full HD screens,
  better visibility of month archives
- Improved the header + footer layout
- Full code refactoring of all HTML pages

### Fixed

- The almanac page won't throw an error anymore if the 
  pyephem package is not available
- Small appearance bugs were fixed - uniform appearance on all pages


## [1.6] - 2021-03-14

### Added

- Finnish translation
- Timespans of graph data can now be adjusted in skin.conf

### Changed

- Apexcharts common config is now centralized in js.inc
- Graph config refactoring
- Structure of skin.conf: better subsections and comments


## [1.5] - 2021-03-12

### Added

- Italian translation
- Horizontal trend arrow if trend = 0

### Changed

- Month archive charts now show the same layout as year 
  charts in the archive (full date, better performance)
  
### Fixed

- Barometer trend can now also be None without throwing an error
- Max value of radiation is now shown correctly
- Partly missing data on a page will now result in a correct
  graph with "null" values instead of just ignoring missing data

### Removed

- Graph animations due to high amount of data / problems with 
  displaying "null" values which increases performance a lot


## [1.4] - 2021-03-08

### Added

- Unit labels to y-axis of charts
- Numbers in charts now have units
- Missing favicons
- Skin version
- Imprint / privacy links in the footer can be set in skin.conf
- Custom logo URL can be set in skin.conf

### Changed

- iOS Webapp appearance is now better and includes a splash screen
- Numbers in charts have the same decimals as the display values


## [1.3] - 2021-03-07

### Added

- Localization support for chart dates (moment.js)
- Charts color palette selection on skin.conf
- Wind direction indicator to all pages

### Changed

- Buttons / headings are now uniform
- Almanac header layout
- Chart numbers are now formatted as the display values

### Fixed

- The responsive layout on footer
- Rain rate / avg label
- Wind direction on archive pages


## [1.2] - 2021-03-03

### Added

- Translucent status bar on ios devices

### Fixed

- UTF8 encoding now set on template pages
- Chart labels can now contain an apostrophe


## [1.1] - 2021-03-02

### Added

- Telemetry page
- Telemetry page link in footer


## [1.0] - 2021-03-01

- Initial release
