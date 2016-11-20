###########
fastd-probe
###########
A fastd_ probing machinery based on gevent_.


************
Introduction
************

Goals
=====
- Conveniently test network connectivity through a fastd tunnel.
- Act as a foundation for different kinds of network probes.

Features
========
- Quick fastd tunnel setup and teardown in less than a second.
- Optionally use the `List of RIPE Atlas Anchors`_ as targets for ping probes,
  see also `Checking your Internet Connectivity with RIPE Atlas Anchors`_.
- Evaluate probe results and panics at an threshold of 75% or more errors.

.. _fastd: https://fastd.readthedocs.io/
.. _gevent: http://www.gevent.org
.. _List of RIPE Atlas Anchors: https://atlas.ripe.net/anchors/list/
.. _Checking your Internet Connectivity with RIPE Atlas Anchors: https://labs.ripe.net/Members/stephane_bortzmeyer/checking-your-internet-connectivity-with-ripe-atlas-anchors


********
Synopsis
********
::

    time sudo fastd-probe

Please also have a look at the provided example configuration file "`fastd-probe.example.ini`_".

.. _fastd-probe.example.ini: https://github.com/fastd-monitor/fastd-probe/blob/master/fastd-probe.example.ini


********
Examples
********
These two examples demonstrate a "success" and a "failure" case.
Both use a ping probe configured with ``targets = RIPE-ATLAS-ANCHORS``,
checking connectivity against all 228 RIPE Atlas Anchors as of 2016-11-20.

----

.. figure:: https://asciinema.org/a/93575.png
    :alt: fastd-probe success
    :target: https://asciinema.org/a/93575

    fastd-probe success: https://asciinema.org/a/93575

----

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

