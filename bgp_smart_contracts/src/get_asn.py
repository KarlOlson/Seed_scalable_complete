from Classes.Account import Account
from Utils.Utils import *
import sys

def main():
    if len(sys.argv) < 2:
        print("please enter a tx_sender and an ASN to check if ASN exists")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inASN = int(sys.argv[2])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")

    asn = tx_sender.tx.sc_getASNOwner(inASN)
    if str(asn) == "none" or Utils.is_null_address(asn):
        print("ASN " + str(inASN) + " does not exist")
    else:
        print("valid ASN in map! (" + str(inASN) + ", " + str(asn) + ")")

if __name__ == "__main__":
    main()