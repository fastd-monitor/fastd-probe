# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl <andreas.motl@elmyra.de>. Licensed under the AGPL 3.
import os
import sys
import types
import jinja2
import logging
import tempfile
import datetime
import colorama
import json_store
import subprocess
import ConfigParser
import gevent
import gevent.monkey
import gevent.event
import gevent.pywsgi
import gevent.subprocess
import gping
from appdirs import user_cache_dir
from ripe.atlas.cousteau.api_listing import AnchorRequest
from progressbar import ProgressBar

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s: %(message)s')
logger = logging.getLogger()


class ProcessManager(object):
    """
    Manage the fastd client process for connecting to a server peer.
    Build appropriate fastd configuration file from settings and template.
    """

    def connect(self, configuration):
        """
        Create configuration file dynamically and start fastd process.
        """

        # Create fastd configuration file
        self.configfile = tempfile.NamedTemporaryFile(suffix='.conf', delete=True)
        logger.info('Writing fastd configuration to {}'.format(self.configfile.name))

        # Render configuration
        fastd_config = self.make_config(configuration)
        self.configfile.write(fastd_config.encode('utf-8'))
        self.configfile.flush()

        # Run fastd client
        logger.info('Connecting to fastd service at {}'.format(configuration['peer']['hostname']))
        fastd = configuration['fastd']
        self.start_process(fastd, self.configfile.name)
        logger.info('Started fastd process with pid {}'.format(self.process.pid))

    def disconnect(self):
        """
        Stop fastd process.
        """
        self.process.terminate()
        self.process.wait()
        logger.info('Disconnected fastd')

    def make_config(self, settings):
        """
        Create fastd configuration from settings and template.
        """

        # Setup Jinja template
        tpl_raw = file('fastd.conf.tpl').read().decode('utf-8')
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        template = env.from_string(tpl_raw)

        # Render template
        return template.render(**settings)

    def start_process(self, fastd, configfile):
        """
        Start fastd process.
        """

        #./fastd --config etc/fastd.conf
        #cmd = [fastd, '--config', configfile, '--log-level', 'verbose', '--daemon']
        #cmd = [fastd, '--config', configfile, '--log-level', 'debug2']
        cmd = [fastd, '--config', configfile, '--log-level', 'info']
        #cmd = [fastd, '--config', configfile]
        #self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        aproc = AsyncProcess(cmd, '[fastd] ')
        aproc.capture_output()
        self.process = aproc.process
        return self.process


class TunnelManager(object):
    """
    Manage fastd process, trace tunnel establishment and run sensor probe.
    """

    def __init__(self, configuration, probe_callback=None, timeout=None):
        logger.info('Starting fastd tunnel')
        self.configuration = configuration
        self.probe_callback = probe_callback
        self.timeout = timeout or 5.0

        self.signalserver = None
        self.vpn_connected = gevent.event.Event()
        self.tunnel_established = gevent.event.Event()

        self.fastd = ProcessManager()

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
            try:
                if self.probe_callback and callable(self.probe_callback):
                    self.probe_callback()

            finally:
                # Shutdown fastd client
                self.fastd.disconnect()

        else:
            # Shutdown fastd client
            self.fastd.disconnect()

    def wait(self):
        self.greenlet.join()

    def wait_vpn(self):
        """
        Wait until "fastd" signalled the "on establish" event to us.
        """
        if self.vpn_connected.wait(self.timeout):
            logger.info('VPN connection established')

            #self.signalserver.stop()
            gevent.spawn_later(0.3, self.signalserver.stop)

            # Run arping to start ARP discovery
            interface = self.configuration['client']['interface']
            remote_ip = self.configuration['network']['remote_ip']
            #subprocess.call(['arping', '-q', '-c1', '-i', interface, remote_ip])
            aproc = AsyncProcess(['arping', '-q', '-c1', '-i', interface, remote_ip], '[arping] ')
            aproc.capture_output()
            aproc.wait()

        else:
            self.signalserver.stop()
            logger.error('Did not receive "on establish" signal from fastd in time. Waited for {} seconds.'.format(self.timeout))

    def wait_arp(self):
        """
        Wait until the ARP table got populated with an appropriate "remote_ip" entry.
        """
        interface = self.configuration['client']['interface']
        remote_ip = self.configuration['network']['remote_ip']
        while True:
            # MUST fire AFTER "DEBUG: learned new MAC address de:a5:4e:13:67:04 on peer <server1>"
            #code = subprocess.call(['arp', '-i', interface, remote_ip])
            aproc = AsyncProcess(['arp', '-i', interface, remote_ip], '[arp] ')
            aproc.capture_output()
            code = aproc.wait()
            if code == 0:
                self.tunnel_established.set()
                return
            #subprocess.call(['arping', '-q', '-c1', '-i', interface, remote_ip])
            gevent.sleep(0.3)

    def start_signalling_server(self):
        """
        Start a HTTP server waiting for the "on establish" event from the fastd process.
        """

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

        logger.info('Starting signalling server on port {}'.format(signalling_port))
        self.signalserver = gevent.pywsgi.WSGIServer(('', signalling_port), handler, log=logger, error_log=logger)
        self.signalserver.serve_forever()


class NetworkProbe(object):

    def __init__(self, configuration, timeout=None):
        logger.info('Starting network probe')
        self.configuration = configuration
        self.timeout = timeout or 5.0
        self.count = 0
        self.success = False

    def run(self):
        for probe in self.configuration['probes']:
            if probe['type'] == 'ping':
                gp = self.ping_probe(self.configuration, probe['targets'])
                self.ping_report(gp)

    def ping_probe(self, configuration, targets):
        # Run a single ping through the VPN interface
        interface = configuration['client']['interface']
        local_ip = configuration['network']['local_ip']
        logger.info('Testing connectivity through interface {interface}'.format(interface=interface))

        # Regular commandline ping
        #ping_cmd = 'ping -c1 -b {interface} google.com'.format(interface=interface)
        #subprocess.call(shlex.split(ping_cmd))

        progress = ProgressBar(max_value=len(targets), term_width=120)
        self.count = 0
        def receiver(ping):
            self.count += 1
            progress.update(self.count)

        # Asynchronous ping
        #gping.ping(['google.com', 'stackoverflow.com', '8.8.8.8'], bind=local_ip)
        return gping.ping(targets, timeout=2.0, max_outstanding=50, bind=local_ip, callback=receiver)

    def ping_report(self, gp):

        total     = len(gp.results)
        successes = len([True for result in gp.results if result['success']])
        errors    = len([True for result in gp.results if result['error']])

        msg_successes = colorama.Fore.CYAN + str(successes) + colorama.Style.RESET_ALL
        msg_errors    = colorama.Fore.RED  + str(errors)    + colorama.Style.RESET_ALL

        error_ratio = float(errors) / float(total)
        details_human = 'This is an error ratio of {}%.'.format(round(error_ratio * 100, 2))

        panic = False
        threshold = 0.75
        if error_ratio >= 0.75:
            panic = True

        if panic:
            outcome_human = colorama.Fore.RED + "Failure. PANIC!"
        else:
            outcome_human = colorama.Fore.GREEN + "Success. Don't panic."
            self.success = True

        message = 'Result:\nThe PING probe collected {} successful responses and {} errors. {}\n{}'.format(msg_successes, msg_errors, details_human, outcome_human)
        message += colorama.Style.RESET_ALL
        print
        print(message)

        #time.sleep(2)


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

    # Get settings for multiple probes from configuration
    probes = []
    for section in config.sections():
        if section.startswith('probe:'):
            probe = dict(config.items(section))
            if probe['type'] == 'ping':
                targets = probe['targets']
                if targets == 'RIPE-ATLAS-ANCHORS':
                    targets = RIPEAtlasAnchors(cached=True).ip_v4_list()
                elif type(targets) in types.StringTypes:
                    targets = map(str.strip, targets.split(','))
                probe['targets'] = targets
                logger.info('Added PING probe with #{} targets'.format(len(targets)))
            probes.append(probe)

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
            settings.update({'probes': probes})
            configurations.append(settings)

    return configurations


class JSONCache(object):

    def __init__(self, appname, filename, callback, ttl=None):
        self.appname = appname
        self.filename = filename
        self.callback = callback
        self.ttl = ttl or 300
        self.file = None
        self.slot = 'results'
        self.cache = {self.slot: None}
        self.setup()

    def setup(self):
        cache_dir = user_cache_dir(self.appname)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.file = os.path.join(cache_dir, self.filename)
        logger.info('Using cache for {}: {}'.format(self.appname, self.file))
        self.cache = json_store.open(self.file)

    def get(self):
        return self.cache[self.slot]

    def refresh(self):
        if self.expired() or self.slot not in self.cache:
            self.cache.update({self.slot: self.callback()})
            self.cache.sync()

    def mtime(self):
        try:
            mtime = os.path.getmtime(self.file)
        except OSError:
            mtime = 0
        last_modified_date = datetime.datetime.fromtimestamp(mtime)
        return last_modified_date

    def expired(self):
        now = datetime.datetime.now()
        if now - self.mtime() > datetime.timedelta(seconds = self.ttl):
            return True
        else:
            return False


class RIPEAtlasAnchors(object):

    def __init__(self, cached=False, ttl=86400):
        self.cached = cached
        self.ttl = ttl
        self.store = []
        self.cache = JSONCache('fastd-probe', 'ripe-atlas-anchors.json', self.fetch, ttl=ttl)
        self.load()

    def load(self):
        if self.cached:
            self.cache.refresh()
            self.store = self.cache.get()
        else:
            self.store = self.fetch()

    def fetch(self):
        logger.info('Fetching list of RIPE Atlas Anchors')
        return list(AnchorRequest())

    def ip_v4_list(self):
        return [item['ip_v4'] for item in self.store]


class AsyncProcess(object):
    """
    Wrapper for running subprocesses asynchronously.
    Pumps stdout and stderr output to a logger instance.

    .. seealso::

        https://stackoverflow.com/questions/19497587/get-live-stdout-from-gevent-subprocess/36160200#36160200
    """

    def __init__(self, cmd, log_prefix=None):
        self.cmd = cmd
        self.log_prefix = log_prefix
        self.process = gevent.subprocess.Popen(self.cmd, stdout=gevent.subprocess.PIPE, stderr=gevent.subprocess.PIPE, shell=False)

    def wait(self, *args, **kwargs):
        return self.process.wait(*args, **kwargs)

    def capture_output(self):
        gevent.sleep(0.01)
        gevent.spawn(self.read_stream, self.process.stdout)
        gevent.spawn(self.read_stream, self.process.stderr)

    def read_stream(self, stream):
        try:
            while not stream.closed:
                line = stream.readline()
                if not line:
                    break
                line = line.rstrip()
                if self.log_prefix:
                    line = self.log_prefix + line
                logger.info(line)
        except RuntimeError:
            # process was terminated abruptly
            pass


def run():

    gevent.monkey.patch_all()

    configurations = compute_configurations()
    outcomes = []
    for configuration in configurations:

        probe = NetworkProbe(configuration, timeout=10.0)
        #tunnel = TunnelManager(configuration)
        tunnel = TunnelManager(configuration, probe.run, timeout=30.0)
        tunnel.wait()

        outcomes.append(probe.success)

    success_total = all(outcomes)
    if not success_total:
        sys.exit(2)

if __name__ == '__main__':
    logger.warning('Nothing here')

