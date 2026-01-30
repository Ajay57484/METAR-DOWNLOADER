import http.server
import socketserver
import urllib.parse
import requests
import re
import time
import os
from datetime import datetime

PORT = int(os.environ.get('PORT', 8080))

class MetarHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        print(f"Request: {self.path}")
        
        if self.path == '/':
            self.home_page()
        elif self.path.startswith('/download?'):
            self.process_download_request()
        elif self.path.startswith('/file/'):
            self.send_file()
        elif self.path.startswith('/batch?'):
            self.process_batch_request()
        else:
            self.send_error(404, f"Not found: {self.path}")
    
    def home_page(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>METAR Smart Downloader</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .glass-card {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 800px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                .header h1 {
                    font-size: 3rem;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                
                .header p {
                    color: #666;
                    font-size: 1.2rem;
                }
                
                .form-section {
                    margin-bottom: 30px;
                }
                
                .section-title {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                    color: #333;
                    font-size: 1.3rem;
                }
                
                .section-title .icon {
                    margin-right: 10px;
                    font-size: 1.5rem;
                }
                
                .input-group {
                    margin-bottom: 25px;
                }
                
                .input-label {
                    display: block;
                    margin-bottom: 8px;
                    color: #555;
                    font-weight: 600;
                    font-size: 1.1rem;
                }
                
                .input-field {
                    width: 100%;
                    padding: 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    font-size: 1.1rem;
                    transition: all 0.3s;
                    background: white;
                }
                
                .input-field:focus {
                    border-color: #667eea;
                    outline: none;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .radio-group {
                    display: flex;
                    gap: 20px;
                    margin: 15px 0;
                }
                
                .radio-option {
                    flex: 1;
                    text-align: center;
                }
                
                .radio-input {
                    display: none;
                }
                
                .radio-label {
                    display: block;
                    padding: 20px;
                    background: #f8f9fa;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.3s;
                    font-weight: 500;
                }
                
                .radio-input:checked + .radio-label {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                }
                
                .button-group {
                    display: flex;
                    gap: 20px;
                    margin-top: 40px;
                }
                
                .btn {
                    flex: 1;
                    padding: 20px;
                    border: none;
                    border-radius: 12px;
                    font-size: 1.2rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                }
                
                .btn-primary {
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                }
                
                .btn-primary:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
                }
                
                .btn-secondary {
                    background: #f8f9fa;
                    color: #555;
                    border: 2px solid #e0e0e0;
                }
                
                .btn-secondary:hover {
                    background: #e9ecef;
                    transform: translateY(-2px);
                }
                
                .quick-stations {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 30px 0;
                }
                
                .station-card {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    border: 2px solid #e0e0e0;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .station-card:hover {
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                }
                
                .station-code {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 5px;
                }
                
                .station-name {
                    color: #666;
                    font-size: 0.9rem;
                }
                
                .highlight {
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                }
                
                .status-bar {
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 12px;
                    text-align: center;
                    color: #666;
                }
                
                .loading {
                    display: none;
                    text-align: center;
                    padding: 40px;
                }
                
                .spinner {
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="glass-card">
                <div class="header">
                    <h1>🌤️ METAR Downloader | AJAY</h1>
                    <p>Download aviation weather reports</p>
                </div>
                
                <form id="downloadForm">
                    <div class="form-section">
                        <div class="section-title">
                            <span class="icon">📍</span>
                            <span>Station Information</span>
                        </div>
                        
                        <div class="input-group">
                            <label class="input-label">ICAO Station Code</label>
                            <input type="text" 
                                   class="input-field" 
                                   id="station" 
                                   name="station" 
                                   value="VOGA" 
                                   maxlength="4" 
                                   required
                                   pattern="[A-Z]{4}"
                                   placeholder="Enter 4-letter ICAO code">
                        </div>
                        
                        <div class="quick-stations">
                            <div class="station-card highlight" onclick="setStation('VOGA')">
                                <div class="station-code">VOGA</div>
                                <div class="station-name">GOA (MOPA)</div>
                            </div>
                            <div class="station-card" onclick="setStation('VOMM')">
                                <div class="station-code">VOMM</div>
                                <div class="station-name">Chennai</div>
                            </div>
                            <div class="station-card" onclick="setStation('VABB')">
                                <div class="station-code">VABB</div>
                                <div class="station-name">Mumbai</div>
                            </div>
                            <div class="station-card" onclick="setStation('VIDP')">
                                <div class="station-code">VIDP</div>
                                <div class="station-name">Delhi</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <div class="section-title">
                            <span class="icon">📅</span>
                            <span>Time Period</span>
                        </div>
                        
                        <div class="input-group">
                            <label class="input-label">Year</label>
                            <input type="number" 
                                   class="input-field" 
                                   id="year" 
                                   name="year" 
                                   value="2024" 
                                   min="2000" 
                                   max="2026" 
                                   required>
                        </div>
                        
                        <div class="radio-group">
                            <div class="radio-option">
                                <input type="radio" id="single" name="mode" value="single" checked class="radio-input">
                                <label for="single" class="radio-label">
                                    📁 Single Month
                                </label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" id="all" name="mode" value="all" class="radio-input">
                                <label for="all" class="radio-label">
                                    📦 All 12 Months
                                </label>
                            </div>
                        </div>
                        
                        <div id="monthSelection">
                            <div class="input-group">
                                <label class="input-label">Month</label>
                                <select class="input-field" id="month" name="month">
                                    <option value="01">January</option>
                                    <option value="02">February</option>
                                    <option value="03">March</option>
                                    <option value="04">April</option>
                                    <option value="05">May</option>
                                    <option value="06">June</option>
                                    <option value="07">July</option>
                                    <option value="08">August</option>
                                    <option value="09">September</option>
                                    <option value="10">October</option>
                                    <option value="11">November</option>
                                    <option value="12">December</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="button-group">
                        <button type="button" class="btn btn-primary" onclick="startDownload()">
                            <span>🚀</span>
                            <span>Start Download</span>
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            <span>↺</span>
                            <span>Reset</span>
                        </button>
                    </div>
                </form>
                
                <div id="loading" class="loading">
                    <div class="spinner"></div>
                    <h3>Downloading METAR Data...</h3>
                    <p id="statusText">Please wait while we process your request</p>
                </div>
                
                <div class="status-bar">
                    <p>📊 It may take a while...The site is currently busy in pondering its existane <br>  Contact : AJAY YADAV (IMD GOA) <br>  ajaypahe02@gmail.com </p>
                </div>
            </div>
            
            <script>
                function setStation(code) {
                    document.getElementById('station').value = code;
                    
                    // Update highlight
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                    });
                    event.currentTarget.classList.add('highlight');
                }
                
                function updateMonthVisibility() {
                    const singleMode = document.getElementById('single').checked;
                    const monthDiv = document.getElementById('monthSelection');
                    monthDiv.style.display = singleMode ? 'block' : 'none';
                }
                
                function startDownload() {
                    const station = document.getElementById('station').value.toUpperCase();
                    const year = document.getElementById('year').value;
                    const mode = document.querySelector('input[name="mode"]:checked').value;
                    const month = mode === 'single' ? document.getElementById('month').value : '00';
                    
                    if (station.length !== 4) {
                        alert('Please enter a valid 4-letter ICAO station code');
                        return;
                    }
                    
                    // Show loading
                    document.getElementById('loading').style.display = 'block';
                    document.querySelector('form').style.display = 'none';
                    
                    // Update status
                    const statusText = document.getElementById('statusText');
                    if (mode === 'all') {
                        statusText.textContent = `Downloading ALL months for ${station} ${year}...`;
                    } else {
                        const monthNames = {
                            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                        };
                        const monthName = monthNames[month] || month;
                        statusText.textContent = `Downloading ${station} ${monthName} ${year}...`;
                    }
                    
                    // Redirect to download page
                    if (mode === 'all') {
                        window.location.href = `/batch?station=${station}&year=${year}`;
                    } else {
                        window.location.href = `/download?station=${station}&year=${year}&month=${month}`;
                    }
                }
                
                function resetForm() {
                    document.getElementById('station').value = 'VOGA';
                    document.getElementById('year').value = '2024';
                    document.getElementById('single').checked = true;
                    document.getElementById('month').value = '01';
                    updateMonthVisibility();
                    
                    // Reset highlights
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                        if (card.querySelector('.station-code').textContent === 'VOGA') {
                            card.classList.add('highlight');
                        }
                    });
                }
                
                // Initialize
                document.addEventListener('DOMContentLoaded', function() {
                    updateMonthVisibility();
                    document.querySelectorAll('input[name="mode"]').forEach(radio => {
                        radio.addEventListener('change', updateMonthVisibility);
                    });
                });
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def process_download_request(self):
        """Handle single month download"""
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = urllib.parse.parse_qs(query)
        
        station = params.get('station', ['VOGA'])[0].upper()
        year = params.get('year', ['2024'])[0]
        month = params.get('month', ['01'])[0]
        
        print(f"Single download: {station} {year}-{month}")
        
        # Download data
        result = self.download_single_month(station, year, month)
        
        # Show result
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = self.create_single_result_page(result, station, year, month)
        self.wfile.write(html.encode('utf-8'))
    
    def process_batch_request(self):
        """Handle all months download"""
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = urllib.parse.parse_qs(query)
        
        station = params.get('station', ['VOGA'])[0].upper()
        year = params.get('year', ['2024'])[0]
        
        print(f"Batch download: {station} {year} (all months)")
        
        # Start batch download
        results = self.download_all_months(station, year)
        
        # Show result
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = self.create_batch_result_page(results, station, year)
        self.wfile.write(html.encode('utf-8'))
    
    def download_single_month(self, station, year, month):
        """Download single month with original cleaning"""
        result = {
            'success': False,
            'filename': '',
            'reports': 0,
            'error': '',
            'raw_data': '',
            'clean_data': ''
        }
        
        try:
            print(f"Downloading {station} {year}-{month}...")
            
            # Get data with original cleaning
            clean_data, raw_data = self.get_metar_data(station, year, month)
            
            if clean_data and len(clean_data.strip()) > 0:
                # Save file
                filename = f"METAR{year}{month}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(clean_data)
                
                # Count reports
                lines = clean_data.strip().split('\n')
                report_count = len([l for l in lines if l.strip()])
                
                result['success'] = True
                result['filename'] = filename
                result['reports'] = report_count
                result['raw_data'] = raw_data
                result['clean_data'] = clean_data
                
                print(f"✅ Saved {report_count} reports to {filename}")
            else:
                result['error'] = "No METAR data found"
                print("❌ No data found")
        
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Exception: {e}")
        
        return result
    
    def download_all_months(self, station, year):
        """Download all 12 months in batches"""
        results = []
        folder_name = f"{station}_{year}"
        os.makedirs(folder_name, exist_ok=True)
        
        month_days = {
            '01': '31', '02': '28', '03': '31', '04': '30',
            '05': '31', '06': '30', '07': '31', '08': '31',
            '09': '30', '10': '31', '11': '30', '12': '31'
        }
        
        month_names = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        is_leap = int(year) % 4 == 0
        
        # Process in batches of 3 (like original)
        all_months = list(range(1, 13))
        batches = [all_months[i:i+3] for i in range(0, len(all_months), 3)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n📦 Batch {batch_idx + 1}/{len(batches)}")
            
            for month_num in batch:
                month = f"{month_num:02d}"
                month_name = month_names.get(month, f"Month {month}")
                
                if month == '02' and is_leap:
                    end_day = '29'
                else:
                    end_day = month_days.get(month, '31')
                
                print(f"  {month_name}...", end="", flush=True)
                
                try:
                    clean_data, _ = self.get_metar_data(station, year, month, end_day)
                    
                    if clean_data and len(clean_data.strip()) > 0:
                        filename = os.path.join(folder_name, f"METAR{year}{month}.txt")
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(clean_data)
                        
                        lines = clean_data.strip().split('\n')
                        report_count = len([l for l in lines if l.strip()])
                        
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': filename,
                            'reports': report_count,
                            'success': True
                        })
                        
                        print(f"✅ {report_count} reports")
                    else:
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': '',
                            'reports': 0,
                            'success': False,
                            'error': 'No data'
                        })
                        print("❌")
                
                except Exception as e:
                    results.append({
                        'month': month,
                        'month_name': month_name,
                        'filename': '',
                        'reports': 0,
                        'success': False,
                        'error': str(e)
                    })
                    print("❌")
                
                time.sleep(0.5)  # Small delay
            
            # Delay between batches
            if batch_idx < len(batches) - 1:
                print("   Waiting 3 seconds before next batch...")
                time.sleep(3)
        
        return {
            'station': station,
            'year': year,
            'folder': folder_name,
            'results': results,
            'total_success': sum(1 for r in results if r['success']),
            'total_reports': sum(r['reports'] for r in results if r['success'])
        }
    
    def get_metar_data(self, station, year, month, end_day=None):
        """Get METAR data with original cleaning"""
        if not end_day:
            month_days = {
                '01': '31', '02': '28', '03': '31', '04': '30',
                '05': '31', '06': '30', '07': '31', '08': '31',
                '09': '30', '10': '31', '11': '30', '12': '31'
            }
            if month == '02' and int(year) % 4 == 0:
                end_day = '29'
            else:
                end_day = month_days.get(month, '31')
        
        # Create session
        session = requests.Session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # Get cookies
        session.get('https://www.ogimet.com/display_metars2.php?lang=en', 
                   headers=headers, timeout=10)
        time.sleep(0.5)
        
        # Form data (EXACTLY like original)
        form_data = {
            'lugar': station,
            'tipo': 'SA',
            'ord': 'DIR',
            'nil': 'NO',
            'fmt': 'txt',
            'ano': year,
            'mes': month,
            'day': '01',
            'hora': '00',
            'min': '00',
            'anof': year,
            'mesf': month,
            'dayf': end_day,
            'horaf': '23',
            'minf': '59',
            'send': 'Send',
            'enviar': 'Send',
            'lang': 'en'
        }
        
        post_headers = headers.copy()
        post_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.ogimet.com/display_metars2.php?lang=en',
        })
        
        # Send request
        response = session.post(
            'https://www.ogimet.com/display_metars2.php',
            data=form_data,
            headers=post_headers,
            timeout=30
        )
        
        raw_data = response.text
        
        # Apply ORIGINAL cleaning
        clean_data = self.original_clean_metar_text(raw_data)
        
        return clean_data, raw_data
    
    def original_clean_metar_text(self, text):
        """ORIGINAL cleaning function from your code"""
        lines = text.split('\n')
        clean_reports = []
        
        for line in lines:
            line = line.strip()
            
            if not line or not ('METAR' in line or 'SPECI' in line):
                continue
            
            if line.startswith(('<', '#', '<!--')):
                continue
            
            # Remove timestamps - KEY FEATURE!
            if re.match(r'^\d{10,14}\s+', line):
                line = re.sub(r'^\d{10,14}\s+', '', line)
            
            elif '->' in line:
                line = line.split('->', 1)[1].strip()
            
            line = ' '.join(line.split())
            
            if (('METAR' in line or 'SPECI' in line) and 
                len(line) > 20 and 
                re.search(r'\d{6}Z', line)):
                clean_reports.append(line)
        
        def get_time(report):
            match = re.search(r'(\d{6})Z', report)
            return match.group(1) if match else '000000'
        
        clean_reports.sort(key=get_time)
        
        return '\n'.join(clean_reports)
    
    def create_single_result_page(self, result, station, year, month):
        """Create result page for single month"""
        month_names = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        month_name = month_names.get(month, month)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Download Result</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 900px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                
                .result-header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                
                .result-icon {{
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                
                .success .result-icon {{ color: #10b981; }}
                .error .result-icon {{ color: #ef4444; }}
                
                .result-title {{
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 40px 0;
                }}
                
                .stat-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                    border: 1px solid #e0e0e0;
                }}
                
                .stat-value {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                
                .stat-label {{
                    color: #666;
                    font-size: 0.9rem;
                }}
                
                .file-preview {{
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 40px 0;
                }}
                
                .preview-content {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    max-height: 400px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                }}
                
                .action-buttons {{
                    display: flex;
                    gap: 20px;
                    margin-top: 40px;
                }}
                
                .action-btn {{
                    flex: 1;
                    padding: 20px;
                    border: none;
                    border-radius: 12px;
                    font-size: 1.2rem;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: none;
                    text-align: center;
                    transition: all 0.3s;
                }}
                
                .download-btn {{
                    background: linear-gradient(90deg, #10b981, #059669);
                    color: white;
                }}
                
                .download-btn:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 15px 30px rgba(16, 185, 129, 0.4);
                }}
                
                .back-btn {{
                    background: #f8f9fa;
                    color: #555;
                    border: 2px solid #e0e0e0;
                }}
                
                .back-btn:hover {{
                    background: #e9ecef;
                    transform: translateY(-2px);
                }}
                
                .note-box {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 20px;
                    color: #856404;
                }}
            </style>
        </head>
        <body>
            <div class="result-card {'success' if result['success'] else 'error'}">
                <div class="result-header">
                    <div class="result-icon">
                        {'✅' if result['success'] else '❌'}
                    </div>
                    <h1 class="result-title">
                        {'Download Successful!' if result['success'] else 'Download Failed'}
                    </h1>
                    <p>Station: {station} | Month: {month_name} {year}</p>
                </div>
        """
        
        if result['success']:
            html += f"""
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{result['reports']}</div>
                        <div class="stat-label">METAR Reports</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{month_name}</div>
                        <div class="stat-label">Month</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{year}</div>
                        <div class="stat-label">Year</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{station}</div>
                        <div class="stat-label">Station</div>
                    </div>
                </div>
                
                <div class="file-preview">
                    <h3>📄 Cleaned File Preview (timestamps removed):</h3>
                    <div class="preview-content">
            """
            
            # Show cleaned content
            if result['clean_data']:
                lines = result['clean_data'].split('\n')
                for i, line in enumerate(lines[:10]):
                    html += f"{line}<br>"
                if len(lines) > 10:
                    html += f"<br>... and {len(lines) - 10} more lines"
            else:
                html += "Preview not available"
            
            html += f"""
                    </div>
                    <div class="note-box">
                        <strong>✓ Original cleaning applied:</strong> Timestamps (202401010030) removed, 
                        only clean METAR reports saved.
                    </div>
                </div>
                
                <div class="action-buttons">
                    <a href="/file/{result['filename']}" class="action-btn download-btn">
                        📥 Download Clean File
                    </a>
                    <a href="/" class="action-btn back-btn">
                        ← Download Another
                    </a>
                </div>
            """
        else:
            html += f"""
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 1.2rem; color: #666; margin-bottom: 30px;">
                        Error: {result['error']}
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 15px; margin: 30px 0;">
                        <h3 style="margin-bottom: 20px;">Try These Stations:</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                            <a href="/download?station=VOGA&year=2024&month=01" 
                               style="background: #667eea; color: white; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center;">
                                VOGA (Priority)
                            </a>
                            <a href="/download?station=VOMM&year=2024&month=01" 
                               style="background: #e0e0e0; color: #333; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center;">
                                VOMM Chennai
                            </a>
                            <a href="/download?station=VABB&year=2024&month=01" 
                               style="background: #e0e0e0; color: #333; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center;">
                                VABB Mumbai
                            </a>
                            <a href="/download?station=VIDP&year=2024&month=01" 
                               style="background: #e0e0e0; color: #333; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center;">
                                VIDP Delhi
                            </a>
                        </div>
                    </div>
                    
                    <a href="/" class="action-btn back-btn" style="max-width: 300px; margin: 0 auto;">
                        ← Try Again
                    </a>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_batch_result_page(self, results, station, year):
        """Create result page for batch download"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Batch Download Complete</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 1000px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                
                .header h1 {{
                    font-size: 2.5rem;
                    color: #333;
                    margin-bottom: 10px;
                }}
                
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 20px;
                    margin: 40px 0;
                }}
                
                .summary-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                }}
                
                .summary-value {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                
                .success-value {{ color: #10b981; }}
                .total-value {{ color: #667eea; }}
                
                .month-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    margin: 40px 0;
                }}
                
                .month-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    border: 2px solid #e0e0e0;
                    text-align: center;
                }}
                
                .month-success {{
                    border-color: #10b981;
                    background: #f0f9f4;
                }}
                
                .month-failed {{
                    border-color: #ef4444;
                    background: #fef2f2;
                }}
                
                .month-name {{
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                
                .month-reports {{
                    font-size: 1.5rem;
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                
                .action-buttons {{
                    display: flex;
                    gap: 20px;
                    margin-top: 40px;
                }}
                
                .action-btn {{
                    flex: 1;
                    padding: 20px;
                    border: none;
                    border-radius: 12px;
                    font-size: 1.2rem;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: none;
                    text-align: center;
                    transition: all 0.3s;
                }}
                
                .download-btn {{
                    background: linear-gradient(90deg, #10b981, #059669);
                    color: white;
                }}
                
                .download-btn:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 15px 30px rgba(16, 185, 129, 0.4);
                }}
                
                .back-btn {{
                    background: #f8f9fa;
                    color: #555;
                    border: 2px solid #e0e0e0;
                }}
                
                .back-btn:hover {{
                    background: #e9ecef;
                    transform: translateY(-2px);
                }}
                
                .note-box {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 20px;
                    color: #856404;
                }}
            </style>
        </head>
        <body>
            <div class="result-card">
                <div class="header">
                    <h1>📦 Batch Download Complete</h1>
                    <p>{station} - {year} (All 12 Months)</p>
                </div>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-value success-value">{results['total_success']}/12</div>
                        <div class="summary-label">Successful Months</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value total-value">{results['total_reports']:,}</div>
                        <div class="summary-label">Total Reports</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{station}</div>
                        <div class="summary-label">Station</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{year}</div>
                        <div class="summary-label">Year</div>
                    </div>
                </div>
                
                <h3 style="margin-bottom: 20px;">Monthly Results:</h3>
                <div class="month-grid">
        """
        
        # Add month cards
        for result in results['results']:
            status_class = 'month-success' if result['success'] else 'month-failed'
            html += f"""
                    <div class="month-card {status_class}">
                        <div class="month-name">{result['month_name']}</div>
                        <div class="month-reports">
                            {result['reports'] if result['success'] else '❌'}
                        </div>
                        <div style="font-size: 0.9rem; color: #666;">
                            {result['month']}
                        </div>
                    </div>
            """
        
        html += f"""
                </div>
                
                <div class="note-box">
                    <strong>✓ Original batch processing:</strong> Downloaded in batches of 3 months 
                    with delays, just like the terminal version. Timestamps removed from all files.
                </div>
                
                <div class="action-buttons">
                    <a href="/file/{results['folder']}" class="action-btn download-btn">
                        📥 Download All Files (Folder)
                    </a>
                    <a href="/" class="action-btn back-btn">
                        ← New Download
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_file(self):
        """Serve file or folder for download"""
        path = self.path[6:]  # Remove '/file/'
        
        if os.path.isdir(path):
            # Create zip of folder
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.txt'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(path))
                            zipf.write(file_path, arcname)
            
            zip_buffer.seek(0)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}.zip"')
            self.send_header('Content-Length', str(zip_buffer.getbuffer().nbytes))
            self.end_headers()
            self.wfile.write(zip_buffer.getvalue())
            
        elif os.path.exists(path):
            # Serve single file
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"')
            
            with open(path, 'rb') as f:
                file_content = f.read()
            
            self.send_header('Content-Length', str(len(file_content)))
            self.end_headers()
            self.wfile.write(file_content)
        else:
            self.send_error(404, "File not found")

# Start server
print("=" * 60)
print("🌤️ METAR COMPLETE WEB APP")
print("=" * 60)
print(f"Server running on: http://localhost:{PORT}")
print("Features:")
print("  • VOGA priority station")
print("  • Single month & All months download")
print("  • Original timestamp cleaning")
print("  • Batch processing (3 months at a time)")
print("  • Professional UI design")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), MetarHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print(f"Error: {e}")
