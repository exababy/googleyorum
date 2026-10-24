"""Google İşletme Profili (Business Profile) API istemcisi."""
import os

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/business.manage"]
TOKEN_FILE = "token.json"

ACCOUNTS_URL = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
LOCATIONS_URL = "https://mybusinessbusinessinformation.googleapis.com/v1/{account}/locations"
REVIEWS_URL = "https://mybusiness.googleapis.com/v4/{location}/reviews"
REPLY_URL = "https://mybusiness.googleapis.com/v4/{review}/reply"

STARS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}


def get_credentials(client_secret_file: str, interactive: bool = False) -> Credentials:
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif interactive:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
    else:
        raise SystemExit("Google girişi yapılmamış. Önce: python -m yorumbot auth")
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    return creds


class BusinessClient:
    def __init__(self, creds: Credentials):
        self.creds = creds

    def _request(self, method: str, url: str, **kwargs) -> dict:
        if not self.creds.valid:
            self.creds.refresh(Request())
        headers = {"Authorization": f"Bearer {self.creds.token}"}
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        if not resp.ok:
            raise RuntimeError(f"{method} {url} -> {resp.status_code}: {resp.text}")
        return resp.json() if resp.content else {}

    def list_accounts(self) -> list[dict]:
        return self._request("GET", ACCOUNTS_URL).get("accounts", [])

    def list_locations(self, account: str) -> list[dict]:
        url = LOCATIONS_URL.format(account=account)
        params = {"readMask": "name,title,storefrontAddress", "pageSize": 100}
        return self._request("GET", url, params=params).get("locations", [])

    def list_reviews(self, location: str):
        """Yorumları en yeniden eskiye doğru sayfa sayfa döndürür."""
        url = REVIEWS_URL.format(location=location)
        params = {"pageSize": 50, "orderBy": "updateTime desc"}
        while True:
            data = self._request("GET", url, params=params)
            yield from data.get("reviews", [])
            token = data.get("nextPageToken")
            if not token:
                break
            params["pageToken"] = token

    def reply(self, review_name: str, text: str) -> dict:
        url = REPLY_URL.format(review=review_name)
        return self._request("PUT", url, json={"comment": text})
