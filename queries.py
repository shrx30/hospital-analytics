"""
Hospital Operations Analytics - SQL Query Repository
This file contains parameterized/standard SQL queries used for operations reporting.
"""

# 1. Bed occupancy by ward
BED_OCCUPANCY_QUERY = """
SELECT 
    w.ward_id,
    w.ward_name,
    d.department_name,
    SUM(CASE WHEN b.bed_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_beds,
    COUNT(b.bed_id) AS total_beds,
    ROUND(SUM(CASE WHEN b.bed_status = 'Occupied' THEN 1 ELSE 0 END) * 100.0 / COUNT(b.bed_id), 2) AS occupancy_rate
FROM bed b
JOIN ward w ON b.ward_id = w.ward_id
JOIN department d ON w.department_id = d.department_id
GROUP BY w.ward_id, w.ward_name, d.department_name
ORDER BY occupancy_rate DESC;
"""

# 2. Patient admissions by department
ADMISSIONS_BY_DEPT_QUERY = """
SELECT 
    d.department_name,
    COUNT(a.admission_id) AS admission_count
FROM admission a
JOIN department d ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY admission_count DESC;
"""

# 3. Revenue by department
REVENUE_BY_DEPT_QUERY = """
SELECT 
    d.department_name,
    SUM(b.total_amount) AS total_revenue,
    SUM(b.insurance_covered_amount) AS insurance_covered,
    SUM(b.patient_payable_amount) AS patient_payable
FROM billing b
JOIN admission a ON b.admission_id = a.admission_id
JOIN department d ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY total_revenue DESC;
"""

# 4. Doctor workload (Diagnostics processed by each doctor)
DOCTOR_WORKLOAD_QUERY = """
SELECT 
    e.employee_name AS doctor_name,
    d.specialization,
    dep.department_name,
    COUNT(pd.patient_diagnostic_id) AS total_tests
FROM doctor d
JOIN employee e ON d.employee_id = e.employee_id
JOIN department dep ON e.department_id = dep.department_id
LEFT JOIN patient_diagnostic pd ON d.doctor_id = pd.doctor_id
GROUP BY d.doctor_id, doctor_name, d.specialization, dep.department_name
ORDER BY total_tests DESC;
"""

# 5. Drug inventory below reorder level
DRUG_REORDER_QUERY = """
SELECT 
    d.drug_name,
    d.brand_name,
    di.current_stock,
    di.reorder_level,
    (di.reorder_level - di.current_stock) AS deficiency_qty
FROM drug_inventory di
JOIN drug d ON di.drug_id = d.drug_id
WHERE di.current_stock < di.reorder_level
ORDER BY deficiency_qty DESC;
"""

# 6. Average patient length of stay
AVG_LENGTH_OF_STAY_QUERY = """
SELECT 
    d.department_name,
    ROUND(AVG(julianday(a.discharge_date) - julianday(a.admission_date)), 2) AS avg_stay_days,
    COUNT(a.admission_id) AS total_patients
FROM admission a
JOIN department d ON a.department_id = d.department_id
GROUP BY d.department_name
ORDER BY avg_stay_days DESC;
"""

# 7. Insurance coverage statistics (financial aggregate)
INSURANCE_STATS_QUERY = """
SELECT 
    ip.provider_name,
    ip.provider_type,
    COUNT(b.bill_id) AS claims_count,
    SUM(b.total_amount) AS total_billed,
    SUM(b.insurance_covered_amount) AS total_insurance_covered,
    SUM(b.patient_payable_amount) AS total_patient_payable,
    ROUND(AVG(pi.coverage_percentage), 2) AS avg_policy_coverage_percent
FROM billing b
JOIN admission a ON b.admission_id = a.admission_id
JOIN patient p ON a.patient_id = p.patient_id
JOIN patient_insurance pi ON p.patient_id = pi.patient_id
JOIN insurance_provider ip ON pi.insurance_provider_id = ip.insurance_provider_id
GROUP BY ip.provider_name, ip.provider_type
ORDER BY total_billed DESC;
"""

# 8. Monthly Revenue Trend
REVENUE_TREND_QUERY = """
SELECT 
    strftime('%Y-%m', b.bill_date) AS bill_month,
    SUM(b.total_amount) AS monthly_revenue,
    SUM(b.insurance_covered_amount) AS monthly_insurance_covered,
    SUM(b.patient_payable_amount) AS monthly_patient_payable
FROM billing b
GROUP BY bill_month
ORDER BY bill_month;
"""

# 9. Daily admissions trend (for filters and patient page timeline chart)
PATIENT_ADMISSIONS_TREND_QUERY = """
SELECT 
    a.admission_date,
    d.department_name,
    COUNT(a.admission_id) AS admission_count
FROM admission a
JOIN department d ON a.department_id = d.department_id
GROUP BY a.admission_date, d.department_name
ORDER BY a.admission_date;
"""

# 10. General overall counts (for high level dashboard stats)
OVERALL_STATS_QUERY = """
SELECT 
    (SELECT COUNT(*) FROM patient) AS total_patients,
    (SELECT COUNT(*) FROM doctor) AS total_doctors,
    (SELECT COUNT(*) FROM admission) AS total_admissions,
    (SELECT SUM(total_amount) FROM billing) AS total_revenue,
    (SELECT COUNT(*) FROM bed WHERE bed_status = 'Occupied') AS active_occupied_beds,
    (SELECT COUNT(*) FROM bed) AS total_beds
"""
