mode tap;
method "xsalsa20-poly1305"; # Verschlüsselungsalgorithmus festlegen
mtu 1426;
interface "{{ client.interface }}";
secret "{{ client.secret }}";

#include peers from "peers";

peer "{{ peer.name }}" {
  key "{{ peer.key }}";
  remote "{{ peer.hostname }}" port {{ peer.port }};
}

# TODO: This might be suitable for Mac OS X only, adapt it to a Linux environment.
on up "
  #ip link set up $INTERFACE
  ifconfig $INTERFACE {{ network.local_ip }}
";

on establish "
  route add -net -ifscope $INTERFACE 0.0.0.0 {{ network.remote_ip }}
";
