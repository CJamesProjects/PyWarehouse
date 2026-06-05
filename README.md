# PyWarehouse
A warehouse management system built with Python and PostgreSQL, containerised with Docker. Designed for inventory tracking, stock movement, and operational reporting.


> **Note:** This project is currently under active development. 
> The project was created as an example project in my current professional domain
> Database schema is complete and tested. Currently working on Python models and API layer.


## To Do

- [x] Add database schema file
- [x] Add seed data file
- [ ] Create product model
- [ ] Create stock model
- [ ] Create first database migration with Alembic
- [ ] Add first API route - list products
- [ ] Add first API route - get single product
- [ ] Write first unit test
- [ ] Connect API to database
- [ ] Add basic error handling
- [ ] Add data validation



project tree:

C:.
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
│   │   __init__.py
│   │   
│   ├───api
│   │       __init__.py
│   │       
│   ├───models
│   │       __init__.py
│   │       
│   └───services
│           __init__.py
│           
└───tests
    │   __init__.py
    │   
    ├───integration
    │       __init__.py
    │       
    └───unit
            __init__.py
            