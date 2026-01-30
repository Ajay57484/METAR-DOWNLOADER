import http.server
import socketserver
import urllib.parse
import requests
import re
import time
import os
from datetime import datetime

PORT = int(os.environ.get('PORT', 8081))

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
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>METAR/TAF Downloader</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    color: #333;
                }
                
                .container {
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                    padding: 25px 30px;
                    text-align: center;
                }
                
                .header h1 {
                    font-size: 1.8rem;
                    font-weight: 600;
                    margin-bottom: 5px;
                }
                
                .header p {
                    font-size: 0.9rem;
                    opacity: 0.9;
                }
                
                .main-content {
                    padding: 30px;
                    display: grid;
                    gap: 25px;
                }
                
                .form-group {
                    display: grid;
                    gap: 20px;
                }
                
                .form-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                
                .input-group {
                    margin-bottom: 15px;
                }
                
                .input-label {
                    display: block;
                    margin-bottom: 8px;
                    color: #555;
                    font-weight: 600;
                    font-size: 0.9rem;
                }
                
                .input-field {
                    width: 100%;
                    padding: 12px 15px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    font-size: 0.95rem;
                    transition: all 0.3s;
                    background: #f9f9f9;
                }
                
                .input-field:focus {
                    border-color: #667eea;
                    outline: none;
                    background: white;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .radio-group {
                    display: flex;
                    gap: 15px;
                    margin: 10px 0;
                }
                
                .radio-option {
                    flex: 1;
                }
                
                .radio-input { display: none; }
                
                .radio-label {
                    display: block;
                    padding: 15px;
                    background: #f5f5f5;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                    font-size: 0.9rem;
                    text-align: center;
                    font-weight: 500;
                }
                
                .radio-input:checked + .radio-label {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                }
                
                .report-type-group {
                    display: flex;
                    gap: 15px;
                    margin: 15px 0;
                }
                
                .report-type-card {
                    flex: 1;
                    padding: 20px;
                    background: white;
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .report-type-card:hover {
                    border-color: #667eea;
                }
                
                .report-type-card.selected {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                }
                
                .report-type-icon {
                    font-size: 1.8rem;
                    margin-bottom: 8px;
                }
                
                .report-type-name {
                    font-size: 1rem;
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                
                .report-type-desc {
                    font-size: 0.8rem;
                    opacity: 0.8;
                }
                
                .quick-stations {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                    margin: 15px 0;
                }
                
                .station-card {
                    padding: 15px;
                    background: white;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .station-card:hover {
                    border-color: #667eea;
                    transform: translateY(-2px);
                }
                
                .station-card.highlight {
                    background: #fff9e6;
                    border-color: #ffc107;
                }
                
                .station-code {
                    font-size: 1.4rem;
                    font-weight: 700;
                    color: #667eea;
                    margin-bottom: 4px;
                }
                
                .station-name {
                    font-size: 0.75rem;
                    color: #666;
                }
                
                .button-group {
                    display: flex;
                    gap: 15px;
                    margin-top: 25px;
                }
                
                .btn {
                    flex: 1;
                    padding: 15px;
                    border: none;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }
                
                .btn-primary {
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                }
                
                .btn-primary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                }
                
                .btn-secondary {
                    background: #f5f5f5;
                    color: #555;
                    border: 2px solid #ddd;
                }
                
                .btn-secondary:hover {
                    background: #e9e9e9;
                }
                
                .info-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #ddd;
                    margin-top: 20px;
                }
                
                .info-title {
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: #555;
                    font-size: 0.9rem;
                }
                
                .info-content {
                    font-size: 0.85rem;
                    color: #666;
                    line-height: 1.5;
                }
                
                .loading {
                    display: none;
                    text-align: center;
                    padding: 40px;
                }
                
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .footer {
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 0.85rem;
                    border-top: 1px solid #ddd;
                }
                
                @media (max-width: 768px) {
                    .form-row { grid-template-columns: 1fr; }
                    .quick-stations { grid-template-columns: repeat(2, 1fr); }
                    .container { border-radius: 10px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌤️ METAR/TAF Downloader</h1>
                    <p>Download aviation weather reports | AJAY YADAV (IMD GOA)</p>
                </div>
                
                <div class="main-content">
                    <form id="downloadForm">
                        <!-- Report Type -->
                        <div class="input-group">
                            <div class="input-label">Report Type</div>
                            <div class="report-type-group">
                                <div class="report-type-card selected" onclick="selectReportType('METAR')" id="metarCard">
                                    <div class="report-type-icon">🌤️</div>
                                    <div class="report-type-name">METAR</div>
                                    <div class="report-type-desc">Weather Report</div>
                                </div>
                                <div class="report-type-card" onclick="selectReportType('TAF')" id="tafCard">
                                    <div class="report-type-icon">📡</div>
                                    <div class="report-type-name">TAF</div>
                                    <div class="report-type-desc">Forecast</div>
                                </div>
                            </div>
                            <input type="hidden" id="reportType" value="METAR">
                        </div>
                        
                        <!-- Station and Year -->
                        <div class="form-row">
                            <div class="input-group">
                                <label class="input-label">Station Code</label>
                                <input type="text" class="input-field" id="station" value="VOGA" 
                                       maxlength="4" pattern="[A-Z]{4}" placeholder="4-letter ICAO" required>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Year</label>
                                <input type="number" class="input-field" id="year" value="2024" min="2000" max="2026" required>
                            </div>
                        </div>
                        
                        <!-- Quick Stations -->
                        <div class="input-group">
                            <div class="input-label">Quick Stations</div>
                            <div class="quick-stations">
                                <div class="station-card highlight" onclick="setStation('VOGA')">
                                    <div class="station-code">VOGA</div>
                                    <div class="station-name">GOA</div>
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
                        
                        <!-- Download Mode -->
                        <div class="input-group">
                            <div class="input-label">Download Mode</div>
                            <div class="radio-group">
                                <div class="radio-option">
                                    <input type="radio" id="single" name="mode" value="single" checked class="radio-input">
                                    <label for="single" class="radio-label">Single Month</label>
                                </div>
                                <div class="radio-option">
                                    <input type="radio" id="all" name="mode" value="all" class="radio-input">
                                    <label for="all" class="radio-label">All Months</label>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Month Selection -->
                        <div id="monthSelection">
                            <div class="input-group">
                                <label class="input-label">Month</label>
                                <select class="input-field" id="month">
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
                        
                        <!-- Buttons -->
                        <div class="button-group">
                            <button type="button" class="btn btn-primary" onclick="startDownload()">
                                <span>🚀</span>
                                <span>Start Download</span>
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="resetForm()">
                                <span>↻</span>
                                <span>Reset</span>
                            </button>
                        </div>
                    </form>
                    
                    <!-- Info Box -->
                    <div class="info-box">
                        <div class="info-title">ℹ️ Information</div>
                        <div class="info-content">
                            • METAR: Timestamps removed<br>
                            • TAF: Leading timestamps removed, BECMG/TEMPO kept<br>
                            • Files: METARYYYYMM.txt / TAFYYYYMM.txt<br>
                            • Batch: 3 months at a time
                        </div>
                    </div>
                    
                    <!-- Loading -->
                    <div id="loading" class="loading">
                        <div class="spinner"></div>
                        <h3>Downloading...</h3>
                        <p id="statusText">Please wait</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Contact: ajaypahe02@gmail.com | It may take awhile...</p>
                </div>
            </div>
            
            <script>
                function selectReportType(type) {
                    document.getElementById('reportType').value = type;
                    document.getElementById('metarCard').classList.remove('selected');
                    document.getElementById('tafCard').classList.remove('selected');
                    if (type === 'METAR') {
                        document.getElementById('metarCard').classList.add('selected');
                    } else {
                        document.getElementById('tafCard').classList.add('selected');
                    }
                }
                
                function setStation(code) {
                    document.getElementById('station').value = code;
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                    });
                    event.currentTarget.classList.add('highlight');
                }
                
                function updateMonthVisibility() {
                    const singleMode = document.getElementById('single').checked;
                    document.getElementById('monthSelection').style.display = singleMode ? 'block' : 'none';
                }
                
                function startDownload() {
                    const reportType = document.getElementById('reportType').value;
                    const station = document.getElementById('station').value.toUpperCase();
                    const year = document.getElementById('year').value;
                    const mode = document.querySelector('input[name="mode"]:checked').value;
                    const month = mode === 'single' ? document.getElementById('month').value : '00';
                    
                    if (station.length !== 4) {
                        alert('Enter valid 4-letter ICAO code');
                        return;
                    }
                    
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('downloadForm').style.opacity = '0.5';
                    document.getElementById('downloadForm').style.pointerEvents = 'none';
                    
                    const statusText = document.getElementById('statusText');
                    if (mode === 'all') {
                        statusText.textContent = `Downloading ALL months of ${reportType} for ${station} ${year}...`;
                    } else {
                        const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
                        const monthName = monthNames[parseInt(month)-1] || month;
                        statusText.textContent = `Downloading ${reportType} ${station} ${monthName} ${year}...`;
                    }
                    
                    if (mode === 'all') {
                        window.location.href = `/batch?station=${station}&year=${year}&type=${reportType}`;
                    } else {
                        window.location.href = `/download?station=${station}&year=${year}&month=${month}&type=${reportType}`;
                    }
                }
                
                function resetForm() {
                    document.getElementById('reportType').value = 'METAR';
                    document.getElementById('station').value = 'VOGA';
                    document.getElementById('year').value = '2024';
                    document.getElementById('single').checked = true;
                    document.getElementById('month').value = '01';
                    selectReportType('METAR');
                    updateMonthVisibility();
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                        if (card.querySelector('.station-code').textContent === 'VOGA') {
                            card.classList.add('highlight');
                        }
                    });
                }
                
                document.addEventListener('DOMContentLoaded', function() {
                    selectReportType('METAR');
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
        report_type = params.get('type', ['METAR'])[0].upper()
        
        print(f"{report_type} download: {station} {year}-{month}")
        
        result = self.download_single_month(station, year, month, report_type)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = self.create_single_result_page(result, station, year, month, report_type)
        self.wfile.write(html.encode('utf-8'))

    def process_batch_request(self):
        """Handle all months download"""
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = urllib.parse.parse_qs(query)
        station = params.get('station', ['VOGA'])[0].upper()
        year = params.get('year', ['2024'])[0]
        report_type = params.get('type', ['METAR'])[0].upper()
        
        print(f"Batch {report_type} download: {station} {year}")
        
        results = self.download_all_months(station, year, report_type)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = self.create_batch_result_page(results, station, year, report_type)
        self.wfile.write(html.encode('utf-8'))

    def download_single_month(self, station, year, month, report_type):
        """Download single month"""
        result = {
            'success': False,
            'filename': '',
            'reports': 0,
            'error': '',
            'clean_data': '',
            'report_type': report_type
        }
        
        try:
            print(f"Downloading {report_type} {station} {year}-{month}...")
            
            clean_data, raw_data = self.get_weather_data(station, year, month, report_type)
            
            if clean_data and len(clean_data.strip()) > 0:
                filename = f"{report_type}{year}{month}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(clean_data)
                
                # Better counting for TAF
                if report_type == 'TAF':
                    # Count TAF issuances (lines starting with TAF)
                    lines = clean_data.strip().split('\n')
                    report_count = 0
                    for line in lines:
                        if line.strip().startswith('TAF'):
                            report_count += 1
                else:
                    lines = clean_data.strip().split('\n')
                    report_count = len([l for l in lines if l.strip()])
                
                result['success'] = True
                result['filename'] = filename
                result['reports'] = report_count
                result['clean_data'] = clean_data
                
                print(f"✅ Saved {report_count} {report_type} reports")
            else:
                result['error'] = f"No {report_type} data found"
                print(f"❌ No {report_type} data")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")
        
        return result

    def download_all_months(self, station, year, report_type):
        """Download all 12 months"""
        results = []
        folder_name = f"{report_type}_{station}_{year}"
        os.makedirs(folder_name, exist_ok=True)
        
        month_days = {
            '01': '31', '02': '28', '03': '31', '04': '30',
            '05': '31', '06': '30', '07': '31', '08': '31',
            '09': '30', '10': '31', '11': '30', '12': '31'
        }
        
        month_names = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        
        is_leap = int(year) % 4 == 0
        
        all_months = list(range(1, 13))
        batches = [all_months[i:i+3] for i in range(0, len(all_months), 3)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n📦 {report_type} Batch {batch_idx + 1}/{len(batches)}")
            
            for month_num in batch:
                month = f"{month_num:02d}"
                month_name = month_names.get(month, f"M{month}")
                
                if month == '02' and is_leap:
                    end_day = '29'
                else:
                    end_day = month_days.get(month, '31')
                
                print(f"  {month_name}...", end="", flush=True)
                
                try:
                    clean_data, _ = self.get_weather_data(station, year, month, report_type, end_day)
                    
                    if clean_data and len(clean_data.strip()) > 0:
                        filename = os.path.join(folder_name, f"{report_type}{year}{month}.txt")
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(clean_data)
                        
                        # Better counting for TAF
                        if report_type == 'TAF':
                            lines = clean_data.strip().split('\n')
                            report_count = 0
                            for line in lines:
                                if line.strip().startswith('TAF'):
                                    report_count += 1
                        else:
                            lines = clean_data.strip().split('\n')
                            report_count = len([l for l in lines if l.strip()])
                        
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': filename,
                            'reports': report_count,
                            'success': True
                        })
                        
                        print(f"✅ {report_count}")
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
                
                time.sleep(0.5)
            
            if batch_idx < len(batches) - 1:
                time.sleep(2)
        
        return {
            'station': station,
            'year': year,
            'report_type': report_type,
            'folder': folder_name,
            'results': results,
            'total_success': sum(1 for r in results if r['success']),
            'total_reports': sum(r['reports'] for r in results if r['success'])
        }

    def get_weather_data(self, station, year, month, report_type='METAR', end_day=None):
        """Get METAR or TAF data"""
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
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        try:
            session.get('https://www.ogimet.com/display_metars2.php?lang=en', headers=headers, timeout=10)
            time.sleep(0.5)
        except:
            pass
        
        tipo = 'FC' if report_type == 'TAF' else 'SA'
        
        form_data = {
            'lugar': station,
            'tipo': tipo,
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
            'send': 'send',
            'enviar': 'Send',
            'lang': 'en'
        }
        
        post_headers = headers.copy()
        post_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.ogimet.com/display_metars2.php?lang=en',
        })
        
        try:
            response = session.post(
                'https://www.ogimet.com/display_metars2.php',
                data=form_data,
                headers=post_headers,
                timeout=60
            )
            
            print(f"  Response status: {response.status_code}")
            print(f"  Response size: {len(response.text)} bytes")
            
            raw_data = response.text
            
            # Save raw data for debugging
            debug_filename = f"debug_raw_{report_type}_{station}_{year}{month}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(raw_data)
            print(f"  Raw data saved to: {debug_filename}")
            
            if report_type == 'TAF':
                clean_data = self.clean_taf_text_fixed(raw_data)
            else:
                clean_data = self.clean_metar_text_original(raw_data)
            
            # Save cleaned data for debugging
            clean_filename = f"debug_clean_{report_type}_{station}_{year}{month}.txt"
            with open(clean_filename, 'w', encoding='utf-8') as f:
                f.write(clean_data)
            print(f"  Clean data saved to: {clean_filename}")
            print(f"  Clean data length: {len(clean_data)} chars")
            
            return clean_data, raw_data
            
        except Exception as e:
            print(f"  Request error: {e}")
            return "", f"Request error: {e}"

    def clean_metar_text_original(self, text):
        """Clean METAR text - remove timestamps"""
        lines = text.split('\n')
        clean_reports = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Skip HTML/comments
            if line.startswith(('<', '#', '<!--')):
                continue
            
            # Only process METAR/SPECI lines
            if 'METAR' in line or 'SPECI' in line:
                # Remove timestamps
                if re.match(r'^\d{10,14}\s+', line):
                    line = re.sub(r'^\d{10,14}\s+', '', line)
                elif '->' in line:
                    line = line.split('->', 1)[1].strip()
                
                line = ' '.join(line.split())
                
                # Validate it's a proper METAR
                if len(line) > 20 and re.search(r'\d{6}Z', line):
                    clean_reports.append(line)
        
        # Sort by time
        def get_time(report):
            match = re.search(r'(\d{6})Z', report)
            return match.group(1) if match else '000000'
        
        clean_reports.sort(key=get_time)
        
        return '\n'.join(clean_reports)

    def clean_taf_text_fixed(self, text):
        """Improved TAF cleaning that captures ALL TAF lines"""
        lines = text.split('\n')
        clean_tafs = []
        current_taf = []
        in_taf = False
        
        print(f"  Processing {len(lines)} lines for TAF cleaning")
        
        for i, line in enumerate(lines):
            line = line.rstrip()  # Only remove trailing spaces
            
            if not line:
                continue
            
            # Skip HTML/comments
            if line.startswith(('<', '#', '<!--')):
                continue
            
            # Debug: Print first few lines to see what we're getting
            if i < 5:
                print(f"    Line {i}: '{line[:50]}...'")
            
            # Check if this is a TAF line (timestamp followed by TAF)
            if re.match(r'^\d{12}\s+(TAF|TAF\s+AMD|TAF\s+COR)', line):
                # Save previous TAF if exists
                if current_taf:
                    clean_taf = self.process_taf_lines_fixed(current_taf)
                    if clean_taf:
                        clean_tafs.append(clean_taf)
                        print(f"    Added TAF: {clean_taf[:50]}...")
                    current_taf = []
                
                # Start new TAF - REMOVE leading timestamp
                clean_line = re.sub(r'^\d{12}\s+', '', line)
                current_taf.append(clean_line)
                in_taf = True
                print(f"    Found new TAF at line {i}")
            
            # If we're in a TAF and line continues it
            elif in_taf:
                # Check for continuation lines (start with spaces, BECMG, TEMPO, FM, PROB, or just more TAF text)
                if (line.startswith(' ') or line.startswith('\t') or 
                    line.startswith('BECMG') or line.startswith('TEMPO') or 
                    line.startswith('FM') or line.startswith('PROB') or
                    line.startswith('INTER') or '=' in line or
                    re.match(r'^\s*\d{4}/\d{4}', line) or
                    re.match(r'^\s*[A-Z]{2}\d{2}', line)):
                    
                    # Clean the continuation line
                    clean_line = line.strip()
                    if clean_line:
                        current_taf.append(clean_line)
                
                # If line doesn't continue TAF (new TAF or other content)
                elif not (line.startswith(' ') or line.startswith('\t')):
                    # End current TAF
                    if current_taf:
                        clean_taf = self.process_taf_lines_fixed(current_taf)
                        if clean_taf:
                            clean_tafs.append(clean_taf)
                            print(f"    Completed TAF: {clean_taf[:50]}...")
                        current_taf = []
                    in_taf = False
        
        # Add last TAF if exists
        if current_taf:
            clean_taf = self.process_taf_lines_fixed(current_taf)
            if clean_taf:
                clean_tafs.append(clean_taf)
                print(f"    Final TAF: {clean_taf[:50]}...")
        
        print(f"  Total TAFs found: {len(clean_tafs)}")
        
        # Sort by time (extract from TAF line)
        def get_taf_time(taf):
            # Extract timestamp from first line
            first_line = taf.split('\n')[0] if '\n' in taf else taf
            match = re.search(r'(\d{6})Z', first_line)
            return match.group(1) if match else '000000'
        
        clean_tafs.sort(key=get_taf_time)
        
        # Join with newlines (not spaces) to keep multi-line format
        return '\n'.join(clean_tafs)

    def process_taf_lines_fixed(self, taf_lines):
        """Process TAF lines - keep multi-line format"""
        if not taf_lines:
            return ""
        
        # Join with newline to keep multi-line format
        clean_taf = '\n'.join(taf_lines)
        
        # Remove extra spaces but preserve newlines
        lines = clean_taf.split('\n')
        cleaned_lines = []
        for line in lines:
            line = ' '.join(line.split())  # Remove extra spaces within line
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        clean_taf = '\n'.join(cleaned_lines)
        
        # Ensure it's a valid TAF
        if 'TAF' in clean_taf and re.search(r'\d{6}Z', clean_taf):
            return clean_taf
        return ""

    def create_single_result_page(self, result, station, year, month, report_type):
        """Create result page"""
        month_names = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        month_name = month_names.get(month, month)
        report_type_lower = report_type.lower()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download Result</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    color: #333;
                }}
                
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                    padding: 25px 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    font-size: 1.8rem;
                    font-weight: 600;
                    margin-bottom: 5px;
                }}
                
                .header p {{
                    font-size: 0.9rem;
                    opacity: 0.9;
                }}
                
                .content {{
                    padding: 30px;
                }}
                
                .result-icon {{
                    font-size: 3.5rem;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                
                .success .result-icon {{ color: #10b981; }}
                .error .result-icon {{ color: #ef4444; }}
                
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin: 30px 0;
                }}
                
                .stat-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid #ddd;
                }}
                
                .stat-value {{
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: #667eea;
                    margin-bottom: 5px;
                }}
                
                .stat-label {{
                    font-size: 0.85rem;
                    color: #666;
                }}
                
                .preview {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 25px 0;
                    border: 1px solid #ddd;
                }}
                
                .preview-title {{
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: #555;
                    font-size: 0.95rem;
                }}
                
                .preview-content {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 0.85rem;
                    line-height: 1.4;
                    border: 1px solid #ddd;
                }}
                
                .buttons {{
                    display: flex;
                    gap: 15px;
                    margin-top: 25px;
                }}
                
                .btn {{
                    flex: 1;
                    padding: 15px;
                    border: none;
                    border-radius: 8px;
                    font-size: 1rem;
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
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
                }}
                
                .back-btn {{
                    background: #f5f5f5;
                    color: #555;
                    border: 2px solid #ddd;
                }}
                
                .back-btn:hover {{
                    background: #e9e9e9;
                }}
                
                .note {{
                    background: #fff9e6;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 20px;
                    border: 1px solid #ffc107;
                    font-size: 0.85rem;
                    color: #856404;
                }}
                
                @media (max-width: 768px) {{
                    .stats {{ grid-template-columns: repeat(2, 1fr); }}
                    .buttons {{ flex-direction: column; }}
                }}
            </style>
        </head>
        <body>
            <div class="container {'success' if result['success'] else 'error'}">
                <div class="header">
                    <h1>{'Download Complete!' if result['success'] else 'Download Failed'}</h1>
                    <p>{report_type} | {station} | {month_name} {year}</p>
                </div>
                
                <div class="content">
                    <div class="result-icon">
                        {'✅' if result['success'] else '❌'}
                    </div>
        """
        
        if result['success']:
            html += f"""
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-value">{result['reports']}</div>
                            <div class="stat-label">Reports</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{month_name[:3]}</div>
                            <div class="stat-label">Month</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{year}</div>
                            <div class="stat-label">Year</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{report_type}</div>
                            <div class="stat-label">Type</div>
                        </div>
                    </div>
                    
                    <div class="preview">
                        <div class="preview-title">Preview (first {min(20, result['reports'])} lines):</div>
                        <div class="preview-content">
            """
            
            if result['clean_data']:
                lines = result['clean_data'].split('\n')
                for i, line in enumerate(lines[:20]):
                    html += f"{line}<br>"
                if len(lines) > 20:
                    html += f"<br>... {len(lines)-20} more lines"
            else:
                html += "No preview available"
            
            html += f"""
                        </div>
                    </div>
                    
                    <div class="note">
                        {'✓ TAF: Leading timestamps removed, BECMG/TEMPO preserved' if report_type == 'TAF' else '✓ METAR: Timestamps removed'}
                        <br>✓ File: {result['filename']}
                    </div>
                    
                    <div class="buttons">
                        <a href="/file/{result['filename']}" class="btn download-btn">
                            📥 Download File
                        </a>
                        <a href="/" class="btn back-btn">
                            ← Back
                        </a>
                    </div>
            """
        else:
            html += f"""
                    <div style="text-align: center; padding: 30px 0;">
                        <div style="font-size: 1.1rem; color: #666; margin-bottom: 25px;">
                            <strong>Error:</strong> {result['error']}
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                            <div style="font-weight: 600; margin-bottom: 15px; color: #555;">Try These Stations:</div>
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                                <a href="/download?station=VOGA&year=2024&month=01&type={report_type_lower}" 
                                   style="background: #667eea; color: white; padding: 12px; border-radius: 8px; text-decoration: none; text-align: center; font-size: 0.9rem;">
                                    VOGA
                                </a>
                                <a href="/download?station=VOMM&year=2024&month=01&type={report_type_lower}" 
                                   style="background: #e0e0e0; color: #333; padding: 12px; border-radius: 8px; text-decoration: none; text-align: center; font-size: 0.9rem;">
                                    VOMM
                                </a>
                                <a href="/download?station=VABB&year=2024&month=01&type={report_type_lower}" 
                                   style="background: #e0e0e0; color: #333; padding: 12px; border-radius: 8px; text-decoration: none; text-align: center; font-size: 0.9rem;">
                                    VABB
                                </a>
                                <a href="/download?station=VIDP&year=2024&month=01&type={report_type_lower}" 
                                   style="background: #e0e0e0; color: #333; padding: 12px; border-radius: 8px; text-decoration: none; text-align: center; font-size: 0.9rem;">
                                    VIDP
                                </a>
                            </div>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 0.85rem; color: #666;">
                            <strong>Debug Info:</strong> Check debug_raw_{report_type}_{station}_{year}{month}.html and debug_clean_{report_type}_{station}_{year}{month}.txt files
                        </div>
                        
                        <a href="/" class="btn back-btn" style="max-width: 200px; margin: 0 auto;">
                            ← Try Again
                        </a>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def create_batch_result_page(self, results, station, year, report_type):
        """Create batch result page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Batch Complete</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    color: #333;
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                    padding: 25px 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    font-size: 1.8rem;
                    font-weight: 600;
                    margin-bottom: 5px;
                }}
                
                .header p {{
                    font-size: 0.9rem;
                    opacity: 0.9;
                }}
                
                .content {{
                    padding: 30px;
                }}
                
                .summary {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin: 25px 0;
                }}
                
                .summary-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid #ddd;
                }}
                
                .summary-value {{
                    font-size: 1.8rem;
                    font-weight: 700;
                    margin-bottom: 5px;
                }}
                
                .success-value {{ color: #10b981; }}
                .total-value {{ color: #667eea; }}
                
                .summary-label {{
                    font-size: 0.85rem;
                    color: #666;
                }}
                
                .months {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 12px;
                    margin: 30px 0;
                }}
                
                .month-card {{
                    padding: 15px;
                    background: white;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    text-align: center;
                }}
                
                .month-success {{ border-color: #10b981; background: #f0f9f4; }}
                .month-failed {{ border-color: #ef4444; background: #fef2f2; }}
                
                .month-name {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    font-size: 0.95rem;
                }}
                
                .month-reports {{
                    font-size: 1.4rem;
                    color: #667eea;
                    margin-bottom: 5px;
                    font-weight: 700;
                }}
                
                .buttons {{
                    display: flex;
                    gap: 15px;
                    margin-top: 25px;
                }}
                
                .btn {{
                    flex: 1;
                    padding: 15px;
                    border: none;
                    border-radius: 8px;
                    font-size: 1rem;
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
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
                }}
                
                .back-btn {{
                    background: #f5f5f5;
                    color: #555;
                    border: 2px solid #ddd;
                }}
                
                .back-btn:hover {{
                    background: #e9e9e9;
                }}
                
                .note {{
                    background: #fff9e6;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 20px;
                    border: 1px solid #ffc107;
                    font-size: 0.85rem;
                    color: #856404;
                }}
                
                @media (max-width: 768px) {{
                    .summary {{ grid-template-columns: repeat(2, 1fr); }}
                    .months {{ grid-template-columns: repeat(2, 1fr); }}
                    .buttons {{ flex-direction: column; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📦 Batch Complete</h1>
                    <p>{report_type} | {station} | {year}</p>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <div class="summary-card">
                            <div class="summary-value success-value">{results['total_success']}/12</div>
                            <div class="summary-label">Success</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-value total-value">{results['total_reports']:,}</div>
                            <div class="summary-label">Reports</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-value">{station}</div>
                            <div class="summary-label">Station</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-value">{report_type}</div>
                            <div class="summary-label">Type</div>
                        </div>
                    </div>
                    
                    <h3 style="margin-bottom: 15px; color: #555; font-size: 1.1rem;">Monthly Results:</h3>
                    <div class="months">
        """
        
        for result in results['results']:
            status_class = 'month-success' if result['success'] else 'month-failed'
            html += f"""
                        <div class="month-card {status_class}">
                            <div class="month-name">{result['month_name']}</div>
                            <div class="month-reports">
                                {result['reports'] if result['success'] else '❌'}
                            </div>
                            <div style="font-size: 0.8rem; color: #666;">{result['month']}</div>
                        </div>
            """
        
        html += f"""
                    </div>
                    
                    <div class="note">
                        ✓ {report_type}: {'Leading timestamps removed, BECMG/TEMPO kept' if report_type == 'TAF' else 'Timestamps removed'}<br>
                        ✓ Processed in batches of 3 months<br>
                        ✓ Folder: {results['folder']}
                    </div>
                    
                    <div class="buttons">
                        <a href="/file/{results['folder']}" class="btn download-btn">
                            📥 Download All (ZIP)
                        </a>
                        <a href="/" class="btn back-btn">
                            ← New Download
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def send_file(self):
        """Serve file or folder"""
        path = self.path[6:]  # Remove '/file/'
        
        if os.path.isdir(path):
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

print("=" * 60)
print("🌤️ METAR/TAF Downloader")
print("=" * 60)
print(f"Server: http://localhost:{PORT}")
print("Fixed TAF processing | Compact design")
print("Debug files: debug_raw_* and debug_clean_*")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), MetarHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print(f"Error: {e}")
