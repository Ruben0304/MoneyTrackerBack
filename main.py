import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import auth, users, accounts, transactions, budgets, categories, chat, income_presets, expense_presets

load_dotenv()

app = FastAPI(
    title="MoneyApp API",
    description="Backend API for MoneyApp expense tracker",
    version="1.0.0"
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(budgets.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(income_presets.router, prefix="/api/income-presets", tags=["Income Presets"])
app.include_router(expense_presets.router, prefix="/api/expense-presets", tags=["Expense Presets"])
# app.include_router(auto_savings.router, prefix="/api/auto-savings", tags=["Auto Savings"]) # Omitted as requested

@app.get("/")
def read_root():
    return {"message": "MoneyApp API is running!", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)