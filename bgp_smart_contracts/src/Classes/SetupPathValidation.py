from Classes.Contract import Contract
import sys

class SetupPathValidation:
    def __init__(self, _ASN):
        print("init SetupPathValidation")
        self.ASN = _ASN
        self.tx_sender_name = "ACCOUNT"+str(self.ASN)
        self.contract = None

    def compile_contract(self):
        print("compiling pathvalidation contract for AS: " + str(self.ASN))
        self.contract = Contract("PATH_VALIDATION")
        self.contract.compile()

    def deploy_contract(self):
        print("deploying pathvalidation contract for AS: " + str(self.ASN))

        if self.contract == None:
            print("No contract object set. Did you forget to compile your contract?")
            sys.exit(-1)
        
        self.contract.deploy(self.ASN)


