

class MutablePacket():
    def __init__(self, pkt):
        self.pkt = pkt
        self.been_modified = False

    def is_bgp(self):
        if (str(self.summary()).find('BGPHeader') > 0):
            return True
        return False
    
    def is_bgp_update(self):
        if (self.is_bgp() and self.packet()[BGPHeader].type == 2):
            return True
        return False

    def get_segment_length(self):
        return self.packet()[BGPUpdate].path_attr[1].attribute.segments[0].segment_length

    def get_segment_asn(self):
        return self.pkt[BGPUpdate].path_attr[1].attribute.segments[1].segment_length

    def get_bgp_segment_next_hop(self):
        return self.pkt[BGPUpdate].path_attr[2].attribute.next_hop

    def print_bgp_update_summary(self):
        print ("    Destination IP = " + self.pkt[IP].dst) #Local AS
        print ("    Source IP = " + self.pkt[IP].src) #Remote AS
        print ("    BGP Segment AS = " + str(self.get_segment_asn())) #even though it says segment length, that field is used to announce the A>
        print ("    BGP Segment Next Hop = " + str(self.get_bgp_segment_next_hop()))

    def get_nlris(self):
        return self.pkt[BGPUpdate].nlri

    def get_adv_segment(self, nlri):
        return [self.get_segment_asn(), str(nlri.prefix).split('/')[0], str(nlri.prefix).split('/')[1], "Internal"]

    def bytes(self):
        return bytes(self.pkt)

    def byte_array(self):
        return bytearray(self.pkt.bytes())

    def remove_nlri(self, nlri):
        nlri_bytes = bytes(nlri)
        print("len of nlri: " + str(len(nlri_bytes)))
        pkt_byte_array = self.byte_array()
        
        try: 
            index = pkt_byte_array.index(nlri_bytes)
            print("start index of nlri to remove: " + str(index))

            # delete the nlri from the packet
            del pkt_byte_array[index:index+len(nlri_bytes)]

            self.pkt = IP(bytes(pkt_byte_array))
            print("modify length of bgp packet")
            self.pkt[BGPHeader].len = self.pkt[BGPHeader].len - len(nlri_bytes)
            del self.pkt[IP].chksum
            del self.pkt[TCP].chksum 
            self.pkt[IP].len = self.pkt[IP].len - len(nlri_bytes)
            self.pkt.show2()
            self.set_modified()
        except ValueError as v:
            print("Error. nlri not found in packet. this is weird: " + repr(v))
            print("nlri not found:")
            nlri.show()

    def is_modified(self):
        return self.been_modified

    def set_modified(self):
        self.been_modified = True

    def packet(self):
        return self.pkt

    def summary(self):
        return self.pkt.summary()

    def show(self):
        return self.pkt.show()

    

    # def bgpchain_validate_advertisements(self):
