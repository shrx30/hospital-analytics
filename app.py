"""
Hospital Operations Analytics - Streamlit Dashboard
Multi-page analytical dashboard for hospital administrators to track operational performance,
identify bottlenecks, and make operational decisions.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set up page configurations
st.set_page_config(
    page_title="Hospital Operations dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom header styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #0D9488;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 16px;
        color: #94A3B8;
        margin-bottom: 25px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Check if database exists, run auto-ingest or prompt user
import database
import analysis

if not analysis.verify_db_exists():
    st.info("🏥 Hospital Operations database file not detected.")
    st.write("Click below to download the Hospital HMIS dataset from Kaggle and configure the SQLite database automatically.")
    
    if st.button("Download Dataset & Initialize SQLite DB", type="primary"):
        with st.spinner("Downloading from Kaggle and preparing tables... This may take a minute..."):
            try:
                database.download_and_setup_data()
                database.load_data_to_sqlite()
                st.success("Database initialized! Reloading dashboard...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to setup database: {e}")
    st.stop()

# Load common statistics
@st.cache_data
def get_stats():
    return analysis.get_overall_stats()

# Helper components
def render_kpi(title, value, icon, color="#0D9488"):
    """
    Displays a custom, beautifully formatted metric card in HTML.
    """
    st.markdown(
        f"""
        <div style="background-color: #1E293B; border-left: 5px solid {color}; padding: 18px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 12px; height: 110px;">
            <p style="margin: 0; font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">{title}</p>
            <h3 style="margin: 8px 0 0 0; font-size: 26px; color: #FFFFFF; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                <span style="color: {color};">{icon}</span> {value}
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_insight_card(title, observation, recommendation, status):
    """
    Displays bootstrap-like alert cards for operations insights.
    """
    colors = {
        "danger": {"bg": "#7F1D1D", "border": "#EF4444", "text": "#FBCFE8", "icon": "🚨"},
        "warning": {"bg": "#78350F", "border": "#F59E0B", "text": "#FEF3C7", "icon": "⚠️"},
        "success": {"bg": "#064E3B", "border": "#10B981", "text": "#D1FAE5", "icon": "✅"},
    }
    c = colors.get(status, {"bg": "#1E293B", "border": "#0D9488", "text": "#E2E8F0", "icon": "💡"})
    st.markdown(
        f"""
        <div style="background-color: {c['bg']}; border: 1px solid {c['border']}; border-left: 6px solid {c['border']}; padding: 18px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin: 0; font-size: 15.5px; color: #FFFFFF; font-weight: 700;">{c['icon']} {title}</h4>
            <p style="margin: 8px 0; font-size: 13.5px; color: #E2E8F0; line-height: 1.5;"><strong>Observation:</strong> {observation}</p>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(255, 255, 255, 0.2);">
                <p style="margin: 0; font-size: 12px; color: {c['border']}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">💡 Recommendation:</p>
                <p style="margin: 2px 0 0 0; font-size: 13.5px; color: #F8FAFC; font-style: italic;">{recommendation}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Sidebar navigation setup
st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #0D9488; margin-bottom: 5px; font-weight: 800;">🏥 HMIS Portal</h2>
        <p style="color: #94A3B8; font-size: 13px;">Operations Analyst Workbench</p>
    </div>
    """,
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Go To Page:",
    [
        "Executive Dashboard",
        "Patient Analytics",
        "Operations Dashboard",
        "Financial Dashboard",
        "Inventory Dashboard",
        "AI Operations Assistant"
    ]
)

# Fetch overall aggregate stats
stats = get_stats()
total_patients = stats.iloc[0]['total_patients']
total_doctors = stats.iloc[0]['total_doctors']
total_admissions = stats.iloc[0]['total_admissions']
total_revenue = stats.iloc[0]['total_revenue']
active_occupied = stats.iloc[0]['active_occupied_beds']
total_beds = stats.iloc[0]['total_beds']
current_bed_occupancy_rate = round((active_occupied / total_beds) * 100, 1)

# Fetch dataframes for dashboard
admissions_by_dept = analysis.get_admissions_by_dept()
revenue_by_dept = analysis.get_revenue_by_dept()
bed_occupancy = analysis.get_bed_occupancy()
doctor_workload = analysis.get_doctor_workload()
drug_reorder = analysis.get_drug_reorders()
avg_stay = analysis.get_avg_length_of_stay()
insurance_stats = analysis.get_insurance_stats()

# Set departments list for sidebar filter
all_departments = sorted(admissions_by_dept['department_name'].unique().tolist())

# Shared template style for Plotly charts
def update_plotly_dark(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=50, b=40),
        font=dict(color="#F8FAFC", family="Arial")
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1E293B", linecolor="#334155")
    fig.update_yaxes(showgrid=True, gridcolor="#1E293B", linecolor="#334155")
    return fig

# ----------------- 1. EXECUTIVE DASHBOARD -----------------
if page == "Executive Dashboard":
    st.markdown("<h1 class='main-title'>Hospital Executive Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Operations Overview, High-Level Key Performance Indicators & Operations Insights</p>", unsafe_allow_html=True)

    # Key Performance Indicators Row
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        render_kpi("Overall Patients", f"{total_patients:,}", "👥", "#3B82F6")
    with kpi_cols[1]:
        render_kpi("Total Admissions", f"{total_admissions:,}", "🛏️", "#0D9488")
    with kpi_cols[2]:
        render_kpi("Total Invoiced", f"${total_revenue/1e6:.2f}M", "💳", "#10B981")
    with kpi_cols[3]:
        render_kpi("Live Occupancy", f"{current_bed_occupancy_rate}%", "🏨", "#F59E0B")
    with kpi_cols[4]:
        render_kpi("Stock Reorders", f"{len(drug_reorder)}", "💊", "#EF4444")

    # Main columns
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### Clinical Admissions & Financial Volume")
        # Combine Admissions & Billing details for a Dual Chart
        admissions_revenue_df = pd.merge(admissions_by_dept, revenue_by_dept, on="department_name")
        
        # Dual Plot
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=admissions_revenue_df['department_name'],
            y=admissions_revenue_df['admission_count'],
            name="Patient Admissions",
            marker_color="#0D9488",
            yaxis="y1"
        ))
        fig.add_trace(go.Scatter(
            x=admissions_revenue_df['department_name'],
            y=admissions_revenue_df['total_revenue'] / 1000,
            name="Revenue ($k)",
            mode="lines+markers",
            line=dict(color="#FF8A65", width=3),
            yaxis="y2"
        ))
        
        fig.update_layout(
            title="Department admissions vs Invoiced Revenue",
            yaxis=dict(title="Number of Admissions", color="#0D9488"),
            yaxis2=dict(title="Billing ($k)", overlaying="y", side="right", color="#FF8A65"),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(15,23,42,0.8)"),
            hovermode="x unified"
        )
        update_plotly_dark(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        # Bed occupancy status across departments
        st.markdown("### Department Inpatient Stay Bottlenecks")
        stay_bed = pd.merge(avg_stay, bed_occupancy, on="department_name", how="inner")
        fig_stay = px.scatter(
            stay_bed,
            x="avg_stay_days",
            y="occupancy_rate",
            size="total_beds",
            hover_name="department_name",
            color="department_name",
            text="department_name",
            title="Ward Occupancy Rate vs Average Length of Stay",
            labels={"avg_stay_days": "Average Stay (Days)", "occupancy_rate": "Bed Occupancy Rate (%)"}
        )
        fig_stay.update_traces(textposition="top center", marker=dict(sizeref=0.5))
        update_plotly_dark(fig_stay)
        st.plotly_chart(fig_stay, use_container_width=True)

    with col_right:
        st.markdown("### 📋 System Operations Insights")
        st.caption("Auto-generated alerts requiring administrative action:")
        
        insights = analysis.get_operations_insights()
        for ins in insights:
            render_insight_card(
                title=ins['insight_type'],
                observation=ins['observation'],
                recommendation=ins['recommendation'],
                status=ins['status']
            )

# ----------------- 2. PATIENT ANALYTICS -----------------
elif page == "Patient Analytics":
    st.markdown("<h1 class='main-title'>Patient Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Inpatient Flow, Admissions Scheduling & Clinical Department Distribution</p>", unsafe_allow_html=True)

    # Sidebar parameters inside sidebar specifically for filtering
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Patient Filters")
    selected_depts = st.sidebar.multiselect("Select Departments:", all_departments, default=all_departments)
    
    # Date range filters
    admissions_df = analysis.get_patient_admissions_trend()
    min_date = admissions_df['admission_date'].min().date()
    max_date = admissions_df['admission_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range Filter:",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Format filters
    # If the user selects date range
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    # Filter admissions data
    filtered_admissions = admissions_df[
        (admissions_df['admission_date'] >= start_date) & 
        (admissions_df['admission_date'] <= end_date) &
        (admissions_df['department_name'].isin(selected_depts))
    ]

    # Calculate filtered KPIs
    filt_count = filtered_admissions['admission_count'].sum()
    avg_stay_df = avg_stay[avg_stay['department_name'].isin(selected_depts)]
    filt_stay = avg_stay_df['avg_stay_days'].mean() if not avg_stay_df.empty else 0.0

    p_cols = st.columns(3)
    with p_cols[0]:
        render_kpi("Filtered Admissions", f"{filt_count:,}", "🎟️", "#3B82F6")
    with p_cols[1]:
        render_kpi("Mean Stay Duration", f"{filt_stay:.2f} Days", "⌛", "#0D9488")
    with p_cols[2]:
        render_kpi("Dept coverage", f"{len(selected_depts)} / {len(all_departments)}", "🏥", "#F59E0B")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("### Total Admissions Trend")
        # Regroup daily to show admissions curve
        daily_trend = filtered_admissions.groupby('admission_date')['admission_count'].sum().reset_index()
        fig_trend = px.line(
            daily_trend,
            x="admission_date",
            y="admission_count",
            title="Daily Admissions Volume",
            line_shape="spline",
            color_discrete_sequence=["#0D9488"]
        )
        update_plotly_dark(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_chart2:
        st.markdown("### Avg Length of Stay (LoS) by Department")
        fig_stay = px.bar(
            avg_stay_df,
            y="department_name",
            x="avg_stay_days",
            orientation="h",
            color="avg_stay_days",
            color_continuous_scale="Viridis",
            labels={"department_name": "Clinical Department", "avg_stay_days": "Days"},
            title="Length of Stay (LoS) Comparison"
        )
        update_plotly_dark(fig_stay)
        st.plotly_chart(fig_stay, use_container_width=True)

    # Detailed table view
    st.markdown("### Clinical Admissions Inpatient Dataset Table")
    # Read raw admissions table join department
    raw_adm = analysis.run_query("""
        SELECT a.admission_id, a.admission_date, a.discharge_date, a.admission_type, a.admission_status, 
               p.gender, p.blood_group, d.department_name, ds.disease_name
        FROM admission a
        JOIN patient p ON a.patient_id = p.patient_id
        JOIN department d ON a.department_id = d.department_id
        LEFT JOIN disease ds ON a.disease_id = ds.disease_id
    """)
    raw_adm['admission_date'] = pd.to_datetime(raw_adm['admission_date'])
    filt_raw_adm = raw_adm[
        (raw_adm['admission_date'] >= start_date) &
        (raw_adm['admission_date'] <= end_date) &
        (raw_adm['department_name'].isin(selected_depts))
    ]
    st.dataframe(filt_raw_adm.head(500), use_container_width=True)

# ----------------- 3. OPERATIONS DASHBOARD -----------------
elif page == "Operations Dashboard":
    st.markdown("<h1 class='main-title'>Hospital Operations Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Capacity Management, Bed Allocation Stats & Provider Workload Distribution</p>", unsafe_allow_html=True)

    # KPIs Row
    op_kpis = st.columns(4)
    with op_kpis[0]:
        render_kpi("Total Bed Count", f"{total_beds}", "🛏️", "#3B82F6")
    with op_kpis[1]:
        render_kpi("Occupied Beds", f"{active_occupied}", "🔴", "#EF4444")
    with op_kpis[2]:
        render_kpi("Available Beds", f"{total_beds - active_occupied}", "🟢", "#10B981")
    with op_kpis[3]:
        render_kpi("Bed Occupancy Rate", f"{current_bed_occupancy_rate}%", "📊", "#F59E0B")

    col_beds, col_workload = st.columns([1, 1])

    with col_beds:
        st.markdown("### Bed Occupancy Rates by Ward")
        # Create clear Plotly chart showing occupancy levels
        fig_oc = px.bar(
            bed_occupancy,
            x="ward_name",
            y="occupancy_rate",
            color="occupancy_rate",
            color_continuous_scale="Peach",
            labels={"occupancy_rate": "Occupancy Rate (%)", "ward_name": "Ward Name"},
            title="Bed Occupancy Rate (%) per Ward"
        )
        update_plotly_dark(fig_oc)
        st.plotly_chart(fig_oc, use_container_width=True)

    with col_workload:
        st.markdown("### Doctor Workload Distribution")
        # Bar chart showing diagnostic tests processed
        top_docs = doctor_workload.head(15)
        fig_doc = px.bar(
            top_docs,
            x="total_tests",
            y="doctor_name",
            color="specialization",
            orientation="h",
            title="Top 15 Doctors by Diagnostic Workload",
            labels={"doctor_name": "Doctor", "total_tests": "Diagnostic Tests Cleared"}
        )
        update_plotly_dark(fig_doc)
        st.plotly_chart(fig_doc, use_container_width=True)

    # Ward Table details
    st.markdown("### Ward Bed Asset Inventory Details")
    # Join bed table
    ward_details = analysis.run_query("""
        SELECT w.ward_name, w.ward_type, d.department_name,
               SUM(CASE WHEN b.bed_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_beds,
               SUM(CASE WHEN b.bed_status = 'Available' THEN 1 ELSE 0 END) AS available_beds,
               COUNT(b.bed_id) as total_beds
        FROM bed b
        JOIN ward w ON b.ward_id = w.ward_id
        JOIN department d ON w.department_id = d.department_id
        GROUP BY w.ward_name, w.ward_type, d.department_name
    """)
    st.dataframe(ward_details, use_container_width=True)

# ----------------- 4. FINANCIAL DASHBOARD -----------------
elif page == "Financial Dashboard":
    st.markdown("<h1 class='main-title'>Hospital Financial Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Billing Analyses, Invoiced Revenue Trends & Insurance Claims Status</p>", unsafe_allow_html=True)

    # Financial KPIs
    total_insurance = insurance_stats['total_insurance_covered'].sum()
    total_payable = insurance_stats['total_patient_payable'].sum()
    total_billing_value = revenue_by_dept['total_revenue'].sum()

    f_cols = st.columns(4)
    with f_cols[0]:
        render_kpi("Gross Billings", f"${total_billing_value:,.2f}", "💵", "#3B82F6")
    with f_cols[1]:
        render_kpi("Insurance covered", f"${total_insurance:,.2f}", "🛡️", "#10B981")
    with f_cols[2]:
        render_kpi("Patient Out-of-Pocket", f"${total_payable:,.2f}", "💸", "#F59E0B")
    with f_cols[3]:
        render_kpi("Provider Claims Filed", f"{insurance_stats['claims_count'].sum():,}", "📜", "#8B5CF6")

    col_rev_trend, col_rev_dept = st.columns(2)

    with col_rev_trend:
        st.markdown("### Monthly Billing Run Rate")
        rev_trend_df = analysis.get_revenue_trends()
        
        # Plotly Area Chart
        fig_trend = px.area(
            rev_trend_df,
            x="bill_month",
            y=["monthly_revenue", "monthly_insurance_covered", "monthly_patient_payable"],
            labels={"value": "Total Amount ($)", "bill_month": "Billing Month", "variable": "Revenue Streams"},
            title="MoM Billing Trend Breakdown",
            color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B"]
        )
        update_plotly_dark(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_rev_dept:
        st.markdown("### Revenue Breakdown by Clinical Department")
        # Stacked bar showing insurance vs out-of-pocket
        fig_dept_rev = go.Figure()
        fig_dept_rev.add_trace(go.Bar(
            x=revenue_by_dept['department_name'],
            y=revenue_by_dept['insurance_covered'],
            name="Insurance Covered",
            marker_color="#10B981"
        ))
        fig_dept_rev.add_trace(go.Bar(
            x=revenue_by_dept['department_name'],
            y=revenue_by_dept['patient_payable'],
            name="Patient Out-Of-Pocket",
            marker_color="#F59E0B"
        ))
        fig_dept_rev.update_layout(barmode="stack", title="Department billing: Insurance Covered vs Patient Out-of-Pocket")
        update_plotly_dark(fig_dept_rev)
        st.plotly_chart(fig_dept_rev, use_container_width=True)

    # Data table of Insurance Providers details
    st.markdown("### Insurance Providers Claims Performance Table")
    st.dataframe(insurance_stats, use_container_width=True)

# ----------------- 5. INVENTORY DASHBOARD -----------------
elif page == "Inventory Dashboard":
    st.markdown("<h1 class='main-title'>Hospital Inventory Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Pharmacy Stocks Management, Manufacturer Ratings & Restocking Signals</p>", unsafe_allow_html=True)

    # General KPIs
    total_drugs = analysis.run_query("SELECT COUNT(*) as count FROM drug").iloc[0]['count']
    total_stock_count = analysis.run_query("SELECT SUM(current_stock) as count FROM drug_inventory").iloc[0]['count']
    shortage_count = len(drug_reorder)

    inv_cols = st.columns(3)
    with inv_cols[0]:
        render_kpi("Drug Catalog Items", f"{total_drugs}", "🏷️", "#3B82F6")
    with inv_cols[1]:
        render_kpi("Current Stock Inventory", f"{int(total_stock_count):,}", "📦", "#10B981")
    with inv_cols[2]:
        render_kpi("Critical Reorder Alert", f"{shortage_count}", "⚠️", "#EF4444")

    col_inv1, col_inv2 = st.columns(2)

    with col_inv1:
        st.markdown("### Critical Low Stock Items overview")
        top_reorder = drug_reorder.head(10)
        
        if not top_reorder.empty:
            # Bar chart displaying stock level vs reorder level
            fig_inv = go.Figure()
            fig_inv.add_trace(go.Bar(
                y=top_reorder['drug_name'],
                x=top_reorder['current_stock'],
                name='Current Stock Status',
                orientation='h',
                marker_color='#EF4444'
            ))
            fig_inv.add_trace(go.Bar(
                y=top_reorder['drug_name'],
                x=top_reorder['reorder_level'],
                name='Required Safety Level',
                orientation='h',
                marker_color='#334155'
            ))
            fig_inv.update_layout(barmode='group', title="Critical Drug Stock vs Safety Reorder Levels")
            update_plotly_dark(fig_inv)
            st.plotly_chart(fig_inv, use_container_width=True)
        else:
             st.success("No drug stocks are below safety reorder limits!")

    with col_inv2:
        st.markdown("### Pharmacy manufacturer Supplier Metrics")
        # Manufacturer reliability rating scatter chart
        manufacturers = analysis.run_query("""
            SELECT manufacturer_name, country, reliability_rating, contract_status
            FROM drug_manufacturer
        """)
        fig_mfg = px.scatter(
            manufacturers,
            x="reliability_rating",
            y="manufacturer_name",
            color="contract_status",
            size="reliability_rating",
            hover_data=["country"],
            title="Manufacturer Reliability Rating Index",
            labels={"reliability_rating": "Reliability Score (1-10)", "manufacturer_name": "Supplier"},
            color_discrete_sequence=["#10B981", "#EF4444", "#F59E0B"]
        )
        update_plotly_dark(fig_mfg)
        st.plotly_chart(fig_mfg, use_container_width=True)

    # Low Inventory list and action recommendation
    st.markdown("### 🛒 Immediate Restock Operations Order List")
    if not drug_reorder.empty:
        # Create restock suggestions list
        st.dataframe(drug_reorder, use_container_width=True)
    else:
        st.info("No supplier purchase orders needed. Current pharmacy inventories are fully stocked.")

# ----------------- 6. AI OPERATIONS ASSISTANT -----------------
elif page == "AI Operations Assistant":
    st.markdown("<h1 class='main-title'>AI Operations Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Ask natural language questions about the hospital system. Translated to SQL & answered using NVIDIA NIM API.</p>", unsafe_allow_html=True)

    # API credentials check in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 NVIDIA NIM Setup")
    
    # Read API key from environment, or let user input it
    env_api_key = os.environ.get("NVIDIA_API_KEY", "")
    api_key_input = st.sidebar.text_input("NVIDIA API Key:", value=env_api_key, type="password", help="Enter your NVAPI key starting with 'nvapi-'")
    
    selected_model = st.sidebar.selectbox(
        "NIM LLM Model:",
        ["meta/llama-3.1-70b-instruct", "nvidia/llama-3.1-nemotron-70b-instruct", "meta/llama-3.1-8b-instruct"]
    )
    
    # Simple alert if key is missing
    if not api_key_input:
        st.warning("🔒 Please enter an NVIDIA API Key in the sidebar to chat with the database.")
        st.info("💡 You can get a free developer API key with 1000 credits on the [NVIDIA API Catalog](https://build.nvidia.com).")
    
    # Show database schema so the user knows what they can ask
    with st.expander("📋 Database Schema Map"):
        st.write("Here is the exact schema map mapped to our SQLite database tables:")
        st.code(analysis.get_db_schema(), language="text")

    # Chat interface
    st.markdown("### 💬 Operations Assistant Chat")
    
    # Prompt examples
    st.caption("Try asking questions like:")
    st.code("Show me the average patient stay by department.\nWhich drugs have current stock below 50 units?\nHow much total revenue is generated by department?\nWho are the top 5 doctors by number of tests handled?")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message and message["sql"]:
                with st.expander("🔍 SQL Query Executed"):
                    st.code(message["sql"], language="sql")
            if "df" in message and message["df"] is not None:
                st.dataframe(message["df"], use_container_width=True)

    # Accept user input
    if prompt := st.chat_input("Ask a question about database tables..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process response
        if not api_key_input:
            with st.chat_message("assistant"):
                st.error("Error: Please provide a valid NVIDIA API Key in the sidebar first.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("AI is examining schema and compiling query..."):
                    res = analysis.query_db_with_ai(prompt, api_key_input, selected_model)
                    
                    if res["error"]:
                        st.error(res["error"])
                        if res["sql"]:
                            st.code(res["sql"], language="sql")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"Failed to complete query. Error: {res['error']}",
                            "sql": res["sql"],
                            "df": None
                        })
                    else:
                        with st.expander("🔍 SQL Query Executed"):
                            st.code(res["sql"], language="sql")
                        st.dataframe(res["results"], use_container_width=True)
                        st.markdown(res["response"])
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": res["response"],
                            "sql": res["sql"],
                            "df": res["results"]
                        })
