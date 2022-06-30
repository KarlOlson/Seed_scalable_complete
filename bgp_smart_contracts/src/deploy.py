from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import sys

def main():
    if len(sys.argv) < 2:
        print("please enter a tx_sender (e.g. ACCOUNT0) to deploy contract from")
        sys.exit(-1)

    tx_sender_name = str(sys.argv[1])

    # create accounts
    tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
    tx_sender.load_account_keys()

    tx_sender.generate_deploy_contract_object("IANA")

    # Generate deploy contract transaction object
    tx = tx_sender.tx.deploy_smart_contract(tx_sender.get_nonce())

    # sign and deploy contract
    tx_hash, tx_receipt, err = tx_sender.tx.sign_and_execute_transaction(tx)
    if TxErrorType(err) != TxErrorType.OK:
        print("ERROR: " + str(TxErrorType(err)) + ". Contract NOT deployed. Transaction failed")
        
    print("SUCCESS: Contract deployed")
    print("Contract address: " + tx_receipt.contractAddress)

if __name__ == "__main__":
    main()