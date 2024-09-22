import random
import string

def generate_verification_code():
    """Generates a random 4-character verification code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def verify_code(bank_account, input_code):
    """Verifies the given input code against the bank account's expected verification code."""
    return bank_account.verification_code == input_code
