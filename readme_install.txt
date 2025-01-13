+----------------------------------------------------------------------------------------------------------+
|                                                                                                          |
|       ()    ()   _   _                                            _                                      |
|                 | \ | | ___  ___   __ _ _ __ ___  _   _ _ __   __| |                                     |
|    ()    ()     |  \| |/ _ \/ _ \ / _` | '__/ _ \| | | | '_ \ / _` |                                     |
|                 | |\  |  __/ (_) | (_| | | | (_) | |_| | | | | (_| |                                     |
|       ()    ()  |_| \_|\___|\___/ \__, |_|  \___/ \__,_|_| |_|\__,_|                                     |
|                                   |___/                                                                  |
|    ()    ()                                                  G m b H                                     |
|                                                                                                          |
|              weather (at) neoground.com        https://neoground.com                                     |
|                                                                                                          |
+----------------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------------+
|                                                                                                          |
|                N E O W X    M A T E R I A L    S K I N                                                   |
|                                                                                                          |
|                              current fork                                                                |
|               https://github.com/seehase/neowx-material                                                  |
|                                                                                                          |
|                                 V 1.35.x                                                                   |
|                                                                                                          |
|                              R E A D   M E                                                               |
|                                                                                                          |
+----------------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------------+
|                                                                                                          |
| Project information:    https://neoground.com/projects/neowx-material                                    |
|                                                                                                          |
|       Documentation:    https://neoground.com/docs/neowx-material                                        |
|                                                                                                          |
|     original Github:    https://github.com/neoground/neowx-material                                      |
| current fork Github:    https://github.com/seehase/neowx-material                                        |
|                                                                                                          |
+----------------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------------+
|                                                                                                          |
| Installation instructions  tested with weewx 5.1                                                         |
|                                                                                                          |
| 1) install latest version via extension                                                                  |
|    > weectl extension install https://github.com/seehase/neowx-material/archive/refs/heads/master.zip    |
|                                                                                                          |
| 2) restart WeeWX                                                                                         |
|    > sudo systemctl restart weewx                                                                        |
|  or                                                                                                      |
|    > sudo service weewx restart                                                                          |
|                                                                                                          |
+----------------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------------+
|                                                                                                          |
| Manual installation instructions                                                                         |
|                                                                                                          |
| 1) copy files to the weeWX skins directory                                                               |
|    > cp -rp skins/neowx-material /etc/weewx/skins                                                        |
|                                                                                                          |
| 3) copy /bin/user/historygenerator.py to                                                                 |
|              $WEEWX_ROOT/user. default: /etc/weewx/bin/user                                              |
|                                                                                                          |
| 3) in the weeWX configuration file, add / change a report and set                                        |
|    neowx-material as its skin                                                                            |
|    [StdReport]                                                                                           |
|        ...                                                                                               |
|            [[StandardReport]]                                                                            |
|                skin = neowx-material                                                                     |
|                                                                                                          |
| 3) restart WeeWX                                                                                         |
|    > sudo systemctl restart weewx                                                                        |                                         |
|  or                                                                                                      |
|    > sudo service weewx restart                                                                          |
|                                                                                                          |
+----------------------------------------------------------------------------------------------------------+
