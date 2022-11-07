from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys

def main():
    if len(sys.argv) < 5:
        print("please enter an tx_sender, ip, subnet, and next hop to add to your advertisement contract")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inIP = IPv4Address(sys.argv[2])
    inSubnet = int(sys.argv[3])
    inNextHop = int(sys.argv[4]) #e.g. 2

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    my_path_validation_contract_env_name = tx_sender_name + "_PATH_VALIDATION_CONTRACT"
    tx_sender.generate_transaction_object("PATH_VALIDATION", my_path_validation_contract_env_name)

    # Generate deploy contract transaction object
    tx = tx_sender.tx.sc_addAdvertisementToMyContract(tx_sender.get_nonce(), int(inIP), inSubnet, inNextHop, )
    # sign and deploy contract
    tx_hash, tx_receipt, err = tx_sender.tx.sign_and_execute_transaction(tx)
    if TxErrorType(err) != TxErrorType.OK:
        print("ERROR: " + str(TxErrorType(err)) + ". Contract failed to execute! Advertisement not added!")

    print("SUCCESS: advertisement: {" + str(inIP) + "/" + str(inSubnet) + " -> " + str(inNextHop) + "} added")

if __name__ == "__main__":
    main()