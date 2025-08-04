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
sport_list_xlsx_path = 'Sport List.xlsx'
sport_list_df = pd.read_excel(sport_list_xlsx_path)
sport = st.selectbox("Choose sport", sport_list_df['Sport'].values.tolist())

city_list = ['Jakarta Selatan', 'Jakarta Barat', 'Jakarta Pusat', 'Jakarta Utara']
city = st.selectbox("Choose city", city_list)

start_date = st.date_input("Start date", value=date.today())
end_date = st.date_input("End date", value=start_date, min_value=start_date)

time_slots_xlsx_path = 'Time Slots.xlsx'
time_slots_df = pd.read_excel(time_slots_xlsx_path)
time_slots = time_slots_df['Time Slots'].values.tolist()
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
    web_options = Options()
    web_options.add_argument('--headless=new')
    web_options.add_argument('--window-size=1920,1080')
    web_options.add_argument('--disable-gpu')
    prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.fonts": 2
        }
    web_options.add_experimental_option("prefs", prefs)

    location_list = get_location_list(web_options, city, sport)

    process_pools = int(os.cpu_count() * 0.75)
    if process_pools > len(location_list):
        process_pools = len(location_list)

    min_days_later = (start_date - date.today()).days
    max_days_later = (end_date - date.today()).days
    args_list = [(web_options, city, sport, min_days_later, max_days_later, loc, start_time, end_time) for loc in location_list]
    
    start_time = datetime.now()

    with Pool(processes=process_pools) as pool:
        dfs = pool.starmap(get_schedule_wrapper, args_list)
    
    finish_time = datetime.now()
    load_time = finish_time - start_time
    print(f'\nScraped from {start_date} to {end_date}')
    print('start time:', start_time)
    print('finish time:', finish_time)
    print('load time:', load_time)

    non_empty_dfs = [df for df in dfs if isinstance(df, pd.DataFrame) and not df.empty]
    if not non_empty_dfs:
        message = 'No available court...'
        print(message)
        st.write(message)
    else:
        maindf = pd.concat([maindf, *non_empty_dfs], ignore_index=True)
        maindf = maindf.sort_values(by=['Date', 'Price', 'Location', 'Court'], ignore_index=True)
        print(maindf)
        status.empty()
        status.write(f"Available {sport} Courts in {city}")
        status.dataframe(maindf)
