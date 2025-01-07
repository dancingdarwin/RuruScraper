# Web Scraping Tools
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Google API OAuth2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail Functions
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Other
import os.path
from datetime import datetime
import traceback
import yaml
import platform

def test_instock(driver,url):
    '''
    Looks up whether Lulu Lemon item is sold out.
    
    INPUT
        driver: Selenium WebDriver to access website
        url: url of the Lulu Lemon Item

    OUTPUT
        instock: None if there's an error with accesing the website. True if in stock. False if sold out.
    '''
    driver.get(url)
    instock = None
    try:
        driver.find_element(By.XPATH, "//button[contains(.,'SOLD OUT - NOTIFY ME')]")
        instock = False
    except NoSuchElementException: 
        try:
            driver.find_element(By.XPATH, "//button[contains(.,'Add to Bag')]")
            instock = True
        except:
            instock = None
    except Exception as error:
        print(error)
        instock = None
    return instock
        
def google_authenticate():
    '''
    Attempts to get OAuth token for accessing Google API.

    OUTPUT
        creds: Google API Credentials
    '''
    
    creds = None
    SCOPES = ["https://www.googleapis.com/auth/gmail.send",
             "https://www.googleapis.com/auth/spreadsheets"]
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds

def gmail_send_message(creds,recipient,sender,body="Test",subject="Ruru Scraper has a Message!"):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id
  """

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(body)

    message["To"] = recipient
    message["From"] = sender
    message["Subject"] = subject


    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message

def get_values(creds, spreadsheet_id, values):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    
    try:
        service = build("sheets", "v4", credentials=creds)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=values)
            .execute()
        )
        rows = result.get("values", [])
        print(f"{len(rows)} rows retrieved from Google Sheet")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
    

def write_value(creds,spreadsheet_id,target,content,value_input_option='RAW'):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    # pylint: disable=maybe-no-member
    try:
        service = build("sheets", "v4", credentials=creds)
        body = {"values": content}
        result = (service.spreadsheets()
                  .values()
                  .update(
                      spreadsheetId=spreadsheet_id,
                      range=target,
                      valueInputOption=value_input_option,
                      body=body,
                  ).execute()
                 )
        print(f"{result.get('updatedCells')} cells updated in Google Sheet.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
    
def get_datetime():
    ''' Returns current formatted time'''
    # Get the current date and time
    now = datetime.now()

    # Format the datetime object into a string
    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")

    # Print the formatted string
    return formatted_datetime

def parse_emails():
    with open("Emails.yaml") as stream:
        try:
            emails = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return emails

if __name__ == '__main__':
    try:
        emails = parse_emails()

        creds = google_authenticate()

        if 'ubuntu' in platform.version().lower():
            geckodriver_path = "/snap/bin/geckodriver"
            driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
        firefox_options = webdriver.firefox.options.Options()
        firefox_options.add_argument('--headless')
        driver = webdriver.Firefox(options = firefox_options)
    
        items = get_values(creds,spreadsheet_id=emails['spreadsheet_id'],values='A1:C100')['values']

        found_items = ''
        updated_spreadsheet = []
        new_found_item = False

        num_rows = len(items)

        if num_rows > 1:
            for idx in range(1,num_rows):
                row = items[idx]
                item_name = row[0]
                url = row[1]
            
                if len(row) > 2:
                    prev_status = row[2]
                else:
                    prev_status = 'Never Checked'
    
                instock = test_instock(driver,url)
            
                if instock is None:
                    text_status = 'Error!'
                elif instock:
                    text_status = 'In Stock'
                else:
                    text_status = 'Sold Out'
            

                # If in stock, add the item to the email message
                if instock:
                    found_items += f"- {item_name}: {url}\n"
                    if prev_status != 'In Stock':
                        new_found_item = True

                updated_spreadsheet.append([text_status,get_datetime()])
    
        # Update spreadsheet with latest status
        write_value(creds,
                    spreadsheet_id=emails['spreadsheet_id'],
                    target=f'C2:D{num_rows}',
                    content=updated_spreadsheet)

        # Send Email if any new found items
        if new_found_item:
            print('Found New Items!')
            print(found_items)
            gmail_send_message(creds,
                               recipient=emails['recipient'],
                               sender=emails['sender'],
                               body=found_items,
                               subject='RuRu Scraper has found new in stock items!')
        else:
            print('Found no new items :(')
    except:
        traceback.print_exc()
    finally:
        driver.quit()