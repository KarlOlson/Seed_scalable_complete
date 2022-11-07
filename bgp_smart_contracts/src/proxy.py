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
from Classes.MutablePacket import MutablePacket
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

def pkt_in(packet):
    local_index = global_index.incr_index()
    def ts_print(*args, **kwargs):
        old_print(str(datetime.datetime.now()) + "--" + str(local_index), *args, **kwargs)

    print = ts_print

    print("rx packet")
    pkt = IP(packet.get_payload())
    m_pkt = MutablePacket(pkt)
    # TODO: wrap this pkt with an m_pkt class. can track packet modifications
    print(packet)
    print(m_pkt.show())

    packet_modified = False
    if m_pkt.is_bgp_update(): # checks for both bgp packet and bgp update
        print("rx BGP Update pkt")
        try:
            if m_pkt.get_segment_length() == 1:
                print("rx BGP Update pkt with single segment")
                m_pkt.print_bgp_update_summary()
                for count, nlri in enumerate(m_pkt.get_nlris()):
                    print("nlri count: " + str(count))
                    print ("BGP NLRI check: " + str(nlri.prefix))

                    # chain mutable list = [AS, Network Prefix, CIDR]
                    adv_segment = m_pkt.get_adv_segment(nlri)
                    print ("Advertised Segment: " + str(m_pkt.get_adv_segment(nlri)))
                    print ("validating advertisement for ASN: " + str(m_pkt.get_segment_asn()))
                    
                    validationResult = bgpchain_validate(adv_segment, tx_sender)
                    if validationResult == validatePrefixResult.prefixValid:
                        print("NLRI " + str(count) + " passed authorization...checking next ASN")
                    elif validationResult == validatePrefixResult.prefixNotRegistered:
                        handle_invalid_advertisement(m_pkt, nlri, validationResult)
                        print('packet modified')
                    elif validationResult == validatePrefixResult.prefixOwnersDoNotMatch:
                        handle_invalid_advertisement(m_pkt, nlri, validationResult)
                        print('packet modified')
                    else:
                        print("error. should never get here. received back unknown validationResult: " + str(validationResult))
                print ("All Advertised ASN's have been checked")
                if m_pkt.is_modified():
                    print("modified packet: ") 
                    print(m_pkt.show())
                    print("setting modified packet payload")
                    packet.set_payload(m_pkt.bytes())
                packet.accept()
            else:
                print("Not a new neighbor path announcement")
                packet.accept()
        except IndexError as ie:
            print("index error. diff type of bgp announcement. accept packet. error: " + repr(ie))
            packet.accept()
            print("accepted other bgp type packet")
        except Exception as e: 
            print("bgp msg other: " + repr(e))
            # packet.accept()
            pass
    else:
        packet.accept()


def handle_invalid_advertisement(m_pkt, nlri, validationResult):
    print ("AS " + str(m_pkt.get_segment_asn()) + " Failed Authorization. [" + str(validationResult) + "]")
    remove_invalid_nlri_from_packet(m_pkt, nlri)


def remove_invalid_nlri_from_packet(m_pkt, nlri):
    m_pkt.remove_nlri(nlri)
    if m_pkt.is_modified():
        print("packet modified")
    else:
        print("ERROR: packet modification failed")


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

    print ("Checking segment: AS" + str(inASN)+ " , " + str(inIP) + "/" + str(inSubnet))
    validationResult = tx_sender.tx.sc_validatePrefix(int(inIP), inSubnet, inASN)
    print(str(validationResult))
    return validationResult

 

if __name__=='__main__':
    global_index = Index() 
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
