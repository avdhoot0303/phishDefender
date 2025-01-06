# app/email_service.py
import base64
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import dateutil.parser as parser

def fetch_emails(service, max_results=25, page_token=None):
    """Fetch emails in batches of max_results."""
    try:
        query_params = {
            'userId': 'me',
            'labelIds': ['INBOX'],
            'maxResults': max_results,
        }
        if page_token:
            query_params['pageToken'] = page_token

        response = service.users().messages().list(**query_params).execute()
        return response
    except Exception as e:
        return {"error": str(e)}

def process_emails(messages, service):
    """Extract details from emails."""
    email_list = []
    for mssg in messages:
        temp_dict = {}
        m_id = mssg['id']
        try:
            message = service.users().messages().get(userId='me', id=m_id).execute()
            payload = message['payload']
            headers = payload.get('headers', [])

            for header in headers:
                if header['name'] == 'Subject':
                    temp_dict['Subject'] = header['value']
                elif header['name'] == 'Date':
                    date_parse = parser.parse(header['value'])
                    temp_dict['Date'] = str(date_parse.date())
                elif header['name'] == 'From':
                    temp_dict['Sender'] = header['value']

            temp_dict['Snippet'] = message.get('snippet', '')

            try:
                parts = payload.get('parts', [])
                body = parts[0]['body'].get('data', '') if parts else ''
                clean_body = base64.urlsafe_b64decode(body).decode('utf-8')
                soup = BeautifulSoup(clean_body, "lxml")
                temp_dict['Message_body'] = soup.get_text()
            except Exception as body_error:
                temp_dict['Message_body'] = f"Error extracting body: {body_error}"

            email_list.append(temp_dict)
        except Exception as e:
            continue
    return email_list
