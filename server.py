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
            <title>METAR/TAF Smart Downloader</title>
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
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .container {
                    display: flex;
                    width: 95%;
                    max-width: 1400px;
                    gap: 30px;
                }
                .glass-card {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }
                .header h1 {
                    font-size: 2.8rem;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .header p {
                    color: #666;
                    font-size: 1.2rem;
                }
                .content-wrapper {
                    display: flex;
                    gap: 40px;
                }
                .form-column {
                    flex: 1;
                    min-width: 500px;
                }
                .info-column {
                    flex: 1;
                    min-width: 500px;
                }
                .form-section {
                    margin-bottom: 30px;
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.05);
                }
                .section-title {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                    color: #333;
                    font-size: 1.3rem;
                    font-weight: 600;
                }
                .section-title .icon {
                    margin-right: 12px;
                    font-size: 1.4rem;
                }
                .input-group {
                    margin-bottom: 20px;
                }
                .input-label {
                    display: block;
                    margin-bottom: 10px;
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
                .report-type-group {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }
                .report-type-card {
                    background: white;
                    padding: 25px;
                    border-radius: 12px;
                    border: 2px solid #e0e0e0;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .report-type-card:hover {
                    border-color: #667eea;
                    transform: translateY(-2px);
                }
                .report-type-card.selected {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
                }
                .report-type-icon {
                    font-size: 2.2rem;
                    margin-bottom: 12px;
                }
                .report-type-name {
                    font-size: 1.3rem;
                    font-weight: bold;
                    margin-bottom: 8px;
                }
                .report-type-desc {
                    font-size: 0.95rem;
                    opacity: 0.9;
                }
                .quick-stations {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
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
                    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                }
                .station-card.highlight {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                }
                .station-card.highlight .station-code {
                    color: white;
                }
                .station-card.highlight .station-name {
                    color: rgba(255, 255, 255, 0.9);
                }
                .station-code {
                    font-size: 1.8rem;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 8px;
                }
                .station-name {
                    color: #666;
                    font-size: 0.95rem;
                }
                .radio-group {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }
                .radio-option {
                    text-align: center;
                }
                .radio-input {
                    display: none;
                }
                .radio-label {
                    display: block;
                    padding: 18px;
                    background: #f8f9fa;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.3s;
                    font-weight: 500;
                    font-size: 1.1rem;
                }
                .radio-input:checked + .radio-label {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                }
                .year-month-group {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                #monthSelection {
                    grid-column: span 2;
                }
                .action-buttons {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 30px;
                }
                .btn {
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
                    gap: 12px;
                }
                .btn-primary {
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    color: white;
                }
                .btn-primary:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
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
                .status-bar {
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 15px;
                    text-align: center;
                    color: #666;
                    font-size: 1rem;
                    border: 1px solid #e0e0e0;
                }
                .info-panel {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 25px;
                    border-radius: 15px;
                    border: 1px solid #dee2e6;
                    height: 100%;
                }
                .info-title {
                    color: #333;
                    font-size: 1.3rem;
                    margin-bottom: 20px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .info-content {
                    color: #666;
                    font-size: 1rem;
                    line-height: 1.6;
                }
                .info-list {
                    list-style: none;
                    padding: 0;
                    margin: 20px 0;
                }
                .info-list li {
                    margin-bottom: 15px;
                    padding-left: 30px;
                    position: relative;
                }
                .info-list li:before {
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #667eea;
                    font-weight: bold;
                    font-size: 1.2rem;
                }
                .loading {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    z-index: 1000;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .spinner {
                    width: 60px;
                    height: 60px;
                    border: 6px solid #f3f3f3;
                    border-top: 6px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 25px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @media (max-width: 1200px) {
                    .container {
                        width: 98%;
                        gap: 20px;
                    }
                }
                @media (max-width: 1024px) {
                    .content-wrapper {
                        flex-direction: column;
                    }
                    .form-column, .info-column {
                        min-width: 100%;
                    }
                }
                @media (max-width: 768px) {
                    .glass-card {
                        padding: 25px;
                    }
                    .header h1 {
                        font-size: 2.2rem;
                    }
                    .year-month-group {
                        grid-template-columns: 1fr;
                    }
                    #monthSelection {
                        grid-column: span 1;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="glass-card">
                    <div class="header">
                        <h1>🌤️ METAR/TAF Smart Downloader</h1>
                        <p>Download aviation weather reports (METAR/TAF)</p>
                    </div>
                    
                    <div class="content-wrapper">
                        <!-- Left Column: Input Form -->
                        <div class="form-column">
                            <form id="downloadForm">
                                <!-- Report Type -->
                                <div class="form-section">
                                    <div class="section-title">
                                        <span class="icon">📋</span>
                                        <span>Report Type</span>
                                    </div>
                                    <div class="report-type-group">
                                        <div class="report-type-card selected" onclick="selectReportType('METAR')" id="metarCard">
                                            <div class="report-type-icon">🌤️</div>
                                            <div class="report-type-name">METAR</div>
                                            <div class="report-type-desc">Aviation Routine Weather Report</div>
                                        </div>
                                        <div class="report-type-card" onclick="selectReportType('TAF')" id="tafCard">
                                            <div class="report-type-icon">📡</div>
                                            <div class="report-type-name">TAF</div>
                                            <div class="report-type-desc">Terminal Aerodrome Forecast</div>
                                        </div>
                                    </div>
                                    <input type="hidden" id="reportType" name="reportType" value="METAR">
                                </div>
                                
                                <!-- Station Information -->
                                <div class="form-section">
                                    <div class="section-title">
                                        <span class="icon">📍</span>
                                        <span>Station Information</span>
                                    </div>
                                    <div class="input-group">
                                        <label class="input-label">ICAO Station Code</label>
                                        <input type="text" class="input-field" id="station" name="station" value="VOGA" 
                                               maxlength="4" required pattern="[A-Z]{4}" placeholder="Enter 4-letter ICAO code">
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
                                
                                <!-- Time Period -->
                                <div class="form-section">
                                    <div class="section-title">
                                        <span class="icon">📅</span>
                                        <span>Time Period</span>
                                    </div>
                                    <div class="year-month-group">
                                        <div class="input-group">
                                            <label class="input-label">Year</label>
                                            <input type="number" class="input-field" id="year" name="year" value="2025" min="2000" max="2026" required>
                                        </div>
                                        <div class="input-group">
                                            <label class="input-label">Download Mode</label>
                                            <div class="radio-group">
                                                <div class="radio-option">
                                                    <input type="radio" id="single" name="mode" value="single" checked class="radio-input">
                                                    <label for="single" class="radio-label">📁 Single Month</label>
                                                </div>
                                                <div class="radio-option">
                                                    <input type="radio" id="all" name="mode" value="all" class="radio-input">
                                                    <label for="all" class="radio-label">📦 All 12 Months</label>
                                                </div>
                                            </div>
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
                                
                                <!-- Action Buttons -->
                                <div class="action-buttons">
                                    <button type="button" class="btn btn-primary" onclick="startDownload()">
                                        <span>🚀</span>
                                        <span>Start Download</span>
                                    </button>
                                    <button type="button" class="btn btn-secondary" onclick="resetForm()">
                                        <span>↺</span>
                                        <span>Reset Form</span>
                                    </button>
                                </div>
                            </form>
                            
                            <!-- Status Bar -->
                            <div class="status-bar">
                                <p>📊 It may take a while...The site is busy pondering its existence.</p>
                                <p style="margin-top: 10px; font-size: 0.95rem;">
                                    <strong>Contact:</strong> AJAY YADAV (IMD GOA)<br>
                                    <strong>Email:</strong> ajaypahe02@gmail.com
                                </p>
                            </div>
                        </div>
                        
                        <!-- Right Column: Information -->
                        <div class="info-column">
                            <div class="info-panel">
                                <div class="info-title">
                                    <span>ℹ️</span>
                                    <span>Application Features</span>
                                </div>
                                <ul class="info-list">
                                    <li>Download METAR/TAF reports from OGIMET database</li>
                                    <li>Single month or all 12 months batch download</li>
                                    <li>Automatic data cleaning and formatting</li>
                                    <li>Original file naming: METARYYYYMM.txt / TAFYYYYMM.txt</li>
                                    <li>Batch processing with intelligent delays</li>
                                    <li>Quick station selection for Indian airports</li>
                                </ul>
                                
                                <div class="info-title" style="margin-top: 30px;">
                                    <span>⚡</span>
                                    <span>How to Use</span>
                                </div>
                                <div class="info-content">
                                    <p>1. Select report type (METAR or TAF)</p>
                                    <p>2. Enter ICAO station code or click quick station</p>
                                    <p>3. Choose year and download mode</p>
                                    <p>4. For single month, select specific month</p>
                                    <p>5. Click Start Download button</p>
                                    <p>6. Wait for processing and download file</p>
                                </div>
                                
                                <div class="info-title" style="margin-top: 30px;">
                                    <span>✅</span>
                                    <span>Recommended Stations</span>
                                </div>
                                <div class="info-content">
                                    <p><strong>VOGA (GOA)</strong> - Tested & verified</p>
                                    <p><strong>VOMM (Chennai)</strong> - Major international airport</p>
                                    <p><strong>VABB (Mumbai)</strong> - Busiest airport in India</p>
                                    <p><strong>VIDP (Delhi)</strong> - Capital city airport</p>
                                </div>
                                
                                <div class="info-title" style="margin-top: 30px;">
                                    <span>⏱️</span>
                                    <span>Processing Time</span>
                                </div>
                                <div class="info-content">
                                    <p><strong>Single Month:</strong> 10-30 seconds</p>
                                    <p><strong>All 12 Months:</strong> 1-2 minutes (batches of 3)</p>
                                    <p><strong>Note:</strong> OGIMET server may have delays</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Loading Overlay -->
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <h3 id="statusText">Downloading Data...</h3>
                <p id="loadingDetails">Please wait while we process your request</p>
            </div>
            
            <script>
                function selectReportType(type) {
                    document.getElementById('reportType').value = type;
                    
                    // Update UI
                    document.getElementById('metarCard').classList.remove('selected');
                    document.getElementById('tafCard').classList.remove('selected');
                    
                    if (type === 'METAR') {
                        document.getElementById('metarCard').classList.add('selected');
                    } else {
                        document.getElementById('tafCard').classList.add('selected');
                    }
                    
                    // Update station highlights
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                        if (card.querySelector('.station-code').textContent === 'VOGA') {
                            card.classList.add('highlight');
                        }
                    });
                }
                
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
                    const reportType = document.getElementById('reportType').value;
                    const station = document.getElementById('station').value.toUpperCase();
                    const year = document.getElementById('year').value;
                    const mode = document.querySelector('input[name="mode"]:checked').value;
                    const month = mode === 'single' ? document.getElementById('month').value : '00';
                    
                    if (station.length !== 4) {
                        alert('Please enter a valid 4-letter ICAO station code');
                        return;
                    }
                    
                    // Show loading
                    document.getElementById('loading').style.display = 'flex';
                    
                    // Update status
                    const statusText = document.getElementById('statusText');
                    const loadingDetails = document.getElementById('loadingDetails');
                    const monthNames = {
                        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                    };
                    
                    if (mode === 'all') {
                        statusText.textContent = `Downloading ALL months of ${reportType} for ${station} ${year}...`;
                        loadingDetails.textContent = 'Processing in batches of 3 months with delays...';
                    } else {
                        const monthName = monthNames[month] || month;
                        statusText.textContent = `Downloading ${reportType} ${station} ${monthName} ${year}...`;
                        loadingDetails.textContent = 'Connecting to OGIMET server...';
                    }
                    
                    // Redirect to download page
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
                    
                    // Update UI
                    selectReportType('METAR');
                    updateMonthVisibility();
                }
                
                // Initialize
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
        
        # Download data
        result = self.download_single_month(station, year, month, report_type)
        
        # Show result
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
        
        print(f"Batch {report_type} download: {station} {year} (all months)")
        
        # Start batch download
        results = self.download_all_months(station, year, report_type)
        
        # Show result
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = self.create_batch_result_page(results, station, year, report_type)
        self.wfile.write(html.encode('utf-8'))

    def download_single_month(self, station, year, month, report_type):
        """Download single month with original cleaning"""
        result = {
            'success': False,
            'filename': '',
            'reports': 0,
            'error': '',
            'raw_data': '',
            'clean_data': '',
            'report_type': report_type
        }
        
        try:
            print(f"Downloading {report_type} {station} {year}-{month}...")
            
            # Get data with original cleaning
            clean_data, raw_data = self.get_weather_data(station, year, month, report_type)
            
            if clean_data and len(clean_data.strip()) > 0:
                # Save file with CORRECT naming (original format)
                if report_type == 'METAR':
                    filename = f"METAR{year}{month}.txt"
                else:  # TAF
                    filename = f"TAF{year}{month}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(clean_data)
                
                # Count reports - count each TAF issuance
                if report_type == 'TAF':
                    # Count TAF lines (lines starting with TAF)
                    lines = clean_data.strip().split('\n')
                    report_count = len([l for l in lines if l.strip() and 'TAF' in l])
                else:
                    lines = clean_data.strip().split('\n')
                    report_count = len([l for l in lines if l.strip()])
                
                result['success'] = True
                result['filename'] = filename
                result['reports'] = report_count
                result['raw_data'] = raw_data
                result['clean_data'] = clean_data
                
                print(f"✅ Saved {report_count} {report_type} reports to {filename}")
            else:
                result['error'] = f"No {report_type} data found"
                print(f"❌ No {report_type} data found")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Exception: {e}")
        
        return result

    def download_all_months(self, station, year, report_type):
        """Download all 12 months in batches"""
        results = []
        file_prefix = 'METAR' if report_type == 'METAR' else 'TAF'
        folder_name = f"{file_prefix}_{station}_{year}"
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
            print(f"\n📦 {report_type} Batch {batch_idx + 1}/{len(batches)}")
            
            for month_num in batch:
                month = f"{month_num:02d}"
                month_name = month_names.get(month, f"Month {month}")
                
                if month == '02' and is_leap:
                    end_day = '29'
                else:
                    end_day = month_days.get(month, '31')
                
                print(f"  {month_name}...", end="", flush=True)
                
                try:
                    clean_data, _ = self.get_weather_data(station, year, month, report_type, end_day)
                    
                    if clean_data and len(clean_data.strip()) > 0:
                        # CORRECT file naming (original format)
                        filename = os.path.join(folder_name, f"{file_prefix}{year}{month}.txt")
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(clean_data)
                        
                        # Count reports
                        if report_type == 'TAF':
                            lines = clean_data.strip().split('\n')
                            report_count = len([l for l in lines if l.strip() and 'TAF' in l])
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
                        
                        print(f"✅ {report_count} reports")
                    else:
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': '',
                            'reports': 0,
                            'success': False,
                            'error': f'No {report_type} data'
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
                    print(f"❌ Error: {e}")
                
                time.sleep(1)  # Increased delay
            
            # Delay between batches
            if batch_idx < len(batches) - 1:
                print("  Waiting 3 seconds before next batch...")
                time.sleep(3)
        
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
        """Get METAR or TAF data with original cleaning"""
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
        
        try:
            # Get cookies
            session.get('https://www.ogimet.com/display_metars2.php?lang=en', 
                       headers=headers, timeout=10)
            time.sleep(0.5)
        except:
            pass
        
        # Set report type (METAR=SA, TAF=FC)
        tipo = 'FC' if report_type == 'TAF' else 'SA'
        
        # Form data
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
            
            raw_data = response.text
            
            # Debug: Save raw response
            with open(f"debug_{report_type}_{station}_{year}{month}.html", "w", encoding="utf-8") as f:
                f.write(raw_data)
            
            # Apply cleaning based on report type
            if report_type == 'TAF':
                clean_data = self.clean_taf_text_original(raw_data)
            else:
                clean_data = self.clean_metar_text_original(raw_data)
            
            # Debug: Save cleaned response
            with open(f"debug_clean_{report_type}_{station}_{year}{month}.txt", "w", encoding="utf-8") as f:
                f.write(clean_data)
            
            return clean_data, raw_data
            
        except Exception as e:
            print(f"  Request error: {e}")
            return "", f"Request error: {e}"

    def clean_metar_text_original(self, text):
        """ORIGINAL METAR cleaning - remove timestamps"""
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
                # Remove timestamps - KEY FEATURE!
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

    def clean_taf_text_original(self, text):
        """ORIGINAL TAF cleaning"""
        lines = text.split('\n')
        clean_tafs = []
        current_taf = []
        in_taf = False
        
        for line in lines:
            line = line.rstrip()  # Only remove trailing spaces
            
            if not line:
                continue
            
            # Skip HTML/comments
            if line.startswith(('<', '#', '<!--')):
                continue
            
            # Check if this is a TAF line (timestamp followed by TAF)
            if re.match(r'^\d{12}\s+(TAF|TAF\s+AMD|TAF\s+COR)', line):
                # Save previous TAF if exists
                if current_taf:
                    clean_taf = self.process_taf_lines(current_taf)
                    if clean_taf:
                        clean_tafs.append(clean_taf)
                    current_taf = []
                
                # Start new TAF - REMOVE leading timestamp
                clean_line = re.sub(r'^\d{12}\s+', '', line)
                current_taf.append(clean_line)
                in_taf = True
            
            # If we're in a TAF and line continues it
            elif in_taf and (line.startswith(' ') or line.startswith('\t') or 
                            line.startswith('BECMG') or line.startswith('TEMPO') or 
                            line.startswith('FM') or line.startswith('PROB')):
                # Check if this is a continuation of current TAF
                current_taf.append(line.strip())
            
            # If line doesn't continue TAF
            elif in_taf and not (line.startswith(' ') or line.startswith('\t')):
                # End current TAF
                if current_taf:
                    clean_taf = self.process_taf_lines(current_taf)
                    if clean_taf:
                        clean_tafs.append(clean_taf)
                    current_taf = []
                in_taf = False
        
        # Add last TAF if exists
        if current_taf:
            clean_taf = self.process_taf_lines(current_taf)
            if clean_taf:
                clean_tafs.append(clean_taf)
        
        # Sort by time (extract from TAF line)
        def get_taf_time(taf):
            first_line = taf.split('\n')[0]
            match = re.search(r'(\d{6})Z', first_line)
            return match.group(1) if match else '000000'
        
        clean_tafs.sort(key=get_taf_time)
        
        return '\n'.join(clean_tafs)

    def process_taf_lines(self, taf_lines):
        """Process and clean TAF lines"""
        if not taf_lines:
            return ""
        
        # Join lines with single space
        clean_taf = ' '.join(taf_lines)
        
        # Remove extra spaces
        clean_taf = re.sub(r'\s+', ' ', clean_taf)
        
        # Ensure proper format
        if 'TAF' in clean_taf and re.search(r'\d{6}Z', clean_taf):
            return clean_taf
        return ""

    def create_single_result_page(self, result, station, year, month, report_type):
        """Create result page for single month"""
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
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .container {{
                    display: flex;
                    width: 95%;
                    max-width: 1400px;
                    gap: 30px;
                }}
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .result-header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }}
                .result-icon {{
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                .success .result-icon {{
                    color: #10b981;
                }}
                .error .result-icon {{
                    color: #ef4444;
                }}
                .result-title {{
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                    color: #333;
                }}
                .content-wrapper {{
                    display: flex;
                    gap: 40px;
                }}
                .stats-column {{
                    flex: 1;
                    min-width: 500px;
                }}
                .preview-column {{
                    flex: 1;
                    min-width: 500px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin: 30px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.05);
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
                    font-size: 1rem;
                }}
                .file-preview {{
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 30px 0;
                }}
                .preview-content {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    height: 350px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    white-space: pre-wrap;
                }}
                .action-buttons {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 40px;
                }}
                .action-btn {{
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
                .quick-stations {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 30px 0;
                }}
                @media (max-width: 1024px) {{
                    .content-wrapper {{
                        flex-direction: column;
                    }}
                    .stats-column, .preview-column {{
                        min-width: 100%;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="result-card {'success' if result['success'] else 'error'}">
                    <div class="result-header">
                        <div class="result-icon">
                            {'✅' if result['success'] else '❌'}
                        </div>
                        <h1 class="result-title">
                            {'Download Successful!' if result['success'] else 'Download Failed'}
                        </h1>
                        <p>{report_type} Report | Station: {station} | Month: {month_name} {year}</p>
                    </div>
                    
                    <div class="content-wrapper">
        """
        
        if result['success']:
            html += f"""
                        <!-- Left Column: Stats -->
                        <div class="stats-column">
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <div class="stat-value">{result['reports']}</div>
                                    <div class="stat-label">{report_type} Reports</div>
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
                                    <div class="stat-value">{report_type}</div>
                                    <div class="stat-label">Report Type</div>
                                </div>
                            </div>
                            
                            <div class="note-box">
                                <strong>File Information:</strong><br>
                                ✓ File saved as: {result['filename']}<br>
                                ✓ Report type: {'TAF (tipo=FC)' if report_type == 'TAF' else 'METAR (tipo=SA)'}<br>
                                ✓ Original cleaning applied
                            </div>
                            
                            <div class="action-buttons">
                                <a href="/file/{result['filename']}" class="action-btn download-btn">
                                    📥 Download Clean {report_type} File
                                </a>
                                <a href="/" class="action-btn back-btn">
                                    ← Download Another
                                </a>
                            </div>
                        </div>
                        
                        <!-- Right Column: Preview -->
                        <div class="preview-column">
                            <h3 style="margin-bottom: 20px; color: #333;">📄 Cleaned {report_type} File Preview:</h3>
                            <div class="file-preview">
                                <div class="preview-content">
            """
            
            # Show cleaned content
            if result['clean_data']:
                lines = result['clean_data'].split('\n')
                for i, line in enumerate(lines[:25]):
                    html += f"{line}<br>"
                if len(lines) > 25:
                    html += f"<br>... and {len(lines) - 25} more lines"
            else:
                html += "Preview not available"
            
            html += f"""
                                </div>
                            </div>
                            <div style="margin-top: 20px; color: #666; font-size: 1rem;">
                                <strong>Note:</strong> File saved with original naming format: {report_type}YYYYMM.txt
                            </div>
                        </div>
            """
        else:
            html += f"""
                        <!-- Error View -->
                        <div style="flex: 1; text-align: center; padding: 30px;">
                            <div style="font-size: 1.2rem; color: #666; margin-bottom: 30px; background: #f8f9fa; padding: 25px; border-radius: 15px;">
                                <strong>Error:</strong> {result['error']}
                            </div>
                            
                            <div style="background: white; padding: 30px; border-radius: 15px; margin: 30px 0; border: 1px solid #e0e0e0;">
                                <h3 style="margin-bottom: 25px; color: #333;">Try These Stations:</h3>
                                <div class="quick-stations">
                                    <a href="/download?station=VOGA&year=2024&month=01&type={report_type_lower}" 
                                       style="background: #667eea; color: white; padding: 20px; border-radius: 12px; text-decoration: none; text-align: center; display: block;">
                                        <div style="font-size: 1.5rem; font-weight: bold;">VOGA</div>
                                        <div style="font-size: 1rem;">GOA (Priority)</div>
                                    </a>
                                    <a href="/download?station=VOMM&year=2024&month=01&type={report_type_lower}" 
                                       style="background: #f8f9fa; color: #333; padding: 20px; border-radius: 12px; text-decoration: none; text-align: center; display: block; border: 2px solid #e0e0e0;">
                                        <div style="font-size: 1.5rem; font-weight: bold;">VOMM</div>
                                        <div style="font-size: 1rem;">Chennai</div>
                                    </a>
                                    <a href="/download?station=VABB&year=2024&month=01&type={report_type_lower}" 
                                       style="background: #f8f9fa; color: #333; padding: 20px; border-radius: 12px; text-decoration: none; text-align: center; display: block; border: 2px solid #e0e0e0;">
                                        <div style="font-size: 1.5rem; font-weight: bold;">VABB</div>
                                        <div style="font-size: 1rem;">Mumbai</div>
                                    </a>
                                    <a href="/download?station=VIDP&year=2024&month=01&type={report_type_lower}" 
                                       style="background: #f8f9fa; color: #333; padding: 20px; border-radius: 12px; text-decoration: none; text-align: center; display: block; border: 2px solid #e0e0e0;">
                                        <div style="font-size: 1.5rem; font-weight: bold;">VIDP</div>
                                        <div style="font-size: 1rem;">Delhi</div>
                                    </a>
                                </div>
                            </div>
                            
                            <a href="/" class="action-btn back-btn" style="max-width: 350px; margin: 0 auto;">
                                ← Try Again
                            </a>
                        </div>
            """
        
        html += """
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def create_batch_result_page(self, results, station, year, report_type):
        """Create result page for batch download"""
        report_type_lower = report_type.lower()
        
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
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .container {{
                    display: flex;
                    width: 95%;
                    max-width: 1400px;
                    gap: 30px;
                }}
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }}
                .header h1 {{
                    font-size: 2.5rem;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .content-wrapper {{
                    display: flex;
                    gap: 40px;
                }}
                .summary-column {{
                    flex: 1;
                    min-width: 500px;
                }}
                .months-column {{
                    flex: 1;
                    min-width: 500px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin: 30px 0;
                }}
                .summary-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.05);
                    border: 1px solid #e0e0e0;
                }}
                .summary-value {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .success-value {{
                    color: #10b981;
                }}
                .total-value {{
                    color: #667eea;
                }}
                .month-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    margin: 30px 0;
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
                    font-size: 1.1rem;
                }}
                .month-reports {{
                    font-size: 1.8rem;
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                .action-buttons {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 40px;
                }}
                .action-btn {{
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
                @media (max-width: 1024px) {{
                    .content-wrapper {{
                        flex-direction: column;
                    }}
                    .summary-column, .months-column {{
                        min-width: 100%;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="result-card">
                    <div class="header">
                        <h1>📦 {report_type} Batch Download Complete</h1>
                        <p>{station} - {year} (All 12 Months)</p>
                    </div>
                    
                    <div class="content-wrapper">
                        <!-- Left Column: Summary -->
                        <div class="summary-column">
                            <div class="summary-grid">
                                <div class="summary-card">
                                    <div class="summary-value success-value">{results['total_success']}/12</div>
                                    <div class="summary-label">Successful Months</div>
                                </div>
                                <div class="summary-card">
                                    <div class="summary-value total-value">{results['total_reports']:,}</div>
                                    <div class="summary-label">Total {report_type} Reports</div>
                                </div>
                                <div class="summary-card">
                                    <div class="summary-value">{station}</div>
                                    <div class="summary-label">Station</div>
                                </div>
                                <div class="summary-card">
                                    <div class="summary-value">{report_type}</div>
                                    <div class="summary-label">Report Type</div>
                                </div>
                            </div>
                            
                            <div class="note-box">
                                <strong>Processing Details:</strong><br>
                                ✓ Files saved with original naming: {report_type}YYYYMM.txt<br>
                                ✓ Downloaded in batches of 3 months with delays.<br>
                                ✓ Report type: {'TAF (tipo=FC)' if report_type == 'TAF' else 'METAR (tipo=SA)'}<br>
                                ✓ Folder: {results['folder']}.zip
                            </div>
                            
                            <div class="action-buttons">
                                <a href="/file/{results['folder']}" class="action-btn download-btn">
                                    📥 Download All {report_type} Files (Folder)
                                </a>
                                <a href="/" class="action-btn back-btn">
                                    ← New Download
                                </a>
                            </div>
                        </div>
                        
                        <!-- Right Column: Months -->
                        <div class="months-column">
                            <h3 style="margin-bottom: 20px; color: #333;">Monthly Results:</h3>
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
                            <div style="margin-top: 30px; color: #666; font-size: 1rem;">
                                <strong>Folder Structure:</strong><br>
                                {results['folder']}/<br>
                                ├── {report_type}{year}01.txt<br>
                                ├── {report_type}{year}02.txt<br>
                                ├── {report_type}{year}03.txt<br>
                                ├── ... (all 12 months)<br>
                                └── Download as ZIP archive
                            </div>
                        </div>
                    </div>
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
try:
    with socketserver.TCPServer(("", PORT), MetarHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print(f"Error: {e}")
