import hashlib
import json
from datetime import datetime
from typing import List, Dict

class MockBlock:
    def __init__(self, index: int, timestamp: str, data: Dict, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class MockBlockchain:
    def __init__(self):
        self.chain: List[MockBlock] = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = MockBlock(
            index=0,
            timestamp=str(datetime.now()),
            data={"message": "Genesis Block for Lost & Found System"},
            previous_hash="0"
        )
        self.chain.append(genesis_block)
    
    def add_report(self, report_data: Dict) -> Dict:
        """Add a new report to the blockchain"""
        last_block = self.chain[-1]
        
        new_block = MockBlock(
            index=len(self.chain),
            timestamp=str(datetime.now()),
            data={
                "type": "report",
                "report_id": report_data.get("report_id"),
                "report_type": report_data.get("type"),
                "item_name": report_data.get("item_name"),
                "vehicle_id": report_data.get("vehicle_id"),
                "timestamp": report_data.get("timestamp", str(datetime.now()))
            },
            previous_hash=last_block.hash
        )
        
        self.chain.append(new_block)
        
        return {
            "success": True,
            "message": "Report added to blockchain",
            "block_index": new_block.index,
            "block_hash": new_block.hash,
            "transaction_hash": f"0x{new_block.hash[:20]}..."
        }
    
    def verify_report(self, report_id: int) -> Dict:
        """Verify if a report exists in the blockchain"""
        for block in self.chain:
            if block.data.get("type") == "report" and block.data.get("report_id") == report_id:
                return {
                    "exists": True,
                    "verified": True,
                    "block_data": block.to_dict()
                }
        return {"exists": False, "verified": False}
    
    def get_chain(self) -> List[Dict]:
        """Get entire blockchain"""
        return [block.to_dict() for block in self.chain]
    
    def is_chain_valid(self) -> bool:
        """Validate the blockchain integrity"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if current block hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

# Global blockchain instance
blockchain = MockBlockchain()

# Test function
def test_blockchain():
    print("🧪 Testing Mock Blockchain...")
    
    # Test 1: Add a report
    test_report = {
        "report_id": 1,
        "type": "lost",
        "item_name": "Test iPhone",
        "vehicle_id": "BUS001",
        "timestamp": str(datetime.now())
    }
    
    result = blockchain.add_report(test_report)
    print(f"✅ Added report: {result}")
    
    # Test 2: Verify report
    verification = blockchain.verify_report(1)
    print(f"🔍 Verification: {verification}")
    
    # Test 3: Check chain validity
    print(f"🔗 Chain valid: {blockchain.is_chain_valid()}")
    
    # Test 4: Show chain length
    print(f"📦 Chain length: {len(blockchain.get_chain())} blocks")
    
    return True

if __name__ == "__main__":
    test_blockchain()