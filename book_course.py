import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION (from .env) ---
# 1. The URL of the specific course page (where you normally click "Buchen")
start_url = os.getenv('COURSE_URL')

# 2. The main script URL (used for all POSTs)https://www.hochschulsport.uni-mannheim.de/angebote/aktueller_zeitraum_0/_Power_Move.html#K11911010
post_url = "https://www.hochschulsport.uni-mannheim.de/cgi/anmeldung.fcgi"

# 3. Your Personal Data (from environment variables)
user_data = {
    'sex': os.getenv('SEX', 'X'),
    'vorname': os.getenv('VORNAME'),
    'name': os.getenv('NAME'),
    'strasse': os.getenv('STRASSE'),
    'ort': os.getenv('ORT'),
    'statusorig': os.getenv('STATUS'),
    'matnr': os.getenv('MATNR'),
    'email': os.getenv('EMAIL'),
    'telefon': os.getenv('TELEFON', ''),
    'tnbed': '1',   # Terms & Conditions
    'tnbed2': '1',  # Code of Conduct
}

# Validate required fields
required_fields = ['vorname', 'name', 'strasse', 'ort', 'statusorig', 'matnr', 'email']
missing = [f for f in required_fields if not user_data.get(f)]
if missing:
    raise ValueError(f"Missing required environment variables: {missing}")
if not start_url:
    raise ValueError("Missing COURSE_URL in .env file")

# Use a Session to keep cookies (Essential!)
session = requests.Session()

# Browser-like headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

def post_form(url, data, referer):
    """Post form data with proper headers"""
    post_headers = {
        **headers,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.hochschulsport.uni-mannheim.de',
        'Referer': referer,
    }
    return session.post(url, data=data, headers=post_headers)

try:
    # --- STEP 1: GET COURSE LISTING PAGE ---
    print("1. Fetching course listing page...")
    r1 = session.get(start_url, headers=headers)
    soup1 = BeautifulSoup(r1.text, 'html.parser')
    
    # Find the 'buchen' button - name is like "BS_Kursid_XXXXX"
    book_btn = soup1.find('input', {'value': 'buchen'})
    if not book_btn:
        raise Exception("No 'buchen' button found on the course listing page!")
    
    book_btn_name = book_btn['name']
    print(f"   > Found booking button: {book_btn_name}")
    
    # Find the form action URL
    form = book_btn.find_parent('form')
    form_action = form.get('action', post_url) if form else post_url
    if not form_action.startswith('http'):
        form_action = "https://www.hochschulsport.uni-mannheim.de" + form_action
    
    time.sleep(0.5)  # Small delay to mimic human behavior
    
    # --- STEP 2: CLICK BUCHEN TO GET DATE SELECTION ---
    print("2. Clicking 'buchen' to get date selection...")
    
    payload_step1 = {book_btn_name: 'buchen'}
    r2 = post_form(form_action, payload_step1, start_url)
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    with open('debug_step2_dates.html', 'w', encoding='utf-8') as f:
        f.write(r2.text)
    print("   > Saved response to debug_step2_dates.html")
    
    # Get the FID from date selection page
    fid_input = soup2.find('input', {'name': 'fid'})
    if not fid_input:
        raise Exception("No FID found on date selection page!")
    fid = fid_input['value']
    print(f"   > Got FID: {fid}")
    
    # Find available date buttons (BS_Termin_YYYY-MM-DD)
    date_buttons = soup2.find_all('input', {'value': 'buchen', 'name': lambda x: x and x.startswith('BS_Termin_')})
    if not date_buttons:
        raise Exception("No available dates found! Course may be fully booked.")
    
    # Select the first available date
    date_btn = date_buttons[0]
    date_btn_name = date_btn['name']
    termin_date = date_btn_name.replace('BS_Termin_', '')
    print(f"   > Available dates: {[btn['name'].replace('BS_Termin_', '') for btn in date_buttons]}")
    print(f"   > Selecting date: {termin_date}")
    
    time.sleep(0.5)
    
    # --- STEP 3: CLICK DATE TO GET REGISTRATION FORM ---
    print("3. Clicking date to get registration form...")
    
    payload_step2 = {
        'fid': fid,
        date_btn_name: 'buchen'
    }
    r3 = post_form(post_url, payload_step2, post_url)
    soup3 = BeautifulSoup(r3.text, 'html.parser')
    
    with open('debug_step3_form.html', 'w', encoding='utf-8') as f:
        f.write(r3.text)
    print("   > Saved response to debug_step3_form.html")
    
    # Check if we got the registration form (should have sex/vorname/name fields)
    sex_field = soup3.find('select', {'name': 'sex'}) or soup3.find('input', {'name': 'sex'})
    if not sex_field:
        # We might have skipped directly to confirmation if already registered before
        if soup3.find('input', {'name': '_formdata'}):
            print("   > Skipped to confirmation (may have saved data)")
            soup4 = soup3
            r4 = r3
        else:
            raise Exception("Did not get registration form as expected!")
    else:
        # --- STEP 4: SUBMIT PERSONAL DATA ---
        print("4. Submitting personal data...")
        
        # Get hidden fields
        hidden_fields = {}
        for hidden in soup3.find_all('input', {'type': 'hidden'}):
            name = hidden.get('name')
            value = hidden.get('value', '')
            if name:
                hidden_fields[name] = value
        
        payload_step3 = {
            **hidden_fields,
            **user_data
        }
        
        print(f"   > Payload keys: {list(payload_step3.keys())}")
        
        # IMPORTANT: The registration form has an anti-bot countdown timer (btime=21)
        # When formdata.ik === 0, the submit button is disabled for ~21 seconds
        # The server may also validate this timing, so we need to wait
        print("   > Waiting 22 seconds (anti-bot countdown timer)...")
        time.sleep(22)
        
        r4 = post_form(post_url, payload_step3, post_url)
        soup4 = BeautifulSoup(r4.text, 'html.parser')
        
        with open('debug_step4_confirm.html', 'w', encoding='utf-8') as f:
            f.write(r4.text)
        print("   > Saved response to debug_step4_confirm.html")
    
    # --- STEP 5: FINAL CONFIRMATION ---
    print("5. Looking for confirmation form...")
    
    form_data_input = soup4.find('input', {'name': '_formdata'})
    if not form_data_input:
        # Check for error messages
        error_msg = soup4.find('div', {'class': 'bs_meldung'})
        if error_msg:
            print(f"   > Server error: {error_msg.get_text(strip=True)[:200]}")
        raise Exception("No _formdata token found! Cannot confirm booking.")
    
    form_data_token = form_data_input['value']
    print(f"   > Got _formdata token: {form_data_token}")
    
    # Get ALL hidden fields from confirmation page - this is crucial
    confirm_payload = {}
    for inp in soup4.find_all('input'):
        name = inp.get('name')
        value = inp.get('value', '')
        input_type = inp.get('type', 'text')
        # Include hidden fields (these contain all the required data)
        if name and input_type == 'hidden':
            confirm_payload[name] = value
        # Also include text fields (like optional password field) - send empty if no value
        elif name and input_type == 'text':
            confirm_payload[name] = value  # Include even if empty
    
    # Note: Keep _formdata as-is from the server.
    # The JavaScript chk_pw() function would modify it under certain conditions,
    # but those conditions don't apply with the current server response.
    # if '_formdata' in confirm_payload:
    #     original_formdata = int(confirm_payload['_formdata'])
    #     confirm_payload['_formdata'] = str(original_formdata + 2)
    #     print(f"   > Modified _formdata: {original_formdata} -> {confirm_payload['_formdata']}")
    
    print(f"   > Confirmation payload: {confirm_payload}")
    
    time.sleep(0.5)
    
    print("6. Sending FINAL confirmation...")
    r5 = post_form(post_url, confirm_payload, post_url)
    
    with open('debug_step5_final.html', 'w', encoding='utf-8') as f:
        f.write(r5.text)
    print("   > Saved response to debug_step5_final.html")
    
    # --- CHECK SUCCESS ---
    response_text = r5.text.lower()
    if r5.status_code == 200 and ("bestätigung" in response_text or "gebucht" in response_text or "erfolgreich" in response_text):
        print("\n✅ SUCCESS! Registration Complete.")
    else:
        print("\n❌ Check debug_step5_final.html. Registration might have failed.")
        if "warteliste" in response_text:
            print("   Note: You may have been added to the waiting list.")
        if "ausgebucht" in response_text:
            print("   Note: The course appears to be fully booked.")
        if "fehler" in response_text:
            print("   Note: An error occurred.")
        # Print error details
        soup5 = BeautifulSoup(r5.text, 'html.parser')
        error_div = soup5.find('div', {'class': 'bs_meldung'})
        if error_div:
            print(f"   Server message: {error_div.get_text(strip=True)[:300]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
