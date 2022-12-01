pragma solidity ^0.8.0;

// Implements Path Validation (BGPSEC) without heavy BGPSEC signing
// Contract to store each AS's advertisments.
// Each AS has a copy of one of these contracts
// Contract is only writable by the AS that owns this contract
// Contract is readable by any AS

contract PATH_VALIDATION {

    struct Prefix{
        uint32 ip;
        uint8 mask;
    }

    struct Advertisement {
        Prefix prefix;
        int32 nextHop;
        //uint64 timestamp; //could be useful for staleness or something
    }

    /// Enum of the validatePrefix() return types
    /// @param advertisementValid VALID: ip/mask and next hop all match. good to go
    /// @param advertisementInvalid INVALID: ip/mask and next hop do not exist
    enum validateAdvertisementResult {
        advertisementValid,
        advertisementInvalid
    }

    // This will have to do for now. 
    // But we're basically storing double data. ip=>mask=>advertisement(prefix, nextHop)
    // Keep this for now incase we need to add more things to advertisement struct
    mapping (uint32 => mapping (uint8 => Advertisement) ) internal advertisementsMap;

    // All the people who can change the function pointers
    mapping (address => bool) public ownerMap;

     /// Simple modifier to ensure that only owners can make changes
    modifier onlyOwners {
        require(ownerMap[msg.sender] == true);
        _;
    }

    constructor() public {
        // Automatically add the contract creator as an owner
        ownerMap[msg.sender] = true;
    }


    /// Adds the specified advertisement to the advertisement mapping. Must be done by the owner of the prefixes containing
    /// @param ip The IP address of the prefix to add
    /// @param mask The number of bits in the netmask of the prefix to add
    /// @param nextHop The AS number we're sending this BGP message to.
    function addAdvertisement(uint32 ip, uint8 mask, int32 nextHop) public onlyOwners {
        // Only valid subnet masks and ASNs
        require (mask <= 32);
        require (nextHop <= 65535);

        Advertisement memory newAdvertisement;
        newAdvertisement.prefix.ip = ip;
        newAdvertisement.prefix.mask = mask;
        newAdvertisement.nextHop = nextHop;


        advertisementsMap[ip][mask] = newAdvertisement;

        //maybe add timestamp here...
    }


    //Validate a received advertisement (prefix, path, next hop) is valid
    function validateAdvertisement(uint32 ip, uint8 mask, int32 nextHop) public view returns (validateAdvertisementResult) {
        // Only valid subnet masks and ASNs
        require (mask <= 32);
        require (nextHop <= 65535);

        if(advertisementsMap[ip][mask].nextHop == nextHop) {
            return validateAdvertisementResult.advertisementValid;
        }
        return validateAdvertisementResult.advertisementInvalid;
    }

}