from __functions import *
freeze_support()

st.set_page_config(
    page_title="Sport Court Availability Checker",  # This sets the tab title
    page_icon="🎾",              # Optional: sets the tab icon
    layout="centered",           # Optional: layout options ("centered" or "wide")
    initial_sidebar_state="auto" # Optional: sidebar state ("auto", "expanded", "collapsed")
)

st.title("Sport Court Availability Checker")

# Input fields
sports_menu_df = get_sports_menu()
sports_list = sports_menu_df['Sport'].values.tolist()
sport = st.selectbox("Choose sport", sports_list)
sport_id = sports_menu_df.loc[sports_menu_df['Sport'] == sport, 'Sport ID'].values[0]
city_list = ['Jakarta Selatan', 'Jakarta Barat', 'Jakarta Pusat', 'Jakarta Utara']
city = st.selectbox("Choose city", city_list)

start_date = st.date_input("Start date", value=date.today())
end_date = st.date_input("End date", value=start_date, min_value=start_date)

with open("time_slots.json", "r", encoding="utf-8") as f:
    time_slots = json.load(f)
start_time = st.selectbox("Choose start time slot", time_slots)
index = time_slots.index(start_time)
end_time = st.selectbox("Choose end time slot", time_slots[index + 1:])

# start_time = st.slider(
#     "Choose start time",
#     min_value=0,
#     max_value=23,
#     value=0,
#     step=1,
#     format="%02d:00"
# )

# end_time = st.slider(
#     "Choose end time",
#     min_value=start_time + 1,
#     max_value=24,
#     value=start_time + 1,
#     step=1,
#     format="%02d:00"
# )
# if end_time == 24:
#     end_time = 0

# start_time = f'0{start_time}:00' if start_time < 10 else f'{start_time}:00'
# end_time = f'0{end_time}:00' if end_time < 10 else f'{end_time}:00'

# Submit button
if st.button("Check Availability"):
    status = st.empty() 

    date_range_str = f'on {start_date}' if start_date == end_date else f'from {start_date} to {end_date}'
    status.write(f"Searching {sport} court availability in {city} {date_range_str}, {start_time} - {end_time}...")
    
    location_df = get_location_menu(sport, city)
    print(location_df)

    # Generate list of dates
    date_list = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
        for i in range((end_date - start_date).days + 1)]

    # Prepare all tasks first
    tasks = []
    for index, row in location_df.iterrows():
        for date in date_list:
            tasks.append((row['Venue ID'], sport_id, date, start_time, end_time, row['Location Name']))
    
    start_run_time = datetime.now()

    # Run in parallel
    maindf = pd.DataFrame()
    workers = 8 #range 5 - 10
    with ThreadPoolExecutor(max_workers=workers) as executor:  # Adjust workers as needed
        task_map = {executor.submit(fetch_data, task): task for task in tasks}
        for future in as_completed(task_map):
            task = task_map[future]  # This is the original (venue_id, date, location_name)
            df = future.result()

            if len(df) > 0:
                maindf = pd.concat([maindf, df], ignore_index=True)
            
            del df

    finish_run_time = datetime.now()
    load_time = finish_run_time - start_run_time
    print(f'\nScraped from {start_date} to {end_date}')
    print('start time:', start_run_time)
    print('finish time:', finish_run_time)
    print('load time:', load_time)

    status.empty()
    if len(maindf) == 0:
        message = 'No available court...'
        print(message)
        status.write(message)
    else:
        maindf = maindf.sort_values(by=['Date', 'Price per Hour', 'Start Time', 'Location', 'Court'], ignore_index=True)
        print(maindf)
        status.write(f"Available {sport} Courts in {city}")
        status.dataframe(maindf)
    
    del maindf

