################
fastd-probe TODO
################

- [o] Problem when reconnecting too fast will lead to 20 second delays::

        fastd[6063]: received repeated handshakes from <client>[77.12.148.125:49337], ignoring

  Workaround: Only connect each 15 seconds, not more often! Or tune the parameters in build.h.in



