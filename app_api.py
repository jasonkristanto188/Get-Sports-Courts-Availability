from get_schedule_app import *
freeze_support()

st.set_page_config(
    page_title="Sport Court Availability Checker",  # This sets the tab title
    page_icon="🎾",              # Optional: sets the tab icon
    layout="centered",           # Optional: layout options ("centered" or "wide")
    initial_sidebar_state="auto" # Optional: sidebar state ("auto", "expanded", "collapsed")
)

st.title("Sport Court Availability Checker")

# Input fields
with open("sports.json", "r", encoding="utf-8") as f:
    sports_list = json.load(f)
sport = st.selectbox("Choose sport", sports_list)

city_list = ['Jakarta Selatan', 'Jakarta Barat', 'Jakarta Pusat', 'Jakarta Utara']
city = st.selectbox("Choose city", city_list)

start_date = st.date_input("Start date", value=date.today())
end_date = st.date_input("End date", value=start_date, min_value=start_date)
min_days_later = (start_date - date.today()).days
max_days_later = (end_date - date.today()).days

with open("time_slots.json", "r", encoding="utf-8") as f:
    time_slots = json.load(f)
start_time_slot = st.selectbox("Choose start time slot", time_slots)
index = time_slots.index(start_time_slot)
end_time_slot = st.selectbox("Choose end time slot", time_slots[index + 1:])

# Submit button
if st.button("Check Availability"):
    status = st.empty() 

    date_range_str = f'on {start_date}' if start_date == end_date else f'from {start_date} to {end_date}'
    start_time = start_time_slot.split(':')[0].strip()
    end_time = end_time_slot.split('-')[-1].split(':')[0].strip()
    status.write(f"Searching {sport} court availability in {city} {date_range_str}, {start_time}:00 - {end_time}:00...")
    
    # Here you can call your scraping function (after refactoring it to be reusable)
    maindf = pd.DataFrame()

    start_run_time = datetime.now()
    
    # Replace with your server's IP if not running locally
    url = 'http://192.168.7.80:1881/get_court_schedule'

    payload = {
        "city": city,
        "sport": sport,
        "min_days_later": min_days_later,
        "max_days_later": max_days_later,
        "start_time": start_time,
        "end_time": end_time
    }
    
    response = requests.post(url, json=payload)
    non_empty_dfs = None

    if response.status_code == 200:
        print("Results:", response.json())
        # json_data = response.json()
        non_empty_dfs = pd.DataFrame(response.json())

        maindf = pd.concat([maindf, *non_empty_dfs], ignore_index=True)
        maindf = maindf.sort_values(by=['Date', 'Price', 'Location', 'Court'], ignore_index=True)
        print(maindf)
        status.empty()
        status.write(f"Available {sport} Courts in {city}")
        status.dataframe(maindf)
    else:
        print("Error:", response.status_code, response.text)

        message = 'No available court...'
        status.empty()
        st.write(message)

    finish_run_time = datetime.now()
    load_time = finish_run_time - start_run_time
    print(f'\nScraped from {start_date} to {end_date}')
    print('start time:', start_run_time)
    print('finish time:', finish_run_time)
    print('load time:', load_time)
