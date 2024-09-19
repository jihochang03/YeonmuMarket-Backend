import random
import string


#네글자 랜덤으로 전송하는 코드, 이때 그 네글자를 사람마다 저장을 해놔야될 거 같은데 이건 추가 필요. 
def generate_verification_code():
    """Generates a random 4-character verification code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def verify_code(bank_account, input_code):
    """Verifies the given input code against the bank account's expected verification code."""
    return bank_account.verification_code == input_code