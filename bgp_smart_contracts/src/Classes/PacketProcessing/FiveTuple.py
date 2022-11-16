from scapy.all import *
from FlowDirection import FlowDirection

class FiveTuple:
    def __init__(self, proto, src_port, dst_port, src_ip, dst_ip):
        self.proto = proto

        # standardize direction
        if src_ip < dst_ip:
            self.src_port = src_port
            self.dst_port = dst_port
            self.src_ip = src_ip
            self.dst_ip = dst_ip
            self.direction = FlowDirection.outbound
        else:
            self.src_port = dst_port
            self.dst_port = src_port
            self.src_ip = dst_ip
            self.dst_ip = src_ip
            self.direction = FlowDirection.inbound

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

