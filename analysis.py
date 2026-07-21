"""
Hospital Operations Analytics - Data Analysis Module
Exposes helper methods to query the SQLite database and retrieve Pandas DataFrames.
"""

import os
import sqlite3
import pandas as pd
from queries import (
    BED_OCCUPANCY_QUERY,
    ADMISSIONS_BY_DEPT_QUERY,
    REVENUE_BY_DEPT_QUERY,
    DOCTOR_WORKLOAD_QUERY,
    DRUG_REORDER_QUERY,
    AVG_LENGTH_OF_STAY_QUERY,
    INSURANCE_STATS_QUERY,
    REVENUE_TREND_QUERY,
    PATIENT_ADMISSIONS_TREND_QUERY,
    OVERALL_STATS_QUERY
)

# SQLite database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "hospital_operations.db")

def verify_db_exists():
    """
    Checks if the SQLite database file exists.
    """
    return os.path.exists(DB_PATH)

def run_query(query, params=None):
    """
    Executes a SQL query against the SQLite database and returns the result as a DataFrame.
    """
    if not verify_db_exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH}. Please run database.py pipeline first.")
    
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

# Data Access APIs

def get_overall_stats():
    """
    Fetches high level summary statistics of patients, doctors, admissions, etc.
    """
    return run_query(OVERALL_STATS_QUERY)

def get_bed_occupancy():
    """
    Fetches bed occupancy rates by ward and department.
    """
    return run_query(BED_OCCUPANCY_QUERY)

def get_admissions_by_dept():
    """
    Fetches patient admissions grouped by department.
    """
    return run_query(ADMISSIONS_BY_DEPT_QUERY)

def get_revenue_by_dept():
    """
    Fetches aggregate and custom breakdown revenue components by department.
    """
    return run_query(REVENUE_BY_DEPT_QUERY)

def get_doctor_workload():
    """
    Fetches the number of diagnostic tests handled by each doctor.
    """
    return run_query(DOCTOR_WORKLOAD_QUERY)

def get_drug_reorders():
    """
    Fetches list of drugs whose stock is below reorder level.
    """
    return run_query(DRUG_REORDER_QUERY)

def get_avg_length_of_stay():
    """
    Fetches average length of stay in days grouped by department.
    """
    return run_query(AVG_LENGTH_OF_STAY_QUERY)

def get_insurance_stats():
    """
    Fetches insurance financial statistics by provider.
    """
    return run_query(INSURANCE_STATS_QUERY)

def get_revenue_trends():
    """
    Fetches monthly revenue trend details.
    """
    df = run_query(REVENUE_TREND_QUERY)
    # Ensure month column is parsed or formatted
    if not df.empty:
        df['bill_month'] = pd.to_datetime(df['bill_month'], format='%Y-%m')
        df = df.sort_values('bill_month')
    return df

def get_patient_admissions_trend():
    """
    Fetches calendar daily admissions details.
    """
    df = run_query(PATIENT_ADMISSIONS_TREND_QUERY)
    if not df.empty:
         df['admission_date'] = pd.to_datetime(df['admission_date'])
    return df

def get_operations_insights():
    """
    Evaluates key performance parameters dynamically and generates operational alerts.
    Returns:
        A list of dictionaries with 'insight_type', 'observation', and 'recommendation'.
    """
    insights = []
    
    # 1. Department with highest workload (from admissions or tests)
    try:
        admissions_df = get_admissions_by_dept()
        if not admissions_df.empty:
            highest_dept = admissions_df.iloc[0]['department_name']
            highest_count = admissions_df.iloc[0]['admission_count']
            insights.append({
                "insight_type": "Department Workload",
                "observation": f"The '{highest_dept}' department has the highest workload with {highest_count} total patient admissions.",
                "recommendation": f"Allocate additional nursing shifts and administrative staff load to the '{highest_dept}' department to optimize throughput.",
                "status": "warning"
            })
    except Exception as e:
        print(f"Could not calculate workload insight: {e}")

    # 2. Bed occupancy analysis (find ward with highest occupancy rate)
    try:
        beds_df = get_bed_occupancy()
        if not beds_df.empty:
            highest_ward = beds_df.iloc[0]
            if highest_ward['occupancy_rate'] >= 80:
                status = "danger"
            elif highest_ward['occupancy_rate'] >= 60:
                status = "warning"
            else:
                status = "success"
                
            insights.append({
                "insight_type": "Bed Capacity Limits",
                "observation": f"Ward '{highest_ward['ward_name']}' ({highest_ward['department_name']}) has the highest occupancy rate of {highest_ward['occupancy_rate']}%.",
                "recommendation": f"Trigger care-coordination discharge planning in '{highest_ward['ward_name']}' or redirect low-acuity admissions to alternative wards.",
                "status": status
            })
    except Exception as e:
         print(f"Could not calculate bed occupancy insight: {e}")

    # 3. Drugs below reorder level analysis
    try:
        drugs_df = get_drug_reorders()
        if not drugs_df.empty:
            total_short = len(drugs_df)
            top_short = drugs_df.iloc[0]
            insights.append({
                "insight_type": "Drug Inventory Shortage",
                "observation": f"There are {total_short} pharmaceutical drug items below safety stocks. '{top_short['drug_name']}' ({top_short['brand_name']}) has a deficiency of {int(top_short['deficiency_qty'])} units.",
                "recommendation": f"Approve immediate purchase order restocks for '{top_short['drug_name']}' and expedite procurement directly with the manufacturers.",
                "status": "danger"
            })
        else:
            insights.append({
                "insight_type": "Drug Inventory Shortage",
                "observation": "All pharmacy stock inventories are maintained at safe capacity levels.",
                "recommendation": "Maintain current audit intervals and supplier transaction frequencies.",
                "status": "success"
            })
    except Exception as e:
         print(f"Could not calculate drug inventory insight: {e}")

    # 4. Department with the longest average patient stay
    try:
        length_of_stay_df = get_avg_length_of_stay()
        if not length_of_stay_df.empty:
            longest_stay_dept = length_of_stay_df.iloc[0]['department_name']
            longest_stay_days = length_of_stay_df.iloc[0]['avg_stay_days']
            insights.append({
                "insight_type": "Average Length of Stay (LoS)",
                "observation": f"The '{longest_stay_dept}' department has the longest average patient length of stay at {longest_stay_days:.1f} days.",
                "recommendation": f"Establish daily case management check-ins and audits in the '{longest_stay_dept}' department to safely minimize unnecessary inpatient days.",
                "status": "warning"
            })
    except Exception as e:
         print(f"Could not calculate LoS insight: {e}")

    # 5. Highest revenue-producing department
    try:
        revenue_df = get_revenue_by_dept()
        if not revenue_df.empty:
            top_revenue_dept = revenue_df.iloc[0]['department_name']
            top_revenue_amount = revenue_df.iloc[0]['total_revenue']
            insights.append({
                "insight_type": "Financial Performance",
                "observation": f"The '{top_revenue_dept}' department generates the highest total billing revenue of ${top_revenue_amount:,.2f}.",
                "recommendation": f"Monitor billing audits and insurance coverage efficiency for '{top_revenue_dept}' to protect margins and reduce claim denials.",
                "status": "success"
            })
    except Exception as e:
         print(f"Could not calculate financial revenue insight: {e}")

    return insights

def get_db_schema():
    """
    Dynamically queries SQLite database schema to build a schema context
    containing tables, headers, and types.
    """
    if not verify_db_exists():
        return ""
    
    schema_details = []
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            col_desc = [f"{col[1]} ({col[2]})" for col in columns]
            schema_details.append(f"Table: {table}\nColumns: {', '.join(col_desc)}")
            
    return "\n\n".join(schema_details)

def query_db_with_ai(question, api_key, model="meta/llama-3.1-70b-instruct"):
    """
    Main orchestrator for AI Chatbot:
    1. Generates SQL based on database schema via NVIDIA NIM.
    2. Runs query on SQLite.
    3. Feeds back to LLM to write a friendly natural language response.
    Returns:
        dict containing 'sql', 'results' (DataFrame), 'response' (str), and 'error' (str or None)
    """
    from openai import OpenAI
    
    result = {
        "sql": "",
        "results": None,
        "response": "",
        "error": None
    }
    
    # Check API key
    if not api_key:
        result["error"] = "NVIDIA API Key is missing. Please set it in the sidebar."
        return result
        
    try:
        # Build client
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        
        schema = get_db_schema()
        
        # System instructions to produce strictly SQL code blocks
        system_prompt = f"""You are a specialized SQL expert database assistant for a hospital HMIS system.
Your job is to translate the user's natural language question into a syntactic, valid SQLite query.
Here is the strict database schema detail:
{schema}

CRITICAL RULES:
1. Return ONLY valid SQLite SQL statements within a single markdown SQL code block. For example:
   ```sql
   SELECT ... LIMIT 10;
   ```
2. Do not explain the query. Do not write text before or after the code block.
3. Use only tables and columns described in the schema.
4. If writing date operations, remember this is SQLite, so use julianday(), strftime(), etc.
5. Limit results to a maximum of 100 rows unless specified otherwise.
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.0
        )
        
        sql_content = response.choices[0].message.content.strip()
        
        # Extract SQL from markdown code block
        sql_query = ""
        if "```sql" in sql_content:
            sql_query = sql_content.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_content:
            sql_query = sql_content.split("```")[1].split("```")[0].strip()
        else:
            sql_query = sql_content
            
        result["sql"] = sql_query
        
        # Verify and run the query
        try:
            df = run_query(sql_query)
            result["results"] = df
        except Exception as query_err:
            result["error"] = f"SQLite Error: {query_err}"
            # Still attempt to give a friendly response that it failed
            return result
            
        # Generate friendly descriptive narrative
        data_preview = df.head(15).to_string()
        narrative_prompt = f"""You are a professional healthcare business analyst.
The user asked: "{question}"
To answer it, this SQL query was run:
```sql
{sql_query}
```
Here is the resulting table output from the database:
{data_preview}
(Total rows returned: {len(df)})

Write a concise, natural language response summarizing the findings for a hospital executive. 
Highlight key numbers, metrics, or insights, and provide one operational suggestion based on this data.
"""
        
        narrative_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": narrative_prompt}
            ],
            temperature=0.7
        )
        
        result["response"] = narrative_response.choices[0].message.content.strip()
        
    except Exception as e:
        result["error"] = f"NVIDIA NIM API Error: {e}"
        
    return result

if __name__ == "__main__":
    # Test queries
    if verify_db_exists():
        print("Testing statistical queries:")
        print(f"Overall stats:\n{get_overall_stats()}")
        print(f"Admissions:\n{get_admissions_by_dept().head(2)}")
        print("\nGet operations schema:")
        print(get_db_schema()[:400] + "...")
        print("\nOperations insights:")
        for ins in get_operations_insights():
            print(f"- [{ins['insight_type']}] {ins['observation']}\n  Rec: {ins['recommendation']}")
    else:
        print("Database not initialized. Run database.py first.")
