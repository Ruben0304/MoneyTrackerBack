#!/usr/bin/env python3
"""
Script to import all JSON files from mongojsons directory into MongoDB.
Database: Money (localhost:27017)
"""

import json
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError
import sys

def connect_to_mongodb():
    """Connect to MongoDB database"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        client.admin.command('ping')
        db = client['Money']
        print("Connected to MongoDB successfully")
        return db
    except ConnectionFailure:
        print("Failed to connect to MongoDB. Make sure MongoDB is running on localhost:27017")
        sys.exit(1)

def import_json_file(db, file_path, collection_name):
    """Import a JSON file into a MongoDB collection"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not isinstance(data, list):
            data = [data]
        
        collection = db[collection_name]
        
        # Clear existing data
        collection.delete_many({})
        
        # Insert new data
        if data:
            result = collection.insert_many(data)
            print(f"Imported {len(result.inserted_ids)} documents into '{collection_name}' collection")
        else:
            print(f"No data found in {file_path}")
            
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
    except BulkWriteError as e:
        print(f"Error importing {file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error importing {file_path}: {e}")

def main():
    """Main function to import all JSON files"""
    print("Starting MongoDB data import...")
    
    # Connect to MongoDB
    db = connect_to_mongodb()
    
    # Define the mongojsons directory
    mongojsons_dir = os.path.join(os.path.dirname(__file__), 'mongojsons')
    
    if not os.path.exists(mongojsons_dir):
        print(f"Directory not found: {mongojsons_dir}")
        sys.exit(1)
    
    # Define collection mappings (filename -> collection_name)
    json_files = {
        'users.json': 'users',
        'accounts.json': 'accounts',
        'categories.json': 'categories',
        'transactions.json': 'transactions',
        'budgets.json': 'budgets'
    }
    
    print(f"Looking for JSON files in: {mongojsons_dir}")
    
    # Import each JSON file
    for filename, collection_name in json_files.items():
        file_path = os.path.join(mongojsons_dir, filename)
        if os.path.exists(file_path):
            print(f"Importing {filename} -> {collection_name} collection...")
            import_json_file(db, file_path, collection_name)
        else:
            print(f"File not found: {filename}")
    
    print("\nData import completed!")
    print(f"Database: Money")
    print(f"MongoDB URL: mongodb://localhost:27017/")

if __name__ == "__main__":
    main()