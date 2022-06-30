pragma solidity ^0.5.7;
pragma experimental ABIEncoderV2;
contract IANA_base {

    string public name = "IANA base contract"; //stored on BC
    address public owner; //IANA

    struct IPPrefix {
        uint32 ip;
        uint8 mask;
        uint32 owningAS;
        uint[] subPrefixes; // Pointer to prefix index in the larger prefixes array.
    }

    struct ASResource {
        uint32 ASN; //not sure if should be ASN or name of AS
        string RIR; // ARIN, AFRINIC, etc
        string owner; //RIR, NIR, LIR
        uint stime; //start time
        uint vperiod; //period. or end time?? 
    }

    enum IPState {
        Unregistered,
        Registered,
        Allocated,
        Assigned,
        Binded
    }

    struct IPResource {
        IPPrefix prefix;
        IPState state;
        string RIR;     // authority -> ISP. could be RIR -> NIR -> ISP but leaving out for now
        // string xIR;     // authority2, rir, nir, lir
        string owner;   // ISP
        string leasee;  // 
    }


    // All the people who can change the function pointers
    mapping (address => bool) public ownerList;
    // The associative mapping that maps ASNs to their owner's public key.
    mapping (uint32 => address) public ASNList;
    // List of prefixes.
    IPPrefix[] public prefixes;
    IPResource[] public ipresources;

    // Holds the table of links keyed by sha256(encodePacked(ASN1,ASN2))
    // A link is valid if both ASN1->ASN2 and ASN2->ASN1 exist.
    // This particular structure has the potential to be astoundingly large.
    mapping (bytes32 => bool) links;

    constructor() public {
        // Automatically add the contract creator as an owner
        ownerList[msg.sender] = true; //owner = msg.sender    

        //Build IP resource for root resource (IANA)
        IPResource memory rootResource;
        
        // Build up the prefix for the root prefix
        IPPrefix memory rootPrefix;
        rootPrefix.ip = 0;
        rootPrefix.mask = 0;
        rootPrefix.owningAS = 0;
        prefixes.push(rootPrefix);

        rootResource.prefix = rootPrefix;
        rootResource.state = IPState.Unregistered;
        rootResource.RIR = "";      //hasn't been allocated to any RIR. owned by IANA
        rootResource.owner = "";    //hasn't been allocated to any RIR
        rootResource.leasee = "";   //hasn't been leased to anybody
        ipresources.push(rootResource);

        // Mark that the root is owned by a dummy address.
        ASNList[0] = address(0);
    }

}
