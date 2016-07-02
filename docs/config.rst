.. _config:

Configuration
=============

Arachnado can be configured using a config file. Put it to one of the common
locations:

* `/etc/arachnado.conf`
* `~/.config/arachnado.conf`
* `~/.arachnado.conf'`

or pass the file name as an argument when starting the server::

    arachnado --config ./my-config.conf

Available options and their default values:

.. literalinclude::
    ../arachnado/config/defaults.conf
