import os
import json
import sys
from Config import ROOT_DIR
from web3 import Web3

# python compile.py PATH_VALIDATION
# python compile.py IANA
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please enter a contract to contract (e.g. IANA, PATH_VALIDATION, etc")
        sys.exit(-1)

    contract = str(sys.argv[1])

    #  compile  solidity
    # https://github.com/iamdefinitelyahuman/py-solc-x
    from solcx import compile_standard, install_solc

    contract_path = os.path.join(ROOT_DIR, '../contracts/' + contract + '.sol')
    with open(contract_path, 'r', encoding='utf-8') as f:
        contract_file = f.read()


    #  download 0.8.0 Version of Solidity compiler 
    install_solc('0.8.0')

    #  compile Solidity
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            # Solidity file 
            "sources": {contract + ".sol": {"content": contract_file}},
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

    compiled_json_path = os.path.join(ROOT_DIR, 'compiled_json/compiled_' + contract + '_code.json')
    with open(compiled_json_path, 'w') as f:
        json.dump(compiled_sol, f)