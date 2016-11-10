###########
fastd-probe
###########


********
Synopsis
********
::

    sudo fastd-probe


*************
Prerequisites
*************
Please make sure ``fastd``, ``curl`` and ``arping`` are installed.


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

