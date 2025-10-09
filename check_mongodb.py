#!/usr/bin/env python3
"""
MongoDB Setup Verification Script

This script checks if MongoDB is properly configured and accessible.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.utils.mongodb_storage import MongoDBStorage
import json
from datetime import datetime


def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}


def check_mongodb_connection():
    """Check if MongoDB is accessible"""
    print("="*80)
    print("MongoDB Connection Test")
    print("="*80)
    
    config = load_config()
    mongodb_config = config.get('mongodb', {})
    
    print(f"\nConfiguration:")
    print(f"  Enabled: {mongodb_config.get('enabled', 'Not set')}")
    print(f"  Connection String: {mongodb_config.get('connection_string', 'Not set')}")
    print(f"  Database: {mongodb_config.get('database', 'Not set')}")
    
    if not mongodb_config.get('enabled', False):
        print("\n⚠️  MongoDB is disabled in config.json")
        print("   To enable it, set 'mongodb.enabled' to true")
        return False
    
    print("\n🔄 Attempting to connect to MongoDB...")
    
    try:
        mongodb = MongoDBStorage(
            mongodb_config.get('connection_string', 'mongodb://localhost:27017/'),
            mongodb_config.get('database', 'stock_data')
        )
        
        if mongodb.client is None:
            print("❌ Failed to connect to MongoDB")
            print("\nTroubleshooting steps:")
            print("1. Ensure MongoDB is installed and running")
            print("   macOS (Homebrew): brew services start mongodb-community")
            print("   Docker: docker run -d -p 27017:27017 --name mongodb mongo:latest")
            print("2. Check if port 27017 is accessible")
            print("3. Verify connection string in config.json")
            return False
        
        print("✅ Successfully connected to MongoDB!")
        
        # Check collections
        print("\n📊 Database Information:")
        db_info = mongodb.db.command("dbStats")
        print(f"  Database: {mongodb.database_name}")
        print(f"  Collections: {len(mongodb.db.list_collection_names())}")
        print(f"  Data Size: {db_info.get('dataSize', 0) / 1024 / 1024:.2f} MB")
        print(f"  Storage Size: {db_info.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        
        # Check if timeseries collection exists
        collections = mongodb.db.list_collection_names()
        print(f"\n📁 Collections:")
        for col in collections:
            count = mongodb.db[col].count_documents({})
            print(f"  - {col}: {count} documents")
        
        # Check indexes
        if 'timeseries' in collections:
            print(f"\n🔍 Indexes on 'timeseries' collection:")
            indexes = mongodb.db['timeseries'].list_indexes()
            for idx in indexes:
                print(f"  - {idx['name']}: {idx.get('key', {})}")
        
        # Get some sample data
        if 'timeseries' in collections:
            sample = mongodb.db['timeseries'].find_one()
            if sample:
                print(f"\n📈 Sample Data:")
                print(f"  Ticker: {sample.get('ticker', 'N/A')}")
                print(f"  Date: {sample.get('date', 'N/A')}")
                print(f"  Close: ${sample.get('close', 'N/A')}")
                
                # Get ticker statistics
                tickers = mongodb.db['timeseries'].distinct('ticker')
                print(f"\n📊 Statistics:")
                print(f"  Unique Tickers: {len(tickers)}")
                print(f"  Tickers: {', '.join(sorted(tickers)[:10])}")
                if len(tickers) > 10:
                    print(f"           ... and {len(tickers) - 10} more")
        
        # Check run metadata
        if 'run_metadata' in collections:
            latest_run = mongodb.db['run_metadata'].find_one(sort=[('run_timestamp', -1)])
            if latest_run:
                print(f"\n🏃 Latest Run:")
                print(f"  Run ID: {latest_run.get('run_id', 'N/A')}")
                print(f"  Timestamp: {latest_run.get('run_timestamp', 'N/A')}")
                print(f"  Status: {latest_run.get('status', 'N/A')}")
                print(f"  Tickers: {', '.join(latest_run.get('tickers', []))}")
        
        mongodb.close()
        
        print("\n" + "="*80)
        print("✅ MongoDB is properly configured and ready to use!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease check:")
        print("1. MongoDB service is running")
        print("2. Connection string is correct")
        print("3. No firewall blocking port 27017")
        return False


def show_mongo_commands():
    """Show useful MongoDB commands"""
    print("\n" + "="*80)
    print("Useful MongoDB Commands")
    print("="*80)
    
    print("\n📝 Connect to MongoDB shell:")
    print("   mongosh")
    
    print("\n📝 Use stock_data database:")
    print("   use stock_data")
    
    print("\n📝 View all tickers:")
    print("   db.timeseries.distinct('ticker')")
    
    print("\n📝 Get recent data for a ticker:")
    print("   db.timeseries.find({ticker: 'AAPL'}).sort({date: -1}).limit(10)")
    
    print("\n📝 Count records per ticker:")
    print("   db.timeseries.aggregate([")
    print("     { $group: { _id: '$ticker', count: { $sum: 1 } } },")
    print("     { $sort: { count: -1 } }")
    print("   ])")
    
    print("\n📝 View run history:")
    print("   db.run_metadata.find().sort({run_timestamp: -1}).limit(5)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    success = check_mongodb_connection()
    
    if success:
        show_mongo_commands()
    else:
        print("\n❌ MongoDB setup verification failed")
        print("\nFor detailed setup instructions, see: MONGODB_SETUP.md")
        sys.exit(1)
