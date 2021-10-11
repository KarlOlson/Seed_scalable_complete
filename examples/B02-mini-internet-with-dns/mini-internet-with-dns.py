#!/usr/bin/env python3
# encoding: utf-8

from seedemu.core import Emulator, Binding, Filter, Action
from seedemu.mergers import DEFAULT_MERGERS
from seedemu.compiler import Docker
from seedemu.services import DomainNameCachingService
from seedemu.layers import Base

emuA = Emulator()
emuB = Emulator()

# Load the pre-built components and merge them
emuA.load('../B00-mini-internet/base-component.bin')
emuB.load('../B01-dns-component/dns-component.bin')
emu = emuA.merge(emuB, DEFAULT_MERGERS)


#####################################################################################
# Bind the virtual nodes in the DNS infrastructure layer to physical nodes.
# Action.FIRST will look for the first acceptable node that satisfies the filter rule.
# There are several other filters types that are not shown in this example.

# bind root servers randomly in AS171
emu.addBinding(Binding('.*-root-server', filter=Filter(asn=171)))

# bind com servers randomly in AS151, net on 152, edu on 153, and cn on 154
emu.addBinding(Binding('.*-com-server', filter=Filter(asn=151)))
emu.addBinding(Binding('.*-net-server', filter=Filter(asn=152)))
emu.addBinding(Binding('.*-edu-server', filter=Filter(asn=153)))
emu.addBinding(Binding('.*-cn-server', filter=Filter(asn=154)))

# for the domain servers, bind them randomly in any AS
emu.addBinding(Binding('ns-.*'))

#####################################################################################
# Create two local DNS servers (virtual node).
ldns = DomainNameCachingService()
ldns.install('global-dns-1')
ldns.install('global-dns-2')

# Create two new host in AS-152 and AS-153, use them to host the local DNS server.
# We can also host it on an existing node.
emu.addBinding(Binding('global-dns-1', filter = Filter(ip = '10.152.0.53')), action = Action.NEW)
emu.addBinding(Binding('global-dns-2', filter = Filter(ip = '10.153.0.53')), action = Action.NEW)

# Add 10.152.0.53 as the local DNS server for AS-160 and AS-170
# Add 10.153.0.53 as the local DNS server for all the other nodes
# We can also set this for individual nodes
base: Base = emu.getLayer('Base')

base.getAutonomousSystem(160).setNameServers(['10.152.0.53'])
base.getAutonomousSystem(170).setNameServers(['10.152.0.53'])
base.setNameServers(['10.153.0.53'])

# Add the ldns layer
emu.addLayer(ldns)

# Dump to a file
emu.dump('base_with_dns.bin')


###############################################
# Render the emulation and further customization
emu.render()

###############################################
# Render the emulation

emu.compile(Docker(), './output')

