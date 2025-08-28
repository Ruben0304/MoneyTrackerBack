import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "moneyapp")

client = MongoClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
users_collection = database.get_collection("users")
accounts_collection = database.get_collection("accounts")
transactions_collection = database.get_collection("transactions")
categories_collection = database.get_collection("categories")
budgets_collection = database.get_collection("budgets")
income_presets_collection = database.get_collection("income_presets")
expense_presets_collection = database.get_collection("expense_presets")
auto_savings_collection = database.get_collection("auto_savings")

def get_database():
    return database