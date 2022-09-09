from Classes.Account import Account
from Utils.Utils import *
import ipaddress
import sys

def main():
    if len(sys.argv) < 3:
        print("please enter a tx_sender, and an ASN to get all prefixes owned by the ASN")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inASN = int(sys.argv[2])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")

    prefix_list = tx_sender.tx.sc_getAllPrefixesOwnedByASN(inASN)

    if len(prefix_list) == 0:
        print("ASN " + str(inASN) + " owns no prefixes")
    else:
        [print(str(ipaddress.ip_address(prefix[0])) + "/" + str(prefix[1])) for prefix in prefix_list]

if __name__ == "__main__":
    main()