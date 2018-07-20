import hmac
import hashlib
import time
import base64
from requests.auth import AuthBase

class ExioAuth(AuthBase):
  # signing-a-message

  def __init__(self, key, secret, passphrase):
    self.key = key
    self.secret = secret
    self.passphrase = passphrase

  def __call__(self, request):
    # Monotonic sequence number. We recommend using seconds since UNIX epoch.
    timestamp = str(int(time.time()))
    message = ''.join([timestamp, request.method,
                       request.path_url, (request.body or '')])
    headers = getAuthHeaders(timestamp, message,
                             self.key,
                             self.secret,
                             self.passphrase)

    request.headers.update(headers)
    return request

def getAuthHeaders(timestamp, message, key, secret, passphrase):
  message = message.encode('ascii')
  hmac_key = base64.b64decode(secret)
  signature = hmac.new(hmac_key, message, digestmod=hashlib.sha256)
  signature_b64 = base64.b64encode(signature.digest()).decode('utf-8').rstrip('\n')
  return {
      "ex-access-sign": signature_b64,
      "ex-access-timestamp": timestamp,
      "ex-access-key": key,
      "ex-access-passphrase": passphrase
  }
