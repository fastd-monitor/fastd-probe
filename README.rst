###########
fastd-probe
###########
A fastd_ probing machinery based on gevent_. Features:

- Test quick network connectivity through a fastd tunnel in less than a second.
- Use the `List of RIPE Atlas Anchors`_ as ping targets, see also `Checking your Internet Connectivity with RIPE Atlas Anchors`_.
- Evaluates probe results and panics at an threshold of 75% or more errors.

.. _fastd: https://fastd.readthedocs.io/
.. _gevent: http://www.gevent.org
.. _List of RIPE Atlas Anchors: https://atlas.ripe.net/anchors/list/
.. _Checking your Internet Connectivity with RIPE Atlas Anchors: https://labs.ripe.net/Members/stephane_bortzmeyer/checking-your-internet-connectivity-with-ripe-atlas-anchors


********
Synopsis
********
::

    time sudo fastd-probe


.. figure:: https://asciinema.org/a/93575.png
    :alt: fastd-probe success
    :target: https://asciinema.org/a/93575

    fastd-probe success: https://asciinema.org/a/93575


.. figure:: https://asciinema.org/a/93576.png
    :alt: fastd-probe failure
    :target: https://asciinema.org/a/93576

    fastd-probe failure: https://asciinema.org/a/93576


*************
Prerequisites
*************
Please make sure ``fastd``, ``curl``, ``arp`` and ``arping`` are installed.
Also, ``fastd`` requires `TUN/TAP`_ virtual network interfaces.
While VTun_ should be a commodity on Linux, see `TunTap OSX`_ for an implementation for Mac OS X.

.. _TUN/TAP: https://en.wikipedia.org/wiki/TUN/TAP
.. _VTun: http://vtun.sourceforge.net/
.. _TunTap OSX: http://tuntaposx.sourceforge.net/


*****
Setup
*****
::

    git clone https://github.com/fastd-monitor/fastd-probe.git
    cd fastd-probe
    virtualenv .venv27
    source .venv27/bin/activate
    python setup.py develop


*************
Configuration
*************
::

    # Adapt to your needs
    cp fastd-probe.example.ini fastd-probe.ini

