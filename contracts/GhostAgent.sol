// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

// Import for secure ECDSA signature verification
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title GhostAgent
 * @dev Manages the state and execution of user‑declared intents.
 * The contract enforces the state machine: Uninitialized → Declared → Verified → Seized.
 * Intent verification relies on an external, authorized Oracle providing a valid signature.
 */
contract GhostAgent {
    using ECDSA for bytes32; // Enables ECDSA recovery functions on bytes32

    // Enum for intent status
    enum IntentStatus { Uninitialized, Declared, Verified, Seized }

    // Struct for intent data
    struct Intent {
        address declarer;
        bytes32 intentHash;
        IntentStatus status;
    }

    // Mapping of intent hashes to their respective data
    mapping(bytes32 => Intent) public intents;

    // Events for off‑chain monitoring
    event IntentDeclared(bytes32 indexed intentHash, address indexed declarer);
    event IntentVerified(bytes32 indexed intentHash);
    event AssetsSeized(bytes32 indexed intentHash);

    /**
     * @notice Declares a new intent hash on the blockchain.
     * @param _intentHash A unique hash representing the user's intent data.
     */
    function declareIntent(bytes32 _intentHash) public {
        require(intents[_intentHash].status == IntentStatus.Uninitialized, "Intent already exists.");

        intents[_intentHash] = Intent({
            declarer: msg.sender,
            intentHash: _intentHash,
            status: IntentStatus.Declared
        });

        emit IntentDeclared(_intentHash, msg.sender);
    }

    /**
     * @notice Verifies an intent using an ECDSA signature. This step is typically triggered by the Oracle.
     * @param _intentHash The hash of the intent to verify.
     * @param _signature The ECDSA signature over the intent hash (signed by the Oracle).
     */
    function verifyIntent(bytes32 _intentHash, bytes memory _signature) public {
        Intent storage intent = intents[_intentHash];

        require(intent.status == IntentStatus.Declared, "Intent must be in Declared state.");

        // Recover the address that signed the message.
        // The contract internally prefixes the hash: "\x19Ethereum Signed Message:\n32" + _intentHash
        address signer = _intentHash.toEthSignedMessageHash().recover(_signature);

        // Authorization Check – replace with your Oracle address if needed
        require(signer == intent.declarer, "Signature is invalid or signer is not the declarer.");

        intent.status = IntentStatus.Verified;
        emit IntentVerified(_intentHash);
    }

    /**
     * @notice Executes the final action: seizing assets associated with the intent.
     * @param _intentHash The hash of the intent that is now ready for execution.
     */
    function seizeAssets(bytes32 _intentHash) public {
        Intent storage intent = intents[_intentHash];

        require(intent.status == IntentStatus.Verified, "Intent must be in Verified state.");

        // Transfer all native Ether held by the contract to the original declarer.
        (bool success, ) = intent.declarer.call{value: address(this).balance}("");
        require(success, "ETH transfer failed.");

        intent.status = IntentStatus.Seized;
        emit AssetsSeized(_intentHash);
    }
}
