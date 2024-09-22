import requests

def send_kakao_message(user, message):
    kakao_token = user.userprofile.kakao_token

    if kakao_token:
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            "Authorization": f"Bearer {kakao_token}",
        }
        data = {
            "template_object": {
                "object_type": "text",
                "text": message,
                "link": {
                    "web_url": "http://yourdomain.com",
                    "mobile_web_url": "http://yourdomain.com"
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            # 메시지 전송 실패 시 예외 처리 (토큰 만료 등)
            return False
        return True
    return False
