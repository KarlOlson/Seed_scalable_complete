pragma solidity ^0.8.0;

contract IANA {

    struct prefix{
        uint32 ip;
        uint8 mask;
        //could add here the ASN owner of this prefix
        //could add here the ASN that allocated this prefix to the current ASN owner
    }

    /// Enum of the validatePrefix() return types
    /// @param prefixValid VALID: ip/mask and ASN all match. Valid advertisment
    /// @param prefixNotRegistered INVALID: ip/mask advertised is owned by IANA - aka not registered. Could be not registered or non participant
    /// @param prefixOwnersDoNotMatch INVALID: The ASN that owns the advertised ip/mask does not match the ASN that advertised the ip/mask. 
    enum validatePrefixResult {
        prefixValid,
        prefixNotRegistered, 
        prefixOwnersDoNotMatch
    }
    
    // All the people who can change the function pointers
    mapping (address => bool) public ownerMap;
    // The associative mapping that maps ASNs to their owner's public key.
    mapping (uint32 => address) public ASNMap;

    // ip => masks => ASN
    mapping (uint32 => mapping(uint8 => uint32)) public PrefixASNMap;
    
    //ASN => List of ip/mask Map
    mapping (uint32 => prefix[]) public ASNPrefixMap;

    /// Simple modifier to ensure that only owners can make changes
    modifier onlyOwners {
        require(ownerMap[msg.sender] == true);
        _;
    }

    constructor() public {
        // Automatically add the contract creator as an owner
        ownerMap[msg.sender] = true;

        // Mark that the root is owned by a dummy address.
        ASNMap[0] = address(0);
        // Build up the prefix for the root prefix
        PrefixASNMap[0][0] = 0;

    }

    /// Adds the specified prefix to the prefix table. Must be done by the owner of the prefixes containing
    /// AS and must include the signature of the message returned by IANA_getPrefixSignatureMessage for the new AS.
    /// @param ip The IP address of the prefix to add
    /// @param mask The number of bits in the netmask of the prefix to add
    /// @param newOwnerAS The AS number to associate with the new prefix to.
    function prefix_addPrefix(uint32 ip, uint8 mask, uint32 newOwnerAS, uint8 sigV, bytes32 sigR, bytes32 sigS) public {
        // Only valid subnet masks
        require (mask <= 32);
        // Get the ASN's owner
        address newOwnerAddress = ASNMap[newOwnerAS];

        // The owning ASN must exist
        require (newOwnerAddress != address(0), "ASN not added to ASNMap");

        // check we haven't already added this ip/mask <=> ASN binding
        require(PrefixASNMap[ip][mask] != newOwnerAS, "ip/mask <=> ASN binding already exists");

        // The owning ASN must have signed the message.
        require(ecrecover(IANA_getPrefixSignatureMessage(ip, mask, newOwnerAS, newOwnerAddress), sigV, sigR, sigS) == newOwnerAddress, "ERROR: ecrecover failed");

        //create the new prefix struct and populate it
        prefix memory newPrefix;
        newPrefix.ip = ip;
        newPrefix.mask = mask;

        // check who currently owns this ip/mask combo. 
        //If 0 owns, that means IANA owns it. Ensure IANA is calling this function.
        if (PrefixASNMap[ip][mask] == 0) {
            require (ownerMap[msg.sender] == true, "IANA currently owns IP/mask, IANA MUST call this function to allocate IP/mask to another entity");
        } 
        else {
            // If IANA does not own it, then someone else owns it. 
            // Ensure the caller of this function owns the IP/mask.
            // The caller MUST call this function to transfer IP/mask to another ASN
            uint32 currentOwnerASN = PrefixASNMap[ip][mask];
            require (msg.sender == ASNMap[currentOwnerASN]);

            //remove ownership of prefix from the old owner
            prefix[] memory prefixes = ASNPrefixMap[currentOwnerASN];
            //loop through all prefixes owned by the currentOwnerASN
            //Find the prefix that we're trying to give to the newOwnerAS
            //Delete the prefix from the currentOwnerASN ASNPrefixMap
            for(uint32 i = 0; i < prefixes.length; i++) {
                if(helper_prefixesEqual(prefixes[i], newPrefix)) {
                    helper_removePrefixASNPrefixMap(currentOwnerASN, i);
                }
            }
        }
        
        //Update prefix<=>ASN map
        PrefixASNMap[newPrefix.ip][newPrefix.mask] = newOwnerAS;

        //Update ASN<=>prefix map
        ASNPrefixMap[newOwnerAS].push(newPrefix);

    }

    //remove prefix from ASN and return to IANA
    /// @param ip The IP address of the prefix to remove
    /// @param mask The number of bits in the netmask of the prefix to remove
    function prefix_removePrefix(uint32 ip, uint8 mask) public {
        // Only valid subnet masks
        require (mask <= 32);

        uint32 currentOwnerASN = getPrefixOwner(ip, mask);
        require(currentOwnerASN != 0, "ERROR: prefix owned by IANA, can't remove");
        
        address owningASAddress = ASNMap[currentOwnerASN];

        // Require that the public address calling us owns the prefix
        // (aka you can't remove a prefix that you don't own)
        require (msg.sender == owningASAddress, "ERROR: Caller of method does not own the prefix they're trying to remove!");

        //create the prefix struct and populate it
        prefix memory prefixToRemove;
        prefixToRemove.ip = ip;
        prefixToRemove.mask = mask;

        //remove ownership of prefix from the old owner
        prefix[] memory prefixes = ASNPrefixMap[currentOwnerASN];
        //loop through all prefixes owned by the currentOwnerASN
        //Find the prefix that we're trying to remove
        //Delete the prefix from the currentOwnerASN ASNPrefixMap
        //This will remove ownership from currentOwnerASN
        for(uint32 i = 0; i < prefixes.length; i++) {
            if(helper_prefixesEqual(prefixes[i], prefixToRemove)) {
                helper_removePrefixASNPrefixMap(currentOwnerASN, i);
            }
        }

        PrefixASNMap[ip][mask] = 0; //Set ownership of prefix passed in to IANA

    }


    /// Determines if a given prefix is owned by the advertisedAS.
    /// all we're checking here is that an ASN and IP/subnet are matched together in the contract.
    /// we do not check that the advertisement received was actually sent by the ASN. 
    /// this would require signing BGP updates/announcements. and adding signature in the BGP payload or something.
    /// NOTE: we don't use "require" here, so spammers could advertise false prefixes all the time \
    /// which would charge other nodes to keep validating prefixes
    /// @param advertisedIp The IP address of the prefix to be checked.
    /// @param advertisedMask The mask of the prefix to be checked.
    /// @param advertisedASN the ASN of the AS we're checking the prefix against
    /// @return validatePrefixResult enum indicating VALID advertisement or INVALID advertisement. INVALID has two types (1. owned by IANA/not registered, 2. ASNs do not match)
    function prefix_validatePrefix(uint32 advertisedIp, uint8 advertisedMask, uint32 advertisedASN) public view returns (validatePrefixResult) {
        require (advertisedMask <= 32, "Invalid mask");

        //check that the input IP/mask is owned by the ASN advertising the IP/mask
        uint32 trueOwnerAS = PrefixASNMap[advertisedIp][advertisedMask];
        
        // ensure IP/mask mapping to ASN exists. will be 0 if IP/mask has not been assigned and is owned by IANA
        // If trueOwnerAS == 0, advertised prefix owned by IANA. Invalid advertisement
        // Could be not registered or non participant sending the advertisement
        if (trueOwnerAS == 0) {
            return validatePrefixResult.prefixNotRegistered;
        }

        // Ensure the ASN from advertisement and ASN stored in PrefixASNMap are the same
        // If not, this is an invalid advertisement
        if (advertisedASN != trueOwnerAS) {
            return validatePrefixResult.prefixOwnersDoNotMatch;
        }       

        return validatePrefixResult.prefixValid;
    }

    /// Generates the message text to be signed for add authentication.
    /// @param ASN The ASN to be added
    /// @param ASNOwner The public key of the new owner.
    /// @return bytes32 The keccak hash of abi.encodePacked(ASN,ASNOwner).
    function IANA_getPrefixSignatureMessage(uint32 ip, uint8 mask, uint32 ASN, address ASNOwner) pure public returns(bytes32) {
        bytes32 base_message = keccak256(abi.encodePacked(ip, mask, ASN, ASNOwner));
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", base_message));
    }
    
    /// Returns the owner's address for the given ASN, or 0 if no one owns the ASN.
    /// @param ASN The ASN whose owner is to be returned
    /// @return address The address of the owner.
    function IANA_getASNOwner(uint32 ASN) public view returns (address) {
        return ASNMap[ASN];
    }
    
    /// Generates the message text to be signed for add authentication.
    /// @param ASN The ASN to be added
    /// @param ASNOwner The public key of the new owner.
    /// @return bytes32 The sha256 hash of abi.encodePacked(ASN,ASNOwner).
    function IANA_getSignatureMessage(uint32 ASN, address ASNOwner) pure public returns(bytes32) {
        bytes32 base_message = keccak256(abi.encodePacked(ASN,ASNOwner));
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", base_message));
    }

    /// Adds an additional ASN to the ASN list. The operation has to include a signature
    /// from the ASN owner signing keccak256(abi.encodePacked(ASN,ASNOwner)) which can be
    /// generated by calling IANA_getSignatureMessage()
    /// @param ASN The ASN to be added
    /// @param ASNOwner The public key of the new owner.
    function IANA_addASN(uint32 ASN, address ASNOwner, uint8 sigV, bytes32 sigR, bytes32 sigS) public onlyOwners {
        // It must be signed by the new ASNOwner. We don't have to check for the IANA owner because
        // the onlyOwners routine does that for us.

        require(ecrecover(IANA_getSignatureMessage(ASN, ASNOwner), sigV, sigR, sigS) == ASNOwner);
        require(ASN != 0);
        require(ASNMap[ASN] == address(0), "ASN<=>ASNOwner mapping already added");
        
        // At this point, we have two party agreement on ASN ownership. Add it to the ANSList.
        ASNMap[ASN] = ASNOwner;
    }

    /// Removes an ASN to the ASN list. The operation has to include a signature
    /// from the ASN owner signing sha256(abi.encodePacked(ASN,ASNOwner)) which can be
    /// generated by calling IANA_getSignatureMessage()
    /// @param ASN The ASN to be added
    /// @param ASNOwner The public key of the new owner.
    /// @param sigV The V parameter of the signature.
    /// @param sigR The R parameter of the signature.
    /// @param sigS The S parameter of the signature.
    function IANA_removeASN(uint32 ASN, address ASNOwner, uint8 sigV, bytes32 sigR, bytes32 sigS) public onlyOwners {
        // ensure message we have received is signed by the current ASNOwner. We don't have to check for the IANA owner because
        // the onlyOwners routine does that for us.
        require(ecrecover(IANA_getSignatureMessage(ASN, ASNOwner), sigV, sigR, sigS) == ASNOwner);

        require(ASN != 0);
        require(ASNMap[ASN] != address(0), "ERROR: ASN is not added to ASNMap. It's not registered.");

        //Return any owned prefix to IANA
        //Set ownership of prefix to 0 (aka IANA)
        for (uint i=0; i<ASNPrefixMap[ASN].length; i++) {
            prefix memory prefixToReturn = ASNPrefixMap[ASN][i];
            PrefixASNMap[prefixToReturn.ip][prefixToReturn.mask] = 0;
        }
        //delete the ASN from the ASNPrefix map which will delete the ASN's ownership over its prefixes
        delete(ASNPrefixMap[ASN]);

         // At this point, we have two party agreement on ASN ownership. Mark the ASN as unowned
        ASNMap[ASN] = address(0);
    }

    /// Adds an additional user to the owners table, allowing them to modify the discovery tables.
    /// @param owner The public key of the new owner.
    function IANA_addOwner(address owner) public onlyOwners {
        ownerMap[owner] = true;
    }

    /// Removes a user from the owners table, who will no longer be allowed to edit the discovery table.
    /// @param owner The public key of the owner to be removed.
    function IANA_removeOwner(address owner) public onlyOwners {
        delete(ownerMap[owner]);
    }

    /// Returns the ASN for given IP/mask prefix, or 0 if IANA owns the Prefix.
    /// @param ip The ip
    /// @param mask the mask
    /// @return uint32 the ASN that owns the prefix
    function getPrefixOwner(uint32 ip, uint8 mask) public view returns (uint32) {
        // Only valid subnet masks
        require (mask <= 32, "invalid subnet");
        return PrefixASNMap[ip][mask];
    }

    /// Returns all Prefixes for any given ASN in ASNMap.
    /// @param ASN the ASN whose prefixes you want
    /// @return prefix[] list of the prefixes owned by the ASN
    function getAllPrefixesOwnedByASN(uint32 ASN) public view returns (prefix[] memory) {
        //ensure ASN is in map. If not, they don't have prefixes
        address asnAddress = ASNMap[ASN];
        // The owning ASN must exist
        require (asnAddress != address(0), "ASN not added to ASNMap");
        
        //return prefixes
        return ASNPrefixMap[ASN];

    }

    /// Compares two prefixes together
    /// @param prefix1 prefix 1
    /// @param prefix2 prefix 2
    /// @return bool returns true if prefix structs are equal
    function helper_prefixesEqual(prefix memory prefix1, prefix memory prefix2) internal view returns (bool) {
        bytes32 p1_hash = keccak256(abi.encodePacked(prefix1.ip, prefix1.mask));
        bytes32 p2_hash = keccak256(abi.encodePacked(prefix2.ip, prefix2.mask));
        return p1_hash == p2_hash;
    }

    /// Removes element from array. Does not maintain order of array! But it is cheap
    /// @param index index of array to remove
    /// @param currentOwnerASN ASN of prefix to remove from ASN
    function helper_removePrefixASNPrefixMap(uint32 currentOwnerASN, uint32 index) internal {
        uint256 prefixArrayLen = ASNPrefixMap[currentOwnerASN].length;
        ASNPrefixMap[currentOwnerASN][index] = ASNPrefixMap[currentOwnerASN][prefixArrayLen - 1];
        ASNPrefixMap[currentOwnerASN].pop();
    }   

}
