#!/usr/bin/python

"""
Topology consists of 5 hosts connected with 3 HTTP servers via switch.
It uses the remote Ryu controller located on a different machine.
The HTTP servers are located in separated subnet and the users connect to them using Virtual IP.
The switch is responsible for balancing the traffic based on the commands from the controller.
Ryu controller sends commands concerning CPU and memory usages of HTTP servers.
While any host tries to send the request to Virtual IP (10.0.0.100), Ryu controller redirects the traffic to the least congested server.

           h1   h2  h3  h4  h5
           |    |   |   |   |
           ------------------   10.0.0.0/8
                    |
                    s0
                    |
                    | 10.0.0.99/8
                   nat0
                    | 192.168.99.99/24
                    |
                    s1
                    |
            ----------------    192.168.99.0/24
            |       |      |
           srv1    srv2   srv3
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, Node, CPULimitedHost
from mininet.nodelib import NAT
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink
from bottle import route, run
import threading
import netifaces as ni
import subprocess
import re

net = Mininet(controller=RemoteController, link=TCLink)

ni.ifaddresses('ens38')
ip=ni.ifaddresses('ens38')[ni.AF_INET][0]['addr']

def create_topo():
    switches = list()
    switches.append(net.addSwitch('s0', dpid='1'))
    switches.append(net.addSwitch('s1', dpid='2'))

# Add node responsible for NAT service
    host_int = 'nat-eth0'
    srv_int = 'nat-eth1'
    nat = net.addHost('nat0', cls=NAT, subnet='192.168.99.0/24', ip='10.0.0.99', inetIntf=host_int, localIntf=srv_int)
    net.addLink(nat, switches[0], bw=50, intfName1=host_int)
    net.addLink(nat, switches[1], bw=50, intfName1=srv_int)
    nat.setIP('192.168.99.99', 24, srv_int)
    
    private_dirs = [ '/var/log', '/var/run', '/etc/sdn/' ]
    servers = []
    for i in range(3):
        servers.append(net.addHost('srv{}'.format(i+1), ip='192.168.99.{}/24'.format(i+1), cpu=0.05, defaultRoute='via 192.168.99.99', privateDirs=private_dirs))
        net.addLink(servers[i], switches[1], bw=10)
        servers[i].cmd('truncate -s 1m /etc/sdn/data.file') if i==0 else servers[i].cmd('truncate -s {}m /etc/sdn/data.file'.format((i+1)*10))
        servers[i].popen('python -m http_server &')
        servers[i].cmd('route add default dev srv{}-eth0'.format(i+1))
        servers[i].cmd('(while sleep 1; do (ps --no-headers -p $(pgrep -f mininet:srv{0} | head -1) -o %cpu > /etc/sdn/cpu) ; done) &'.format(i+1))
        servers[i].cmd('(while sleep 1; do (ps --no-headers -p $(pgrep -f mininet:srv{0} | head -1) -o %mem > /etc/sdn/mem) ; done) &'.format(i+1))

    hosts = []
    for i in range(5):
        hosts.append(net.addHost('h{}'.format(i+1), ip='10.0.0.{}/24'.format(i+1), cpu=0.05, defaultRoute='via 10.0.0.99', privateDirs=private_dirs))
        net.addLink(hosts[i], switches[0], bw=10)
        hosts[i].cmd('route add default dev h{}-eth0'.format(i+1))
	hosts[i].popen('python -m http_getter &')

    c0 = net.addController('c0', controller=RemoteController, ip='192.168.152.137', port=6633)
    net.build()
    c0.start()
    switches[0].start([c0])
    switches[1].start([c0])
    CLI(net)
    net.stop()

@route('/stats/servers/')
def calc_cpu():
    params_dict = {}
    for i in range(3):
	cpu = net.get('srv{}'.format(i+1)).cmd('cat /etc/sdn/cpu')
	cpu = re.findall('\d+\.\d+', cpu)[0]
	mem = net.get('srv{}'.format(i+1)).cmd('cat /etc/sdn/mem')
	mem = re.findall('\d+\.\d+', mem)[0]
	mac = net.get('srv{}'.format(i+1)).MAC()
	data = {"id": i+1, "name": "srv{}".format(i+1), "cpu":cpu, "mem":mem, "mac":mac}
    	params_dict[i] = data
    return params_dict


if __name__ == '__main__':
    setLogLevel('info')
    rest_thread = threading.Thread(target=run, kwargs={'host':ip, 'port':8080})
    rest_thread.daemon = True
    rest_thread.start()
    create_topo()
    subprocess.Popen("sudo kill $(pgrep -f http_)", shell=True)
