// ghost-agent-sdk.js – frontend SDK for GhostAgent

class GhostAgentSDK {
    CONTRACT_ADDRESS = "0xYourDeployedContractAddressHere"; // Replace with deployed contract
    GHOST_AGENT_ABI = [
        "function declareIntent(bytes32 _intentHash)",
        "function intents(bytes32) view returns (address declarer, bytes32 intentHash, uint8 status)",
        "event IntentDeclared(bytes32 indexed intentHash, address indexed declarer)"
    ];

    provider = null;
    signer = null;
    contract = null;

    async init() {
        if (typeof window.ethereum === 'undefined') {
            throw new Error("Ethereum wallet (e.g., MetaMask) not detected.");
        }
        this.provider = new ethers.BrowserProvider(window.ethereum);
        await this.provider.send("eth_requestAccounts", []);
        this.signer = await this.provider.getSigner();
        this.contract = new ethers.Contract(
            this.CONTRACT_ADDRESS,
            this.GHOST_AGENT_ABI,
            this.signer
        );
        console.log(`✅ SDK Initialized. Connected as: ${await this.signer.getAddress()}`);
        return await this.signer.getAddress();
    }

    async declareIntent(intentData) {
        if (!this.contract) throw new Error("SDK not initialized. Call init() first.");
        const canonicalData = (typeof intentData === 'object') ? JSON.stringify(intentData) : String(intentData);
        const intentHash = ethers.sha256(ethers.toUtf8Bytes(canonicalData));
        console.log(`🔑 Intent Hash Generated: ${intentHash}`);
        const tx = await this.contract.declareIntent(intentHash);
        console.log(`🚀 Transaction sent: ${tx.hash}`);
        const receipt = await tx.wait();
        if (receipt.status === 1) {
            console.log("✅ Intent declared successfully!");
            return intentHash;
        } else {
            throw new Error(`Transaction failed with status: ${receipt.status}`);
        }
    }

    async getIntentStatus(intentHash) {
        if (!this.contract) throw new Error("SDK not initialized. Call init() first.");
        const STATUS_MAP = ["Uninitialized", "Declared", "Verified", "Seized"];
        const result = await this.contract.intents(intentHash);
        const statusIndex = Number(result[2]);
        return {
            declarer: result[0],
            intentHash: result[1],
            status: statusIndex,
            statusName: STATUS_MAP[statusIndex] || "Unknown"
        };
    }
}

// Optionally export class
// export { GhostAgentSDK };