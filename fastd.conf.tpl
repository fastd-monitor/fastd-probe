mode tap;
method "xsalsa20-poly1305"; # Verschlüsselungsalgorithmus festlegen
mtu 1426;
interface "{{ client.interface }}";
secret "{{ client.secret }}";

peer "{{ peer.name }}" {
  key "{{ peer.key }}";
  remote "{{ peer.hostname }}" port {{ peer.port }};
}

# TODO: This might be suitable for Mac OS X only, so maybe adapt it to a Linux environment.
on up "
  #ip link set up $INTERFACE
  ifconfig $INTERFACE {{ network.local_ip }}
";

on establish "

  # Add route via remote peer
  route add -net -ifscope $INTERFACE 0.0.0.0 {{ network.remote_ip }}

  # Signal connection establishment to fastd-probe
  curl --silent -XPOST localhost:8912/establish

";
