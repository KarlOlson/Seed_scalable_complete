#!/usr/bin/python3
#To Run:
#Install scapy: $sudo pip install scapy
#Run Proxy Sniffer $sudo python3 <filename.py>
#Must run from sudo for packet processing privileges.
from operator import add
from netfilterqueue import NetfilterQueue
from scapy.all import *
from Classes.Account import Account
from Utils.Utils import *
from Classes.PacketProcessing.MutablePacket import MutablePacket
from Classes.PacketProcessing.BGPUpdate import BGPUpdate
from Classes.PacketProcessing.Index import Index
from Classes.PacketProcessing.ConnectionTracker import ConnectionTracker
from Classes.PacketProcessing.FiveTuple import FiveTuple
from Classes.PacketProcessing.FlowDirection import FlowDirection
from ipaddress import IPv4Address
import os, sys
import datetime
import subprocess

ACCEPT_UNREGISTERED_ADVERTISEMENTS = True # set to False to remove all advertisements that are not registered

global_index = None
connections = None

load_contrib('bgp') #scapy does not automatically load items from Contrib. Must call function and module name to load.

#####Synchronizes ASN with blockchain account data##################
tx_sender_name = "ACCOUNT"+str(sys.argv[1]) #must add an asn # after account, eg. ACCOUNT151 we do this programmatically later in program
tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
#print(tx_sender)
tx_sender.load_account_keys()
# tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")
# print("Transaction setup complete for: " + tx_sender_name)

################Establishes local IPTABLES Rule to begin processing packets############
QUEUE_NUM = 1
# insert the iptables FORWARD rule
os.system("iptables -I INPUT -p tcp --dport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I INPUT -p tcp --sport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I OUTPUT -p tcp --dport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))
os.system("iptables -I OUTPUT -p tcp --sport 179 -j NFQUEUE --queue-num {}".format(QUEUE_NUM))

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

    if not connections.connection_exists(m_pkt):
        connections.add_connection(m_pkt)
    # connections.update_connection(m_pkt)

    if m_pkt.is_bgp_update(): # checks for both bgp packet and bgp update
        print("rx BGP Update pkt")
        try:
            # iterate over packet bgp payloads (bgp layers)
            layer_index = 0
            for payload in m_pkt.iterpayloads():
                if isinstance(payload,  scapy.contrib.bgp.BGPHeader):
                    most_recent_bgp_header = payload
                elif isinstance(payload, scapy.contrib.bgp.BGPUpdate):
                    layer_index += 1
                    print(type(payload))
                    # m_pkt.add_bgp_update(BGPUpdate())
                    update = BGPUpdate(most_recent_bgp_header, payload, layer_index)
                    if not update.has_withdraw_routes() and update.has_nlri_advertisements():
                        # Get the next hop ASN from the BGP packet
                        # next_hop_asn = update.get_next_hop_asn()
                        # next_hop_asn = m_pkt.get_next_hop_asn()
                        for count, nlri in enumerate(update.nlri()):
                            segment = update.get_segment(nlri)
                            print("nlri count: " + str(count))
                            print("BGP NLRI check: " + str(nlri.prefix))
                            print ("Advertised Segment: " + str(segment))
                            print ("validating advertisement for ASN: " + str(update.get_origin_asn()))

                            validationResult = bgpchain_validate(segment, tx_sender)
                            if validationResult == validatePrefixResult.prefixValid:
                                print("NLRI " + str(count) + " passed authorization...checking next ASN")
                            elif validationResult == validatePrefixResult.prefixNotRegistered:
                                handle_unregistered_advertisement(m_pkt, nlri, validationResult, update)
                            elif validationResult == validatePrefixResult.prefixOwnersDoNotMatch:
                                handle_invalid_advertisement(m_pkt, nlri, validationResult, update)
                            else:
                                print("error. should never get here. received back unknown validationResult: " + str(validationResult))
                        if m_pkt.is_bgp_modified():
                            print("BGP Update packet has been modified")
                        else:
                            print("BGP update and headers are not modified")
                    else:
                        print("BGP Update packet has no NLRI advertisements")
                else:
                    print("Packet layer is not a BGPUpdate or BGPHeader layer")
            print ("All Advertised ASN's within all BGP Updates have been checked")
            if m_pkt.is_bgp_modified():
                print("BGP Update packet has been modified")
                connections.update_connection(m_pkt)
                print("setting modified bgp packet. accept:")
                m_pkt.recalculate_checksums()
                packet.set_payload(m_pkt.bytes())
            else:
                connections.update_connection(m_pkt)
                if m_pkt.are_headers_modified():
                    print("headers updated, accept header modified packet")
                    m_pkt.recalculate_checksums()
                    packet.set_payload(m_pkt.bytes())
                else:
                    print("packet not modified. accepting as is")
            packet.accept()

        except IndexError as ie:
            print("index error. diff type of bgp announcement. accept packet. error: " + repr(ie))
            packet.accept()
            print("accepted other bgp type packet")
        except Exception as e: 
            print("bgp msg other: " + repr(e))
            packet.accept()
    else:
        print("not a bgp update packet. are headers modified? ")
        connections.update_connection(m_pkt)
        if m_pkt.are_headers_modified():
            m_pkt.recalculate_checksums()
            print("yes headers modified. set packet bytes.")
            packet.set_payload(m_pkt.bytes())
        print("accept non bgp packet")
        packet.accept()

def handle_unregistered_advertisement(m_pkt, nlri, validationResult, update):
    print ("AS " + str(update.get_origin_asn()) + " Failed Authorization. [" + str(validationResult) + "]. BGPUpdate layer: " + str(update.get_layer_index()))
    if ACCEPT_UNREGISTERED_ADVERTISEMENTS:
        print("Accepting unregistered advertisement")
    else:
        print("Dropping unregistered advertisement")
        remove_invalid_nlri_from_packet(m_pkt, nlri, update)

def handle_invalid_advertisement(m_pkt, nlri, validationResult, update):
    print ("AS " + str(update.get_origin_asn()) + " Failed Authorization. [" + str(validationResult) + "]. BGPUpdate layer: " + str(update.get_layer_index()))
    remove_invalid_nlri_from_packet(m_pkt, nlri, update)


def remove_invalid_nlri_from_packet(m_pkt, nlri, update):
    m_pkt.remove_nlri(nlri, update)
    if m_pkt.is_bgp_modified():
        print("bgp packet modified")
    else:
        print("ERROR: packet modification failed")


#Chain check function. Needs to be updated with smart contract calls.  
def bgpchain_validate(segment, tx_sender):
    inIP = IPv4Address(segment[1])
    inSubnet = int(segment[2])
    inASN = int(segment[0])

    print ("Validating segment: AS" + str(inASN)+ " , " + str(inIP) + "/" + str(inSubnet))
    
    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")
    print("Transaction setup complete for: " + tx_sender_name)
    
    validationResult = tx_sender.tx.sc_validatePrefix(int(inIP), inSubnet, inASN)
    print(str(validationResult))
    return validationResult

# def bgpchain_validate_path(path):
#     print("validating path: " + str(path))

# def write_next_hop_asn_to_our_path_validation_contract(next_hop_asn, segment):
#     advIP = IPv4Address(segment[1])
#     advSubnet = int(segment[2])
#     print("writing next hop ASN to our path validation contract") 
#     print("Next Hop ASN: " + str(next_hop_asn) + " , Prefix: " + str(advIP) + "/" + str(advSubnet))

#     my_path_validation_contract_env_name = tx_sender_name + "_PATH_VALIDATION_CONTRACT"
#     tx_sender.generate_transaction_object("PATH_VALIDATION", my_path_validation_contract_env_name)

#     if next_hop_asn == -1:
#         print("Sending advertisement to a route server")
#     else:
#         print("sending advertisement to an ASN")

#     # Generate deploy contract transaction object
#     tx = tx_sender.tx.sc_addAdvertisementToMyContract(tx_sender.get_nonce(), int(advIP), advSubnet, next_hop_asn)
#     # sign and deploy contract
#     tx_hash, tx_receipt, err = tx_sender.tx.sign_and_execute_transaction(tx)
#     if TxErrorType(err) != TxErrorType.OK:
#         print("ERROR: " + str(TxErrorType(err)) + ". Contract failed to execute! Advertisement not added!")
#         return TxErrorType(err)
#     return TxErrorType.OK
    




if __name__=='__main__':
    global_index = Index() 
    connections = ConnectionTracker()

    print("Accept Unregistered Advertisements Flag: " + str(ACCEPT_UNREGISTERED_ADVERTISEMENTS))

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
