#last updated: 2025-07-24

from __dependencies import *

def safe_click(driver, element):
    try:
        element.click()
    except Exception as e1:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            driver.execute_script("arguments[0].click();", element)
        except Exception as e2:
            try:
                ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
            except Exception as e3:
                print("safe_click failed:", e1, e2, e3)

def get_schedule_wrapper(web_options, city, chosen_sport, min_days_later, max_days_later, location_name, start_time, end_time):
    print('\nCurrent location:', location_name)

    driver = webdriver.Edge(options=web_options)
    wait = WebDriverWait(driver, 30)
    driver.get('https://ayo.co.id/venues')
    mainlist = []
    
    try:
        location_textbox_xpath = '//*[@id="namesearch"]'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, location_textbox_xpath)))
        location_textbox = driver.find_element(By.XPATH, location_textbox_xpath)
        location_textbox.send_keys(location_name)

        cari_venue_button_xpath = '//*[@id="submitSearchSparring"]'
        cari_venue_button = driver.find_element(By.XPATH, cari_venue_button_xpath)
        safe_click(driver, cari_venue_button)

        target_location_xpath = '/html/body/main/div[3]/div[2]/form/div/div[3]/div/div[1]/div/a/div/div'
        target_location_name_xpath = f'{target_location_xpath}/h5[1]'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, target_location_xpath)))
        target_location_name = driver.find_element(By.XPATH, target_location_name_xpath).text
        if location_name.lower().strip() == target_location_name.lower().strip():
            target_location = driver.find_element(By.XPATH, target_location_name_xpath)
            safe_click(driver, target_location)

        for days_later in range(min_days_later, max_days_later + 1):
            date_available = False

            #click calendar icon
            if days_later > 0:
                while True:
                    try:
                        calendar_button_xpath = '//*[@id="field-full-calendar-btn"]'
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, calendar_button_xpath)))
                        calendar_button = driver.find_element(By.XPATH, calendar_button_xpath)
                        safe_click(driver, calendar_button)
                        time.sleep(3)
                        break
                    except:
                        print('Scrolling for calendar button...')
                        scroll_value = 100 if days_later == min_days_later else -200
                        ActionChains(driver).scroll_by_amount(0, scroll_value).perform()

                #start scraping from today until max_range
                try:
                    next_datetime = datetime.now() + timedelta(days=days_later)
                    datekey = next_datetime.strftime('%Y-%m-%d')
                    # price = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, f'ffci-price-{datekey}'))).text
                    price = driver.find_element(By.ID, f'ffci-price-{datekey}').text
                    
                    if price.strip() != '':
                        target_date = driver.find_element(By.ID, f'ffci-{datekey}')
                        safe_click(driver, target_date)
                        time.sleep(3)

                        check_calendar_xpath = '//*[@id="field_option_section"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]'
                        check_calendar_text = driver.find_element(By.XPATH, check_calendar_xpath).text.strip()
                        
                        replace_months = {
                            'Mei': 'May', 'Agu': 'Aug', 'Okt': 'Oct', 'Des': 'Dec'
                        }
                        for indo, eng in replace_months.items():
                            check_calendar_text = check_calendar_text.replace(indo, eng)
                        
                        monthday_key = datetime.strptime(datekey, '%Y-%m-%d').strftime('%d %b')
                        if monthday_key.startswith('0'):
                            monthday_key = monthday_key[1:]
                        
                        if check_calendar_text == monthday_key:
                            date_available = True 
                        else:
                            print(f'Booking NOT AVAILABLE for {location_name} on {datekey}... Moving on to the next location...')
                            break
                    else:
                        print(f'Booking NOT AVAILABLE for {location_name} on {datekey}... Moving on to the next location...')
                        break
                except:
                    print(f'Error in selecting {datekey}... Moving on to the next location...')
                    break
            
            if date_available:

                #get time slots from each court found in the location
                courts_xpath = '/html/body/main/div[3]/div[7]/div[2]/div[4]/div'
                courts = wait.until(EC.visibility_of_all_elements_located((By.XPATH, courts_xpath)))
                for court_index in range(1, len(courts) + 1):
                    current_court_xpath = f'{courts_xpath}[{court_index}]'
                    current_court_name_xpath = f'{current_court_xpath}/div[1]/div[2]/div/div[1]'
                    current_court_name = driver.find_element(By.XPATH, current_court_name_xpath).text
                    
                    sports_xpath = f'{current_court_xpath}/div[1]/div[2]/div/div[4]'
                    while True:
                        try:
                            sport = wait.until(EC.visibility_of_element_located((By.XPATH, sports_xpath))).text.strip()
                            break
                        except:
                            ActionChains(driver).scroll_by_amount(0, 50).perform()
                    if sport.lower().strip() != chosen_sport.lower().strip():
                        continue
                    
                    jadwal_button_xpath = f'{current_court_xpath}/div[1]/div[2]/div/div[10]/span[2]'
                    while True:
                        try:
                            jadwal_button = wait.until(EC.visibility_of_element_located((By.XPATH, jadwal_button_xpath)))
                            break
                        except:
                            ActionChains(driver).scroll_by_amount(0, 50).perform()

                    if 'jadwal tersedia' in jadwal_button.text.lower().strip():
                        print(f'AVAILABLE: {current_court_name} for {sport} at {location_name} on {datekey}...')   
                        safe_click(driver, jadwal_button)
                        time.sleep(3)

                        court_type_xpath = f'{current_court_xpath}/div[1]/div[2]/div/div[8]'
                        court_type = driver.find_element(By.XPATH, court_type_xpath).text

                        time_slots_xpath = f'{current_court_xpath}/div[1]/div[2]/div/div[12]/div'
                        time_slots = driver.find_elements(By.XPATH, time_slots_xpath)
                        # print(f'there are {len(time_slots)} found for {court_type} at {location_name} on {datekey}')
                        
                        for time_slot_index in range(1, len(time_slots) + 1):
                            current_time_slot_xpath = f'{time_slots_xpath}[{time_slot_index}]/div/div/span'
                            time_status_xpath = f'{current_time_slot_xpath}[3]'
                            time_status = driver.find_element(By.XPATH, time_status_xpath).text

                            current_time_xpath = f'{current_time_slot_xpath}[2]'
                            current_time = driver.find_element(By.XPATH, current_time_xpath).text
                            current_start_time = current_time.split(':')[0].strip()

                            if time_status.strip().lower() != 'booked' and time_status.strip().lower() != '' \
                                and (start_time <= current_start_time and current_start_time < end_time):
                                harga_lapangan_xpath = f'{current_time_slot_xpath}[3]'
                                harga_lapangan = driver.find_element(By.XPATH, harga_lapangan_xpath).text
                                mainlist.append([location_name, current_court_name, court_type, harga_lapangan, current_time, datekey])
                    else:
                        print(f'NOT AVAILABLE: {current_court_name} for {sport} at {location_name} on {datekey}...')   
    except:
        print('\nScraping has gone for too long....\n')
        pass

    if len(mainlist) > 0:
        df = pd.DataFrame(mainlist)
        df.columns = ['Location', 'Court', 'Court Type', 'Price', 'Time Slot', 'Date']
        print(df)
        return df
    else:
        return pd.DataFrame()

def get_location_list(web_options, city, chosen_sport):
    driver = webdriver.Edge(options=web_options)
    wait = WebDriverWait(driver, 60)

    driver.get('https://ayo.co.id/venues')
    pilih_kota_textbox_xpath = '/html/body/main/div[3]/div[2]/form/div/div[1]/div[2]/input'
    wait.until(EC.visibility_of_element_located((By.XPATH, pilih_kota_textbox_xpath))).send_keys(city)
    time.sleep(2)

    #enter city
    city_choice_xpath = '/html/body/ul/li'
    city_choice = wait.until(EC.visibility_of_element_located((By.XPATH, city_choice_xpath)))
    safe_click(driver, city_choice)

    pilih_cabang_olaraga_button = driver.find_element(By.XPATH, '//*[@id="aktifitas"]')
    safe_click(driver, pilih_cabang_olaraga_button)

    sport_choices_xpath = '//*[@id="list-search"]/div/div[1]/div[3]/ul/li'
    sport_choices = wait.until(EC.visibility_of_all_elements_located((By.XPATH, sport_choices_xpath)))
    for sport_index in range(1, len(sport_choices) + 1):
        sport_xpath = f'{sport_choices_xpath}[{sport_index}]/a'
        try:
            sport_elem = driver.find_element(By.XPATH, sport_xpath)
            if sport_elem.text.lower().strip() == chosen_sport.lower().strip():
                safe_click(driver, sport_elem)
                break
        except:
            ActionChains(driver).scroll_by_amount(0, 50).perform()

    # click search
    cari_venue_button_xpath = '//*[@id="submitSearchSparring"]'
    safe_click(driver, driver.find_element(By.XPATH, cari_venue_button_xpath))
    time.sleep(3)

    # fetch locations
    locations_xpath = '/html/body/main/div[3]/div[2]/form/div/div[3]/div/div[1]/div'
    wait.until(EC.presence_of_element_located((By.XPATH, locations_xpath)))
    location_elements = driver.find_elements(By.XPATH, locations_xpath)

    location_list = []
    for location_index in range(1, len(location_elements) + 1):
        current_location_xpath = f'{locations_xpath}[{location_index}]'
        harga_path = f'{current_location_xpath}/a/div/div/p[2]/span[2]'
        harga = wait.until(EC.visibility_of_element_located((By.XPATH, harga_path))).text

        #if harga = 0, just check another location
        if harga.lower().strip() == 'rp0':
            continue

        location_name_path = f'{current_location_xpath}/a/div/div/h5[1]'
        location_name = driver.find_element(By.XPATH, location_name_path).text
        location_list.append(location_name)
    
    driver.quit()

    return location_list
