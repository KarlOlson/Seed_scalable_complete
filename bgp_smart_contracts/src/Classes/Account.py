from dotenv import load_dotenv
import sys
from Utils.Utils import *
from Classes.Web3Obj import Web3Obj
from Classes.Transaction import Transaction

class Account(Web3Obj):
    def __init__(self, account_type, account_name):
        if "ACCOUNT" not in account_name:
            print("Account name not recognized. must be of form: ACCOUNT<N>, e.g. ACCOUNT2")
            sys.exit(-1)

        self.w3 = Web3Obj.w3
        self.account_type = account_type
        self.account_name = account_name
        self.public_key = None
        self.private_key = None
        self.tx = None

    def load_account_keys(self):
        self.public_key, self.private_key = Utils.load_account_from_env_v2(self.account_name)

    def get_nonce(self):
        if self.public_key == None:
            print("ERROR: public key not set. can't get nonce")
            sys.exit(-1)
        return self.w3.eth.get_transaction_count(self.public_key)

    def generate_transaction_object(self, contract_name, contract_address_env):
        self.tx = Transaction(contract_name, contract_address_env)
        self.tx.set_tx_sender_pub_key(self.public_key)
        self.tx.set_tx_sender_priv_key(self.private_key)

    def generate_deploy_contract_object(self, contract_name):
        self.tx = Transaction(contract_name)
        self.tx.set_tx_sender_pub_key(self.public_key)
        self.tx.set_tx_sender_priv_key(self.private_key)

    def hash_and_sign_message(self, data_types, data):
        _, signed_message, err = Utils.hash_and_sign_message(
            self.w3,
            data_types, 
            data,
            self.private_key
        )
        if err:
            print("ERROR: failed to hash and sign message")
        
        return signed_message, err

    def generate_signature_validation_data_from_signed_message(self, signed_message):
        sigV, sigR, sigS = Utils.generate_message_validation_data(signed_message)
        self.tx.set_signature_validation_data(sigV, sigR, sigS)

