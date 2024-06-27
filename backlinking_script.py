import csv
import time
import re
from urllib.parse import urlparse
from googlesearch import search
from bs4 import BeautifulSoup
import requests
import os
import random

# Define a list of User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.74 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 EdgA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 EdgA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 EdgA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 EdgA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 EdgA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4140.105 Safari/537.36 EdgA",
]

# List of proxies to rotate
proxies = [
    "103.210.35.131:8080",
    "107.162.143.146:80",
    "125.77.25.178:8080",
    "125.77.25.178:8090",
    "157.181.18.10:80",
    "161.34.40.112:3128",
    # Add more proxies as needed
]

# List of social media domains to exclude
social_media_domains = [
    "youtube.com", "facebook.com", "twitter.com", "linkedin.com",
    "instagram.com", "pinterest.com", "tiktok.com", "snapchat.com",
]

def is_social_media_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    for social_domain in social_media_domains:
        if social_domain in domain:
            return True
    return False

def get_random_proxy():
    return random.choice(proxies)

def scrape_emails(domain):
    user_agent = random.choice(user_agents)  # Select a random User-Agent
    headers = {"User-Agent": user_agent}
    proxy = get_random_proxy()  # Get a random proxy
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }
    max_retries = 5
    retry_delay = 1
    attempt = 0

    while attempt < max_retries:
        try:
            response = requests.get(f'https://{domain}', headers=headers, proxies=proxies, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            emails = set()
            # Find emails in the href attributes
            for a in soup.find_all('a', href=True):
                if '@' in a['href'] and not is_social_media_url(a['href']):
                    email = a['href'].replace("mailto:", "").strip()
                    emails.add(email)
            # Find emails in the text
            text = soup.get_text()
            emails.update(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
            print(f"Found {len(emails)} emails on {domain}")
            return list(emails)
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {domain}: {e}. Retrying...")
            attempt += 1
            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
    print(f"Failed to scrape {domain} after {max_retries} attempts.")
    return []

def get_google_urls(query):
    urls = []
    for j in search(query, num_results=100):  # Adjust num_results as needed
        urls.append(j)
        time.sleep(random.uniform(1, 3))  # Add a random wait time between requests
    print(f"Fetched {len(urls)} urls for query '{query}'")
    return urls

def extract_domains(urls):
    domains = set()
    for url in urls:
        parsed_url = urlparse(url)
        if parsed_url.netloc and not is_social_media_url(url):
            domains.add(parsed_url.netloc)
    print("Extracted", len(domains), "domains")
    return domains

def read_domains_from_csv(file_name):
    domains = set()
    try:
        with open(file_name, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row if present
            for row in reader:
                domains.add(row[0])
        print("Read", len(domains), "domains from CSV")
    except UnicodeDecodeError:
        print(f"UTF-8 decoding error encountered while reading {file_name}. Trying 'ISO-8859-1' encoding.")
        try:
            with open(file_name, mode='r', encoding='ISO-8859-1') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row if present
                for row in reader:
                    domains.add(row[0])
            print("Read", len(domains), "domains from CSV using ISO-8859-1 encoding")
        except Exception as e:
            print(f"Unexpected error: {e}")
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return domains

def write_emails_to_csv(file_name, emails):
    try:
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for email in emails:
                # Strip "mailto:" prefix if present
                email = email.replace("mailto:", "").strip()
                writer.writerow([email])
        print("Wrote", len(emails), "unique emails to CSV")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def filter_domains(main_domains, competitors_file):
    competitors_domains = read_domains_from_csv(competitors_file)
    filtered_domains = main_domains - competitors_domains
    print("Filtered domains:", len(filtered_domains))
    return filtered_domains

def safe_scrape_emails(domain):
    emails = scrape_emails(domain)
    time.sleep(1)  # Sleep for 1 second between requests to comply with rate limits
    return emails

if __name__ == "__main__":
    keywords = [
        "inteligencia artificial aplicada a la empresa blog",
        "experiencia de usuario blog",
        # Add more keywords as needed
    ]

    all_urls = []
    for keyword in keywords:
        urls = get_google_urls(keyword)
        all_urls.extend(urls)
    
    domains = extract_domains(all_urls)
    
    # Use absolute paths
    current_directory = os.path.dirname(os.path.abspath(__file__))
    contacts_csv_path = os.path.join(current_directory, 'contacts_backlinking.csv')
    competitors_csv_path = os.path.join(current_directory, 'competitors_domains.csv')
    
    existing_domains = read_domains_from_csv(contacts_csv_path)
    all_domains = domains | existing_domains
    
    filtered_domains = filter_domains(all_domains, competitors_csv_path)
    
    # Initialize an empty list to store emails
    emails_list = []
    
    # Iterate over filtered domains to scrape emails
    for domain in filtered_domains:
        emails = safe_scrape_emails(domain)  # Use the modified function with rate limiting
        emails_list.extend(emails)  # Extend the list with emails from the current domain
    
    # Remove duplicates by converting the list to a set and back to a list
    emails_list = list(set(emails_list))
    
    # Log the total number of unique emails collected
    print(f"Total unique emails collected: {len(emails_list)}")
    
    # Write the collected emails to the CSV file, stripping "mailto:" prefix
    write_emails_to_csv(contacts_csv_path, emails_list)
