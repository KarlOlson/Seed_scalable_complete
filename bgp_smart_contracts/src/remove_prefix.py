from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys

def main():
    if len(sys.argv) < 4:
        print("please enter an tx_sender, ASN, and its address to remove from ASNMap")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inIP = IPv4Address(sys.argv[2])
    inSubnet = int(sys.argv[3])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")

    # generate contract transaction
    tx = tx_sender.tx.sc_removePrefix(tx_sender.get_nonce(), int(inIP), inSubnet)

    # sign and execute transaction
    tx_hash, tx_receipt, err = tx_sender.tx.sign_and_execute_transaction(tx)
    if TxErrorType(err) != TxErrorType.OK:
        print("ERROR: " + str(TxErrorType(err)) + ". Transaction NOT executed")
        
    print("SUCCESS: ASN<=>Address removed. All Prefixes owned by ASN returned to IANA")

if __name__ == "__main__":
    main()