import streamlit as st
import pandas as pd
import requests, os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

def format_date(date_str):
    """Convert any date string to DD-MM-YYYY format."""
    try:
        # Try different date formats and convert to desired format
        date_formats = [
            "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d",
            "%d-%m-%y", "%d/%m/%y", "%y-%m-%d", "%y/%m/%d"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime("%d-%m-%Y")
            except ValueError:
                continue
                
        # If no format matches, try to extract date parts using Gemini
        prompt = f"Extract day, month, and year from this text and return in DD-MM-YYYY format: {date_str}"
        response = model.generate_content(prompt)
        formatted_date = response.text.strip()
        
        # Validate the formatted date
        datetime.strptime(formatted_date, "%d-%m-%Y")
        return formatted_date
    except:
        return "01-01-2024"  # Default date if parsing fails

def parse_product_info(text):
    """Extract product name and quantity from text."""
    prompt = f"""
    From this text: "{text}", extract:
    1. Product/item name (without numbers)
    2. Quantity (only the number)
    
    Return in format: name|quantity
    Example: "500 computers" should return: computers|500
    """
    response = model.generate_content(prompt)
    parts = response.text.strip().split('|')
    if len(parts) == 2:
        name = parts[0].strip()
        try:
            quantity = int(''.join(filter(str.isdigit, parts[1])))
        except:
            quantity = 0
        return name, quantity
    return "Unknown", 0

def insert_to_csv(data):
    """Insert data to CSV file."""
    try:
        # Extract product name and quantity
        product_name, number_of_items = parse_product_info(data[0])

        # Format the data
        formatted_data = {
            "Goals": product_name,  # Product name without quantity
            "Number of Items": number_of_items,
            "Outcomes": data[1],
            "Due Date": format_date(data[2]),
            "Key Results": "NA"  # Default value
        }
        
        # Check if file exists
        if os.path.exists("company_goals.csv"):
            existing_df = pd.read_csv("company_goals.csv")
            new_df = pd.DataFrame([formatted_data], columns=["Goals", "Number of Items", "Outcomes", "Due Date", "Key Results"])
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = pd.DataFrame([formatted_data], columns=["Goals", "Number of Items", "Outcomes", "Due Date", "Key Results"])
        
        # Save to CSV
        updated_df.to_csv("company_goals.csv", index=False)
        return True, formatted_data
    except Exception as e:
        st.error(f"Error saving to CSV: {str(e)}")
        return False, None

def read_from_csv():
    """Read data from CSV file."""
    # Read data from CSV
    df = pd.read_csv("company_goals.csv")
    return df

def company_goals():
    st.title("Create Company Goals")
    st.write("Chatbot interface goes here...")

    # Input from user
    user_input = st.text_input("Enter your goals in natural language:")

    if st.button("Submit"):
        if user_input:
            prompt = f"""
            You are a business analyst. Given the following text: {user_input}, extract:
            1. Product/item description with quantity (e.g., "500 PCs" or "10 hamburgers")
            2. Expected outcomes
            3. Due date
            
            Return the output separated by | delimiter without any headers.
            Make sure the product description includes both item name and quantity.
            Example: 500 computers | Increased inventory | 31-12-2024
            """
            
            response = model.generate_content(prompt)
            goals = response.text.strip()

            # Split the response and clean the data
            goals_list = [goal.strip() for goal in goals.split('|') if goal.strip()]
            
            if len(goals_list) >= 3:  # We only need 3 fields now
                success, formatted_data = insert_to_csv(goals_list)
                if success:
                    st.success("Goal added successfully!")
                    
                    # Display the newly added goal
                    st.write("Extracted Goals:")
                    st.write({
                        "Goals": formatted_data["Goals"],
                        "Number of Items": formatted_data["Number of Items"],
                        "Outcomes": formatted_data["Outcomes"],
                        "Due Date": formatted_data["Due Date"],
                        "Key Results": formatted_data["Key Results"]
                    })
            else:
                st.error("Invalid response format from AI. Please try again.")
        else:
            st.warning("Please enter some text before submitting.")
    
    # Add a divider
    st.divider()
    
    # Display existing goals
    st.header("Existing Company Goals")
    try:
        existing_goals = read_from_csv()
        if not existing_goals.empty:
            st.dataframe(
                existing_goals,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Goals": st.column_config.TextColumn("Goals", width="medium"),
                    "Number of Items": st.column_config.NumberColumn("Number of Items", width="small"),
                    "Outcomes": st.column_config.TextColumn("Outcomes", width="medium"),
                    "Due Date": st.column_config.TextColumn("Due Date", width="small"),
                    "Key Results": st.column_config.TextColumn("Key Results", width="medium")
                }
            )
        else:
            st.info("No existing goals found.")
    except FileNotFoundError:
        st.info("No goals have been created yet.")
