#!/usr/bin/env python3
"""
Setup script for Alpaca Trading API examples
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print("✅ Python version is compatible")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'alpaca-py',
        'pandas',
        'numpy',
        'python-dotenv',
        'requests',
        'websocket-client'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_environment():
    """Set up environment variables"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Copy .env.example to .env
    try:
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit .env file with your Alpaca API credentials")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_api_credentials():
    """Check if API credentials are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or api_key == 'your_paper_api_key_here':
        print("❌ ALPACA_API_KEY not set in .env file")
        return False
    
    if not secret_key or secret_key == 'your_paper_secret_key_here':
        print("❌ ALPACA_SECRET_KEY not set in .env file")
        return False
    
    print("✅ API credentials are configured")
    return True

def test_connection():
    """Test connection to Alpaca API"""
    try:
        from alpaca.trading.client import TradingClient
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
        
        account = client.get_account()
        print(f"✅ Successfully connected to Alpaca API")
        print(f"   Account ID: {account.id}")
        print(f"   Status: {account.status}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Alpaca API: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Alpaca Trading API Examples")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and run setup again.")
        return
    
    print()
    
    # Setup environment
    if not setup_environment():
        return
    
    print()
    
    # Check API credentials
    if not check_api_credentials():
        print("\nPlease configure your API credentials in the .env file and run setup again.")
        return
    
    print()
    
    # Test connection
    if not test_connection():
        print("\nPlease check your API credentials and internet connection.")
        return
    
    print()
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review the examples in simple_options_trading.py")
    print("2. Review the advanced examples in multi_leg_options_trading.py")
    print("3. Start with paper trading to test your strategies")
    print("4. Always use proper risk management")

if __name__ == "__main__":
    main()