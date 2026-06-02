# DirOps Database Schema Design

## Overview
Kertas Kerja Monitoring Proyek (KKMP) is a project monitoring system for Direktorat Operasi. Each Excel file represents one project with multiple tracking sheets.

---

## Tables

### 1. `projects`
Master table for all projects.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_code | VARCHAR(50) | Unique project code (e.g., `1LC-522UD013`) |
| project_name | VARCHAR(255) | Project name |
| customer | VARCHAR(255) | Customer name |
| business_scheme | VARCHAR(100) | e.g., `MAIN CONTRACTOR` |
| status | VARCHAR(50) | Project status (e.g., `CARRY OVER`) |
| unit_kerja | VARCHAR(100) | Unit kerja (e.g., `Project Operation - 3`) |
| contract_value_idr | DECIMAL(18,2) | Contract value in IDR |
| contract_value_valas | DECIMAL(18,2) | Contract value in foreign currency |
| currency | VARCHAR(10) | Foreign currency code (e.g., `EUR`) |
| cogs_percent | DECIMAL(5,2) | COGS percentage |
| cogs_idr | DECIMAL(18,2) | COGS in IDR |
| gpm_percent | DECIMAL(5,2) | Gross Profit Margin percentage |
| gpm_idr | DECIMAL(18,2) | Gross Profit Margin in IDR |
| contract_signed_date | DATE | Contract signing date |
| effective_date | DATE | Contract effective date |
| end_date | DATE | Contract end date |
| duration_months | INT | Contract duration in months |
| after_sales_start | DATE | After sales / warranty start |
| after_sales_end | DATE | After sales / warranty end |
| project_leader | VARCHAR(100) | Project Manager name |
| project_analyst | VARCHAR(100) | Project Analyst name |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 2. `project_milestones`
Payment milestones for each project.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| milestone_name | VARCHAR(255) | Milestone name |
| milestone_category | VARCHAR(100) | Category (e.g., `Maintenance Progress Review`, `Warehouse Acceptance`) |
| percentage | DECIMAL(5,2) | Percentage of contract |
| target_date | DATE | Target completion date |
| is_cash_in | BOOLEAN | True for cash-in milestone |
| status | VARCHAR(50) | Status (e.g., `PENDING`, `ACHIEVED`) |
| actual_date | DATE | Actual achievement date |
| notes | TEXT | Additional notes |

### 3. `wbs_items`
Work Breakdown Structure items per project.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| parent_id | UUID | FK to parent wbs_item (nullable, for hierarchy) |
| wbs_number | VARCHAR(50) | WBS code/number |
| wbs_name | VARCHAR(255) | WBS description |
| category | VARCHAR(100) | Category (e.g., `Services`, `Inspection and Acceptance`) |
| division | VARCHAR(100) | Responsible division (e.g., `Project Deployment Center`) |
| pic_name | VARCHAR(100) | Person in charge |
| activity_type | VARCHAR(10) | `P` (Plan) or `A` (Actual) |
| contract_value | DECIMAL(18,2) | Activity contract value |
| weight_percent | DECIMAL(5,2) | Weight percentage of total project |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 4. `weekly_progress`
Weekly progress data per WBS item.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| wbs_id | UUID | FK to wbs_items |
| week_number | INT | Week number (1-52) |
| year | INT | Year |
| week_label | VARCHAR(20) | Week label (e.g., `Jan W1`, `Feb W2`) |
| week_start_date | DATE | Start date of the week |
| plan_value | DECIMAL(5,2) | Planned progress % for this week |
| actual_value | DECIMAL(5,2) | Actual progress % achieved |
| accumulated_plan | DECIMAL(5,2) | Accumulated plan % |
| accumulated_actual | DECIMAL(5,2) | Accumulated actual % |
| deviation | DECIMAL(5,2) | Deviation (actual - plan) |
| revenue_value | DECIMAL(18,2) | Revenue value for this week |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Unique constraint:** `(project_id, wbs_id, year, week_number)`

### 5. `recovery_plans`
Recovery plan entries for deviated targets.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| year | INT | Year |
| week_number | INT | Week number |
| week_label | VARCHAR(20) | Week label |
| target_rkap | DECIMAL(5,2) | Target RKAP for the week |
| target_project | DECIMAL(5,2) | Target project for the week |
| realization | DECIMAL(5,2) | Actual realization |
| deviation | DECIMAL(5,2) | Deviation percentage |
| recovery_plan_percent | DECIMAL(5,2) | Recovery plan percentage (if any) |
| recovery_plan_description | TEXT | Description of recovery actions |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 6. `action_trackers`
Action/issue tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| ref_number | INT | Reference number |
| action_description | TEXT | Description of the action |
| organization_responsible | VARCHAR(100) | Responsible organization |
| actionee | VARCHAR(100) | Person assigned |
| open_date | DATE | Date action was opened |
| due_date | DATE | Due date |
| due_day | INT | Days until due (negative = overdue) |
| status | VARCHAR(20) | `OPEN`, `CLOSED` |
| case_description | TEXT | Case/issue description |
| update_notes | TEXT | Update notes |
| reference | VARCHAR(255) | Reference document |
| priority | VARCHAR(20) | `HIGH`, `MEDIUM`, `LOW` |
| critical_issue_date | DATE | Date critical issue was raised |
| critical_issue | TEXT | Critical issue description |
| impact | TEXT | Impact description |
| action_plan | TEXT | Action plan |
| high_level_support | TEXT | High level management support needed |
| high_level_action_plan | TEXT | High level action plan |
| pmo_recommendation | TEXT | PMO recommendation |
| closed_date | DATE | Date when action was closed |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 7. `budget_controls`
Budget control entries by WBS category.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| wbs_category | VARCHAR(100) | WBS category name |
| remaining_budget_sap | DECIMAL(18,2) | Remaining budget in SAP |
| wbs_not_input | DECIMAL(18,2) | WBS not yet input |
| total | DECIMAL(18,2) | Total |
| estimated_need | DECIMAL(18,2) | Estimated need |
| difference | DECIMAL(18,2) | Difference (total - estimated) |
| difference_percent | DECIMAL(5,2) | Difference percentage |
| budget_open | DECIMAL(18,2) | Open budget |
| absorption | DECIMAL(18,2) | Absorption amount |
| remaining_budget | DECIMAL(18,2) | Remaining budget |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 8. `budget_detail_lines`
Detailed budget lines for each WBS object.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| wbs_object | VARCHAR(100) | WBS object identifier |
| description | VARCHAR(255) | Description |
| budget | DECIMAL(18,2) | Budget amount |
| actual | DECIMAL(18,2) | Actual spending |
| commitment | DECIMAL(18,2) | Commitment amount |
| park_document | DECIMAL(18,2) | Parked document amount |
| remaining_order_plan | DECIMAL(18,2) | Remaining order plan |
| assigned | DECIMAL(18,2) | Assigned amount |
| available | DECIMAL(18,2) | Available amount |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 9. `cashflow_in`
Cash-in (revenue) projections.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| year | INT | Year |
| month | INT | Month (1-12) |
| month_label | VARCHAR(20) | Month label (e.g., `Jan`, `Feb`) |
| amount | DECIMAL(18,2) | Cash-in amount |
| description | VARCHAR(255) | Description / milestone |
| no_nota | VARCHAR(50) | Nota number |
| no_spp | VARCHAR(50) | SPP number |
| notes | TEXT | Additional notes |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 10. `cashflow_out`
Cash-out (expense) transactions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| year | INT | Year |
| month | INT | Month (1-12) |
| month_label | VARCHAR(20) | Month label |
| vendor_id | UUID | FK to vendors |
| vendor_name | VARCHAR(255) | Vendor name (denormalized) |
| amount | DECIMAL(18,2) | Cash-out amount |
| description | VARCHAR(255) | Description |
| no_nota | VARCHAR(50) | Nota number |
| no_spp | VARCHAR(50) | SPP number |
| payment_status | VARCHAR(50) | Payment status |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 11. `vendors`
Vendor/supplier master data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| vendor_code | VARCHAR(50) | Vendor code |
| vendor_name | VARCHAR(255) | Vendor name |
| vendor_type | VARCHAR(100) | Type (e.g., `Local`, `Foreign`) |
| country | VARCHAR(100) | Country |
| contact_email | VARCHAR(255) | Contact email |
| contact_phone | VARCHAR(50) | Contact phone |
| address | TEXT | Address |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 12. `procurement_items`
Procurement items per project.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| procurement_name | VARCHAR(255) | Name of procurement |
| vendor_id | UUID | FK to vendors |
| target_date | DATE | Target procurement date |
| status | VARCHAR(50) | Status |
| progress | DECIMAL(5,2) | Progress percentage |
| priority | VARCHAR(20) | Priority |
| procurement_type | VARCHAR(100) | Type of procurement |
| payment_type | VARCHAR(100) | Payment type |
| procurement_policy | VARCHAR(100) | Procurement policy |
| hps_value | DECIMAL(18,2) | HPS (Harga Perkiraan Sendiri) value |
| hps_date | DATE | HPS date |
| rks_value | DECIMAL(18,2) | RKS value |
| rks_date | DATE | RKS date |
| ome_value | DECIMAL(18,2) | OME value |
| pr_number | VARCHAR(50) | PR number |
| proc_ops | VARCHAR(100) | ProcOps |
| po_number | VARCHAR(50) | PO number |
| contract_value | DECIMAL(18,2) | Contract value |
| currency | VARCHAR(10) | Currency |
| efficiency | DECIMAL(5,2) | Efficiency percentage |
| due_date | DATE | Due date |
| estimated_delivery | DATE | Estimated delivery date |
| delivery_status | VARCHAR(50) | Delivery status |
| payment_status | VARCHAR(50) | Payment status |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 13. `procurement_payments`
Payment terms for procurement items.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| procurement_item_id | UUID | FK to procurement_items |
| payment_term_number | INT | Payment term number (1-6) |
| payment_type | VARCHAR(50) | `DP`, `TERMIN 1`, etc. |
| submit_date | DATE | Payment submission date |
| amount | DECIMAL(18,2) | Payment amount |
| gr_ses | VARCHAR(50) | GR/SES number |
| no_spp | VARCHAR(50) | SPP number |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 14. `proc_ops_status`
Procurement Operations Status Monitoring.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| proc_ops_id | INT | ProcOps ID number |
| officer | VARCHAR(100) | Officer name |
| pr_number | VARCHAR(50) | PR number |
| po_manual | VARCHAR(50) | Manual PO number |
| po_sap | VARCHAR(50) | SAP PO number |
| description | TEXT | Description |
| supplier | VARCHAR(255) | Supplier name |
| amount | DECIMAL(18,2) | Amount |
| currency | VARCHAR(10) | Currency |
| delivery_time | DATE | Delivery time |
| project_name | VARCHAR(255) | Project name |
| user_name | VARCHAR(100) | User/requester name |
| status | VARCHAR(50) | Status |
| follow_up | TEXT | Follow-up notes |
| deadline | DATE | Deadline |
| issue | TEXT | Issue description |
| project_code | VARCHAR(50) | Project code |
| status_2 | VARCHAR(50) | Secondary status |
| k3 | VARCHAR(50) | Additional status field |
| k4 | VARCHAR(50) | Additional status field |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 15. `proc_pol_status`
Procurement Policy Status Monitoring.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| request_id | INT | Request ID |
| request_date | DATE | Request date |
| request_description | TEXT | Request description |
| request_number | VARCHAR(50) | Request number |
| project_code | VARCHAR(50) | Project/program code |
| project_name | VARCHAR(255) | Project/program name |
| project_manager | VARCHAR(100) | Project manager |
| work_unit_officer | VARCHAR(100) | ILS/Work Unit Officer |
| work_unit_email | VARCHAR(255) | ILS/Work Unit email |
| executor_name | VARCHAR(100) | Executor name |
| user_remarks | TEXT | User remarks |
| gm_feedback | TEXT | GM feedback |
| request_status | VARCHAR(50) | Request status |
| posting_date | DATE | Posting date |
| rfp_number | VARCHAR(50) | RFP number |
| rfp_date | DATE | RFP date |
| rfp_procurement_category | VARCHAR(100) | Procurement category |
| rfp_company_name | VARCHAR(255) | RFP company name |
| rfp_receiving_email | VARCHAR(255) | RFP receiving email |
| rfp_department | VARCHAR(100) | RFP department |
| rfp_status | VARCHAR(50) | RFP status |
| hps_number | VARCHAR(50) | HPS number |
| hps_date | DATE | HPS date |
| hps_currency | VARCHAR(10) | HPS currency |
| hps_amount | DECIMAL(18,2) | HPS amount |
| hps_item | VARCHAR(255) | HPS purchasing item |
| hps_status | VARCHAR(50) | HPS status |
| rks_number | VARCHAR(50) | RKS number |
| rks_date | DATE | RKS date |
| rks_title | VARCHAR(255) | RKS procurement title |
| rks_type | VARCHAR(100) | RKS procurement type |
| rks_method | VARCHAR(100) | RKS procurement method |
| rks_delivery_terms | VARCHAR(255) | Delivery terms |
| rks_delivery_time | VARCHAR(100) | Delivery time |
| rks_payment_terms | VARCHAR(255) | Payment terms |
| rks_currency | VARCHAR(10) | RKS currency |
| rks_amount | DECIMAL(18,2) | RKS total amount |
| rks_status | VARCHAR(50) | RKS status |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 16. `project_photos`
Documentation photos of project activities.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| activity_date | DATE | Date of activity |
| activity_description | TEXT | Description of activity |
| photo_url | VARCHAR(500) | URL/path to photo |
| notes | TEXT | Additional notes |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### 17. `exchange_rates`
Exchange rates for currency conversion.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to projects (nullable for global rates) |
| currency_code | VARCHAR(10) | Currency code (e.g., `USD`, `EUR`, `SGD`) |
| rate | DECIMAL(18,2) | Exchange rate to IDR |
| effective_date | DATE | Effective date |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

---

## Summary Dashboard Data (Denormalized View)

For reporting purposes, a `project_dashboard_summary` view can be created:

| Field | Source Table |
|-------|-------------|
| project_code | projects |
| project_name | projects |
| customer | projects |
| status | projects |
| contract_value_idr | projects |
| progress_achieved | Latest weekly_progress |
| target_progress_year | Latest weekly_progress |
| deviation | Latest weekly_progress |
| open_actions | action_trackers (count, status=OPEN) |
| closed_actions | action_trackers (count, status=CLOSED) |
| overdue_actions | action_trackers (count, due_day < 0 AND status=OPEN) |
| remaining_budget | budget_controls |
| estimated_need | budget_controls |
| budget_difference | budget_controls |
| cash_in_total | cashflow_in (sum) |
| cash_out_total | cashflow_out (sum) |

---

## Relationships

```
projects (1) ─────< (N) wbs_items
projects (1) ─────< (N) weekly_progress
projects (1) ─────< (N) project_milestones
projects (1) ─────< (N) recovery_plans
projects (1) ─────< (N) action_trackers
projects (1) ─────< (N) budget_controls
projects (1) ─────< (N) cashflow_in
projects (1) ─────< (N) cashflow_out
projects (1) ─────< (N) procurement_items
projects (1) ─────< (N) proc_ops_status
projects (1) ─────< (N) proc_pol_status
projects (1) ─────< (N) project_photos

vendors (1) ─────< (N) procurement_items
vendors (1) ─────< (N) cashflow_out

procurement_items (1) ─────< (N) procurement_payments
wbs_items (1) ─────< (N) weekly_progress
```

---

## Indexes

### Primary Indexes
- `projects`: `project_code` (unique)
- `vendors`: `vendor_code` (unique)

### Secondary Indexes
- `weekly_progress`: `(project_id, year, week_number)`
- `action_trackers`: `(project_id, status)`
- `procurement_items`: `(project_id, status)`
- `cashflow_in`: `(project_id, year, month)`
- `cashflow_out`: `(project_id, year, month)`
- `wbs_items`: `(project_id, wbs_number)`
