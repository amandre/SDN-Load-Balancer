#!/usr/bin/python

"""
Topology consists of 5 hosts connected with 3 HTTP servers via switch.
It uses the remote Ryu controller located on a different machine.
The HTTP servers are located in separated subnet and the users connect to them using Virtual IP.
switch is responsible for balancing the traffic based on the commands from the controller.
Ryu controller sends commands concerning free capacities on links and the CPU usages of HTTP servers.

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


def create_topo():
    net = Mininet(controller=RemoteController, link=TCLink)
    switches = list()
    switches.append(net.addSwitch('s0'))
    switches.append(net.addSwitch('s1'))

    # Add node responsible for NAT service
    host_int = 'nat-eth0'
    srv_int = 'nat-eth1'
    nat = net.addHost('nat0', cls=NAT, subnet='192.168.99.0/24', ip='10.0.0.99', inetIntf=host_int, localIntf=srv_int)
    net.addLink(nat, switches[0], bw=50, intfName1=host_int)
    net.addLink(nat, switches[1], bw=50, intfName1=srv_int)
    nat.setIP('192.168.99.99', 24, srv_int)

    private_dirs = [ '/var/log', '/var/run', '/etc/sdn/' ]
    hosts = []
    for i in range(5):
        hosts.append(net.addHost('h{}'.format(i+1), ip='10.0.0.{}/24'.format(i+1), cpu=0.05, defaultRoute='via 10.0.0.99', privateDirs=private_dirs))
        net.addLink(hosts[i], switches[0], bw=10)
        hosts[i].cmd('route add default dev h{}-eth0'.format(i+1))

    servers = []
    for i in range(3):
        servers.append(net.addHost('srv{}'.format(i+1), ip='192.168.99.{}/24'.format(i+1), cpu=0.05, defaultRoute='via 192.168.99.99', privateDirs=private_dirs))
        net.addLink(servers[i], switches[1], bw=10)
        servers[i].cmd('truncate -s 1m /etc/sdn/1mb_from_srv{0}.file'.format(i+1)) if i==0 else servers[i].cmd('truncate -s {0}m ~/sdn/srv{1}/{0}mb_from_srv{1}.file'.format((i+1)*10,(i+1)))
        servers[i].cmd('cd /etc/sdn/ |  python -m SimpleHTTPServer 8080 &')
        servers[i].cmd('route add default dev srv{}-eth0'.format(i+1))
        servers[i].cmd('(while sleep 1; do (ps --no-headers -p $(pgrep -f mininet:srv{0} | head -1) -o %cpu > /etc/sdn/cpu_srv{0}) ; done) &'.format(i+1))
    c0 = net.addController('c0', controller=RemoteController, ip='192.168.152.137', port=6633)
    net.build()
    c0.start()
    switches[0].start([c0])
    switches[1].start([c0])
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topo()