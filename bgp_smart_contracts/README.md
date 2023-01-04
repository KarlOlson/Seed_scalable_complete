# bgp_smart_contracts


## TODO (written: 5/29/22) (updated: 9/5/22):
1) Make the below programs easier to run
    - [x] pass in "owner" and "modifier" accounts in command line
    - [x] I should be able to toggle between any of the three accounts across all python scripts instead of having to go in and change the account we're reading from in the env file. it's confusing lol
2) Implement The following
    - [x] Remove ASN 
    - [x] Remove Prefix
    - [x] Validate Prefix
    - [x] Add Advertisement
    - [x] Valdiate Advertisement 
    - [x] Partial Deployment Support - P -> NP -> P 
3) BGP Code integration
    - [x] Add Origin Validation into BGP code
    - [ ] Add Path Validation to BGP code
    - [ ] Ensure Origin/Path validation working together

# Update: 12/5/22 - Experiment for A20-Nano-Internet
1) Deploy A20-nano-internet
    - Add ASNs/prefixes (including IXs!) to blockchain (see `account_scripy.py`)
    - Add a Dummy Prefix to blockchain (`ASN199`, `10.199.0.0/24`) - Need since we need to hijack an already owned prefix. Can't be unregistered
    - Proxy by default will accept unregistered advertisements. To change, see `proxy.py` at `ACCEPT_UNREGISTERED_ADVERTISEMENTS`
2) Configure Routers so they can reach the blockchain
    - You must run: `sudo ./bgp_smart_contracts/src/scripts/a20-update-routers-for-bgp.sh`
    - ^ This updates the `ix100`, `ix101`, `3_r1`, and `3_r4` so all routers can reach the blockchain for validation
3) Everything is setup, now you can run a hijack. See next (4)
4) To hijack `10.199.0.0/24` on a random router, run:
    - `sudo ./Random_Hijack 10.199.0.0/24`
    - This will also print out which router we are running the hijack from
5) To see how many routers accepted the invalid advertisement, run:
    - `sudo ./control_plane 10.199.0.0/24`
6) Verify Result. With BGP_Chain, we expect to see 
    - 6 routers WITHOUT the hijacked route (`10.199.0.0/24`) in their routing tables
    - 1 router WITH the hijacked route (`10.199.0.0/24`) in its routing table - This should be whichever router was running the hijack (i.e. 151 or 152, etc)

# Update: 1/3/23 - Experiment for B00-mini-internet
1) Very similar to above (A20-nano-internet). Must accept unregistered advertisements!!!
2) Run `sudo ./bgp_smart_contracts/src/scripts/b00-update-routers-for-bgp`
    - updates all router configs as set by Karl. See router configs in `bgp_smart_contracts/configs/b00-mini-internet/`
3) We run into an error after we deploy b00 and set the update router configs.
    - some of the routers fail to reach the blockchain, so they cannot validate an advertisement
    - The router will send a request to the blockchain, but the request will timeout. This causes a BGP desync and the routers will disconnect
    - I don't know why this happens. I can't remember but I think Karl said that without BGP Chain, aka just vanilla bgp with the router updates, everything works fine and all the routers can reach the blockchain router. BUT, as soon as we add in BGP chain stuff, things fail on some routers.
    - This is weird because this was the same error I saw deploying with A20 initially but as soon as I added in the `ACCEPT_UNREGISTERED_ADVERTISEMENTS` flag and set to true everything worked. But for some reason that is not solving everything here. 
    - This is the last thing I got too. Did not have time to investigate deeper. - Greg


## How to Run (so far)
#### General Methods
- compile contract
- deploy contract

#### Origin Validation Methods
- add/remove ASN
- add/remove prefix
- validate prefix
- get ASN owner
- get prefix owner
- get prefixes owned by ASN

#### Path Validation Methods
- add advertisement
- validate advertisement

**Implementation done with cryptographic signings**

## Install Python Dependancies
```
python -m pip install -r requirements.txt
```

### A couple notes
The following accounts/addresses must be stored in .env
- ACCOUNT0_ADDRESS, ACCOUNT0_PRIVATE_KEY
    - The IANA account. Owner of the smart contract
- ACCOUNT1_ADDRESS, ACCOUNT1_PRIVATE_KEY
    - An AS Account (1)
- ACCOUNT2_ADDRESS, ACCOUNT2_PRIVATE_KEY
    - Another AS Account (2)

For path validation, each AS must have the contract address of all other AS's Path Validation Contracts
- Need asn_address_mapping.yaml

### Comile and deploy the smart contract
```
python compile.py <contract-name> 
# e.g. 
python compile.py IANA 
# or
python compile.py PATH_VALIDATION

python deploy.py <accountN> <contract-name>
# e.g. 
python deploy.py ACCOUNT0 PATH_VALIDATION
```

Next: 
For IANA contract deploy, 
- Copy address printed out from deploy.py into .env file

For PATH_VALIDATION contract deploy,
- Copy address printed out into the asn_address_mapping.yaml file under the apprpriate ASN

If use ACCOUNT0
- Note: these two commands will deploy from ACCOUNT0_ADDRESS in .env
- ACCOUNT0_ADDRESS becomes the owner of the contract. 
- ACCOUNT0_ADDRESS is the owner/IANA


### Add ASN to ASN<=>Address 
- this gives an ASN the ability to get assigned IP prefixes
- But an AS first needs to get added to the AS map by IANA

#### Add ASN1 to ASNMap
```
python add_asn.py <account0> <account1> <ASN1> <account1_address>
```
e.g.
```
python add_asn.py ACCOUNT0 ACCOUNT1 100 0x79bb7739B28ab9D6a846012156f5eadD0dE67361
```
- Note ensure account1_address passed in is equivalent to account1 in the .env file. (You can change this but they way it's set up now, you have make sure they are equivalent)

#### Add ASN2 to ASNMap
- Now update add_prefix.py. And read in account2 data instead of account 1. This will allow us to add an ASN for account2
```
python add_asn.py <account0> <account2> <ASN2> <account2_address>
```
e.g.
```
python add_asn.py ACCOUNT0 ACCOUNT2 200 0xcF0A72EFd623c7aC7f9886213daFd93a2D62832
```

### Add Prefix! IP/Subnet<=> ASN
-Note: IANA initially owns all IP space. And only IANA can allocate that space to someone else. unless that space is owned by someone else

#### Add a prefix for ASN1 (account1_address)
```
python add_prefix.py <account0> <account1> <ASN1> <ip1> <subnet1> <account1_address>
```
Example: 
```python add_prefix.py ACCOUNT0 ACCOUNT1 100 100.0.100.0 24 0x79bb7739B28ab9D6a846012156f5eadD0dE67361 ```
- Note same issue as above, acct1 in .env == <account1_address>

#### Add a prefix for ASN2 (account2_address)
- Now update add_prefix.py. And read in account2 data instead of account 1. This will allow us to add a prefix for account2
```
python add_prefix.py <ASN2> <ip2> <subnet> <account2_address>
```
Example: 
```python add_prefix.py ACCOUNT0 ACCOUNT2 200 200.0.200.0 24 0xcF0A72EFd623c7aC7f9886213daFd93a2D628327```
- Note same issue as above, acct2 in .env == <account2_address>


### Tests
- These should all fail
```
python add_prefix.py <account0> <account2> <ASN2> <ip2> <subnet> <account1_address>
python add_prefix.py <account0> <account2> <ASN1> <ip2> <subnet> <account1_address>
```

- These should succeed
```
python add_prefix.py <account0> <account2> <ASN2> <ip3> <subnet3> <account2_address>
python add_prefix.py <account0> <account2> <ASN2> <ip3> <subnet5> <account2_address>
```

### Transfer Prefix From ASN1 to ASN2
- Now, let's give ASN2 ASN1's IP/mask
    - this may occur if ASN2 is a customer of ASN1 and ASN1 needs to give IP space to ASN2
- we're going to use `add_prefix.py` here
- this will transfer ASN1's IP/mask to ASN2. 

```
python add_prefix.py <account1> <account2> <ASN2> <ip1> <subnet1> <account2_address>

```
Example:
```
python add_prefix.py ACCOUNT1 ACCOUNT2 200 100.0.100.0 24 0xcF0A72EFd623c7aC7f9886213daFd93a2D628327
```
- Flow: ASN2 says they want to now own ip1/subnet1, so they hash and sign the data and "send" it to acct1.
    - Not really sent here. It's just passed to acct1 in the python file
- ASN1 takes the signed message from ASN2, generates the sigV, sigR, sigS, and then calls `prefix_addPrefix()` in the smart contract.
- the smart contract will 
    - validate that ASN2 signed the message saying it want ASN1's IP/subnet. 
    - ensure ASN1 is the one calling `prefix_addPrefix()`.
        - This is important because we don't want someone else to be able to call `prefix_addPrefix()` and transfer ASN1's IP/subnet away to someone else.

### Valdiate Prefix
```
python validate_prefix.py <account1> <ip2> <subnet2> <ASN2>
```

Example:
```
python validate_prefix.py ACCOUNT1 100.0.100.0 24 200
```

## Path Validation
- BGPSEC implementation without all the heavyweight signing
- Each AS has its own advertisement contract!
  - Owner of contract can write to it but anybody can read from it
  - Contract contains:
    - Prefix and the ASN of the next Hop

### Env Files examples
#### .env
```
GANACHE_RPC_URL=http://127.0.0.1:7545
CHAIN_ID = 1337

ACCOUNT0_ADDRESS=<pubkey>
ACCOUNT0_PRIVATE_KEY=<private-key>

ACCOUNT1_ADDRESS=<pubkey>
ACCOUNT1_PRIVATE_KEY=<private-key>

ACCOUNT2_ADDRESS=<pubkey>
ACCOUNT2_PRIVATE_KEY=<private-key>

ACCOUNT3_ADDRESS=<pubkey>
ACCOUNT3_PRIVATE_KEY=<private-key>

ACCOUNT4_ADDRESS=<pubkey>
ACCOUNT4_PRIVATE_KEY=<private-key>

ACCOUNT5_ADDRESS=<pubkey>
ACCOUNT5_PRIVATE_KEY=<private-key>

ACCOUNT6_ADDRESS=<pubkey>
ACCOUNT6_PRIVATE_KEY=<private-key>


IANA_CONTRACT_ADDRESS=<IANA-contract-address>

ACCOUNT1_PATH_VALIDATION_CONTRACT=<account1-path-validation-contract-address>
ACCOUNT2_PATH_VALIDATION_CONTRACT=<account2-path-validation-contract-address>
ACCOUNT3_PATH_VALIDATION_CONTRACT=<account3-path-validation-contract-address>
ACCOUNT4_PATH_VALIDATION_CONTRACT=<account4-path-validation-contract-address>
ACCOUNT5_PATH_VALIDATION_CONTRACT=<account5-path-validation-contract-address>
ACCOUNT6_PATH_VALIDATION_CONTRACT=<account6-path-validation-contract-address>
```

#### asn_address_mapping.yaml example
```
---
asn_0:
  validation_contract: <account0-path-validation-contract-address>
asn_100:
  validation_contract: <account1-path-validation-contract-address>
asn_200:
  validation_contract: <account2-path-validation-contract-address>
asn_300:
  validation_contract: <account3-path-validation-contract-address>
asn_400:
  validation_contract: <account4-path-validation-contract-address>
asn_500:
  validation_contract: <account5-path-validation-contract-address>
asn_600:
  validation_contract: <account6-path-validation-contract-address>
```


### Example
ASNs in order sending an update message for 10.0.20.0/24
- Path: 100 -> 200 -> 300 -> 400 -> 500 -> 600 

A1: 10.0.20.0/24 : 100
  - writes to 100's own advertisement contract {10.0.20.0/24, nextHop = 200}
  - sends A1 to 200

A2: 10.0.20.0/24 : 200, 100
  - checks there is a 10.0.20.0/24 with next hop 200 in 100's advertisement contract
  - writes to 200's own advertisement contract {10.0.20.0/2, nextHop = 300}
  - sends A2 to 300

A3: 10.0.20.0/24 : 300, 200, 100
  - checks there is a 10.0.20.0/24 with next hop 300 in 200's advertisement contract
  - checks there is a 10.0.20.0/24 with next hop 200 in 100's advertisement contract
  - writes to 300's own advertisement contract {10.0.20.0/2, nextHop = 400}
  - sends A3 to 400...

### Add Announcement Example 1
Path of advertisements for example:
- Path: 100 -> 200 -> 300 -> 400 -> 500 -> 600 
  
Format:
```
python add_advertisement.py <account> <ip> <subnet> <nextHopASN>
```

Example:
```
python add_advertisement.py ACCOUNT1 10.0.20.0 24 200
python add_advertisement.py ACCOUNT2 10.0.20.0 24 300
python add_advertisement.py ACCOUNT3 10.0.20.0 24 400
python add_advertisement.py ACCOUNT4 10.0.20.0 24 500
python add_advertisement.py ACCOUNT5 10.0.20.0 24 600
```

### Validate Advertisement Example 1

```
python validate_advertisement.py <account2> <ip> <subnet> <myASN> <Received advertisement's AS_PATH>
```

Example - Account 2 (ASN200) needs to validate that ASN100 has said for this ip/prefix it is sending it to ASN200
```
python validate_advertisement.py ACCOUNT2 10.0.20.0 24 200 100
```

Example - Account 3 (ASN300) needs to check down path that path 2->3 exists and 1->2 exists
```
python validate_advertisement.py ACCOUNT3 10.0.20.0 24 300 200 100
```

Example - Account 4 (ASN 400) checks down path that paths 3->4, 2->3, and 1->2 exist
```
python validate_advertisement.py ACCOUNT4 10.0.20.0 24 400 300 200 100
```
Example output for the last command:
```
AS_PATH Validation Results for: "10.0.20.0/24 : 300, 200, 100"
ASN 300 -> ASN 400 hop in AS_PATH is: valdiateAdvertisementResult.advertisementVALID
ASN 200 -> ASN 300 hop in AS_PATH is: valdiateAdvertisementResult.advertisementVALID
ASN 100 -> ASN 200 hop in AS_PATH is: valdiateAdvertisementResult.advertisementVALID
```

Example of a bad path:
- Account 5 (ASN 500) gets an advertisement: `10.0.20.0/24 : 300 200 100`
- Note that ASN300 never said they were sending to ASN500! So this should fail. Let's try:

```
python validate_advertisement.py ACCOUNT5 10.0.20.0 24 500 300 200 100
```
Result:
```
AS_PATH Validation Results for: "10.0.20.0/24 : 300, 200, 100"
ASN 300 -> ASN 500 hop in AS_PATH is: valdiateAdvertisementResult.advertisementINVALID
ASN 200 -> ASN 300 hop in AS_PATH is: valdiateAdvertisementResult.advertisementVALID
ASN 100 -> ASN 200 hop in AS_PATH is: valdiateAdvertisementResult.advertisementVALID
```
^ so this path 100 -> 200 -> 300 -> 500 is invalid!


### Add Announcement Example 2
Path of advertisements for example:
- Path: 100 -> 200 -> 300 -> 400 -> 500 -> 600 
  
Format:
```
python add_advertisement.py <account> <ip> <subnet> <nextHopASN>
```

Example:
```
python add_advertisement.py ACCOUNT1 10.0.20.0 24 200
python add_advertisement.py ACCOUNT2 10.0.20.0 24 300
python add_advertisement.py ACCOUNT3 10.0.20.0 24 400
# skip announcement from 400 to 500. 
python add_advertisement.py ACCOUNT5 10.0.20.0 24 600
```


### Validate Advertisement Example 2 - Partial Deployment

```
python validate_advertisement.py <account2> <ip> <subnet> <myASN> <Received advertisement's AS_PATH>
```

#### Example 2: Non participant in path
Account 6 (ASN600) needs to validate that the entire 100 -> 200 -> 300 -> 400 -> 500 -> 600 is valid
```
python validate_advertisement.py ACCOUNT6 10.0.20.0 24 600 500 400 300 200 10
```
Output:
```
All ASNs in AS_PATH are participants
AS_PATH Validation Results for: "10.0.20.0/24 : 500, 400, 300, 200, 100"
ASN 500 -> ASN 600 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 400 -> ASN 500 hop in AS_PATH is: validateAdvertisementResult.advertisementINVALID
ASN 300 -> ASN 400 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 200 -> ASN 300 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 100 -> ASN 200 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
Entire Path is: validatePathResult.pathINVALID
Invalid advertisements: ['400->500']
```
Here ^ we have an invalid path. since ACCOUNT4 (ASN400) never said it was announcing to ASN500

#### Example 2: Partial Deployment Valid path
Account 6 (ASN600) needs to validate that the entire 100 -> 200 -> 300 -> 400 -> 500 -> 600 is valid
- In this case, ASN400 will not participate. To simulate this, comment out the folling lines in `asn_address_mapping.yaml`:
```
asn_400:
  validation_contract: <account4-path-validation-contract-address>
```
- Now, when we look for ASN 400's contract, it won't exist, indicating we don't know it or ASN400 is a non participant

Run:
```
python validate_advertisement.py ACCOUNT6 10.0.20.0 24 600 500 400 300 200 100
```
Output:
```
P -> NP -> P found for: (300,400,500)
AS_PATH Validation Results for: "10.0.20.0/24 : 500, 400, 300, 200, 100"
ASN 500 -> ASN 600 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 400 -> ASN 500 hop in AS_PATH is: validateAdvertisementResult.nonParticipantSource
ASN 300 -> ASN 400 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 200 -> ASN 300 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
ASN 100 -> ASN 200 hop in AS_PATH is: validateAdvertisementResult.advertisementVALID
Entire Path is: validatePathResult.pathPnpVALID
Non participants: [400]
```
Result:
- Here ^ we have a non partipant (NP) surrounded by 2 participating ASNs (P). 
- If we assume no two ASNs are scheming together, this should be a valid advertisement. 
  - ASN500 checks that ASN300 sent to ASN400. And ASN500 got the message from ASN400. 
  
Note: if there are two or more non participants in a row, then the path validation should fail.



------------------------------------------

## Notes/Thoughts
prefix_validatePrefix(addvertisedIp, advertisedMask, advertisedASN)
- all we're checking here is that an ASN and IP/subnet are matched together in the contract.
- we do not check that the advertisement received was actually sent by the ASN. 
    - this would require signing BGP updates/announcements. and adding signature in the BGP payload or something.
- 


Check
- who owns this. 
    - if ASN<=>IP/mask binding returns 0, then IANA owns it. in that case, caller of this function must be IANA? (let's start here)
    - if ASN<=>IP/mask binding returns some address, we need to figure out who that is.
        - we may need to make this a transfer_prefix() function or something. Need both current owner and new owner to sign and approve.
        - in fact, we could just ensure that the caller of this function (msg.sender) is the current owner of the IP/mask.
    - so it would just need to be an if statement. 
        - if current owner is 0,
            - Then this function must be called by someone in the owner's list (aka iana)
        - if current owner is 0xAFD14...A398F, then they must be the ones calling this function. 
    - essentially enforced a top down approach. current owner must delegate to new owner. 
    - but then new owner and current owner must both agree or something when to give up the space. or something. idk
