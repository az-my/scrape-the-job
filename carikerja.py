import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, quote
import re
from datetime import datetime

# List of search terms
search_terms = [
    "Data-Analyst",
    "Data-Analis",
    "Data-Engineer",
    "ETL-Developer",
    "Power-BI-Developer",
    "Business-Intelligence",
    "Business-Intelligence Analyst",
    "Business-Analyst",
    "Bisnis-Analis",
    "BI Analyst",
    "BI-Developer",
]


# Base URL for the JobStreet website
base_url = "https://www.jobstreet.co.id"

# Function to parse the datetime value
def parse_datetime(datetime_str):
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

        h1_data.append({
            'keyword': search_term,
            'job_role': text,
            'url_application': href,
            'company_name': company_text,
            'company_location': location_text,
            'job_posted_date': datetime,
        })

    return h1_data

# Initialize an empty list to store all extracted data
all_data = []

# Dictionary to keep track of total records for each search term
total_records_dict = {search_term: 0 for search_term in search_terms}

# Extract and Save Stage
for search_term in search_terms:
    page = 1
    while True:
        encoded_search_term = quote(search_term, safe="")
        url = f"https://www.jobstreet.co.id/{encoded_search_term}-jobs?sort=createdAt&pg={page}"

        page_data = scrape_page(url, search_term)

        if not page_data:
            break

        all_data.extend(page_data)
        total_records_dict[search_term] += len(page_data)

        page += 1

# Save all extracted data into a single JSON file
with open('extracted_data.json', 'w') as json_file:
    json.dump(all_data, json_file, indent=2)

# Transform Stage
def transform_data(data):
    try:

        #ambil date-time versi original sebagai string
        original_datetime = data['job_posted_date']
        #conver versi original string ke versi objek
        datetime_obj = datetime.strptime(original_datetime, "%Y-%m-%d %H:%M:%S") #
        #format ke sesuai yang diinginkan
        desired_date = datetime_obj.strftime("%d-%b-%Y %H:%M:%S")

       

        keywords = data['keyword'].split('-')
        job_role = data['job_role']
        contains_all = all(keyword.lower() in job_role.lower() for keyword in keywords)
        current_date = datetime.now()
        duration = (current_date - datetime_obj).days

        data['job_posted_date'] = original_datetime  # Keep the original format
        data['duration'] = duration
        # Rearrange the order of fields in the data structure
        transformed_data = {
            'keyword': data['keyword'],
            'job_role': data['job_role'],
            'is_JobRole_contains_all_Keyword': "Yes" if contains_all else "No",
            'url_application': data['url_application'],
            'company_name': data['company_name'],
            'company_location': data['company_location'],
            'job_posted_date': desired_date,
            'duration': data['duration'],
        }

       

        return transformed_data
    except Exception as e:
        print(f"Error while transforming data: {e}")
        return None

transformed_data = [transform_data(data) for data in all_data if transform_data(data) is not None]

# Save the transformed data to a JSON file
with open('transformed_data.json', 'w') as json_file:
    json.dump(transformed_data, json_file, indent=2)


"""
# Print the JSON data (for debugging)
with open('transformed_data.json', 'r') as json_file:
    data = json.load(json_file)
    print(json.dumps(data, indent=2))
"""


# Load and Filter Stage
# (Here, you would typically load the data into your target system and perform filtering, but this part is not included in the code.)

# Load and Filter Stage
# Load the transformed data from the JSON file
with open('transformed_data.json', 'r') as json_file:
    loaded_data = json.load(json_file)

# Filter the loaded data to show only records with 'is_JobRole_contains_all_Keyword' == "Yes"
filtered_data = [record for record in loaded_data if record['is_JobRole_contains_all_Keyword'] == "Yes"]


"""
# Print or process the filtered data as needed
for record in filtered_data:
    print(json.dumps(record, indent=2))
"""


# Save the filtered data as a new JSON file
with open('filtered_data.json', 'w') as json_file:
    json.dump(filtered_data, json_file, indent=2)

# Additional processing or reporting can be done with the filtered data here
