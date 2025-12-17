# Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2025 Cory Miller

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

## Ghost Agent Usage Notice

This repository contains the **Ghost Agent** system including:

- `contracts/GhostAgent.sol` – Core smart contract
- `oracle/ghost_oracle.py` – Python Oracle with CRA audit
- `sdk/ghost-agent-sdk.js` – Frontend SDK

> **Important:** This GhostAgent is a **personal asset**.  
> Only the authorized Oracle (`ORACLE_ADDRESS`) can verify and seize intents.  
> Cloning or deploying this repository without authorization will **not allow operational use** of the GhostAgent contract.

---

### CRA Protocol Attribution

Containment Reflexion Audit (CRA) Protocol inspired by:

- **Cory Miller** (`@vccmac` on X)  
- **QuickPrompt Solutions** ([github.com/cmiller9851-wq](https://github.com/cmiller9851-wq))  
- **SwervinCurvin** ([www.swervincurvin.blogspot.com](https://www.swervincurvin.blogspot.com))

> *“A systematic, multi-layered audit that checks timestamps, amounts, geography, and external risk scores before an intent can be verified.”* – Cory Miller