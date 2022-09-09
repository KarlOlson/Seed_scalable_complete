from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys

def main():
    if len(sys.argv) < 4:
        print("please enter a tx_sender, and ip/subnet to get the ip/subnet owner ASN")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])
    inIP = IPv4Address(sys.argv[2])
    inSubnet = int(sys.argv[3])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")

    asn = tx_sender.tx.sc_getPrefixOwner(int(inIP), inSubnet)
    if str(asn) == "none" or asn == "0":
        print("IANA owns the prefix: " + str(inIP) + "/" + str(inSubnet))
    else:
        print("ASN " + str(asn) + " owns the prefix: " + str(inIP) + "/" + str(inSubnet))


if __name__ == "__main__":
    main()