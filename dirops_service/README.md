# dirops_service

Database service for Direktorat Operasi project monitoring (Kertas Kerja Monitoring Proyek).

## Setup

```bash
cd dirops_service
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Database Options

**SQLite (default for development):**
```bash
DB_TYPE=sqlite
DB_NAME=dirops.db
```

**PostgreSQL (for production):**
```bash
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dirops
DB_USER=postgres
DB_PASSWORD=your_password
```

**MySQL:**
```bash
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=dirops
DB_USER=root
DB_PASSWORD=your_password
```

## Commands

### Initialize Database
```bash
python cli.py init
```

### Reset Database
```bash
python cli.py reset
```

### Run Migrations
```bash
python cli.py migrate
```

### Create New Migration
```bash
python cli.py migration -m "add new column"
```

### Seed from Excel
```bash
python seed_excel.py ../plans/DirOps/
```

### Run Server
```bash
python run.py
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/projects` - List all projects
- `GET /api/projects/<id>` - Get project details
- `GET /api/projects/<id>/summary` - Get project summary (actions, budget, progress)
- `GET /api/projects/<id>/actions?status=OPEN` - Get project actions
- `GET /api/projects/<id>/wbs` - Get project WBS items
- `GET /api/dashboard/summary` - Dashboard summary

## Switching Database Environments

```bash
# Use SQLite
export DB_TYPE=sqlite
python run.py

# Use PostgreSQL
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=dirops
export DB_USER=postgres
export DB_PASSWORD=secret
python run.py
```

## Models

- `Project` - Master project data
- `ProjectMilestone` - Payment milestones
- `WbsItem` - Work Breakdown Structure items
- `WeeklyProgress` - Weekly progress data
- `RecoveryPlan` - Recovery plans for deviated targets
- `ActionTracker` - Action/issue tracking
- `BudgetControl` - Budget control summary
- `BudgetDetailLine` - Budget detail per WBS object
- `CashflowIn` - Cash-in projections
- `CashflowOut` - Cash-out transactions
- `Vendor` - Vendor master data
- `ProcurementItem` - Procurement items
- `ProcurementPayment` - Payment terms
- `ProcOpsStatus` - Procurement operations status
- `ProcPolStatus` - Procurement policy status
- `ProjectPhoto` - Activity documentation photos
- `ExchangeRate` - Exchange rates
