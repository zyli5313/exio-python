import hmac
import hashlib
import time
import base64
from requests.auth import AuthBase


class ExioAuth(AuthBase):
  # Provided by gdax: https://docs.gdax.com/#signing-a-message

  def __init__(self, key, secret):
    self.key = key
    self.secret = secret

  def __call__(self, request):
    # Monotonic sequence number. We recommend using milliseocnds since UNIX
    # epoch.
    timestamp = str(int(time.time() * 1e3))
    message = ''.join([timestamp, request.method,
                       request.path_url, (request.body or '')])
    headers = getAuthHeaders(timestamp, message,
                             self.key,
                             self.secret)
    print headers

    request.headers.update(headers)
    return request


def getAuthHeaders(timestamp, message, key, secret):
  message = message.encode('ascii')
  hmac_key = base64.b64decode(secret)
  signature = hmac.new(hmac_key, message, hashlib.sha256)
  signature_b64 = base64.b64encode(signature.digest()).decode('utf-8').rstrip('\n')
  return {
      'Content-Type': 'Application/JSON',
      'EX-ACCESS-SIGN': signature_b64,
      'EX-ACCESS-NONCE': timestamp,
      'EX-ACCESS-KEY': key
  }
