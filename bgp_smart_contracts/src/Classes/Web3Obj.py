from dotenv import load_dotenv
import sys
from Utils.Utils import *
from web3 import Web3

class Web3Obj():
    load_dotenv(override=True)
    w3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_RPC_URL")))
