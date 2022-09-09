from wsgiref import validate
from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys
from collections import namedtuple

"""
Example:
1 -> 2 -> 3 -> 4 -> ...

A1: 10.0.20.0/24 : 1
    - writes to 1's own advertisement contract {10.0.20.0/24, nextHop = 2}
    - sends A1 to 2
A2: 10.0.20.0/24 : 2, 1
    - checks there is a 10.0.20.0/24 with next hop 2 in 1's advertisement contract
    - writes to 2's own advertisement contract {10.0.20.0/2, nextHop = 3}
    - sends A2 to 3
A3: 10.0.20.0/24 : 3, 2, 1
    - checks there is a 10.0.20.0/24 with next hop 3 in 2's advertisement contract
    - checks there is a 10.0.20.0/24 with next hop 2 in 1's advertisement contract
    - writes to 3's own advertisement contract {10.0.20.0/2, nextHop = 4}
    - sends A3 to 4...

"""

"""
Example
1 -> 2 -> 3 -> 4 -> ...
python add_advertisement.py ACCOUNT0 10.0.20.0 24 2
python add_advertisement.py ACCOUNT1 10.0.20.0 24 3
python add_advertisement.py ACCOUNT2 10.0.20.0 24 4

Now validate

python validate_advertisement.py ACCOUNT0 10.0.20.0 24 <myASN> <Received advertisement's AS_PATH>
ex: 
python validate_advertisement.py ACCOUNT0 10.0.20.0 24 2 1

## check down path that path 2->3 exists and 1->2 exists
python validate_advertisement.py ACCOUNT1 10.0.20.0 24 3 2 1

## check down path that paths 3->4, 2->3, and 1->2 exist
python validate_advertisement.py ACCOUNT1 10.0.20.0 24 4 3 2 1

"""

asnPaticipantStatus = namedtuple("asnPaticipantStatus", "asn status")

def check_connections(path_list):
    path_list = list(reversed(path_list))
    p_np_p = []
    prevHopAndStatus = 0
    hopAndStatus = None 
    nextHopAndStatus = None 
    consecutive_non_participant_counter = 0
    for index, entry in enumerate(path_list):
        if not entry.status:
            if index == 0:
                prevHopAndStatus = asnPaticipantStatus(0, True)
            else:
                prevHopAndStatus = path_list[index - 1]
            
            hopAndStatus = entry
            
            if index >= len(path_list):
                nextHopAndStatus = asnPaticipantStatus(0, True)
            else:
                nextHopAndStatus = path_list[index + 1]

            p_np_p.append((prevHopAndStatus.asn, hopAndStatus.asn, nextHopAndStatus.asn))

            consecutive_non_participant_counter += 1
            if consecutive_non_participant_counter > 1:
                return -1
        else:
            consecutive_non_participant_counter = 0
        
    return p_np_p
        

def main():
    len_args = len(sys.argv)
    if len_args < 6:
        print("please enter an tx_sender, ip, subnet, your own ASN, and the incoming advertisement's AS_PATH (e.g. 3 2 1) to validate path")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inIP = IPv4Address(sys.argv[2])
    inSubnet = int(sys.argv[3])
    myASN = int(sys.argv[4])


    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()
    tx_sender.load_asn_contract_mappings()

    AS_PATH_contract_mappings = {}
    AS_PATH_participation_status = []
    AS_PATH = []
    # AS_PATH_participation_status[int(myASN)] = True # we are calling this, so we have to be a participant
    AS_PATH_participation_status.append(asnPaticipantStatus(int(myASN), True))
    for i in range(5, len_args):
        asn = sys.argv[i]
        AS_PATH.append(str(asn))
        asn_str = "asn_" + str(asn)

        # take only the asn=>contract mappings from the yaml config that are in the input AS_PATH and put them in the AS_PATH_contract_mappings dict
        # |AS_PATH_contract_mappings| <= |tx_sender.asn_contract_mappings| (always!)
        if asn_str in tx_sender.asn_contract_mappings:
            AS_PATH_contract_mappings[int(asn)] = tx_sender.asn_contract_mappings[asn_str]["validation_contract"]
            AS_PATH_participation_status.append(asnPaticipantStatus(int(asn), True))

        else: # this is where we want to do partial advertisement deployment
            # print("No PATH_VALDIATION contract known for ASN (" + str(asn) + ")")
            # print("Check earlier path to see last participant's advertisement")
            AS_PATH_contract_mappings[int(asn)] = False
            AS_PATH_participation_status.append(asnPaticipantStatus(int(asn), False))

    path_validation_result = {}
    nextHopAsn = myASN
    non_participants = []
    for asn_in_path, contract_address in AS_PATH_contract_mappings.items():
        if not contract_address: # an asn_in_path that is not a participant (no validation contract)
            non_participants.append(asn_in_path)
            path_validation_result[asn_in_path] = {"nextHop": nextHopAsn, "result": validateAdvertisementResult.nonParticipantSource }
        else:
            # we actually need to pass in the contract address here. or we can do something with a config file
            tx_sender.generate_transaction_object("PATH_VALIDATION", contract_address, True)
            tx = tx_sender.tx.sc_validateAdvertisement(int(inIP), inSubnet, nextHopAsn)
            path_validation_result[asn_in_path] = {"nextHop": nextHopAsn, "result": tx}
        nextHopAsn = asn_in_path

    pathValidationResultEnum = validatePathResult.pathINVALID
    p_np_p = check_connections(AS_PATH_participation_status)
    if p_np_p == -1:
        print("Too many consecutive non participants to validate path!")
    elif not len(p_np_p):
        print("All ASNs in AS_PATH are participants")
    else:
        for res in p_np_p:
            print("P -> NP -> P found for: (" + str(res[0]) + "," + str(res[1]) + "," + str(res[2]) + ")")
        pathValidationResultEnum = validatePathResult.pathPnpVALID

    print("AS_PATH Validation Results for: \"" + str(inIP) + "/" + str(inSubnet) + " : " + ', '.join(AS_PATH) + "\" ")
    count = 0
    invalidAdvertisementASNs = []
    for hop, result in path_validation_result.items():
        print("ASN " + str(hop) + " -> ASN " + str(result["nextHop"]) + " hop in AS_PATH is: " + str(result["result"]))
        if result["result"] == validateAdvertisementResult.advertisementVALID:
            count += 1
        elif result["result"] == validateAdvertisementResult.advertisementINVALID:
            invalidAdvertisementASNs.append(str((str(hop) + "->" + str(result["nextHop"]))))
            pathValidationResultEnum = validatePathResult.pathINVALID

    if count == len(path_validation_result):
        pathValidationResultEnum = validatePathResult.pathVALID
    
    print("Entire Path is: " + str(pathValidationResultEnum))

    if pathValidationResultEnum  == validatePathResult.pathPnpVALID:
        print("Non participants: " + str(non_participants))
    elif pathValidationResultEnum == validatePathResult.pathINVALID:
        if non_participants:
            print("Non Participants: " + str(non_participants))
        if invalidAdvertisementASNs:
            print("Invalid advertisements: " + str(invalidAdvertisementASNs))
        else:
            print("Too many consecutive non participants to validate path!")




if __name__ == "__main__":
    main()