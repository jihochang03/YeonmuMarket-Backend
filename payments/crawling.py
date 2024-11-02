# backend/crawler.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def check_account(account_num):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.police.go.kr/www/security/cyber/cyber04.jsp")
        
        # 필드 선택 및 값 입력
        field_select = driver.find_element(By.XPATH, '//*[@id="cyc_field"]')
        field_select.click()
        option = driver.find_element(By.XPATH, '//*[@id="cyc_field"]/option[2]')
        option.click()
        
        input_field = driver.find_element(By.XPATH, '//*[@id="idsearch"]')
        input_field.send_keys(account_num)
        
        # 검색 버튼 클릭
        search_button = driver.find_element(By.XPATH, '//*[@id="getXmlSearch"]/img')
        search_button.click()
        
        # 결과 대기 후 추출
        time.sleep(2)
        result = driver.find_element(By.XPATH, '//*[@id="search_result"]').text
        return "없습니다" not in result
    except Exception as e:
        print("Error during crawling:", e)
        return False
    finally:
        driver.quit()