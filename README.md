# Ghost Agent

**Ghost Agent** is a minimal‑viable‑product that lets a user declare an *intent*, have an off‑chain Oracle audit it, and then automatically seize the contract’s Ether once the intent is verified.

## Repository Structure
ghost-agent/
├── contracts/
│   └── GhostAgent.sol          # Core contract with Oracle restriction & contract salt
├── oracle/
│   ├── ghost_oracle.py         # Main Oracle runner (scheduler + event handling)
│   ├── cra_audit.py            # CRA Protocol checks
│   └── utils.py                # Signing, contract salt, and tx helpers
├── sdk/
│   └── ghost-agent-sdk.js      # Frontend SDK
├── README.md
└── LICENSE
## Key Features

- Solidity state machine: `Uninitialized → Declared → Verified → Seized`  
- Oracle-only execution of `verifyIntent` and `seizeAssets`  
- Contract salt ensures only the official GhostAgent instance works  
- CRA Protocol performs timestamp, amount, geography, and external risk checks  

## Usage Notice

> **Important:** This GhostAgent repository is a **personal asset**.  
> Only the authorized Oracle (`ORACLE_ADDRESS`) can verify and seize intents.  
> **Do not deploy or operate this contract** without authorization. Any cloned contract or Oracle instance will fail to function correctly.  

## CRA Protocol Attribution

The CRA audit logic is inspired by:

- **Cory Miller** (`@vccmac` on X)  
- **QuickPrompt Solutions** ([github.com/cmiller9851-wq](https://github.com/cmiller9851-wq))  
- **SwervinCurvin** ([www.swervincurvin.blogspot.com](https://www.swervincurvin.blogspot.com))  

> *“A systematic, multi-layered audit that checks timestamps, amounts, geography, and external risk scores before an intent can be verified.”* – Cory Miller

## License

Apache 2.0 — see `LICENSE`. This repository is formally licensed but **operational use is restricted** as noted above.