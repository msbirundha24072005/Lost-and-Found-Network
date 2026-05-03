from web3 import Web3

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if w3.is_connected():
    print("✅ Connected to Ganache!")
    print(f"Block Number: {w3.eth.block_number}")
    
    # Get accounts
    accounts = w3.eth.accounts
    print(f"\n📋 Available Accounts ({len(accounts)}):")
    for i, account in enumerate(accounts[:3]):  # Show first 3
        balance = w3.eth.get_balance(account)
        print(f"  Account {i}: {account[:10]}... - Balance: {w3.from_wei(balance, 'ether')} ETH")
else:
    print("❌ Failed to connect to Ganache")
    print("Make sure Ganache is running on http://127.0.0.1:7545")