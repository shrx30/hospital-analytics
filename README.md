# Hospital Operations Analytics Dashboard

An interactive, multi-page data analytics platform built in Python using SQLite, Pandas, Plotly, and Streamlit, running on top of a synthetic Hospital Management Information System (HMIS) dataset from Kaggle. 

This project is tailored to demonstrate database design, direct SQL query optimizations, operations engineering, and health-system business insights suitable for Operation Engineering, Healthcare Analytics, and Business Operations roles.

---

## 📂 Project Structure

```text
Hospital-Analytics/
│
├── .streamlit/
│   └── config.toml         # Custom dashboard dark theme setup
├── data/
│   ├── *.csv               # Raw relational CSV data files (copied from Kaggle)
│   └── hospital_operations.db # Ingested SQLite database
├── screenshots/
│   └── *.png               # Dashboard UI walkthrough views
├── app.py                  # Streamlit application UI page layouts
├── database.py             # Automated Kaggle downloader and database compiler
├── analysis.py             # Analysis functions and Operations Insights Engine
├── queries.py              # Central repository for optimized SQL queries
├── requirements.txt        # Core package requirements list
└── README.md               # Main project documentation
```

---

## 📊 Database Schema Details

The dataset models a full hospital relational schema with 19 tables:

1. **patient**: Denormalized patient demographic entries.
2. **employee**: Roster logs containing clinical and administrative staff details.
3. **department**: Medical divisions (Cardiology, Surgery, Pediatrics, ICU, etc.).
4. **doctor**: Medical specialist attributes linked to employees.
5. **admission**: Historical patient admissions detailing arrival, discharge, ward, and bed assignments.
6. **ward & bed**: Room layouts, total capacities, and live bed statuses (Occupied vs. Available).
7. **billing & billing_detail**: Gross bill values, insurance coverage limits, and patient payable out-of-pocket costs.
8. **drug & drug_inventory & drug_manufacturer**: Pharmacy catalog, stock levels, safety thresholds, and suppliers ratings.
9. **prescription & patient_diagnostic & diagnostic_test**: Test results, prescribing doctor logs, and pharmaceutical medication guides.

---

## 🛠️ Main Features

* **Ingestion Automation**: Set up to auto-download via `kagglehub` and build tables locally in SQLite.
* **Operations Insights Engine**: Scanalytically monitors capacity levels, workload, inventory deficits, and length-of-stay bottlenecks to generate direct administrator recommendations.
* **5-Page Executive Workbench**:
  1. *Executive Dashboard*: Overall KPIs (Gross billings, Bed occupancy, stock shortages) and the operations alert board.
  2. *Patient Analytics*: Trend lines on clinical admissions, date-range filters, and average Length of Stay (LoS) distributions.
  3. *Operations Dashboard*: Real-time ward capacity tracking and doctor clinic workload graphs.
  4. *Financial Dashboard*: Stacked billing collections tracking, and insurance claims distribution tables.
  5. *Inventory Dashboard*: Interactive safety reorder gauges and manufacturer reliability indices.
* **AI Operations Assistant**: A natural language chat assistant powered by **NVIDIA NIM API** endpoints. It translates user queries (like *"Show me the average patient stay by department"*) into active SQLite queries, runs them against the database, displays the outputs, and writes human-friendly operational summaries.

---

## 🔍 core SQL Queries

All calculations are powered by optimized queries stored dynamically in `queries.py`. Key queries include:

### 1. Bed Occupancy Rate per Ward
```sql
SELECT 
    w.ward_id, w.ward_name, d.department_name,
    SUM(CASE WHEN b.bed_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_beds,
    COUNT(b.bed_id) AS total_beds,
    ROUND(SUM(CASE WHEN b.bed_status = 'Occupied' THEN 1 ELSE 0 END) * 100.0 / COUNT(b.bed_id), 2) AS occupancy_rate
FROM bed b
JOIN ward w ON b.ward_id = w.ward_id
JOIN department d ON w.department_id = d.department_id
GROUP BY w.ward_id, w.ward_name, d.department_name
ORDER BY occupancy_rate DESC;
```

### 2. Clinical Inpatient Length of Stay (LoS)
```sql
SELECT 
    d.department_name,
    ROUND(AVG(julianday(a.discharge_date) - julianday(a.admission_date)), 2) AS avg_stay_days,
    COUNT(a.admission_id) AS total_patients
FROM admission a
JOIN department d ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY avg_stay_days DESC;
```

### 3. Critical Under-Stock Pharmaceuticals
```sql
SELECT 
    d.drug_name, d.brand_name, di.current_stock, di.reorder_level,
    (di.reorder_level - di.current_stock) AS deficiency_qty
FROM drug_inventory di
JOIN drug d ON di.drug_id = d.drug_id
WHERE di.current_stock < di.reorder_level
ORDER BY deficiency_qty DESC;
```

---

## 🚀 Installation & Running

### 1. Set Up Environment
Ensure you have Python 3.10+ installed. Clone this repository locally.

### 2. Install Dependencies
Run:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Populate SQLite Database
Run the ingestion pipeline:
```bash
python database.py
```
This script will download the HMIS dataset using `kagglehub`, create `/data`, copy the CSV files, and generate the SQLite database file `hospital_operations.db`.

### 4. Run the Streamlit App
Run:
```bash
python -m streamlit run app.py
```
A browser tab will automatically launch at `http://localhost:8501`.

### 5. Chatbot Setup
To use the **AI Operations Assistant** page:
1. Ensure your package dependencies are fully updated (`pip install -r requirements.txt`).
2. Provide your **NVIDIA API Key** (starting with `nvapi-`) in the page's sidebar input field.
3. Alternatively, you can set it as a system environment variable before starting the server:
   ```powershell
   # Windows PowerShell
   $env:NVIDIA_API_KEY="your_nvapi_key_here"
   ```

---

## 🔮 Future Improvements

1. **Scheduling Optimizations**: Model patient wait-times using Queueing Theory (M/M/c models) to suggest queue reductions.
2. **Admission Forecasting**: Integrate ARIMA or Prophet time-series models to anticipate admissions spikes based on historical holidays/seasonality.
3. **SQL Indexing Profiler**: Attach SQLite indexes on frequently joined primary keys (e.g. `admission.admission_id`, `patient.patient_id`) to analyze query speed advantages as the database size increases.
