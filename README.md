# seismic-notifier-for-glass

A simple service for making timeline cards about earthquakes near places that
matter to you. My first attempt at making Glassware.

## Known issues

User credentials are stored every time `/dashboard` is loaded. This becomes very
annoying after a long time, because many duplicate notifications will be sent.

The `datetime` format used for `displayTime` when making cards is finicky. Cards
may not be created properly.

Deleting all the quake cards in a bundle will leave the bundle cover in the
timeline. It needs to be deleted manually.
