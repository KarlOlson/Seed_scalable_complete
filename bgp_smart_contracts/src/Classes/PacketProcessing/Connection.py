import threading
from scapy.all import *
from .FiveTuple import FiveTuple
from .Flow import Flow
from .FlowDirection import FlowDirection

class Connection:

    def __init__(self, pkt):
        if TCP in pkt:
            print("creating connection")
            self.five_tuple = FiveTuple(proto="TCP", src_port=pkt[TCP].sport, dst_port=pkt[TCP].dport, \
                src_ip=pkt[IP].src, dst_ip=pkt[IP].dst)
        else:
            print("TCP not in packet. can't create connection object. returning None")
            return None

        self.out_flow = None
        self.in_flow = None 
        self.total_packets = 0
        self.total_packets_lock = threading.Lock()
        self.peer_surplus_lock = threading.Lock()
        self.our_surplus_lock = threading.Lock()

        self.peer_surplus = 0
        self.our_surplus = 0

    def __hash__(self):
        return hash(self.five_tuple)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.five_tuple == other.five_tuple

    def __repr__(self):
        return f"<Connection five_tuple:{self.five_tuple}>"

    # def is_modified(self):
    #     return (self.peer_surplus or self.our_surplus)

    def increase_peer_surplus(self, amount):
        self.peer_surplus_lock.acquire()
        self.peer_surplus += amount
        self.peer_surplus_lock.release()

    def increase_our_surplus(self, amount):
        self.our_surplus_lock.acquire()
        self.our_surplus += amount
        self.our_surplus_lock.release()

    def incr_total_packets(self):
        self.total_packets_lock.acquire()
        self.total_packets += 1
        self.total_packets_lock.release()

    def get_total_packets(self):
        self.total_packets_lock.acquire()
        val = self.total_packets
        self.total_packets_lock.release()
        return val

    def packet_update(self, m_pkt):
        pkt = m_pkt.packet()
        five_tuple = FiveTuple.from_pkt(m_pkt.packet())
        print("packet_update. flow direction: " + str(five_tuple.direction))

        if five_tuple.direction == FlowDirection.outbound:
            print("outbound flow")
            if not self.out_flow:
                print("outbound for connection not established yet")
                self.out_flow = Flow(pkt[TCP].ack, pkt[TCP].seq, FlowDirection.outbound)
            else:
                print("update outbound flow. outbound already established")
                self.update_outbound_flow(m_pkt)
        elif five_tuple.direction == FlowDirection.inbound:
            print("inbound flow")
            if not self.in_flow:
                print("inbound for connection not established yet")
                self.in_flow = Flow(pkt[TCP].ack, pkt[TCP].seq, FlowDirection.inbound)
            else:
                print("update inbound flow. outbound already established")
                self.update_inbound_flow(m_pkt)
        else:
            print('error packet is not inbound or outbound')        

    def update_outbound_flow(self, m_pkt):
        print("updating outbound flow")
        self.out_flow.update_packet_count()
        if m_pkt.is_bgp_modified():
            print("outbound packet modified. update seq/ack")
            if m_pkt.payload_len_diff() > 0:
                print("outbound payload len diff > 0: " + str(m_pkt.payload_len_diff()))
                self.increase_our_surplus(m_pkt.payload_len_diff())
                # self.increase_peer_surplus(m_pkt.payload_len_diff())
        else:
            print("outbound packet is not modified. but check on sequence numbers")
            if self.peer_surplus > 0: #deleted content received from peer, and we are responding
                print("updating ack outbound")
                m_pkt.incr_ack(self.peer_surplus)
                m_pkt.set_headers_modified()
            else:
                print("no peer surplus. not updating ack")
        
        if self.our_surplus > 0:
            change_in_seq = self.our_surplus - m_pkt.payload_len_diff()
            print("our surplus > 0. updating seq by: " + str(change_in_seq))
            m_pkt.decr_seq(change_in_seq) # only update seq by what we have prviously deleted. do not include current payload len diff
            m_pkt.set_headers_modified()
            # self.out_flow.update_sequence_numbers(m_pkt.seq())
            # self.out_flow.update_ack_numbers(m_pkt.ack())
    
    def update_inbound_flow(self, m_pkt):
        print("updating inbound flow")
        self.in_flow.update_packet_count()
        if m_pkt.is_bgp_modified():
            print("packet modified inbound. update seq/ack")
            if m_pkt.payload_len_diff() > 0: # packet has been reduced in size
                print("inbound payload len diff > 0: " + str(m_pkt.payload_len_diff()))
                self.increase_peer_surplus(m_pkt.payload_len_diff())
        else:
            print("inbound packet is not modified. but check on sequence numbers")
            if self.our_surplus > 0: #deleted content received from peer, and we are responding
                print("updating ack inbound")
                m_pkt.incr_ack(self.our_surplus)
                m_pkt.set_headers_modified()
            else:
                print("no our surplus. not updating ack")
        
        if self.peer_surplus > 0:
            change_in_seq = self.peer_surplus - m_pkt.payload_len_diff()
            print("peer surplus > 0. updating seq by: " + str(change_in_seq))
            m_pkt.decr_seq(change_in_seq) # only update seq by what we have prviously deleted. do not include current payload len diff
            m_pkt.set_headers_modified()
            # self.in_flow.update_sequence_numbers(m_pkt.seq())
            # self.in_flow.update_ack_numbers(m_pkt.ack())


    def update_total_packets(self):
        self.total_packets_lock.acquire()
        self.total_packets += 1
        val = self.total_packets
        self.total_packets_lock.release()
        print("total packets in connection: " + str(val))



    