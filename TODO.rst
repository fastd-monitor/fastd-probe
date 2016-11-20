################
fastd-probe TODO
################

****
Todo
****

Prio 1
======
- [o] Add other probe types like wget or iperf

    - https://serverfault.com/questions/496731/how-to-set-which-ip-to-use-for-a-http-request

- [o] HTTP probe, e.g.: http://nl-ams-as3333.anchors.atlas.ripe.net/4096
- [o] Add commandline argument parsing, e.g. ``--config``, ``--verbose``


Prio 2
======
- [o] Problem when reconnecting too fast will lead to 20 second delays::

        fastd[6063]: received repeated handshakes from <client>[77.12.148.125:49337], ignoring

  Workaround: Don't connect more often than each 15 seconds to the same fastd instance,
  or tune its parameters (``MIN_HANDSHAKE_INTERVAL``, ``MIN_RESOLVE_INTERVAL``) in ``build.h.in``.



****
Done
****
- [x] Specify ping connectivity hosts in configuration file
- [x] Evaluate gping response for connectivity (boolean), set appropriate exit code
- [x] Return proper exit code based on connectivity evaluation
