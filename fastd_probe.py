# -*- coding: utf-8 -*-
import jinja2
import logging
import tempfile
import subprocess
import ConfigParser
import gevent
import gevent.monkey
import gevent.event
import gevent.pywsgi
import gping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def compute_configurations():

    configurations = []

    # Read configuration .ini
    config = ConfigParser.ConfigParser()
    config.read('fastd-probe.ini')

    # Get global settings from configuration
    global_settings = {
        'fastd': config.get('fastd-probe', 'fastd'),
        'client': {
            'secret': config.get('client', 'secret'),
            'interface': config.get('client', 'interface'),
            },
        'network': {
            'remote_ip': config.get('network', 'remote_ip'),
            'local_ip': config.get('network', 'local_ip'),
            },
    }

    # Get settings for multiple fastd peers from configuration
    for section in config.sections():
        if section.startswith('peer:'):
            peer_settings = {
                'name': config.get(section, 'name'),
                'key': config.get(section, 'key'),
                'hostname': config.get(section, 'hostname'),
                'port': config.get(section, 'port'),
                }
            settings = global_settings.copy()
            settings.update({'peer': peer_settings})
            configurations.append(settings)

    return configurations


class FastdWrapper(object):

    def make_config(self, settings):

        # Setup Jinja template
        tpl_raw = file('fastd.conf.tpl').read().decode('utf-8')
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        template = env.from_string(tpl_raw)

        # Render template
        return template.render(**settings)

    def start_process(self, fastd, configfile):
        #./fastd --config etc/fastd.conf
        #cmd = [fastd, '--config', configfile, '--log-level', 'verbose', '--daemon']
        cmd = [fastd, '--config', configfile, '--log-level', 'debug2']
        self.process = subprocess.Popen(cmd, shell=False)
        return self.process

    def connect(self, configuration):

        # Write fastd configuration file
        self.configfile = tempfile.NamedTemporaryFile(suffix='.conf', delete=True)
        logger.info('Writing fastd configuration to {}'.format(self.configfile.name))

        # Render fastd configuration file
        fastd_config = self.make_config(configuration)
        self.configfile.write(fastd_config.encode('utf-8'))
        self.configfile.flush()

        # Run fastd client
        logger.info('Connecting to fastd service at {}'.format(configuration['peer']['hostname']))
        fastd = configuration['fastd']
        self.start_process(fastd, self.configfile.name)
        logger.info('Started fastd process with pid {}'.format(self.process.pid))

    def disconnect(self):
        self.process.terminate()


class FastdManager(object):

    def __init__(self, configuration, timeout=None):
        self.configuration = configuration
        self.timeout = timeout or 5.0

        self.signalserver = None
        self.vpn_connected = gevent.event.Event()
        self.tunnel_established = gevent.event.Event()

        self.fastd = FastdWrapper()

        gevent.spawn(self.start_signalling_server)
        self.greenlet = gevent.spawn(self.start)

    def start(self):

        # Run the fastd client
        self.fastd.connect(self.configuration)

        # Wait for full tunnel establishment
        gevent.spawn(self.wait_vpn)
        gevent.spawn(self.wait_arp)

        if self.tunnel_established.wait(self.timeout):
            logger.info('Network tunnel fully established')

            # Run sensor probe
            self.run_probe()

        # Shutdown fastd client
        self.fastd.disconnect()

    def wait(self):
        self.greenlet.join()

    def wait_vpn(self):
        if self.vpn_connected.wait(self.timeout):
            logger.info('VPN connection established')
            self.signalserver.stop()

            # Run arping to start ARP discovery
            interface = self.configuration['client']['interface']
            remote_ip = self.configuration['network']['remote_ip']
            subprocess.call(['arping', '-q', '-c1', '-i', interface, remote_ip])

        else:
            self.signalserver.stop()
            logger.error('Did not receive "on establish" signal from fastd in time. Waited for {} seconds.'.format(self.timeout))

    def wait_arp(self):
        """
        Wait until the ARP table got populated with an appropriate entry from remote_ip
        """
        interface = self.configuration['client']['interface']
        remote_ip = self.configuration['network']['remote_ip']
        while True:
            # MUST fire AFTER "DEBUG: learned new MAC address de:a5:4e:13:67:04 on peer <server1>"
            code = subprocess.call(['arp', '-i', interface, remote_ip])
            if code == 0:
                self.tunnel_established.set()
                return
            #subprocess.call(['arping', '-q', '-c1', '-i', interface, remote_ip])
            gevent.sleep(0.3)

    def start_signalling_server(self):

        signalling_port = 8912

        def handler(env, start_response):
            if env['PATH_INFO'] == '/':
                start_response('200 OK', [('Content-Type', 'text/plain')])
                return [b"Hello world"]
            elif env['PATH_INFO'] == '/establish':
                logger.info('Received "on establish" event from fastd')
                self.vpn_connected.set()
                start_response('200 OK', [('Content-Type', 'text/plain')])
                return [b"Recognized fastd connection establishment"]
            else:
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b'Not Found']

        self.signalserver = gevent.pywsgi.WSGIServer(('', signalling_port), handler)
        self.signalserver.serve_forever()
        logger.info('Started signalling server on port {}'.format(signalling_port))


class VPNProbe(FastdManager):

    def run_probe(self):
        self.vpn_connectivity_sensor(self.configuration)

    def vpn_connectivity_sensor(self, configuration):
        # Run a single ping through the VPN interface
        interface = configuration['client']['interface']
        local_ip = configuration['network']['local_ip']
        logger.info('Testing connectivity through interface {interface}'.format(interface=interface))
        #ping_cmd = 'ping -c1 -b {interface} google.com'.format(interface=interface)
        #subprocess.call(shlex.split(ping_cmd))
        gping.ping(['google.com', 'stackoverflow.com', '8.8.8.8'], bind=local_ip)
        #time.sleep(2)


def run():

    gevent.monkey.patch_all()

    configurations = compute_configurations()
    for configuration in configurations:

        logger.info('Starting probe')
        probe = VPNProbe(configuration, timeout=30.0)
        probe.wait()


if __name__ == '__main__':
    logger.warning('Nothing here')

