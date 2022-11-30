import subprocess

class BGPUpdate:
    def __init__(self, bgp_header, bgp_update, layer_index):
        self.bgp_header = bgp_header
        self.bgp_update = bgp_update
        self.layer_index = layer_index
        self.origin_asn = -1
        self.next_hop_asn = None

    def get_layer_index(self):
        return self.layer_index

    def get_origin_asn(self):
        return self.origin_asn
    
    def has_nlri_advertisements(self):
        if self.bgp_update.path_attr_len > 0:
            return True
        return False
    
    def has_withdraw_routes(self):
        if self.bgp_update.withdrawn_routes_len > 0:
            return True
        return False

    
    def get_origin_asn_from_payload(self):
        if len(self.bgp_update.path_attr[1].attribute.segments[-1].segment_value) >= 1: #grabs last asn in as_path (origin)
            self.origin_asn = self.bgp_update.path_attr[1].attribute.segments[-1].segment_value[-1]
            # self.origin_asn = self.bgp_update.path_attr[1].attribute.segments[0].segment_value[0]
        else:
            print("ERROR: no origin ASN!1 ahhh")
            # self.origin_asn = self.bgp_update.path_attr[1].attribute.segments[-1].segment_length
            # self.origin_asn = self.bgp_update.path_attr[1].attribute.segments[0].segment_length
        return self.origin_asn

    def nlri(self):
        return self.bgp_update.nlri
   
    def get_segment(self, nlri):
        if self.origin_asn == -1:
            self.get_origin_asn_from_payload()
        return [self.origin_asn, str(nlri.prefix).split('/')[0], str(nlri.prefix).split('/')[1]]

    # def get_next_hop_asn(self):
    #     print("getting next hop ASN")
    #     for i in self.bgp_update.path_attr:
    #         if i.type_code == 0x03: # 0x02 == AS_PATH
    #             self.next_hop_asn = i.attribute.next_hop
    #             print("Next Hop ASN: " + str(self.next_hop_asn))
    #     if self.next_hop_asn == None:
    #         print("No next hop ASN found")
    #         return 0
    #     ret = subprocess.check_output('birdc "sho route where bgp_path ~[= * =]" all | grep ' + self.next_hop_asn + ' | grep ix', shell=True).decode('utf-8')
    #     ret = int(ret.split("ix", 1)[1].strip())
    #     return ret