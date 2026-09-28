import os
from datetime import date, datetime
from supabase import create_client, Client
from resend import Resend

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
MY_EMAIL = os.environ.get("NOTIFICATION_EMAIL")

if not all([SUPABASE_URL, SUPABASE_KEY, RESEND_API_KEY, MY_EMAIL]):
    print("Error: Missing one or more environment variable configurations.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
resend_client = Resend(api_key=RESEND_API_KEY)

def check_and_send_alerts():
    response = supabase.table("purchases").select("*").execute()
    records = response.data
    urgent_items = []
    
    for row in records:
        return_dt = datetime.strptime(row['return_deadline'], "%Y-%m-%d").date()
        days_left = (return_dt - date.today()).days
        
        if days_left == 3:
            urgent_items.append(
                f"⚠️ <b>{row['item_name']}</b> (Store: {row['store']}) — "
                f"Return deadline closes in 3 days ({row['return_deadline']})"
            )
            
    if urgent_items:
        email_body = "<h3>🚨 Expiration Radar Notification</h3>"
        email_body += "<p>You have urgent financial deadlines arriving in 3 days:</p><ul>"
        for item in urgent_items:
            email_body += f"<li>{item}</li>"
        email_body += "</ul><p>Please manage these items inside your dashboard application.</p>"
        
        resend_client.emails.send({
            "from": "ExpirationRadar <onboarding@resend.dev>",
            "to": [MY_EMAIL],
            "subject": "🚨 Notice: 3 Days Remaining Until Return Window Closes",
            "html": email_body
        })
        print(f"Alert engine successful. Dispatched alert digest for {len(urgent_items)} items.")
    else:
        print("Daily automation run complete. No matching deadlines found today.")

if __name__ == "__main__":
    check_and_send_alerts()
