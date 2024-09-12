import requests
import json
from django.conf import settings

def send_message(kakao_id, message):
    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    access_token = settings.KAKAO_ACCESS_TOKEN  # 여기에는 실제 Kakao Access Token을 입력해야 합니다.
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'template_object': {
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': 'https://yourwebsite.com',
                'mobile_web_url': 'https://yourwebsite.com'
            }
        }
    }
    
    response = requests.post(url, headers=headers, data={'template_object': json.dumps(data)})
    
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}', response.text)
