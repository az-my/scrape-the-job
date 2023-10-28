import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from urllib.parse import urljoin, quote
import re

# List of search terms
search_terms = ["Data-Analyst", "Data-Analis","Data Engineer"]

# Base URL for the JobStreet website
base_url = "https://www.jobstreet.co.id"

# Function to parse the datetime value
def parse_datetime(datetime_str):
    # Extract the date and time parts
    date_part, time_part = re.search(r'(\d+-\d+-\d+)T(\d+:\d+:\d+)', datetime_str).groups()
    return f"{date_part} {time_part}"

# Function to scrape job titles, their corresponding href, company links, location links, and datetime
def scrape_page(url, search_term):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage for {search_term}. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    h1_elements = soup.find_all('h1')
    company_links = soup.find_all('a', {'data-automation': 'jobCardCompanyLink'})
    location_links = soup.find_all('a', {'data-automation': 'jobCardLocationLink'})
    time_elements = soup.find_all('time', {'datetime': True})

    h1_data = []

    for h1, company_link, location_link, time_element in zip(h1_elements, company_links, location_links, time_elements):
        text = h1.get_text().strip()
        href = urljoin(base_url, h1.a['href'].split('?')[0])
        company_text = company_link.get_text().strip()
        location_text = location_link.get_text().strip()
        datetime = parse_datetime(time_element['datetime'])
        time_ago = time_element.find('span').get_text().strip()

        h1_data.append({'search_term': search_term, 'text': text, 'href': href, 'company_text': company_text, 'location_text': location_text, 'datetime': datetime, 'time_ago': time_ago})

    return h1_data

# Initialize an empty list to store all scraped data
all_data = []

# Dictionary to keep track of total records for each search term
total_records_dict = {search_term: 0 for search_term in search_terms}

# Dictionary to store the first and last records for each search term
first_record_dict = {search_term: None for search_term in search_terms}
last_record_dict = {search_term: None for search_term in search_terms}

# Loop through the list of search terms
for search_term in search_terms:
    page = 1
    first_record = None  # Store the first record for this search term
    last_record = None   # Store the last record for this search term
    while True:
        encoded_search_term = quote(search_term, safe="")
        url = f"https://www.jobstreet.co.id/\"{encoded_search_term}\"-jobs?pg={page}"

        page_data = scrape_page(url, search_term)

        if not page_data:
            break

        all_data.extend(page_data)
        total_records_dict[search_term] += len(page_data)  # Update the total records

        if first_record is None:
            first_record = page_data[0]  # Set the first record for this search term
        last_record = page_data[-1]  # Set the last record for this search term

        page += 1

    first_record_dict[search_term] = first_record
    last_record_dict[search_term] = last_record

# Save the data to CSV
df = pd.DataFrame(all_data)
df.to_csv('job_data.csv', index=False)

# Save the data to JSON
with open('job_data.json', 'w') as json_file:
    json.dump(all_data, json_file, indent=2)

# Print the first and last records for each search term
for search_term in search_terms:
    print(f"First Record for '{search_term}': {first_record_dict[search_term]}")
    print(f"Last Record for '{search_term}': {last_record_dict[search_term]}")

# Print the total records for each search term
for search_term, total_records in total_records_dict.items():
    print(f"Total Records for '{search_term}': {total_records}")

# Print the total number of records scraped
total_records = len(all_data)
print(f"Total Records Scraped for '{', '.join(search_terms)}': {total_records}")
