import os
import json
import sys
from Config import ROOT_DIR
from web3 import Web3
# https://github.com/iamdefinitelyahuman/py-solc-x
from solcx import compile_standard, install_solc

from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address




class Contract():
    def __init__(self, contract_name):
        available_contracts = {
            "IANA", 
            "PATH_VALIDATION"
        }

        if contract_name not in available_contracts:
            print("Error: Invalid contract name. Contracts available are: ", available_contracts)
            sys.exit(-1)
        
        self.contract = contract_name

        print("creating contract object for: " + self.contract)

    # compile solidity
    def compile(self):

        contract_path = os.path.join(ROOT_DIR, '../contracts/' + self.contract + '.sol')
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract_file = f.read()


        #  download 0.8.0 Version of Solidity compiler 
        install_solc('0.8.0')

        #  compile Solidity
        compiled_sol = compile_standard(
            {
                "language": "Solidity",
                # Solidity file 
                "sources": {self.contract + ".sol": {"content": contract_file}},
                "settings": {
                    "outputSelection": {
                        "*": {
                            #  Content generated after compilation 
                            "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                        }
                    }
                },
            },
            #  edition , When writing smart contracts Solidity The version used corresponds to 
            solc_version="0.8.0",
        )

        #  The compiled results are written to the file 
        compiled_json_dir = os.path.join(ROOT_DIR, 'compiled_json/')
        exists = os.path.exists(compiled_json_dir)
        if not exists:
            os.makedirs(compiled_json_dir)

        compiled_json_path = os.path.join(ROOT_DIR, 'compiled_json/compiled_' + self.contract + '_code.json')
        with open(compiled_json_path, 'w') as f:
            json.dump(compiled_sol, f)


    def deploy(self, ASN):
        tx_sender_name = "ACCOUNT"+str(ASN)

        # create accounts
        tx_sender = Account(AccountType.TransactionSender, tx_sender_name)
        tx_sender.load_account_keys()

        tx_sender.generate_deploy_contract_object(self.contract)

        # Generate deploy contract transaction object
        tx = tx_sender.tx.deploy_smart_contract(tx_sender.get_nonce())

        # sign and deploy contract
        tx_hash, tx_receipt, err = tx_sender.tx.sign_and_execute_transaction(tx)
        if TxErrorType(err) != TxErrorType.OK:
            print("ERROR: " + str(TxErrorType(err)) + ". Contract NOT deployed. Transaction failed")

        print("SUCCESS: " + self.contract + " Contract deployed")
        print("Contract address: " + tx_receipt.contractAddress)