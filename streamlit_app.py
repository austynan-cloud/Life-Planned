import streamlit as st
from datetime import date, datetime
from supabase import create_client, Client
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Initialize Clients Using Encrypted Streamlit Secrets
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# 2. Page Configuration
st.set_page_config(page_title="Expiration Radar", layout="wide")
st.title("⚠️ Expiration Radar & Purchase Tracker")
st.subheader("Never lose money because you forgot a deadline.")

# 3. Enter Free Gemini Key Interface
GEMINI_API_KEY = st.text_input("Enter Gemini API Key (From Google AI Studio)", type="password")

# 4. Define the Data Schema for AI Extraction
class ExtractedPurchase(BaseModel):
    item_name: str = Field(description="The name of the product, subscription, or obligation")
    store: str = Field(description="The store, vendor, website, or company name")
    price: float = Field(description="The total cost or price paid. Defaults to 0.0 if not found.")
    return_deadline: str = Field(description="The final date to return the item or cancel the trial in YYYY-MM-DD format. Calculate this dynamically based on the text.")
    warranty_expiration: str = Field(description="The final date the warranty expires in YYYY-MM-DD format.")

def extract_obligation_from_text(raw_text: str) -> ExtractedPurchase:
    """Uses Gemini Free Tier to parse raw emails, text, or receipts."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    current_date_str = date.today().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are an expert receipt and email parsing engine. 
    Analyze the following text and extract the purchase or obligation details.
    Today's date is: {current_date_str}. Use this to calculate specific calendar dates.
    
    Raw text to parse:
    \"\"\"{raw_text}\"\"\"
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedPurchase,
            temperature=0.1
        ),
    )
    return ExtractedPurchase.model_validate_json(response.text)

# 5. UI Layout: Sidebar for Adding Items
with st.sidebar:
    st.header("➕ Add New Obligation")
    mode = st.radio("Input Method", ["Paste Email/Text (AI)", "Manual Entry"])
    
    if mode == "Paste Email/Text (AI)":
        user_pasted_text = st.text_area(
            "Paste receipt or confirmation email:",
            placeholder="Example: 'Thank you for your order on Sep 25. Your trial of Netflix will automatically renew for $15.49 on Oct 25...'"
        )
        if st.button("✨ Auto-Extract & Preview"):
            if not GEMINI_API_KEY:
                st.error("Please enter your Gemini API Key first.")
            elif not user_pasted_text.strip():
                st.warning("Please paste some text first!")
            else:
                with st.spinner("AI parsing..."):
                    try:
                        parsed_data = extract_obligation_from_text(user_pasted_text)
                        st.session_state['preview_data'] = parsed_data
                        st.success("Extracted! Confirm details below.")
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
    
    else:
        m_item = st.text_input("Item Name")
        m_store = st.text_input("Store/Provider")
        m_price = st.number_input("Price ($)", min_value=0.0, format="%.2f")
        m_return = st.date_input("Return Deadline", value=date.today())
        m_warranty = st.date_input("Warranty Expiration", value=date.today())
        
        if st.button("Save Manual Entry"):
            db_payload = {
                "item_name": m_item, "store": m_store, "price": m_price,
                "return_deadline": str(m_return), "warranty_expiration": str(m_warranty)
            }
            supabase.table("purchases").insert(db_payload).execute()
            st.success("Saved successfully!")
            st.rerun()

    if mode == "Paste Email/Text (AI)" and 'preview_data' in st.session_state:
        st.markdown("---")
        st.subheader("Review AI Extraction")
        data = st.session_state['preview_data']
        
        edit_item = st.text_input("Extracted Item Name", value=data.item_name)
        edit_store = st.text_input("Extracted Store", value=data.store)
        edit_price = st.number_input("Extracted Price ($)", value=data.price)
        edit_return = st.text_input("Return Deadline (YYYY-MM-DD)", value=data.return_deadline)
        edit_warranty = st.text_input("Warranty Expiration (YYYY-MM-DD)", value=data.warranty_expiration)
        
        if st.button("🔒 Confirm & Save to Database"):
            db_payload = {
                "item_name": edit_item, "store": edit_store, "price": edit_price,
                "return_deadline": edit_return, "warranty_expiration": edit_warranty
            }
            supabase.table("purchases").insert(db_payload).execute()
            st.success("Saved to database!")
            del st.session_state['preview_data']
            st.rerun()

# 6. Main Dashboard Render Layer
response = supabase.table("purchases").select("*").execute()
records = response.data

if not records:
    st.info("Your vault is empty. Use the sidebar menu to add an item or paste a receipt!")
else:
    st.markdown("### 🚨 Current Active Obligations & Deadlines")
    
    for row in records:
        return_dt = datetime.strptime(row['return_deadline'], "%Y-%m-%d").date()
        days_left = (return_dt - date.today()).days
        
        if days_left <= 0:
            progress = 1.0
            status_text = "❌ Return Window Closed"
        else:
            progress = max(0.0, min(1.0, (30 - days_left) / 30))
            status_text = f"⏳ {days_left} days left"
            
        col1, col2 = st.columns()
        with col1:
            st.markdown(f"**{row['item_name'].upper()}** — Bought from *{row['store']}* (${row['price']})")
            st.progress(progress)
        with col2:
            st.markdown(f"**{status_text}**")
        st.write("---")
        
