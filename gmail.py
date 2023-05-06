from __future__ import print_function

import asyncio
import os.path
from collections import Counter

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import (  # noqa: E402 module level import not at top of file
    UserCreds,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
READ_MAX = 500


async def find_message(page_token=None):
    """
    https://github.com/googleworkspace/python-samples/blob/main/gmail/quickstart/quickstart.py
    """
    user_creds = await extract_credentials_json()

    async with Aiogoogle(user_creds=user_creds) as google:
        gmail = await google.discover("gmail", "v1")

        try:
            # https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
            # https://developers.google.com/gmail/api/reference/rest/v1/users.threads/list
            response = await google.as_user(
                gmail.users.messages.list(
                    userId='me',
                    q='-has:userlabels is:unread',
                    maxResults=READ_MAX,
                    pageToken=page_token
                )
            )

            result = {
                'nextPageToken': response.get('nextPageToken', None),
                'senders': []
            }

            messages = response.get('messages', [])

            tasks = [asyncio.create_task(find_sender(google, gmail, message)) for message in messages]
            all_senders = await asyncio.gather(*tasks)
            result['senders'].extend(all_senders)

            return result
        except HttpError as error:
            print(F'An error occurred: {error}')


async def extract_credentials_json():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token = 'token.json'
    credentials = 'credentials.json'
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token, 'w') as token:
            token.write(creds.to_json())

    return UserCreds(
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        expires_at=creds.expiry
    )


async def find_sender(google, gmail, message):
    # https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get
    # https://developers.google.com/gmail/api/reference/rest/v1/users.threads/get
    tdata = await google.as_user(gmail.users.messages.get(userId="me", id=message['id']))
    headers = tdata["payload"]["headers"]
    for header in headers:
        if header['name'] == 'From':
            print(header['value'])
            return header['value']
    return None


def print_senders(s):
    sender_counts = Counter(s)
    for sender, c in sender_counts.most_common():
        print(f'{sender}: {c} 개의 이메일')


if __name__ == '__main__':
    senders = []
    total = 0
    result = {
        'nextPageToken': None
    }
    try:
        while True:
            result = asyncio.run(find_message(result['nextPageToken']))
            result_senders = result['senders']
            senders.extend(result_senders)
            result_senders_count = len(result_senders)
            total += result_senders_count
            print(f'total={total}')
            if result_senders_count < READ_MAX:
                break
            print_senders(senders)

    except KeyboardInterrupt:
        print_senders(senders)

    print_senders(senders)
