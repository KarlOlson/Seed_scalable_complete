import os
import json
from web3 import Web3

#  compile  solidity
# https://github.com/iamdefinitelyahuman/py-solc-x
from solcx import compile_standard, install_solc

with open('../contracts/IANA.sol', 'r', encoding='utf-8') as f:
    iana_file = f.read()

#  download 0.8.0 Version of Solidity compiler 
install_solc('0.8.0')

#  compile Solidity
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        # Solidity file 
        "sources": {"IANA.sol": {"content": iana_file}},
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
with open('compiled_code.json', 'w') as f:
    json.dump(compiled_sol, f)