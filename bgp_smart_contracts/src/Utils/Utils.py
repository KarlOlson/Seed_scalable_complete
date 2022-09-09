from compile import *
from web3 import Web3
from eth_account.messages import encode_defunct
from dotenv import load_dotenv
from eth_account.messages import encode_defunct, _hash_eip191_message
from Config import ROOT_DIR
import os
import json
from enum import Enum
import yaml

class TxErrorType(Enum):
    OK = 0
    FailedToSignTx = -1
    FailedToExecuteTx = -2


class AccountType(Enum):
    TransactionSender = 0
    MessageSender = 1

# Enum of the validatePrefix() return types
# @param prefixValid VALID: ip/mask and ASN all match. Valid advertisment
# @param prefixNotRegistered INVALID: ip/mask advertised is owned by IANA - aka not registered. Could be not registered or non participant
# @param prefixOwnersDoNotMatch INVALID: The ASN that owns the advertised ip/mask does not match the ASN that advertised the ip/mask. 
class validatePrefixResult(Enum):
    prefixValid = 0
    prefixNotRegistered = 1
    prefixOwnersDoNotMatch = 2

class validateAdvertisementResult(Enum):
    advertisementVALID = 0
    advertisementINVALID = 1
    nonParticipantSource = 2

class validatePathResult(Enum):
    pathVALID = 0
    pathINVALID = 1
    pathPnpVALID = 2
    

class Utils(object):
    @staticmethod
    def is_null_address(inAddr):
        if str(inAddr) == "0x0000000000000000000000000000000000000000":
            return True
        return False
    
    @staticmethod
    def to_32byte_hex(val):
        return Web3.toHex(Web3.toBytes(val).rjust(32, b'\0'))
   
    @staticmethod
    def load_account_from_env(account_number):
        """
        Loads Ganache accounts from .env
        :param str/int account_number: Account number to load from ganache (0 indexed)
        :return: an accounts public and private key
        """

        load_dotenv()
        index = str(account_number)
        pub_key = "ACCOUNT" + index + "_ADDRESS"
        priv_key = "ACCOUNT" + index + "_PRIVATE_KEY"

        return os.getenv(pub_key), os.getenv(priv_key)

    @staticmethod
    def load_account_from_env_v2(env_name):
        """
        Loads Ganache accounts from .env
        :param str/int account_number: Account number to load from ganache (0 indexed)
        :return: an accounts public and private key
        """

        load_dotenv()
        pub_key = env_name + "_ADDRESS"
        priv_key = env_name + "_PRIVATE_KEY"

        return os.getenv(pub_key), os.getenv(priv_key)

    @staticmethod
    def load_chain_id():
        """
        returns chain ID
        :return chain id from .env
        """

        load_dotenv()
        return int(os.getenv("CHAIN_ID"))

    @staticmethod
    def load_contract_address(contract_name):
        """
        returns contract address
        :param contract_name: name of contract. load it's address
        :return contract address from .env
        """

        load_dotenv()
        return os.getenv(contract_name)

    # ABI (Application Binary Interface), An interface for interacting with methods in a smart contract 
    @staticmethod
    def get_contract_abi(contract_name):
        """
        Returns ABI for the contract_name passed in
        :param str contract_name: name of contract we want to get ABI from
        :return: contract abi
        """

        compiled_json_path = os.path.join(ROOT_DIR, 'compiled_json/compiled_' + contract_name + '_code.json')
        with open(compiled_json_path, "r") as f:
            compiled_sol = json.load(f)
            return json.loads(
                compiled_sol["contracts"][contract_name + ".sol"][contract_name]
                ["metadata"])["output"]["abi"]

    #  Compiled bytecode of smart contract. Needed to deploy contract
    @staticmethod
    def get_contract_bytecode(contract_name):
        """
        Returns contract's bytecode. Need to deploy contract and get address
        """
        compiled_json_path = os.path.join(ROOT_DIR, 'compiled_json/compiled_' + contract_name + '_code.json')
        with open(compiled_json_path, "r") as f:
            compiled_sol = json.load(f)
            return compiled_sol["contracts"][contract_name + ".sol"][contract_name]["evm"]["bytecode"]["object"]


    @staticmethod
    def hash_and_sign_message(w3, argument_types, arguments, priv_key):
        """
        takes in data types and corresponding data. hashes the data and signs it.
        returns the hashed message and signed message

        :param web3 w3: web3 object
        :param list argument_types: types of arguments to be hashed e.g.: [uint32t, address]
        :param list arguments: arguments to be hashed e.g.: [14, <public_key>]
        :param string priv_key: private key of the user signing the message (aka calling this func.)

        :return: hashed message, signed message, error_code
        """

        if(len(argument_types) != len(arguments)):
            print("ERROR: len(argument_types) != len(arguments)")
            return None, None, -1
        
        # append data, and hash it
        base_message = Web3.solidityKeccak(argument_types, arguments)
        message = encode_defunct(primitive=base_message)

        # sign message w/ private key
        signed_message = w3.eth.account.sign_message(message, private_key=priv_key)

        return base_message, signed_message, 0

    @staticmethod
    def generate_message_validation_data(signed_message):
        """
        Takes in signed message we need to validate.
        Generates and returns sigV, sigR, sigS

        :param string signed_message: signed_message we are trying to validate

        :return: sigV, sigR, sigS, error_code
        """

        # get the signature of the signed message - convert to hex and then to bytes
        hex_signature = signed_message.signature.hex()
        sig = Web3.toBytes(hexstr=hex_signature)

        # generate and return sigV, sigR, sigS
        v, hex_r, hex_s = Web3.toInt(sig[-1]), Web3.toHex(sig[:32]), Web3.toHex(sig[32:64])
        return v, hex_r, hex_s

    @staticmethod
    def sign_transaction(w3, transaction, priv_key):
        """ 
        Takes in signed message we need to validate.
        Generates and returns sigV, sigR, sigS

        :param web3 w3: web3 object
        :param transaction transaction: transaction to sign and execute
        :param string priv_key: private key of the user signing and executing the transaction

        :return: signed_transaction, error
        """

        try:
            #  Signature 
            signed_transaction = w3.eth.account.sign_transaction(transaction, private_key=priv_key)
        except Exception as e:
            print("ERROR: Failed to sign transaction!")   
            return None, -1

        return signed_transaction, 0

    @staticmethod
    def send_transaction(w3, signed_transaction):
        """ 
        Takes in signed message we need to validate.
        Generates and returns sigV, sigR, sigS

        :param web3 w3: web3 object
        :param signed_transaction signed_transaction: signed transaction to send

        :return: tx_hash, tx_receipt, error
        """

        try:
            print("sending transaction...")
            tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

            print("waiting for transaction to complete...")
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print("ERROR: Failed to sign transaction!")   
            return None, None, -1   

        return tx_hash, tx_receipt, 0  
        
    @staticmethod
    def load_yaml(yaml_path):
        """
        Load any yaml file and return it to caller
        """
        with open(yaml_path, 'r') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print("ERROR PARSING YAML: {}", e)

            
           
       
        