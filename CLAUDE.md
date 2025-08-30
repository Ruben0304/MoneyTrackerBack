# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development
- **Start development server**: `python main.py` or `uvicorn main:app --reload --host 127.0.0.1 --port 8000`
- **Install dependencies**: `pip install -r requirements.txt`
- **Database setup**: Use `python import_data.py` to populate MongoDB with initial data from `mongojsons/` directory

### Testing
No testing framework is currently configured in this project.

## Architecture Overview

This is a **MoneyApp** backend API built with **FastAPI** that follows **Clean Architecture** principles with clear separation of concerns:

### Core Structure
- **main.py**: FastAPI application entry point with middleware and router registration
- **models/**: Pydantic models for data validation and serialization
- **repositories/**: Data access layer with MongoDB operations
- **routes/**: API endpoints organized by feature domain
- **database/**: MongoDB connection and collection management
- **external_services/**: Third-party integrations (Gemini AI)

### Key Architectural Patterns

#### Repository Pattern
- **BaseRepository** (`repositories/base_repository.py`): Abstract base class with common CRUD operations
- All repositories inherit from BaseRepository and work with MongoDB collections
- Repositories handle ObjectId conversion and provide async database operations

#### Model Organization
- **Base models** (`models/base.py`): Custom PyObjectId class for MongoDB ObjectId handling with Pydantic
- **Domain models**: User, Account, Transaction, Category, Budget, Income/Expense Presets, Auto Savings
- Each model has Create/Update variants for API operations

#### Authentication & Authorization
- JWT-based authentication with role-based access control
- Three user roles: "basic", "pro", "max" with different AI request limits
- Protected endpoints use dependency injection for current user and role validation

#### Database Layer
- MongoDB with pymongo client
- Collections: users, accounts, transactions, categories, budgets, income_presets, expense_presets, auto_savings
- Connection configuration via environment variables (MONGODB_URL, DATABASE_NAME)

### External Integrations
- **Gemini AI**: Chat functionality with streaming support for financial insights
- **CORS**: Configured for cross-origin requests with flexible frontend URL

### Data Management
- **mongojsons/**: Contains seed data with MongoDB import commands
- **import_data.py**: Database initialization script
- Environment variables for sensitive configuration (.env file)

## Important Notes

- All models use PyObjectId for proper MongoDB ObjectId serialization
- User passwords are hashed before storage
- API follows RESTful conventions with proper HTTP status codes
- Authentication tokens include both access and refresh tokens
- The application uses async/await patterns throughout for better performance