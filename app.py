from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Login to Academia SRM using Playwright
def login_to_academia(page, username, password):
    try:
        page.goto('https://academia.srmist.edu.in/')
        
        # Wait for login page to load
        page.wait_for_selector('#txtUserName', timeout=10000)
        
        # Find and fill username
        page.fill('#txtUserName', username)
        
        # Find and fill password
        page.fill('#txtPassword', password)
        
        # Click login button
        page.click('#btnLogin')
        
        # Wait for navigation
        time.sleep(3)
        
        # Check if login was successful
        current_url = page.url.lower()
        if 'student' in current_url or 'dashboard' in current_url:
            return True, "Login successful"
        else:
            return False, "Invalid credentials"
            
    except Exception as e:
        return False, f"Login error: {str(e)}"

# Scrape attendance data
def scrape_attendance(page):
    try:
        # Navigate to attendance page
        page.goto('https://academia.srmist.edu.in/#Page:Attendance')
        time.sleep(3)
        
        # Get page content and parse with BeautifulSoup
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find attendance table
        attendance_data = []
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
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
def scrape_marks(page):
    try:
        # Navigate to marks page
        page.goto('https://academia.srmist.edu.in/#Page:Marks')
        time.sleep(3)
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
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
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            success, message = login_to_academia(page, username, password)
            
            browser.close()
            
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

@app.route('/api/attendance', methods=['POST'])
def api_attendance():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Credentials required'}), 400
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Login first
            success, message = login_to_academia(page, username, password)
            
            if not success:
                browser.close()
                return jsonify({'error': f'Login failed: {message}'}), 401
            
            # Scrape attendance
            attendance_data = scrape_attendance(page)
            
            browser.close()
            
            return jsonify({
                'success': True,
                'data': attendance_data,
                'count': len(attendance_data)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/marks', methods=['POST'])
def api_marks():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Credentials required'}), 400
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Login first
            success, message = login_to_academia(page, username, password)
            
            if not success:
                browser.close()
                return jsonify({'error': f'Login failed: {message}'}), 401
            
            # Scrape marks
            marks_data = scrape_marks(page)
            
            browser.close()
            
            return jsonify({
                'success': True,
                'data': marks_data,
                'count': len(marks_data)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Academia SRM Scraper API starting...")
    print("📍 API will be available at: http://localhost:5000")
    print("📋 Endpoints:")
    print("   - POST /api/login (test credentials)")
    print("   - POST /api/attendance (get attendance data)")
    print("   - POST /api/marks (get marks data)")
    app.run(debug=True, host='0.0.0.0', port=5000)
