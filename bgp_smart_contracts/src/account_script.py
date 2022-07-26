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

def cycle (contract_file):

    with open(r"accounts.txt", 'r') as fp:
    
        asn_numbers=[150,151,152] #Enter the ASNs you want to have running the blockchain and proxy code. Alternatively use range(start, stop[, step]) for a range of values.
        lines =[]
    
        for i, line in enumerate(fp):
            if i in asn_numbers:
                account=line.split(' ')
                os.system('python3 add_asn.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+str(account[1]))
                print('python3 add_asn.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+str(account[1]))  #add asn to smart contract #python add_asn.py <account0> <account1> <ASN1> <account1_address>
                os.system('python3 add_prefix.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+'10.'+str(account[0])+'.0.0'+' 24 '+str(account[1]))
                print('python3 add_prefix.py ACCOUNT0 '+ 'ACCOUNT'+str(account[0])+' '+ str(account[0])+' '+'10.'+str(account[0])+'.0.0'+' 24 '+str(account[1]))  #add prefix to smart contract #python add_prefix.py <account0> <account1> <ASN1> <ip1> <subnet1> <account1_address>
            elif i > 7: #enter ASN# where to stop so it doesn't keep running past your known limit.
                break
	
		
if __name__=='__main__':
    print("generating ASN Accounts on Chain")
    cycle(open('accounts.txt'))   		

#python add_asn.py <account0> <account1> <ASN1> <account1_address>
#python add_prefix.py <account0> <account1> <ASN1> <ip1> <subnet1> <account1_address>
