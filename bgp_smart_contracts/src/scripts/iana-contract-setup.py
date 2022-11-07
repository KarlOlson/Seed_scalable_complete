import sys
toimport = __file__.replace("scripts/iana-contract-setup.py","")
sys.path.insert(0, toimport)
from Classes.Contract import Contract


def run(IANA_account_number):
    contract = Contract("IANA")
    contract.compile()
    contract.deploy(IANA_account_number)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error! Please enter the account number for IANA (e.g. 0) --> python iana-contract-setup.py 0")
        sys.exit(-1)

    IANA_account_number = int(sys.argv[1])
    run(IANA_account_number)