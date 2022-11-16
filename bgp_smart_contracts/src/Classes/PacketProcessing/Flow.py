import threading
from scapy.all import *

class Flow:
    def __init__(self, ack, seq, flow_direction):
        self.true_sequence_number = seq
        self.proxy_sequence_number = seq

        self.true_ack_number = ack
        self.proxy_ack_number = ack

        self.source_surplus = 0
        self.destination_surplus = 0
        self.packet_count = 1
        self.flow_direction = flow_direction

        self.packet_count_lock = threading.Lock()
        self.sequence_number_lock = threading.Lock()
        self.ack_number_lock = threading.Lock()


    def update_packet_count(self):
        self.packet_count_lock.acquire()
        
        self.packet_count += 1
        val = self.packet_count
        
        self.packet_count_lock.release()
        # print("incr packets: " + str(val))
    
    def update_sequence_numbers(self, seq_num):
        self.sequence_number_lock.acquire()
        
        self.true_sequence_number = seq_num
        self.proxy_sequence_number = seq_num
        
        t_seq = self.true_sequence_number
        p_seq = self.proxy_sequence_number
        
        self.sequence_number_lock.release()
        print("seq num update (true, proxy): " + str(t_seq) + ", " + str(p_seq))

    
    def update_ack_numbers(self, ack_num):
        self.ack_number_lock.acquire()

        
        self.true_ack_number = ack_num
        self.proxy_ack_number = ack_num
        
        t_ack = self.true_ack_number
        p_ack = self.proxy_ack_number
        
        self.ack_number_lock.release()
        print("ack num update (true, proxy): " + str(t_ack) + ", " + str(p_ack))

    

