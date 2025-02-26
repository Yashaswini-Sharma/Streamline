import streamlit as st
from screen.company_goals import company_goals
from screen.upload_invoice import upload_invoice
from screen.accounts_payable import accounts_payable
from screen.expenditure_analysis import expenditure_analysis

# Streamlit App Setup
st.set_page_config(page_title="Invoice Fraud Detection", layout="wide")

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Create Company Goals", "Upload Invoices", "Accounts Payable", "Company Expenditure Analysis"])

# Session State for User Roles
if 'role' not in st.session_state:
    st.session_state.role = st.sidebar.selectbox("Select Role", ["AP Specialist", "Compliance Officer", "Finance Manager", "Data Scientist"])


if page == "Create Company Goals" and st.session_state.role == "AP Specialist":
    company_goals()

if page == "Upload Invoices":
    upload_invoice()

if page == "Accounts Payable":
    accounts_payable()

if page == "Company Expenditure Analysis":
    expenditure_analysis()