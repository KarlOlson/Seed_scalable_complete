from dotenv import load_dotenv
import sys
from Utils.Utils import *
from Classes.Web3Obj import Web3Obj

# in an ideal world, i think we should have: contract, transaction, tx_sender, msg_signer objects
class Transaction():
    def __init__(self, contract_name, contract_address_env=None, address_from_config=None):
        load_dotenv()
        self.w3 = Web3Obj.w3
        self.chain_id = Utils.load_chain_id()
        self.abi = Utils.get_contract_abi(contract_name) # ex: IANA
        
        if contract_address_env and address_from_config: #contract address from yaml config
            self.contract_address = contract_address_env
            self.iana = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        elif contract_address_env: # contract address is in env
            self.contract_address = Utils.load_contract_address(contract_address_env) # ex: IANA_CONTRACT_ADDRESS
            if not self.contract_address:
                print("ERROR: contract with name: " + contract_address_env + " not found in .env. Exiting...")
                sys.exit(-1)
            self.iana = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        else:
            # bytecode of contract for deploy
            self.bytecode = Utils.get_contract_bytecode(contract_name)
            self.iana = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)


        self.tx_sender_pub_key = None
        self.tx_sender_priv_key = None

        #signature validation data
        self.sigV = None
        self.sigR = None
        self.sigS = None

    def set_tx_sender_pub_key(self, pub_key):
        self.tx_sender_pub_key = pub_key

    def set_tx_sender_priv_key(self, priv_key):
        self.tx_sender_priv_key = priv_key

    def sign_transaction(self, transaction):
        return Utils.sign_transaction(self.w3, transaction, self.tx_sender_priv_key)

    def execute_transaction(self, signed_transaction):
        return Utils.send_transaction(self.w3, signed_transaction)

    def sign_and_execute_transaction(self, transaction):
        tx_signed, err = self.sign_transaction(transaction)
        if err:
            return None, None, TxErrorType.FailedToSignTx
        tx_hash, tx_receipt, err = self.execute_transaction(tx_signed)
        if err:
            return None, None, TxErrorType.FailedToExecuteTx

        return tx_hash, tx_receipt, TxErrorType.OK

    def set_signature_validation_data(self, _sigV, _sigR, _sigS):
        self.sigV = _sigV
        self.sigR = _sigR
        self.sigS = _sigS


    ############## CONTRACT TRANSACTIONS ################
    def deploy_smart_contract(self, tx_sender_nonce):
        """
        Deploy smart contract  -> Creates transaction
        """
        transaction = self.iana.constructor().buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_addASN(self, tx_sender_nonce, inASN, inAddress):
        """
        Add ASN to contract
        """
        transaction = self.iana.functions.IANA_addASN(inASN, inAddress, self.sigV, self.sigR, self.sigS).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_removeASN(self, tx_sender_nonce, inASN, inAddress):
        """
        Remove ASN from contract, return prefixes to IANA
        """
        transaction = self.iana.functions.IANA_removeASN(inASN, inAddress, self.sigV, self.sigR, self.sigS).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_addPrefix(self, tx_sender_nonce, inIP, inSubnet, inASN):
        """
        Add Prefix<=>ASN binding
        """
        transaction = self.iana.functions.prefix_addPrefix(int(inIP), inSubnet, inASN, self.sigV, self.sigR, self.sigS).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_removePrefix(self, tx_sender_nonce, inIP, inSubnet):
        """
        Remove Prefix<=>ASN binding, return prefix to IANA
        """
        transaction = self.iana.functions.prefix_removePrefix(inIP, inSubnet).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_getASNOwner(self, inASN):
        """
        Return owning address of ASN. 
        """
        return self.iana.functions.IANA_getASNOwner(inASN).call()

    def sc_getPrefixOwner(self, inIP, inSubnet):
        """
        Return the owner of a specific prefix
        """
        return self.iana.functions.getPrefixOwner(inIP, inSubnet).call()

    def sc_getAllPrefixesOwnedByASN(self, inASN):
        """
        Return all prefixes owned by the ASN
        """
        return self.iana.functions.getAllPrefixesOwnedByASN(inASN).call()

    def sc_validatePrefix(self, inIP, inSubnet, inASN):
        """
        Returns if prefix<=>ASN binding is valid
        """
        return validatePrefixResult(self.iana.functions.prefix_validatePrefix(inIP, inSubnet, inASN).call())

    def sc_addAdvertisementToMyContract(self, tx_sender_nonce, inIp, inSubnet, inNextHop):
        """
        Add an advertisement to my own advertisement contract
        """
        transaction = self.iana.functions.addAdvertisement(inIp, inSubnet, inNextHop).buildTransaction({
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
            "from": self.tx_sender_pub_key,
            "nonce": tx_sender_nonce
        })
        return transaction

    def sc_validateAdvertisement(self, inIp, inSubnet, inPrevHop):
        """
        Validate an advertisement received from downstream AS.
        """
        return validateAdvertisementResult(self.iana.functions.validateAdvertisement(inIp, inSubnet, inPrevHop).call())