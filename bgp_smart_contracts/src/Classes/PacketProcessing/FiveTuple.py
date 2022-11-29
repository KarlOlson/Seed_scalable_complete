import psutil
import socket
import fcntl
import struct
from scapy.all import *
from .FlowDirection import FlowDirection

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def get_interface_names():
    addrs = psutil.net_if_addrs()
    print(addrs.keys())
    return addrs.keys()

def get_interface_ips(interface_names):
    ips = []
    for interface_name in interface_names:
        if interface_name == "lo":
            continue
        ips.append(get_ip_address(interface_name))
    return ips

class FiveTuple:
    def __init__(self, proto, src_port, dst_port, src_ip, dst_ip):
        self.proto = proto

        self.direction = self.get_flow_direction()

        # standardize direction
        if self.direction == FlowDirection.outbound:
            self.src_port = src_port
            self.dst_port = dst_port
            self.src_ip = src_ip
            self.dst_ip = dst_ip
        elif self.direction == FlowDirection.inbound:
            self.src_port = dst_port
            self.dst_port = src_port
            self.src_ip = dst_ip
            self.dst_ip = src_ip
        else:
            raise Exception("Invalid flow direction")

    def get_flow_direction(self):
        interface_names = get_interface_names()
        interface_ips = get_interface_ips(interface_names)
        if self.src_ip in interface_ips:
            return FlowDirection.outbound
        else:
            return FlowDirection.inbound



    def __repr__(self):
        return f"<FiveTuple src_port:{self.src_port}, dst_port:{self.dst_port}, src_ip:{self.src_ip}, dst_ip:{self.dst_ip}>"


    @staticmethod
    def from_pkt(pkt):
        return FiveTuple(proto="TCP", src_port=pkt[TCP].sport, dst_port=pkt[TCP].dport, \
                src_ip=pkt[IP].src, dst_ip=pkt[IP].dst)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.proto == other.proto and \
            self.dst_port == other.dst_port and \
            self.src_ip == other.src_ip and \
            self.dst_ip == other.dst_ip and \
            self.src_port == other.src_port


    def __hash__(self):
        return hash((self.proto, self.dst_port, self.src_ip, self.dst_ip,  self.src_port))

