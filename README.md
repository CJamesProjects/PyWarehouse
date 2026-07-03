# PyWarehouse 📦
A warehouse management system built with Python and PostgreSQL, containerised with Docker. Designed for inventory tracking, stock movement, and operational reporting.

> **Note:** This project is currently under active development, created as a portfolio project in my professional domain.
> Database schema, ORM models, core business logic and initial API layer are complete.
> Currently expanding the API layer and adding tests. #just finished these

## To Do
- [x] Add database schema file
- [x] Add seed data file
- [x] Create ORM models for all inventory types
- [x] Add first API route - list products
- [x] Add first API route - get single product
- [x] Write first unit tests
- [x] Connect API to database
- [ ] Create first database migration with Alembic
- [ ] Add stock level endpoints
- [ ] Add receive, dispatch and transfer endpoints
- [ ] Add purchase order endpoints
- [ ] Add outbound order endpoints
- [ ] Add data validation with Pydantic schemas
- [ ] Add basic error handling middleware
- [ ] Add authentication

## API
| Method | Endpoint | Description | Status |
|---|---|---|---|
| GET | `/` | API info | x |
| GET | `/health` | Health check | x |
| GET | `/products` | List all products | x |
| GET | `/products/{id}` | Get single product | x |
| GET | `/stock` | Current stock levels | o |
| POST | `/stock/receive` | Receive stock | o |
| POST | `/stock/dispatch` | Dispatch stock | o |
| POST | `/stock/transfer` | Transfer between locations | o |
| GET | `/stock/low` | Low stock alerts | o |

## Project Structure
│   .env.example
│   .gitignore
│   poetry.lock
│   pyproject.toml
│   README.md
│
├───database
│   │   schema.sql
│   │
│   └───seeds
│           dev_seed.sql
│
├───docker
│       docker-compose.yml
│
├───src
│   │   init.py
│   │   main.py
│   │
│   ├───api
│   │       init.py
│   │       products.py
│   │
│   ├───models
│   │       init.py
│   │       inventory.py
│   │
│   ├───services
│   │       init.py
│   │       stock_service.py
│   │
│   └───utils
│           init.py
│           config.py
│           database.py
│
├───tests
│   test_stock_service.py
│   init.py
│
├───integration
│       init.py
│
└───unit
init.py