from __dependencies import *

def get_sports_menu():
    # Create a session to persist cookies
    session = requests.Session()

    # Set headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://ayo.co.id/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Make the GET request
    response = session.get("https://ayo.co.id/venues", headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <a> tags with id starting with "pilihan"
    pilihan_items = soup.find_all("a", id=lambda x: x and x.startswith("pilihan"))

    menu_list = []
    # Extract and print the sport names
    for item in pilihan_items:
        sport_id = item.get("onclick").split("(")[1].split(",")[0].strip()
        sport_name = item.text.strip()
        menu_list.append([int(sport_id), sport_name])
    
    menu_df = pd.DataFrame(menu_list)
    menu_df.columns = ['Sport ID', 'Sport']
    menu_df = menu_df.sort_values(by='Sport', ignore_index=True)
    
    return menu_df

def get_location_menu(sport, city):
    # Create a session
    session = requests.Session()

    # Define headers (same as before)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "Referer": "https://ayo.co.id/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Define query parameters or form data
    params = {
        "nameuser": city  # This simulates typing into the search bar
    }

    # Send the request
    response = session.get("https://ayo.co.id/venues", headers=headers, params=params)

    # Parse the response
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all venue containers
    venue_containers = soup.find_all("div", class_="venue-card-item")

    # Prepare list for filtered results
    filtered_venues = []

    for container in venue_containers:
        venue_id = container.get("id").split('-')[-1]

        # Find the card body inside each container
        card = container.find("div", class_="card-body")
        if not card:
            continue

        # Extract venue name
        venue_name_tag = card.find("h5", class_="text-left s20-500 turncate")
        venue_name = venue_name_tag.text.strip() if venue_name_tag else None

        # Extract location
        location_tag = card.find("h5", class_="text-left s14-400")
        location_text = location_tag.text.split('Kota')[-1].strip() if location_tag else ""

        # Check for 'Padel' in <img alt="">
        sport_img_tags = card.find_all("img")
        padel_found = any(img.get("alt") == sport for img in sport_img_tags)

        # Apply all filters
        if venue_name and city in location_text and padel_found:
            filtered_venues.append({
                "Venue ID": venue_id,
                "Location Name": venue_name
            })

    df = pd.DataFrame(filtered_venues)
    return df

def get_data(venue_id, sport_id, date, start_time, end_time, location_name):
    # Step 1: Fetch the raw JSON data
    url = f"https://ayo.co.id/venues-ajax/op-times-and-fields?venue_id={venue_id}&date={date}"
    params = {
        "venue_id": {venue_id}
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    response = requests.get(url, params=params, headers=headers)
    response_json = response.json()

    # Step 2: Filter only available slots and keep selected fields
    records = []
    start_time = f"{start_time}:00"
    end_time = f"{end_time}:00"
    for field in response_json.get("fields", []):
        field_name = field.get("field_name")
        obtained_sport_id = field.get("sport_id")
        if obtained_sport_id == sport_id:
            for slot in field.get("slots", []):
                if slot.get("is_available") == 1 and start_time <= slot.get("start_time") and slot.get("start_time") < end_time:
                    current_record = {
                        "Location": location_name,
                        "Court": field_name,
                        "Price": f"{slot.get("price"):,}".replace(",", "."),
                        "Start Time": slot.get("start_time"),
                        "End Time": slot.get("end_time"),
                        "Date": slot.get("date")
                    }
                    records.append(current_record)
                    # print(current_record)

    # Step 3: Create a DataFrame
    df = pd.DataFrame(records)

    return df

# Define a wrapper for get_data
def fetch_data(args):
    venue_id, sport_id, date, start_time, end_time, location_name = args
    return get_data(venue_id, sport_id, date, start_time, end_time, location_name)
