import sys
toimport = __file__.replace("scripts/path-validation-setup.py","")
sys.path.insert(0, toimport)
from Classes.Contract import Contract


def run(ASN):
    contract = Contract("PATH_VALIDATION")
    contract.compile()
    contract.deploy(ASN)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error! Please enter the account number for this router (e.g. 150) --> python path-validation-setup.py <asn>")
        sys.exit(-1)

    print("ASN passed into path-validation-setup: " + str(sys.argv[1]))

    ASN = int(sys.argv[1])
    run(ASN)