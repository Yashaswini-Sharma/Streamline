import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def parse_date(date_str):
    """Parse date string into datetime object, handling different formats."""
    date_formats = [
        "%Y-%m-%d",    # 2024-07-19
        "%d.%m.%Y",    # 19.07.2024
        "%m/%d/%y",    # 7/19/24
        "%d/%m/%y",    # 19/07/24
        "%Y/%m/%d",    # 2024/07/19
        "%m-%d-%y",    # 7-19-24
        "%d-%m-%y",    # 19-07-24
        "%m/%d/%Y",    # 7/19/2024
        "%d/%m/%Y"     # 19/07/2024
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
            
    # If no format matches, try to standardize the date string
    try:
        # Remove any leading/trailing whitespace and handle missing century
        clean_date = date_str.strip()
        if len(clean_date) <= 8:  # Short format like 7/19/24
            # Assume 20xx for year
            parts = clean_date.replace('-', '/').split('/')
            if len(parts) == 3:
                month, day, year = parts
                if len(year) == 2:
                    year = '20' + year
                return datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y")
    except:
        pass
        
    raise ValueError(f"time data '{date_str}' does not match any known format")


def accounts_payable():
    st.title("Accounts Payable")

    # Load or create ap.csv with error handling
    try:
        ap_df = pd.read_csv("ap.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        ap_df = pd.DataFrame()
    except pd.errors.ParserError:
        st.error("Error reading ap.csv - file may be corrupted")
        ap_df = pd.DataFrame()

    # Load invoice data with error handling
    try:
        invoice_df = pd.read_csv("invoice_data.csv")
        # Ensure required columns exist
        required_columns = ["Invoice Number", "Due Date", "Price", "Total", "Category", "Verified"]
        for col in required_columns:
            if col not in invoice_df.columns:
                invoice_df[col] = None
    except (FileNotFoundError, pd.errors.EmptyDataError):
        invoice_df = pd.DataFrame(columns=required_columns)
    except pd.errors.ParserError:
        st.error("Error reading invoice_data.csv - file may be corrupted")
        invoice_df = pd.DataFrame(columns=required_columns)

    # Select necessary columns
    selected_columns = ["Invoice Number", "Due Date", "Price", "Total", "Category", "Verified"]
    df = invoice_df[selected_columns].copy()

    # Add Payment Overdue column
    df["Payment Overdue"] = df["Due Date"].apply(lambda x: "Yes" if parse_date(x) < datetime.now() else "No")

    # Add Payment Status column
    df["Payment Status"] = "Pending"

    # Display summary and pie chart
    st.write("### Overview")
    summary_cols = st.columns([1, 2])

    # Left column: Summary stats
    total_invoices = df.shape[0]
    overdue_count = df[df["Payment Overdue"] == "Yes"].shape[0]
    with summary_cols[0]:
        st.metric("Total Invoices", total_invoices)
        st.metric("Overdue Payments", overdue_count)

    # Right column: Pie chart
    successful_count = df[df["Payment Status"] == "Successful"].shape[0]
    labels = ['Failed Payments', 'Successful Payments']
    sizes = [overdue_count, successful_count]
    colors = ['#FF6B6B', '#6BCB77']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    with summary_cols[1]:
        st.pyplot(fig)

    # Display data in separate columns with buttons
    st.write("### Accounts Payable Overview")
    # Header row
    header_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
    headers = ["Invoice Number", "Due Date", "Price", "Total", "Category", "Verified", "Payment Overdue", "Actions"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")

    for idx, row in df.iterrows():
        cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
        cols[0].write(row["Invoice Number"])
        cols[1].write(row["Due Date"])
        cols[2].write(row["Price"])
        cols[3].write(row["Total"])
        cols[4].write(row["Category"])
        cols[5].write(row["Verified"])
        cols[6].write(f"Overdue: {'🔴' if row['Payment Overdue'] == 'Yes' else '🟢'}")
        if cols[7].button(f"Pay Now", key=f"pay_{idx}"):
            with st.spinner(f"Processing Payment for Invoice {row['Invoice Number']}"):
                st.write("Processing payment...")
                # Simulate payment process
                payment_success = True  # Replace with actual payment logic
                if payment_success:
                    st.success("Payment Successful!")
                    df.at[idx, "Payment Status"] = "Successful"
                else:
                    st.error("Payment Failed!")
                    df.at[idx, "Payment Status"] = "Failed"

    # Save button to write to ap.csv
    if st.button("Save Changes"):
        df.to_csv("ap.csv", index=False)
        st.success("Changes saved to ap.csv")

    # Display existing ap.csv data
    if not ap_df.empty:
        st.write("### Existing Accounts Payable Data")
        st.dataframe(ap_df, use_container_width=True)
