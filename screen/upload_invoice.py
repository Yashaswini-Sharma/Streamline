import matplotlib.pyplot as plt
import streamlit as st
import pytesseract
from PIL import Image
import google.generativeai as genai
import json, os, io
import pandas as pd
from dotenv import load_dotenv
from functools import lru_cache
from utils.similarity_checker import verify_item_against_goals, get_item_variations

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

@lru_cache(maxsize=100)
def get_cached_variations(item):
    """Cache item variations to avoid repeated Gemini API calls."""
    return get_item_variations(item, model)

def extract_text_from_image(image):
    """Extract text from image using OCR."""
    text = pytesseract.image_to_string(image)
    return text

def process_document(file):
    image = Image.open(file)
    text = extract_text_from_image(image)
    return text

def analyze_with_gemini(text):
    """Use Gemini API to extract structured information from text."""
    prompt = """
    You are an invoice analysis expert. Given the following invoice text, extract:
    1. Invoice number
    2. Invoice date
    3. All items with their descriptions, quantities, and prices
    4. Subtotal, tax (if present), and total amount
    5. Categorize the type of product

    Return the data in this JSON format:
    {
        "invoice_info": {
            "number": "invoice number",
            "date": "invoice date"
        },
        "items": [
            {
                "description": "full item description",
                "quantity": number,
                "price": number,
                "total": number,
                "category": "product category"
            }
        ],
        "summary": {
            "subtotal": number,
            "tax": number,
            "total": number
        }
    }

    Invoice text:
    """ + text

    response = model.generate_content(prompt)
    json_str = response.text
    if '```json' in json_str:
        json_str = json_str.split('```json')[1].split('```')[0]
    return json.loads(json_str.strip())

def save_to_csv(data, filename="invoice_data.csv"):
    """Save extracted data to CSV file."""
    # Define standard columns
    columns = [
        "Invoice Number", "Due Date", "Description", "Quantity", "Price",
        "Subtotal", "Tax", "Total", "Category", "Suspicious"  # Removed extra column
    ]
    
    try:
        df = pd.DataFrame(data)
        # Ensure all columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        # Reorder columns
        df = df[columns]
        
        if not os.path.isfile(filename):
            df.to_csv(filename, index=False)
        else:
            df.to_csv(filename, mode='a', header=False, index=False)
            
    except Exception as e:
        st.error(f"Error saving to CSV: {str(e)}")
        raise

def read_from_csv(filename="invoice_data.csv"):
    """Read data from CSV file."""
    columns = [
        "Invoice Number", "Due Date", "Description", "Quantity", "Price",
        "Subtotal", "Tax", "Total", "Category", "Suspicious"  # Removed extra column
    ]
    
    try:
        if os.path.isfile(filename):
            # Read CSV with specific columns
            df = pd.read_csv(filename)
            # Ensure all required columns exist
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            return df[columns]  # Return only specified columns in correct order
        else:
            return pd.DataFrame(columns=columns)
    except pd.errors.ParserError as e:
        st.error(f"Error reading CSV file: {str(e)}")
        # Try to recover data
        try:
            df = pd.read_csv(filename, on_bad_lines='skip')
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            return df[columns]
        except:
            return pd.DataFrame(columns=columns)

def read_company_goals():
    """Read company goals from CSV."""
    try:
        return pd.read_csv("company_goals.csv")
    except FileNotFoundError:
        st.warning("No company goals found. Please add some goals first.")
        return pd.DataFrame(columns=["Goals", "Number of Items", "Outcomes", "Due Date", "Key Results"])

def upload_invoice():
    st.title("Invoice Management")
    
    # Load company goals
    company_goals = read_company_goals()
    
    # Show current goals for reference
    if not company_goals.empty:
        st.info("Current Company Goals:")
        st.dataframe(company_goals[["Goals", "Number of Items"]], use_container_width=True)
    
    uploaded_file = st.file_uploader("Choose an invoice file", type=['png', 'jpg', 'jpeg', 'webp'])

    if uploaded_file is not None:
        text = process_document(uploaded_file)
        
        if text:
            if st.button('Extract Data'):
                with st.spinner('Processing...'):
                    try:
                        data = analyze_with_gemini(text)
                        rows = []
                        
                        # Process each item in the invoice
                        for item in data['items']:
                            # Initialize flags
                            is_suspicious = True  # Default to suspicious
                            matched_goal = None
                            
                            try:
                                if not company_goals.empty:
                                    # Check item against goals using similarity checker
                                    is_suspicious, matched_goal = verify_item_against_goals(
                                        item['description'],
                                        company_goals['Goals'].tolist(),
                                        model
                                    )
                                    
                                    if is_suspicious:
                                        st.warning(f"⚠️ Suspicious item detected: {item['description']}")
                                    else:
                                        # Find matching goal details
                                        goal_row = company_goals[company_goals['Goals'].str.lower() == matched_goal.lower()]
                                        if not goal_row.empty:
                                            st.success(f"✅ Item '{item['description']}' matches goal: {matched_goal}")
                                            
                                            # Check quantity against goal
                                            goal_quantity = goal_row.iloc[0]['Number of Items']
                                            if item['quantity'] > goal_quantity:
                                                st.warning(f"⚠️ Quantity ({item['quantity']}) exceeds goal quantity ({goal_quantity})")
                                                is_suspicious = True
                                else:
                                    st.warning("No company goals defined - all items will be marked as suspicious")
                                    is_suspicious = True
                                    matched_goal = "No goals defined"
                                
                            except Exception as e:
                                st.error(f"Error checking item: {str(e)}")
                                is_suspicious = True
                                matched_goal = "Error checking"
                            
                            row = {
                                "Invoice Number": data['invoice_info']['number'],
                                "Due Date": data['invoice_info']['date'],
                                "Description": item['description'],
                                "Quantity": item['quantity'],
                                "Price": item['price'],
                                "Subtotal": data['summary']['subtotal'],
                                "Tax": data['summary'].get('tax', 0),
                                "Total": data['summary']['total'],
                                "Category": item['category'],
                                "Suspicious": is_suspicious
                            }
                            rows.append(row)
                        
                        # Save to CSV
                        save_to_csv(rows)
                        
                        # Display results with color coding
                        if rows:
                            df = pd.DataFrame(rows)
                            st.dataframe(
                                df,
                                column_config={
                                    "Suspicious": st.column_config.CheckboxColumn(
                                        "Suspicious",
                                        help="Items not matching company goals or exceeding quantities"
                                    ),
                                    "Description": st.column_config.TextColumn(
                                        "Description",
                                        help="Item description",
                                        width="large"
                                    )
                                },
                                use_container_width=True
                            )
                            
                            # Show summary
                            suspicious_count = df['Suspicious'].sum()
                            if suspicious_count > 0:
                                st.warning(f"Found {suspicious_count} suspicious items in this invoice!")
                            else:
                                st.success("All items match company goals!")
                            
                    except Exception as e:
                        st.error(f"Error processing invoice: {str(e)}")

# Display existing information from CSV
st.header("Invoice Data")
existing_data = read_from_csv()
st.dataframe(
    existing_data,
    column_config={
        "Suspicious": st.column_config.CheckboxColumn(
            "Suspicious",
            help="Items not matching company goals"
        ),
        "Matched Goal": st.column_config.TextColumn(
            "Matched Goal",
            help="Matching company goal if found"
        )
    },
    use_container_width=True
)