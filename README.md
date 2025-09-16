# Central Blockchain Development (Educational)

This is a simple blockchain implementation written in *Python*.  
It works as a *centralized blockchain* system where a single authority controls the chain.

## Features
- Block structure with:
  - index
  - timestamp
  - data
  - previous hash
  - nonce
  - hash
- Proof-of-Work mining (configurable difficulty)
- Functions: setBlock, getBlock, blocksExplorer, mineBlock
- Genesis Block creation
- Simple CLI usage

## How to Run
```bash
python central_blockchain.py --list             # Show blockchain
python central_blockchain.py --add "My Data"    # Add a new block
python central_blockchain.py --get 1            # Get block by index
python central_blockchain.py --mine "Preview"   # Preview mining
