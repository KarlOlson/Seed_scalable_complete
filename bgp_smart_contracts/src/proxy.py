#!/usr/bin/python3
#To Run:
#Install scapy: $sudo pip install scapy
#Run Proxy Sniffer $sudo python3 <filename.py>
#Must run from sudo for packet processing privileges.
from operator import add
from netfilterqueue import NetfilterQueue
from scapy.all import *
import socket
import time
from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import os, sys
import datetime
import copy
import Classes.SetupPathValidation as SetupPathValidation
import threading

class Index():
    def __init__(self):
        self.index = 0
        self.lock = threading.Lock()
    
    def incr_index(self):
        self.lock.acquire()
        self.index = self.index + 1
        val = self.index
        self.lock.release()
        return val

global_index = None

load_contrib('bgp') #scapy does not automatically load items from Contrib. Must call function and module name to load.

interface='ix100'
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])

#####Synchronizes ASN with blockchain account data##################
tx_sender_name = "ACCOUNT"+str(sys.argv[1]) #must add an asn # after account, eg. ACCOUNT151 we do this programmatically later in program
tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
#print(tx_sender)
tx_sender.load_account_keys()
tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")
print("Transaction setup complete for: " + tx_sender_name)

print("Setting up Path Validation Contract......")
# path_validation = SetupPathValidation.SetupPathValidation(int(sys.argv[1]))
# path_validation.compile_contract()
# path_validation.deploy_contract()


##################### GET PEERS ############################
# cross_connects = sys.argv[2]
# print("PRINTING CROSS CONNECTS: ")
# print(cross_connects)



################Establishes local IPTABLES Rule to begin processing packets############
QUEUE_NUM = 1
# insert the iptables FORWARD rule
os.system("iptables -I INPUT -p tcp --dport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I INPUT -p tcp --sport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I OUTPUT -p tcp --dport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I OUTPUT -p tcp --sport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))

"""
TODO: implement
Runs after we validate the origin AS
Steps
1) Get AS path from the inbound BGP message
2) ensure access to asn_address_mapping.yaml
3) run validate_advertisement()
4a) process packet if valid
4b) drop packet if invalid

Note: runs on incoming packets
"""
myASN = 123 
def validate_path(pkt):
    print("validate path")

    inIP = pkt.inIP
    inSubnet = pkt.inSubnet
    BGP_AS_PATH = pkt.BGPPAASPath() # or something. idk at this point
    
    return tx_sender.validate_advertisement(inIP, inSubnet, myASN, BGP_AS_PATH)


"""
TODO: implement
When we send a BGP update (whether or not it is originating from ourselves), we need need to
1) get the address of our own advertisement contract
2) run add_advertisement()
3) send update

Note: should be implemented on outgoing packets
"""
def add_to_advertisement_contract(pkt):
    print("add to advertisement contract")
    inIP = pkt[IP].src #this ASes IP
    inSubnet = str(pkt[BGPUpdate].nlri[count].prefix).split('/')[1] # subnet
    inNextHop = pkt.inNextHop

    return tx_sender.add_advertisement(inIP, inSubnet, inNextHop)

def outgoing_packet():
    # Check if packet is outgoing
    return True

def get_datetime():
    return datetime.datetime.now()

old_print = print
# def ts_print(*args, **kwargs):
#     old_print(datetime.datetime.now(), *args, **kwargs)

# print = ts_print

def pkt_in(packet):
    local_index = global_index.incr_index()
    # local_index = incr_index()
    # old_print = print

    def ts_print(*args, **kwargs):
        old_print(str(datetime.datetime.now()) + "--" + str(local_index), *args, **kwargs)

    print = ts_print

    print("rx packet")
    pkt = IP(packet.get_payload())
    # print(str(pkt.summary()))
    print(packet)
    print(pkt)
    print(pkt.show())
    # print("full packet show: " + str(packet))
    # if (str(pkt.summary()).find('BGPHeader') > 0):
    #     print("rx BGP packet")
        # if pkt[BGPHeader].type == 2: #Check if packet has a BGPHeader and if it is of type==2 (BGPUpdate). 
        #     print("rx BGP Update pkt")
        # packet.accept()
    packet_modified = False
    if (str(pkt.summary()).find('BGPHeader') > 0) and (pkt[BGPHeader].type == 2):
        print("rx BGP Update pkt")
        try:
            if pkt[BGPUpdate].path_attr[1].attribute.segments[0].segment_length == 1:
                print ("    Destination IP = " + pkt[IP].dst) #Local AS
                print ("    Source IP = " + pkt[IP].src) #Remote AS
                print ("    BGP Segment AS = " + str(pkt[BGPUpdate].path_attr[1].attribute.segments[1].segment_length)) #even though it says segment length, that field is used to announce the A>
                print ("    BGP Segment Next Hop = " + str(pkt[BGPUpdate].path_attr[2].attribute.next_hop))
                #print ("    BGP Segment NLRI = " + str(pkt[BGPUpdate].nlri[0].prefix))
                #print ("End of BGP Update Packet")
                count = 0
                for i in pkt[BGPUpdate].nlri:
                    print ("BGP NLRI check: " + str(pkt[BGPUpdate].nlri[count].prefix))
                    # chain mutable list = [AS, Network Prefix, CIDR]
                    adv_segment = [pkt[BGPUpdate].path_attr[1].attribute.segments[1].segment_length, str(pkt[BGPUpdate].nlri[count].prefix).split('/')[0], str(pkt[BGPUpdate].nlri[count].prefix).split('/')[1], "Internal"]
                    print ("Advertised Segment="+str(adv_segment))
			        #print ("try seg:" + str(adv_segment[1]))
                    #call check on BGPchain to validate segment advertisement request
                    account_check=str(pkt[BGPUpdate].path_attr[1].attribute.segments[1].segment_length)
                    print ("validating advertisement for ASN: "+account_check)
                    check=bgpchain_validate(adv_segment, tx_sender)
                    #print ("segment check = "+str(check))
                    if check == 'Authorized':
                        print("NLRI " + str(count) + " passed authorization...checking next ASN")
                        count +=1
                        pass
                    else:
                        print ("AS " + str(pkt[BGPUpdate].path_attr[1].attribute.segments[1].segment_length) + " Failed Authorization, Sending Notification...")
                        print("about to modify packet")
                        pkt = edit_packet(pkt)
                        print('packet modified')
                        # packet.drop() #Drops original packet without forwarding
                        print("packet modified. setting flag")
                        packet_modified = True
                        break # stop looping
                print ("All Advertised ASN's have been checked")
                if packet_modified:
                    print("packet modified. forwarding modified packet")
                    print("modified packet: ") 
                    print(pkt.show())
                    print("modified packet bytes: ")
                    print(bytes(pkt))
                    print("setting modified packet payload")
                    packet.set_payload(bytes(pkt))
                print("accepting packet")
                packet.accept()
            else:
                print("Not a new neighbor path announcement")
                print("packet not modified. accepting")
                packet.accept()
                print("packet accepted in else")
        except IndexError as ie:
            print("index error. diff type of bgp announcement. accept packet. error: " + repr(ie))
            packet.accept()
            print("accepted other bgp type packet")
        except Exception as e: 
            print("bgp msg other: " + repr(e))
            # packet.accept()
            pass
    else:
        print("else. packet accept")
        packet.accept()
        print("else. packet accepted")
    
def edit_packet(pkt):
    print("edit packet. bytes:")
    print(bytes(pkt))
    p_hijack_bytes = bytearray(bytes(pkt))
    print("byte array:")
    print(p_hijack_bytes)
    print("byte array length: " + str(len(p_hijack_bytes)))
    print("bytes to remove: ")
    print(p_hijack_bytes[110:115])
    del p_hijack_bytes[110:115]
    pkt_reconstructed = IP(bytes(p_hijack_bytes))
    print("convert back to bgp from bytes:")
    pkt_reconstructed.show()
    print("modify length of bgp packet")
    pkt_reconstructed[BGPHeader].len = pkt_reconstructed[BGPHeader].len - 5
    pkt_reconstructed.show2()
    # new_nlri = BGPNLRI_IPv4(prefix="10.150.1.0/24")
    # new_nlri_bytes = bytes(new_nlri)
    # b_pkt = bytearray(bytes(pkt))
    # b_pkt[126:130] = new_nlri_bytes
    # pkt_reconstructed = CookedLinux(bytes(b_pkt))
    # del pkt_reconstructed[IP].chksum
    # del pkt_reconstructed[TCP].chksum 
    # pkt_reconstructed.show2()
    print("new pkt nlri: " + str(pkt_reconstructed[BGPUpdate].nlri[0].prefix))
    return pkt_reconstructed

    # nlri = pkt[BGPUpdate].nlri[0].prefix
    # # print("type of nlri: " + str(type(nlri)))
    # # new_nlri = "10.150.10.10/24".encode('utf-8')
    # # print("type of new nlri: " + str(type(new_nlri)))
    # new_nlri = "10.150.10.10/24"
    # pkt[BGPUpdate].nlri[0].prefix = new_nlri
    # print("new pkt nlri: " + str(pkt[BGPUpdate].nlri[0].prefix))

    # # pkt[IP].dst = "

#Chain check function. Needs to be updated with smart contract calls.  
def bgpchain_validate(segment, tx_sender):
    print ("Validating segment.....")
    print (tx_sender)
    inIP = IPv4Address(segment[1])
    print (inIP)
    inSubnet = int(segment[2])
    print (str(inSubnet))
    inASN = int(segment[0])
    print (str(inASN))
    #print(type(inASN), inASN)
    #print("tes")
    # Validate the prefix<=>ASN mapping. Returns an enum.
    #print ("testing tx_sender: "+str(tx_sender))
    print ("Checking segment: AS" + str(inASN)+ " , " + str(inIP) + "/" + str(inSubnet))
    validationResult = tx_sender.tx.sc_validatePrefix(int(inIP), inSubnet, inASN)
    print(str(validationResult))
    if validationResult==validatePrefixResult.prefixValid:
        print("Segment Validated.")
        return "Authorized"
    else:
        print("Segment Validation Failed. Error: " + str(validationResult))
        # return False
        return "Unauthorized"
 
#def interface_check():
#    if_list=[]
#    for interface in get_if_list():
#        if interface =="lo" or interface=="dummy0":
#            pass
#       else:
#            if_list.append(interface)
#    return if_list


if __name__=='__main__':
    global_index = Index() 
    # sys.exit(0)
# instantiate the netfilter queue
    nfqueue = NetfilterQueue()
 
    try:
        nfqueue.bind(QUEUE_NUM, pkt_in)
        #nfqueue.bind(2, pkt_in)
        nfqueue.run()
    except KeyboardInterrupt:
        print('')
        # remove that rule we just inserted, going back to normal.
        os.system("iptables --flush")
        nfqueue.unbind()
