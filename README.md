# Fork of NeoWX Material
As the original repository (https://github.com/neoground/neowx-material) is
no longer maintained, this fork contains latest changes, improvements and bugfixes

If you have any comments, just create an github issue

Live: https://weewx.seehausen.org/

# NeoWX Material

**The most versatile and modern weewx skin**

You want a modern UI for your weather station and its archive?

Including translation, customization, great appearance on tablets and
smartphones, and even a dark mode?

Then this skin is the one you're looking for!

This is the new version of the famous NeoWX (based on Sofaskin), 
including a modern Material Design UI, full weather data archive, 
and many more new features.

## Key features

- beautiful Material Design
- many color schemes to choose from
- interactive and zoomable charts
- wind direction + speed visualization as a wind rose
- accessible HTML + NOAA TXT file archive for all years and months
- Skin is internationalized so supports template based translation to many languages out of the box (catalan, german, english, spanish, finnish, french, italian, dutch, swedish)
   - If your language is not available, it's easy to add it! How-to guide can be found [here](https://weewx.com/docs/5.1/custom/localization/#internationalized-your-language-is-available)
- auto dark mode - works great on mobile and desktop
- responsive design - optimized for modern tablets and smartphones
- support for all available sensors
- many options to customize your reports even more - 
  have a look at the skin.conf
- ...and much more!

Learn more about all features on our project page: 
[NeoWX Material | Neoground Projects](https://neoground.com/projects/neowx-material).

## Installation

1. install latest version via extension       
```bash
    weectl extension install https://github.com/seehase/neowx-material/archive/refs/heads/master.zip
```
2. restart weewx: 
```bash
    sudo service weewx restart
```

If your skin doesn't change edit the `weewx.conf` and set `skin = neowx-material`
in the `[StdReport]` section, after that reload weewx: `sudo service weewx reload`.

This skin works best with the python ephem module installed 
(needed for the almanac). Install `pyephem` via pip, or the 
`python3-ephem` package via package manager.

## Localization

### Language translation
To have WeeWx to use the language you want, follow the guide from [this](https://weewx.com/docs/5.1/custom/localization/) page.

Built-in language packs are installed under /lang folder within the skin folder, eg. ```/etc/weewx/skins/neowx-material/lang/```

Language packs are identified with standardized two-letter identifier for each language. 

### Time & date localization
To have the reports with your local time and date format, the needed locale needs to be installed and passed to WeeWx at startup.

1. Query which locales are installed:
```bash
    sudo locale -a
```
2. If your own locale is missing, install it.

   In debian-based machines:
    ```bash
    sudo dpkg-reconfigure locales
    ```
   In RHEL-based machines:
    ```bash
    sudo locale-gen <locale_name>
    ```
3.  Edit the WeeWx startup service to pass LANG-variable to WeeWx

    In systemd-based machines the variable is added under the ```[Service]``` section
    ```bash
    [Service]
    # set LANG to display time/date in local language & format
    Environment="LANG=<locale_name>"
    ...
    ``` 

## Contribution

Feel free to add your own improvements. Contributions are always welcome!

Our previous skin, NeoWX, was used all over the world in many countries.
We hope that this skin will do the same. Please consider translating our skin
in your language.

If you want to provide any improvements, feel free to create a pull request.
As the main repository is no longer maintained please create a pull request in

`https://github.com/seehase/neowx-material`


## Development

Setting up the development environment is easy:

- clone / download repository
- install npm packages (`yarn install` / `npm install`)
- for easy testing create a symlink from your `WEEWX_HOME/skins/neowx-material`
  to the `skins` directory
  
For basic tasks npm / yarn scripts are available.

Styling is done via SCSS, compile it to `css/style.css` by: `yarn run build-css`.

### Available scripts

| Script           | Description                                         |
| ---------------- |-----------------------------------------------------|
| build-css        | Create css/style.css from SCSS files                |
| build-minify-css | Create minified css/style.min.css from SCSS files   |
| build            | Build job: build-css and build-minify-css           |


### Building

Run `yarn run build` to create the CSS and minified CSS.

## Thank You!

This config and some parts of the skin are based on the template code      
of the original "Standard" skin of weewx. Many thanks to Tom Keffer and     
the weewx contributors. 
One of the best solutions for your weather station under linux!

The design is based on 
[Material Design for Bootstrap (MDB) Free](https://mdbootstrap.com).

The NOAA reports, and some parts of the configuration 
are based on the Standard weewx skin as well.

These 3rd party libraries are used:

- [Apexcharts](https://github.com/apexcharts/apexcharts.js) (MIT license)
- [MomentJS](https://github.com/moment/moment) (MIT license)
- [Weather Icons by Erik Flowers](https://github.com/erikflowers/weather-icons) (MIT / SIL OFL 1.1 license)
- [open-meteo](https://open-meteo.com) [(CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
