from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright,expect
import pandas as pd
import time
from datetime import datetime

USEREMAIL = "username@gmail.com"
PASSWORD = "passw0rd"

def main():
    context_manager = sync_playwright()
    playwright = context_manager.__enter__()
    browser = playwright.chromium.launch(headless=False)
    expect.set_options(timeout=30_000)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://ais.usvisa-info.com/tr-tr/niv/users/sign_in")
    time.sleep(3)
    page.get_by_label("E-posta *").click()
    page.get_by_label("E-posta *").fill(USEREMAIL)
    page.get_by_label("E-posta *").press("Tab")
    page.get_by_label("Parola").fill(PASSWORD)
    time.sleep(1)
    page.locator("label").filter(has_text="Gizlilik Politikasını ve").locator("div").click()
    page.get_by_role("button", name="Oturum Aç").click()
    time.sleep(5)
    page.wait_for_selector("img")

    mevcutrandevutarihi = get_current_appointment_date(page)

    page.get_by_role("link", name="Devam Et").click()
    time.sleep(2)
    page.get_by_role("tab", name=" Randevuyu Yeniden Zamanla").click()
    time.sleep(3)
    page.get_by_role("link", name="Randevuyu Yeniden Zamanla").click()
    time.sleep(3)
    page.get_by_label("Randevu Tarihi *").click()
    time.sleep(3)

    buldugumtarih = get_earliest_available_date(page)

    compare_dates_and_notify(mevcutrandevutarihi, buldugumtarih)

    page.get_by_role("link", name="Eylemler").click()
    page.get_by_role("link", name="Oturumu Kapat").click()

    browser.close()

def get_current_appointment_date(page):
    new_html = page.content()
    soup = BeautifulSoup(new_html, 'html.parser')

    given_str = soup.find('p', {'class': 'consular-appt'}).get_text().strip()

    date_str = given_str.split('\n')[1].strip().split(',')[0]
    year = given_str.split('\n')[1].strip().split(',')[1].strip()

    months = {
        'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
        'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12
    }

    date_parts = [part.strip() for part in date_str.split()]
    day = date_parts[0]
    month = date_parts[1]
    year = year

    return datetime(int(year), months[month], int(day))

def get_earliest_available_date(page):
    new_html = page.content()
    soup = BeautifulSoup(new_html, 'html.parser')

    # Find the <div> element
    div_element = soup.find('div', {'id': 'ui-datepicker-div'})

    td_elements = div_element.find_all('td', {'class': 'undefined'})

    # Assuming td_elements contains the list of <td> elements you provided
    filtered_elements = [td for td in td_elements if td.get('class') == ['undefined'] and 
                        td.get('data-event') == 'click' and 
                        td.get('data-handler') == 'selectDay']

    # Initialize an empty list to store the extracted data
    data_list = []

    # Iterate over each element in filtered_elements
    for soup in filtered_elements:
        # Extract date, data-month, and data-year from the soup
        date = soup.find('a').get_text()
        month = soup.get('data-month')
        if len(month) == 1:
            month = "0" + month
        else:
            None
        year = soup.get('data-year')

        # Convert date to the desired format
        date_formatted = f"{date.zfill(2)}/{month}/{year}"

        # Append the extracted data to the data_list
        data_list.append({"Date": date_formatted})

    # Create a pandas DataFrame from the data_list
    df = pd.DataFrame(data_list)

    while df.__len__() == 0:
        page.get_by_title("Next").click()
        new_html = page.content()
        soup = BeautifulSoup(new_html, 'html.parser')

        # Find the <div> element
        div_element = soup.find('div', {'id': 'ui-datepicker-div'})

        td_elements = div_element.find_all('td', {'class': 'undefined'})

        # Assuming td_elements contains the list of <td> elements you provided
        filtered_elements = [td for td in td_elements if td.get('class') == ['undefined'] and 
                            td.get('data-event') == 'click' and 
                            td.get('data-handler') == 'selectDay']

        # Initialize an empty list to store the extracted data
        data_list = []

        # Iterate over each element in filtered_elements
        for soup in filtered_elements:
            # Extract date, data-month, and data-year from the soup
            date = soup.find('a').get_text()
            month = soup.get('data-month')
            if len(month) == 1:
                month = "0" + month
            else:
                None
            year = soup.get('data-year')

            # Convert date to the desired format
            date_formatted = f"{date.zfill(2)}/{month}/{year}"

            # Append the extracted data to the data_list
            data_list.append({"Date": date_formatted})

            # Create a pandas DataFrame from the data_list
            df = pd.DataFrame(data_list)

    buldugumtarih = df['Date'][0]
    return buldugumtarih

def compare_dates_and_notify(mevcutrandevutarihi, buldugumtarih):
    date1 = datetime.strptime(buldugumtarih, '%d/%m/%Y')
    date2 = mevcutrandevutarihi

    randtarihi = mevcutrandevutarihi.strftime('%d/%m/%Y')

    if date1 < date2:
        print("Daha erkene randevu buldum. " + str(buldugumtarih) + """ tarihine randevu acildi. Sizin guncel randevu tarihiniz : """ + str(randtarihi)).encode('utf-8'),

    else:
        print("En erken randevu tarihi " + buldugumtarih + ". Sizin randevu tarihiniz : " + randtarihi)

if __name__ == "__main__":
    main()
