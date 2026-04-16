import pyotp
 

def generate_mfa_secret():
    return pyotp.random_base32()


def get_totp(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()


def generate_qr_url(user_email, secret, issuer="PM-A"):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer)

def verify_mfa_token(secret, token):
    totp = pyotp.TOTP(secret)
    # Allow a 30s window drift for authenticator apps.
    return totp.verify(token, valid_window=1)

    