from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys

def main():
    if len(sys.argv) < 5:
        print("please enter a tx_sender, ip, subnet, and ASN to check if the advertised prefix matches the ASN. aka if valid")
        sys.exit(-1)

    # All we're checking is an ip/subnet<=>ASN binding! Nothing else!
    tx_sender_name = str(sys.argv[1])
    inIP = IPv4Address(sys.argv[2])
    inSubnet = int(sys.argv[3])
    inASN = int(sys.argv[4])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_transaction_object("IANA", "IANA_CONTRACT_ADDRESS")

    # Validate the prefix<=>ASN mapping. Returns an enum.
    validationResult = tx_sender.tx.sc_validatePrefix(int(inIP), inSubnet, inASN)
    print(validationResult)

if __name__ == "__main__":
    main()