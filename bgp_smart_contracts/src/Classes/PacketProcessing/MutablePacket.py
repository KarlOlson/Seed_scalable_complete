from scapy.all import *
load_contrib('bgp') #scapy does not automatically load items from Contrib. Must call function and module name to load.
import subprocess

class MutablePacket():
    def __init__(self, pkt):
        self.pkt = pkt
        self.headers_modified = False
        self.bgp_modified = False

        self.ack_num = pkt[TCP].ack
        self.seq_num = pkt[TCP].seq

        self.headers_modified = False
        self.diff = 0
        self.new_IP_len = 0


    def ack(self):
        return self.ack_num
    
    def seq(self):
        return self.seq_num

    def packet(self):
        return self.pkt

    def payload_len_diff(self):
        return self.diff

    def incr_ack(self, amnt):
        self.set_headers_modified()
        self.ack_num += amnt
        self.pkt[TCP].ack = self.ack_num

    def decr_ack(self, amnt):
        self.set_headers_modified()
        self.ack_num -= amnt
        self.pkt[TCP].ack = self.ack_num

    def incr_seq(self, amnt):
        self.seq_num += amnt
        self.pkt[TCP].seq = self.seq_num

    def decr_seq(self, amnt):
        self.seq_num -= amnt
        self.pkt[TCP].seq = self.seq_num

    def is_bgp(self):
        if (str(self.summary()).find('BGPHeader') > 0):
            return True
        return False
    
    def is_bgp_update(self):
        if (self.is_bgp() and self.pkt[BGPHeader].type == 2):
            return True
        return False

    def bytes(self):
        return bytes(self.pkt)

    def remove_nlri(self, nlri, update):
        print("removing invalid nlri...")
        bgp_update = self.pkt.getlayer(scapy.contrib.bgp.BGPUpdate, update.get_layer_index())

        nlri_bytes = bytes(nlri)
        print("len of nlri: " + str(len(nlri_bytes)))
        # pkt_byte_array = bytearray(bytes(self.pkt))
        update_byte_array = bytearray(bytes(bgp_update))
        
        try: 
            # get index of nlri in the update
            index = update_byte_array.index(nlri_bytes)
            print("start index of nlri to remove: " + str(index))

            # delete the nlri from the update
            del update_byte_array[index:index+len(nlri_bytes)]

            # convert self.pkt to bytearray
            pkt_bytes = bytearray(bytes(self.pkt))
        
            # get index of update in the packet
            pkt_index = pkt_bytes.index(bytes(bgp_update))
            
            # delete the entire update from the packet
            del pkt_bytes[pkt_index:pkt_index+len(bytes(bgp_update))]

            # replace add in the modified update where the old update was
            pkt_bytes[pkt_index:pkt_index] = update_byte_array
            
            # convert the modified bytearray back to a packet
            self.pkt = IP(bytes(pkt_bytes))
            
            # update the bgp header length
            bgp_header = self.pkt.getlayer(scapy.contrib.bgp.BGPHeader, update.get_layer_index())
            bgp_header.len -= len(nlri_bytes)

            # update pkt checksums, and lengths, set modified flag

            self.diff += len(nlri_bytes)
            self.pkt[IP].len -= len(nlri_bytes)
            print("modified packet: ") 
            self.recalculate_checksums()
            # del self.pkt[IP].chksum
            # del self.pkt[TCP].chksum
            # self.pkt.show2()
            self.set_bgp_modified()
        except ValueError as v:
            print("Error. nlri not found in packet. this is weird: " + repr(v))
            print("nlri not found:")
            nlri.show()

    def recalculate_checksums(self):
        del self.pkt[IP].chksum
        del self.pkt[TCP].chksum
        self.pkt.show2()

    def are_headers_modified(self):
        return self.headers_modified

    def is_bgp_modified(self):
        return self.bgp_modified

    def set_bgp_modified(self):
        self.bgp_modified = True

    def set_headers_modified(self):
        self.headers_modified = True

    def packet(self):
        return self.pkt

    def summary(self):
        return self.pkt.summary()

    def show(self):
        return self.pkt.show()

    def show2(self):
        return self.pkt.show2()

    def iterpayloads(self):
        return self.pkt.iterpayloads()

    def del_ip_chksum(self):
        del self.pkt[IP].chksum
    
    def del_tcp_chksum(self):
        del self.pkt[TCP].chksum

    def get_next_hop_asn(self):
        print("getting next hop ASN from dst_ip: " + str(self.pkt[IP].dst))
        next_hop_ip = self.pkt[IP].dst
        try:
            ret = subprocess.check_output('birdc "sho route where bgp_path ~[= * =]" all | grep ' + next_hop_ip + ' | grep ix', shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print("Error getting next hop ASN: " + repr(e))
            if e.returncode == 1:
                print("next_hop_ip: " + str(next_hop_ip) + " has no ASN. Assume sending to an RS")
                return -1
            else:
                print("failed to get next hop IP. bad..... returning None")
                return None
        next_hop_asn = int(ret.split("ix", 1)[1].strip())
        return next_hop_asn