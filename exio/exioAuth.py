import hmac
import hashlib
import time
import base64
from requests.auth import AuthBase


class ExioAuth(AuthBase):
    # Provided by gdax: https://docs.gdax.com/#signing-a-message
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        # Monotonic sequence number. We recommend using milliseocnds since UNIX epoch.
        timestamp = str(int(time.time() * 1e3))
        message = ''.join([timestamp, request.method,
                           request.path_url, (request.body or '')])
        request.headers.update(getAuthHeaders(timestamp, message,
                                                self.api_key,
                                                self.secret_key,
                                                self.passphrase))
        return request


def getAuthHeaders(timestamp, message, api_key, secret_key, passphrase):
    message = message.encode('ascii')
    hmac_key = base64.b64decode(secret_key)
    signature = hmac.new(hmac_key, message, hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
    return {
        'Content-Type': 'Application/JSON',
        'EX-ACCESS-SIGN': signature_b64,
        'EX-ACCESS-NONCE': timestamp,
        'EX-ACCESS-KEY': api_key
    }
