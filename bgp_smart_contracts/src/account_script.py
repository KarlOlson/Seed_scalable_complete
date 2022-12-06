#!/usr/bin/python3.8                                                                                           
#To Run:
#Edit Line 14 to capture the ASN values that will be participating in your network.
#Edit Line 25 to set a break point so the script does not cycle through entire pre-defined accounts.txt list (Currently accounts.txt defines 200 default accounts).
#Make sure Ganache chain is running on one of the platforms (usually 'ix100' unless you have defined separately) by running: $ ganache -a 200 -p 8545 -h 10.100.0.100 --deterministic
#Run -> python3 account_script.py  from any host router to deploy accounts to chain.

from Classes.Account import Account
from Utils.Utils import *
from ipaddress import IPv4Address
import os, sys

hijack_account = 199 #enter ASN# of the dummy hijack account. prefix: 10.199.0.0/24, ASN: 199 

#def cycle (contract_file):
def cycle():
    with open("/bgp_smart_contracts/src/accounts.txt", 'r') as fp:
    
        n=len(sys.argv[1])
        a=sys.argv[1][1:n-1]
        a=a.split(',')
        asn_numbers = [int(i) for i in a] #Enter the ASNs you want to have running the blockchain and proxy code. Alternatively use range(start, stop[, step]) for a range of values.
    
        print("asn_numbers: " +  str(asn_numbers))
        print("adding dummy hijack account: " + str(hijack_account))
        asn_numbers.append(hijack_account)

        for i, line in enumerate(fp):
            if i in asn_numbers:
                account=line.split(' ')
                os.system('python3 /bgp_smart_contracts/src/add_asn.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+str(account[1]))
                print('python3 /bgp_smart_contracts/src/add_asn.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+str(account[1]), flush=True)  #add asn to smart contract #python add_asn.py <account0> <account1> <ASN1> <account1_address>
                os.system('python3 /bgp_smart_contracts/src/add_prefix.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+'10.'+str(account[0])+'.0.0'+' 24 '+str(account[1]))
                print('python3 /bgp_smart_contracts/src/add_prefix.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+'10.'+str(account[0])+'.0.0'+' 24 '+str(account[1]), flush=True)  #add prefix to smart contract #python add_prefix.py <account0> <account1> <ASN1> <ip1> <subnet1> <account1_address>
            # elif i > 153: #enter ASN# where to stop so it doesn't keep running past your known limit.
            #     break
	
		
if __name__=='__main__':
    print("generating ASN Accounts on Chain")
    #cycle(open('accounts.txt'))
    cycle()
    print("ASN accounts and prefix's added to chain")

#python add_asn.py <account0> <account1> <ASN1> <account1_address>
#python add_prefix.py <account0> <account1> <ASN1> <ip1> <subnet1> <account1_address>
