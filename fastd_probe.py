# -*- coding: utf-8 -*-
import os
import time
import shlex
import jinja2
import logging
import tempfile
import subprocess
import ConfigParser
from gevent import monkey
from pprint import pprint

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

def make_fastd_config(settings):

    # Setup Jinja template
    tpl_raw = file('fastd.conf.tpl').read().decode('utf-8')
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    template = env.from_string(tpl_raw)

    # Render template
    return template.render(**settings)

def start_fastd_client(fastd, configfile):
    #./fastd --config etc/fastd.conf
    #cmd = [fastd, '--config', configfile, '--log-level', 'verbose', '--daemon']
    cmd = [fastd, '--config', configfile, '--log-level', 'verbose']
    process = subprocess.Popen(cmd, shell=False)
    return process


def vpn_connectivity(configuration):

    # Write fastd configuration file
    configfile = tempfile.NamedTemporaryFile(suffix='.conf', delete=False)
    logger.info('Writing fastd configuration to {}'.format(configfile.name))

    # Render fastd configuration file
    fastd_config = make_fastd_config(configuration)
    configfile.write(fastd_config.encode('utf-8'))
    configfile.flush()

    # Run fastd client
    logger.info('Connecting to fastd service at {}'.format(configuration['peer']['hostname']))
    fastd = configuration['fastd']
    process = start_fastd_client(fastd, configfile.name)
    logger.info('Started fastd process with pid {}'.format(process.pid))
    # TODO: Wait for signal from fastd "on establish" event.
    time.sleep(1)

    # Run a single ping through the VPN interface
    interface = configuration['client']['interface']
    logger.info('Testing connectivity through interface {interface}'.format(interface=interface))
    ping_cmd = 'ping -c1 -b {interface} google.com'.format(interface=interface)
    subprocess.call(shlex.split(ping_cmd))
    #time.sleep(2)

    # Terminate the fastd process
    logger.info('Terminating fastd process with pid {}'.format(process.pid))
    process.terminate()


def run():

    monkey.patch_all()

    configurations = compute_configurations()
    for configuration in configurations:
        vpn_connectivity(configuration)


if __name__ == '__main__':
    logger.warning('Nothing here')

