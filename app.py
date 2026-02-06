from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure Chrome for headless scraping
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Login to Academia SRM
def login_to_academia(driver, username, password):
    try:
        driver.get('https://academia.srmist.edu.in/')
        
        # Wait for login page to load
        wait = WebDriverWait(driver, 10)
        
        # Find and fill username
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, 'txtUserName'))
        )
        username_field.clear()
        username_field.send_keys(username)
        
        # Find and fill password
        password_field = driver.find_element(By.ID, 'txtPassword')
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.ID, 'btnLogin')
        login_button.click()
        
        # Wait for dashboard to load
        time.sleep(3)
        
        # Check if login was successful
        if 'student' in driver.current_url.lower() or 'dashboard' in driver.current_url.lower():
            return True, "Login successful"
        else:
            return False, "Invalid credentials"
            
    except Exception as e:
        return False, f"Login error: {str(e)}"

# Scrape attendance data
def scrape_attendance(driver):
    try:
        # Navigate to attendance page
        driver.get('https://academia.srmist.edu.in/#Page:Attendance')
        time.sleep(3)
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find attendance table
        attendance_data = []
        table = soup.find('table')  # Adjust selector based on actual page
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:  # Ensure row has all required columns
                    subject_data = {
                        'code': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'type': cols[2].text.strip(),
                        'faculty': cols[3].text.strip(),
                        'slot': cols[4].text.strip(),
                        'conducted': int(cols[5].text.strip() or 0),
                        'attended': int(cols[6].text.strip() or 0),
                        'percentage': float(cols[7].text.strip().replace('%', '') or 0)
                    }
                    attendance_data.append(subject_data)
        
        return attendance_data
        
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return []

# Scrape marks data
def scrape_marks(driver):
    try:
        # Navigate to marks page
        driver.get('https://academia.srmist.edu.in/#Page:Marks')
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        marks_data = []
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    subject_marks = {
                        'code': cols[0].text.strip(),
                        'type': cols[1].text.strip(),
                        'name': cols[1].text.strip(),
                        'test1': cols[2].text.strip() or None,
                        'test2': None,
                        'test3': None
                    }
                    marks_data.append(subject_marks)
        
        return marks_data
        
    except Exception as e:
        print(f"Marks scraping error: {str(e)}")
        return []

# API Endpoints

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Academia SRM Scraper API is running'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    driver = get_driver()
    
    try:
        success, message = login_to_academia(driver, username, password)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        driver.quit()

@app.route('/api/attendance', methods=['POST'])
def api_attendance():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Credentials required'}), 400
    
    driver = get_driver()
    
    try:
        # Login first
        success, message = login_to_academia(driver, username, password)
        
        if not success:
            return jsonify({'error': f'Login failed: {message}'}), 401
        
        # Scrape attendance
        attendance_data = scrape_attendance(driver)
        
        return jsonify({
            'success': True,
            'data': attendance_data,
            'count': len(attendance_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        driver.quit()

@app.route('/api/marks', methods=['POST'])
def api_marks():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Credentials required'}), 400
    
    driver = get_driver()
    
    try:
        # Login first
        success, message = login_to_academia(driver, username, password)
        
        if not success:
            return jsonify({'error': f'Login failed: {message}'}), 401
        
        # Scrape marks
        marks_data = scrape_marks(driver)
        
        return jsonify({
            'success': True,
            'data': marks_data,
            'count': len(marks_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        driver.quit()

if __name__ == '__main__':
    print("🚀 Academia SRM Scraper API starting...")
    print("📍 API will be available at: http://localhost:5000")
    print("📋 Endpoints:")
    print("   - POST /api/login (test credentials)")
    print("   - POST /api/attendance (get attendance data)")
    print("   - POST /api/marks (get marks data)")
    app.run(debug=True, host='0.0.0.0', port=5000)
