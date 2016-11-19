###########
fastd-probe
###########
A fastd_ probing machinery based on gevent_.
Test network connectivity through a fastd tunnel in less than a second.

.. _fastd: https://fastd.readthedocs.io/
.. _gevent: http://www.gevent.org


********
Synopsis
********
::

    sudo fastd-probe


Example
=======
::

    time sudo fastd-probe

    2016-11-11 14:34:17,182 INFO    : Starting fastd probe
    2016-11-11 14:34:17,183 INFO    : Starting signalling server on port 8912
    2016-11-11 14:34:17,191 INFO    : Writing fastd configuration to /tmp/tmpYQNYGY.conf
    2016-11-11 14:34:17,196 INFO    : Connecting to fastd service at fastd.example.org
    2016-11-11 14:34:17,226 INFO    : Started fastd process with pid 55468
    2016-11-11 14:34:17 +0100 --- Info: fastd v18-9-g2fa2187-dirty starting
    2016-11-11 14:34:17 +0100 --- Info: connection with <server1> established.
    192.168.111.1 (192.168.111.1) -- no entry on tap0
    add net 0.0.0.0: gateway 192.168.111.1
    2016-11-11 14:34:17,342 INFO    : Received "on establish" event from fastd
    2016-11-11 14:34:17,343 INFO    : VPN connection established
    ? (192.168.111.1) at 3a:25:53:fb:52:b4 on tap0 ifscope [ethernet]
    2016-11-11 14:34:17,606 INFO    : Network tunnel fully established
    2016-11-11 14:34:17,606 INFO    : Testing connectivity through interface tap0
    IP                  Delay          Hostname                                Message
    85.182.250.153      0.053348       google.com
    151.101.1.69        0.050595       stackoverflow.com
    8.8.8.8             0.054271       8.8.8.8

    2016-11-11 14:34:17 +0100 --- Info: terminating fastd
    2016-11-11 14:34:17 +0100 --- Info: connection with <server1> disestablished.

    real    0m0.803s
    user    0m0.368s
    sys     0m0.112s


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

