from compile import *
from compile_recover import *
from dotenv import load_dotenv
import sys
from utils.utils import *
from eth_account.messages import encode_defunct, _hash_eip191_message

def to_32byte_hex(val):
    return Web3.toHex(Web3.toBytes(val).rjust(32, b'\0'))

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_RPC_URL")))
chain_id = 1337

my_address = os.getenv("ACCOUNT_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")

abi = json.loads(
    compiled_sol["contracts"]["IANA.sol"]["IANA"]["metadata"]
    )["output"]["abi"]

#  call deploy.py Will get contract_address
contract_address = os.getenv("IANA_CONTRACT_ADDRESS")
iana = w3.eth.contract(address=contract_address, abi=abi)

base_message = Web3.soliditySha3(['uint32', 'address'], [13, my_address])
print("msg from solidity sha: " + str(base_message))
message = encode_defunct(primitive=base_message)
signed_message = w3.eth.account.sign_message(message, private_key=private_key)
print("(base_message, messagehash): " + str(base_message) + ", " + str(signed_message.messageHash))

base_message_2, message_hash_2 = iana.functions.IANA_getSignatureMessageTest(13, my_address).call()

print("(base_message_2, messagehash_2): " + str(base_message_2) + ", " + str(message_hash_2))

print(base_message == base_message_2)
print(signed_message.messageHash == message_hash_2 )

######################################################
####################################################

"""
TODO: UNCOMMENT ALL BELOW (HIGHLIGHT AND COMMAND /)
"""
msg = "I♥SF"
message = encode_defunct(text=msg)
signed_message = w3.eth.account.sign_message(message, private_key=private_key)
print(signed_message)


message = encode_defunct(text="I♥SF")
out = w3.eth.account.recover_message(message, signature=signed_message.signature)
print(out)

message_hash = signed_message.messageHash
signature = signed_message.signature
out = w3.eth.account.recoverHash(message_hash, signature=signature)
print(out)

# THIS is case, where we have prodiced signed_message locally. THis prepares it for solidity
# so if a non-owner wanted to call a function that required some signature?
# Unclear if r and s need to be diff format for solidity
ec_recover_args = (msghash, v, r, s) = (
    Web3.toHex(signed_message.messageHash),
    signed_message.v,
    to_32byte_hex(signed_message.r),
    to_32byte_hex(signed_message.s),
)
print(ec_recover_args)

print("---------------------------")

# THIS is case, where we have received a message and a signature encoded to hex.
# This prepares data for solidity
# So i think this is like IANA receiving the data from a user to call a owners only function
hex_message = '0x49e299a55346' #idk what this is
hex_signature = signed_message.signature.hex()

message = encode_defunct(hexstr=hex_message)

message_hash = _hash_eip191_message(message)
hex_message_hash = Web3.toHex(message_hash)

sig = Web3.toBytes(hexstr=hex_signature)
v, hex_r, hex_s = Web3.toInt(sig[-1]), Web3.toHex(sig[:32]), Web3.toHex(sig[32:64])

ec_recover_args = (hex_message_hash, v, hex_r, hex_s)
print(ec_recover_args)


# print(ec_recover_args[0])
# print(type(ec_recover_args[0]))




# ABI (Application Binary Interface), An interface for interacting with methods in a smart contract 
abi = json.loads(
    compiled_recover_sol["contracts"]["Recover.sol"]["Recover"]["metadata"]
    )["output"]["abi"]

#  call deploy.py Will get contract_address
contract_address = os.getenv("RECOVER_CONTRACT_ADDRESS")

#  Instantiate the contract object 
recover = w3.eth.contract(address=contract_address, abi=abi)

# print(type(ec_recover_args[0]), type(ec_recover_args[1]), type(ec_recover_args[2]), type(ec_recover_args[3]) )
addr = recover.functions.ecr(ec_recover_args[0], ec_recover_args[1], ec_recover_args[2], ec_recover_args[3]).call()

print(addr)