# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
python main.py
# Or with uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000` with automatic reload enabled.

### Database Setup
```bash
# Start MongoDB (must be running on localhost:27017)
# Import seed data
mongoimport --db moneyapp --collection categories --file mongojsons/categories.json --jsonArray
mongoimport --db moneyapp --collection users --file mongojsons/users.json --jsonArray
mongoimport --db moneyapp --collection accounts --file mongojsons/accounts.json --jsonArray
mongoimport --db moneyapp --collection transactions --file mongojsons/transactions.json --jsonArray
mongoimport --db moneyapp --collection budgets --file mongojsons/budgets.json --jsonArray
mongoimport --db moneyapp --collection income_presets --file mongojsons/income_presets.json --jsonArray
mongoimport --db moneyapp --collection expense_presets --file mongojsons/expense_presets.json --jsonArray
mongoimport --db moneyapp --collection auto_savings --file mongojsons/auto_savings.json --jsonArray
```

## Architecture Overview

### FastAPI Backend Structure
- **main.py**: FastAPI application entry point with CORS middleware and router inclusion
- **models.py**: Pydantic models for all entities (User, Account, Transaction, Category, Budget) with MongoDB ObjectId support
- **database.py**: MongoDB connection and collection setup using PyMongo
- **auth.py**: JWT-based authentication system with role-based access control
- **routes/**: API endpoints organized by entity type

### Key Components
- **Authentication**: JWT tokens with access/refresh token pattern, bcrypt password hashing
- **Authorization**: Role-based system (basic, pro, max) with AI request limits
- **Database**: MongoDB with collections for users, accounts, transactions, categories, budgets
- **API Structure**: RESTful endpoints under `/api` prefix

### Models and Collections
- **Users**: Authentication, roles, AI request tracking
- **Accounts**: Financial accounts (billetera, tarjeta, ahorro) with USD/CUP currency support
- **Transactions**: Income, expense, and transfer records with category linking
- **Categories**: Predefined income/expense categories with icons and colors
- **Budgets**: Savings goals with progress tracking
- **Income Presets**: Predefined income transactions (salaries, freelance work, etc.)
- **Expense Presets**: Predefined expense transactions (rent, utilities, etc.)
- **Auto Savings**: User settings for automatic savings on income

### Environment Configuration
Required environment variables (see .env):
- `MONGODB_URL`: MongoDB connection string (default: mongodb://localhost:27017)
- `DATABASE_NAME`: Database name (default: moneyapp)
- `FRONTEND_URL`: Frontend URL for CORS (default: http://localhost:3000)
- `JWT_SECRET_KEY`: Secret key for access tokens
- `JWT_REFRESH_SECRET_KEY`: Secret key for refresh tokens

### Data Seeding
The `mongojsons/` directory contains seed data for all collections. Use the mongoimport commands above to populate the database with example data. Note that some files contain placeholders like `REPLACE_WITH_USER_ID` that need to be replaced with actual ObjectIds after importing users.

### API Endpoints
All routes are prefixed with `/api`:
- `/api/auth/*`: Authentication (login, refresh, register)
- `/api/users/*`: User management
- `/api/accounts/*`: Account operations
- `/api/transactions/*`: Transaction management
- `/api/categories/*`: Category listing
- `/api/budgets/*`: Budget tracking
- `/api/income-presets/*`: Income presets management
- `/api/expense-presets/*`: Expense presets management
- `/api/auto-savings/*`: Auto savings configuration

### Security Features
- JWT token authentication with Bearer scheme
- Role-based access control (basic/pro/max)
- Password hashing with bcrypt
- AI request limiting by user role
- CORS configuration for frontend integration