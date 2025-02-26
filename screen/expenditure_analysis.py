import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def expenditure_analysis():
    st.title("Company Expenditure Analysis")

    # Load ap.csv
    try:
        df = pd.read_csv("ap.csv", parse_dates=["Due Date"])
    except FileNotFoundError:
        st.error("ap.csv file not found.")
        return

    # Ensure 'Due Date' is in datetime format
    df["Due Date"] = pd.to_datetime(df["Due Date"], errors='coerce')

    # Extract month and year for grouping
    df["Month"] = df["Due Date"].dt.to_period("M")

    # Create 2 columns 
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Summary view of total company expenditure
        total_expenditure = df["Total"].sum()
        st.metric("Total Company Expenditure", f"${total_expenditure:,.2f}")
    
    with col3:
        # Create a dropdown for selecting departments from the list: ['HR', 'IT', 'Finance', 'Operations']
        department = st.selectbox("Select Department", ['HR', 'IT', 'Finance', 'Operations'])


    # Bar graph: Expenditure per month with category colors
    st.write("### Monthly Expenditure by Category")
    monthly_expenditure = df.groupby(["Month", "Category"])['Total'].sum().unstack().fillna(0)
    monthly_expenditure.plot(kind='bar', stacked=True, figsize=(10, 5))
    plt.xlabel("Month")
    plt.ylabel("Expenditure")
    plt.title("Monthly Expenditure by Category")
    st.pyplot(plt.gcf())

    

    # Line graph: Historical expenditure
    st.write("### Historical Expenditure Trend")
    historical_expenditure = df.groupby("Month")["Total"].sum()
    historical_expenditure.plot(kind='line', marker='o', figsize=(10, 5))
    plt.xlabel("Month")
    plt.ylabel("Total Expenditure")
    plt.title("Historical Expenditure Trend")
    st.pyplot(plt.gcf())