import os
import pandas as pd
from dataclasses import asdict, dataclass, field
import requests
import re
from playwright.sync_api import sync_playwright

EMAIL_VALIDATOR_API_KEY = os.getenv('EMAIL_VALIDATOR_API_KEY')

@dataclass
class Business:
    """holds business data"""
    name: str = "None"
    address: str = "None"
    email: str = "None"
    website: str = "None"
    phone_number: str = "None"
    linkedin: str = "None"
    twitter: str = "None"
    facebook: str = "None"
    instagram: str = "None"

@dataclass
class BusinessList:
    """holds list of Business objects"""
    business_list: list[Business] = field(default_factory=list)

def validate_email_api(email: str) -> bool:
    url = "https://email-validator28.p.rapidapi.com/email-validator/validate"
    querystring = {"email": email}

    headers = {
        "x-rapidapi-key": EMAIL_VALIDATOR_API_KEY,
        "x-rapidapi-host": "email-validator28.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()
        return response_data.get("isValid", False) and response_data.get("isDeliverable", False)
    except Exception as e:
        print(f"Error validating email {email}: {e}")
        return False

def extract_emails_from_page(page):
    """Extract email from a webpage using a regex pattern and validate it"""
    content = page.content()
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, content)

    for email in emails:
        if validate_email_api(email):
            return email
    return "None"

def extract_social_media_links(page):
    """Extracts social media links from a webpage"""
    social_media_links = {
        "Facebook": "None",
        "Instagram": "None",
        "Twitter": "None",
        "LinkedIn": "None"
    }
    
    # Search for social media links
    for platform in social_media_links.keys():
        pattern = rf"https?:\/\/(www\.)?{platform.lower()}\.com\/(\w+)\/?"
        match = re.search(pattern, page.content())
        if match:
            social_media_links[platform] = match.group(0)

    return social_media_links

def main(search_term, quantity, progress):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps")
        page.locator('//input[@id="searchboxinput"]').fill(search_term)
        page.keyboard.press("Enter")

        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        previously_counted = 0
        while True:
            page.mouse.wheel(0, 10000)
            count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
            if count >= quantity:
                listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:quantity]
                break
            else:
                if count == previously_counted:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                    break
                else:
                    previously_counted = count

        total_found = len(listings)

        business_list = BusinessList()

        for i, listing in enumerate(listings):
            try:
                listing.click()
                page.wait_for_timeout(1000)
                business = Business()

                # Scrape details
                business.name = listing.get_attribute('aria-label')
                business.address = page.locator('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]').inner_text() or "None"
                business.website = page.locator('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]').inner_text() or "None"
                business.phone_number = page.locator('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]').inner_text() or "None"

                if business.website != "None":
                    with page.context.expect_page() as new_page_info:
                        page.locator('//a[@data-item-id="authority"]').click()
                    new_page = new_page_info.value
                    new_page.wait_for_load_state("networkidle")
                    business.email = extract_emails_from_page(new_page)
                    social_media_links = extract_social_media_links(new_page)
                    business.facebook = social_media_links["Facebook"]
                    business.instagram = social_media_links["Instagram"]
                    business.twitter = social_media_links["Twitter"]
                    business.linkedin = social_media_links["LinkedIn"]

                business_list.business_list.append(business)

                # Update progress bar
                progress.progress((i + 1) / total_found)  # Update progress

            except Exception as e:
                print(f'Error occurred: {e}')

        # Convert to DataFrame
        data = [asdict(business) for business in business_list.business_list]
        df = pd.DataFrame(data)

        browser.close()

        return df, total_found



if __name__ == "__main__":
    query = input("Enter your search term: ")
    quantity = int(input("Enter the number of businesses to scrape: "))
    main(query, quantity=quantity)
