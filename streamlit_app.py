import streamlit as st
from datetime import datetime, date
from supabase import create_client, Client

# 1. Database Connection (Replace with your free Supabase credentials)
URL = "YOUR_SUPABASE_URL"
KEY = "YOUR_SUPABASE_ANON_KEY"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Expiration Radar", layout="unconstrained")
st.title("⚠️ Expiration Radar & Purchase Tracker")
st.subheader("Never lose money because you forgot a deadline.")

# 2. Add New Purchase Form
with st.sidebar.expander("➕ Add New Purchase / Obligation", expanded=False):
    item = st.text_input("Item / Obligation Name", placeholder="e.g., Sony Headphones")
    store = st.text_input("Store / Provider", placeholder="e.g., Best Buy")
    price = st.number_input("Price ($)", min_value=0.0, format="%.2f")
    p_date = st.date_input("Purchase Date", value=date.today())
    r_dead = st.date_input("Return Deadline")
    w_dead = st.date_input("Warranty Expiration")
    
    if st.button("Save to Vault"):
        data = {
            "item_name": item, "store": store, "price": price,
            "purchase_date": str(p_date), "return_deadline": str(r_dead),
            "warranty_expiration": str(w_dead)
        }
        supabase.table("purchases").insert(data).execute()
        st.success("Saved successfully!")
        st.rerun()

# 3. Fetch and Render the Persistent Dashboard
response = supabase.table("purchases").select("*").execute()
records = response.data

if not records:
    st.info("Your vault is empty. Add an item or forward a receipt to begin!")
else:
    st.markdown("### 🚨 Urgent Attention Required")
    
    for row in records:
        return_dt = datetime.strptime(row['return_deadline'], "%Y-%m-%d").date()
        days_left = (return_dt - date.today()).days
        
        # Calculate visual progress bar logic
        if days_left <= 0:
            progress = 1.0
            status_text = "❌ Return Window Closed"
        else:
            # Assume a standard 30-day return window baseline for visual scaling
            progress = max(0.0, min(1.0, (30 - days_left) / 30))
            status_text = f"⏳ {days_left} days left to return"
            
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{row['item_name'].upper()}** — Bought at {row['store']} (${row['price']})")
            st.progress(progress)
        with col2:
            st.write(status_text)
        st.write("---")
pip install google-genai pydantic

