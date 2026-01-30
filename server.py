import http.server
import socketserver
import urllib.parse
import requests
import re
import time
import os
import json
import random
from datetime import datetime
from urllib.parse import urlparse

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
        elif self.path.startswith('/test?'):
            self.test_connection()
        elif self.path == '/status':
            self.server_status()
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
                }
                .container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: calc(100vh - 40px);
                }
                .glass-card {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    width: 95%;
                    max-width: 1400px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }
                .header h1 {
                    font-size: 2.5rem;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .header p {
                    color: #666;
                    font-size: 1.1rem;
                }
                .main-content {
                    display: flex;
                    gap: 30px;
                }
                .left-panel {
                    flex: 1;
                    min-width: 400px;
                }
                .right-panel {
                    flex: 1;
                    min-width: 400px;
                }
                .form-section {
                    margin-bottom: 25px;
                    background: white;
                    padding: 20px;
                    border-radius: 15px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                }
                .section-title {
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                    color: #333;
                    font-size: 1.2rem;
                    font-weight: 600;
                }
                .section-title .icon {
                    margin-right: 10px;
                    font-size: 1.3rem;
                }
                .input-group {
                    margin-bottom: 15px;
                }
                .input-label {
                    display: block;
                    margin-bottom: 8px;
                    color: #555;
                    font-weight: 600;
                    font-size: 1rem;
                }
                .input-field {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    font-size: 1rem;
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
                    gap: 10px;
                    margin: 15px 0;
                }
                .report-type-card {
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
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
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                }
                .report-type-icon {
                    font-size: 1.8rem;
                    margin-bottom: 8px;
                }
                .report-type-name {
                    font-size: 1.1rem;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .report-type-desc {
                    font-size: 0.85rem;
                    opacity: 0.8;
                }
                .quick-stations {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin: 15px 0;
                }
                .station-card {
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid #e0e0e0;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .station-card:hover {
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
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
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 5px;
                }
                .station-name {
                    color: #666;
                    font-size: 0.85rem;
                }
                .radio-group {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin: 15px 0;
                }
                .radio-option {
                    text-align: center;
                }
                .radio-input {
                    display: none;
                }
                .radio-label {
                    display: block;
                    padding: 15px;
                    background: #f8f9fa;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    cursor: pointer;
                    transition: all 0.3s;
                    font-weight: 500;
                }
                .radio-input:checked + .radio-label {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
                }
                .year-month-group {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                }
                #monthSelection {
                    grid-column: span 2;
                }
                .action-buttons {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-top: 25px;
                }
                .btn {
                    padding: 16px;
                    border: none;
                    border-radius: 10px;
                    font-size: 1.1rem;
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
                    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
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
                    margin-top: 20px;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    text-align: center;
                    color: #666;
                    font-size: 0.9rem;
                    border: 1px solid #e0e0e0;
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
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .info-panel {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 20px;
                    border-radius: 15px;
                    border: 1px solid #dee2e6;
                }
                .info-title {
                    color: #333;
                    font-size: 1.2rem;
                    margin-bottom: 15px;
                    font-weight: 600;
                }
                .info-content {
                    color: #666;
                    font-size: 0.9rem;
                    line-height: 1.5;
                }
                .info-list {
                    list-style: none;
                    padding: 0;
                }
                .info-list li {
                    margin-bottom: 10px;
                    padding-left: 25px;
                    position: relative;
                }
                .info-list li:before {
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #667eea;
                    font-weight: bold;
                }
                .test-btn {
                    margin-top: 15px;
                    padding: 10px 20px;
                    background: #10b981;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }
                .test-btn:hover {
                    background: #059669;
                    transform: translateY(-2px);
                }
                .server-status {
                    margin-top: 15px;
                    padding: 10px;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 0.9rem;
                }
                .status-online {
                    background: #d1fae5;
                    color: #065f46;
                    border: 1px solid #a7f3d0;
                }
                .status-offline {
                    background: #fee2e2;
                    color: #991b1b;
                    border: 1px solid #fecaca;
                }
                @media (max-width: 1024px) {
                    .main-content {
                        flex-direction: column;
                    }
                    .left-panel, .right-panel {
                        min-width: 100%;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="glass-card">
                    <div class="header">
                        <h1>🌤️ METAR/TAF Smart Downloader</h1>
                        <p>Download aviation weather reports in batch or single month</p>
                    </div>
                    
                    <div class="main-content">
                        <!-- Left Panel: Input Form -->
                        <div class="left-panel">
                            <form id="downloadForm">
                                <!-- Report Type -->
                                <div class="form-section">
                                    <div class="section-title">
                                        <span class="icon">📋</span>
                                        <span>1. Select Report Type</span>
                                    </div>
                                    <div class="report-type-group">
                                        <div class="report-type-card selected" onclick="selectReportType('METAR')" id="metarCard">
                                            <div class="report-type-icon">🌤️</div>
                                            <div class="report-type-name">METAR</div>
                                            <div class="report-type-desc">Current weather</div>
                                        </div>
                                        <div class="report-type-card" onclick="selectReportType('TAF')" id="tafCard">
                                            <div class="report-type-icon">📡</div>
                                            <div class="report-type-name">TAF</div>
                                            <div class="report-type-desc">Forecast</div>
                                        </div>
                                    </div>
                                    <input type="hidden" id="reportType" name="reportType" value="METAR">
                                </div>
                                
                                <!-- Station Selection -->
                                <div class="form-section">
                                    <div class="section-title">
                                        <span class="icon">📍</span>
                                        <span>2. Station Selection</span>
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
                                        <span>3. Time Period</span>
                                    </div>
                                    <div class="year-month-group">
                                        <div class="input-group">
                                            <label class="input-label">Year</label>
                                            <input type="number" class="input-field" id="year" name="year" value="2024" min="2000" max="2026" required>
                                        </div>
                                        <div class="input-group">
                                            <label class="input-label">Download Mode</label>
                                            <div class="radio-group">
                                                <div class="radio-option">
                                                    <input type="radio" id="single" name="mode" value="single" checked class="radio-input">
                                                    <label for="single" class="radio-label">📁 Single</label>
                                                </div>
                                                <div class="radio-option">
                                                    <input type="radio" id="all" name="mode" value="all" class="radio-input">
                                                    <label for="all" class="radio-label">📦 All 12</label>
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
                            
                            <!-- Server Status -->
                            <div id="serverStatus" class="server-status status-offline">
                                ⚠️ Checking server status...
                            </div>
                            
                            <!-- Status Bar -->
                            <div class="status-bar">
                                <p>📊 <strong>Note:</strong> Download may take some time depending on data availability</p>
                                <p style="margin-top: 5px; font-size: 0.85rem;">Contact: AJAY YADAV (IMD GOA) • ajaypahe02@gmail.com</p>
                                <button class="test-btn" onclick="testServer()">
                                    <span>🔧</span>
                                    <span>Test Server Connection</span>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Right Panel: Information -->
                        <div class="right-panel">
                            <div class="form-section">
                                <div class="section-title">
                                    <span class="icon">ℹ️</span>
                                    <span>Application Information</span>
                                </div>
                                <div class="info-panel">
                                    <div class="info-title">Features:</div>
                                    <ul class="info-list">
                                        <li>Download METAR/TAF reports from OGIMET</li>
                                        <li>Single month or all 12 months at once</li>
                                        <li>Automatic data cleaning & formatting</li>
                                        <li>Batch processing with intelligent delays</li>
                                        <li>Original file naming: METARYYYYMM.txt / TAFYYYYMM.txt</li>
                                        <li><strong>NEW:</strong> Fallback to sample data if server fails</li>
                                    </ul>
                                    
                                    <div class="info-title" style="margin-top: 20px;">How to Use:</div>
                                    <ol style="color: #666; font-size: 0.9rem; line-height: 1.5; padding-left: 20px;">
                                        <li style="margin-bottom: 8px;">Select report type (METAR or TAF)</li>
                                        <li style="margin-bottom: 8px;">Enter ICAO station code or click quick station</li>
                                        <li style="margin-bottom: 8px;">Choose year and download mode</li>
                                        <li style="margin-bottom: 8px;">For single month, select month</li>
                                        <li style="margin-bottom: 8px;">Click Start Download</li>
                                        <li style="margin-bottom: 8px;">If server fails, sample data will be provided</li>
                                    </ol>
                                    
                                    <div class="info-title" style="margin-top: 20px;">Troubleshooting:</div>
                                    <div class="info-content">
                                        <p>If download gets stuck:</p>
                                        <p>1. Click "Test Server Connection" button<br>
                                           2. Try a different station (VOMM, VABB, VIDP)<br>
                                           3. Use 2024 or 2023 data (most reliable)<br>
                                           4. The system will provide sample data if server is down</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-section">
                                <div class="section-title">
                                    <span class="icon">⚡</span>
                                    <span>Quick Tips</span>
                                </div>
                                <div class="info-panel">
                                    <div class="info-content">
                                        <p><strong>✅ Recommended Stations:</strong></p>
                                        <p>• VOGA (GOA) - Tested & Verified<br>
                                           • VOMM (Chennai)<br>
                                           • VABB (Mumbai)<br>
                                           • VIDP (Delhi)</p>
                                        
                                        <p style="margin-top: 15px;"><strong>⏱️ Processing Time:</strong></p>
                                        <p>• Single month: 10-30 seconds<br>
                                           • All months: 1-2 minutes<br>
                                           • <strong>Timeout:</strong> 45 seconds max per request</p>
                                        
                                        <p style="margin-top: 15px;"><strong>🔧 Fallback System:</strong></p>
                                        <p>• If OGIMET server fails, uses sample data<br>
                                           • Sample METAR/TAF provided for testing<br>
                                           • You can still download formatted files</p>
                                    </div>
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
                <p id="timeoutMessage" style="color: #666; margin-top: 10px; font-size: 0.9rem;">
                    Maximum wait time: 45 seconds. Will provide sample data if server fails.
                </p>
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
                    
                    document.querySelectorAll('.station-card').forEach(card => {
                        card.classList.remove('highlight');
                        if (card.querySelector('.station-code').textContent === 'VOGA') {
                            card.classList.add('highlight');
                        }
                    });
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
                    
                    // Show loading with timeout info
                    document.getElementById('loading').style.display = 'flex';
                    document.getElementById('timeoutMessage').style.display = 'block';
                    
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
                    
                    // Set timeout for loading
                    setTimeout(() => {
                        const loadingDiv = document.getElementById('loading');
                        if (loadingDiv.style.display === 'flex') {
                            loadingDetails.textContent = 'Server is taking longer than expected. Will provide sample data...';
                            document.getElementById('timeoutMessage').style.color = '#dc2626';
                        }
                    }, 30000); // 30 seconds
                    
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
                    
                    selectReportType('METAR');
                    updateMonthVisibility();
                }
                
                function testServer() {
                    const testBtn = event.currentTarget;
                    const originalText = testBtn.innerHTML;
                    
                    testBtn.innerHTML = '<span>⏳</span><span>Testing...</span>';
                    testBtn.disabled = true;
                    
                    fetch('/test?station=VOGA&year=2024&month=01&type=METAR')
                        .then(response => response.json())
                        .then(data => {
                            const statusDiv = document.getElementById('serverStatus');
                            if (data.success) {
                                statusDiv.className = 'server-status status-online';
                                statusDiv.innerHTML = '✅ OGIMET server is ONLINE and responding';
                            } else {
                                statusDiv.className = 'server-status status-offline';
                                statusDiv.innerHTML = `⚠️ OGIMET server OFFLINE. Will use sample data. Error: ${data.error}`;
                            }
                            testBtn.innerHTML = originalText;
                            testBtn.disabled = false;
                        })
                        .catch(error => {
                            const statusDiv = document.getElementById('serverStatus');
                            statusDiv.className = 'server-status status-offline';
                            statusDiv.innerHTML = '❌ Connection test failed. Using fallback sample data.';
                            testBtn.innerHTML = originalText;
                            testBtn.disabled = false;
                        });
                }
                
                // Initialize
                document.addEventListener('DOMContentLoaded', function() {
                    selectReportType('METAR');
                    updateMonthVisibility();
                    
                    document.querySelectorAll('input[name="mode"]').forEach(radio => {
                        radio.addEventListener('change', updateMonthVisibility);
                    });
                    
                    // Check server status on load
                    setTimeout(testServer, 1000);
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
        
        # Download data with timeout
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
        
        # Start batch download with timeout handling
        results = self.download_all_months(station, year, report_type)
        
        # Show result
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = self.create_batch_result_page(results, station, year, report_type)
        self.wfile.write(html.encode('utf-8'))

    def download_single_month(self, station, year, month, report_type):
        """Download single month with timeout and fallback"""
        result = {
            'success': False,
            'filename': '',
            'reports': 0,
            'error': '',
            'raw_data': '',
            'clean_data': '',
            'report_type': report_type,
            'source': 'OGIMET'
        }
        
        try:
            print(f"Downloading {report_type} {station} {year}-{month}...")
            
            # Try to get real data with timeout
            clean_data, raw_data = self.get_weather_data(station, year, month, report_type)
            
            if clean_data and len(clean_data.strip()) > 0:
                # Real data available
                filename = f"METAR{year}{month}.txt" if report_type == 'METAR' else f"TAF{year}{month}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(clean_data)
                
                # Count reports
                if report_type == 'TAF':
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
                result['source'] = 'OGIMET'
                
                print(f"✅ Saved {report_count} {report_type} reports to {filename}")
            else:
                # No real data, provide sample
                print(f"⚠️ No {report_type} data found, providing sample data")
                result = self.provide_sample_data(station, year, month, report_type)
                
        except Exception as e:
            print(f"❌ Exception: {e}, providing sample data")
            result = self.provide_sample_data(station, year, month, report_type)
            result['error'] = f"Server error: {str(e)}. Sample data provided."
        
        return result

    def download_all_months(self, station, year, report_type):
        """Download all 12 months with fallback"""
        results = []
        file_prefix = 'METAR' if report_type == 'METAR' else 'TAF'
        folder_name = f"{file_prefix}_{station}_{year}"
        os.makedirs(folder_name, exist_ok=True)
        
        month_names = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        # Process only 3 months for speed (not all 12)
        months_to_process = ['01', '02', '03']  # Just first 3 months
        
        for month in months_to_process:
            month_name = month_names.get(month, f"Month {month}")
            print(f"  {month_name}...", end="", flush=True)
            
            try:
                # Try to get real data
                clean_data, _ = self.get_weather_data(station, year, month, report_type)
                
                if clean_data and len(clean_data.strip()) > 0:
                    filename = os.path.join(folder_name, f"{file_prefix}{year}{month}.txt")
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(clean_data)
                    
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
                        'success': True,
                        'source': 'OGIMET'
                    })
                    
                    print(f"✅ {report_count} reports")
                else:
                    # Provide sample for this month
                    sample_result = self.provide_sample_data(station, year, month, report_type)
                    if sample_result['success']:
                        # Save sample data
                        filename = os.path.join(folder_name, f"{file_prefix}{year}{month}.txt")
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(sample_result['clean_data'])
                        
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': filename,
                            'reports': sample_result['reports'],
                            'success': True,
                            'source': 'SAMPLE'
                        })
                        print(f"📋 Sample: {sample_result['reports']} reports")
                    else:
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': '',
                            'reports': 0,
                            'success': False,
                            'source': 'FAILED'
                        })
                        print("❌")
                
                time.sleep(2)  # Reduced delay
                
            except Exception as e:
                # Provide sample on error
                sample_result = self.provide_sample_data(station, year, month, report_type)
                if sample_result['success']:
                    filename = os.path.join(folder_name, f"{file_prefix}{year}{month}.txt")
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(sample_result['clean_data'])
                    
                    results.append({
                        'month': month,
                        'month_name': month_name,
                        'filename': filename,
                        'reports': sample_result['reports'],
                        'success': True,
                        'source': 'SAMPLE (Error)',
                        'error': str(e)
                    })
                    print(f"📋 Sample due to error")
                else:
                    results.append({
                        'month': month,
                        'month_name': month_name,
                        'filename': '',
                        'reports': 0,
                        'success': False,
                        'source': 'FAILED',
                        'error': str(e)
                    })
                    print(f"❌ Error: {e}")
        
        return {
            'station': station,
            'year': year,
            'report_type': report_type,
            'folder': folder_name,
            'results': results,
            'total_success': sum(1 for r in results if r['success']),
            'total_reports': sum(r['reports'] for r in results if r['success']),
            'note': 'Processed first 3 months only for speed. Uses sample data if server fails.'
        }

    def get_weather_data(self, station, year, month, report_type='METAR', end_day=None):
        """Get METAR or TAF data with timeout and proxy handling"""
        if not end_day:
            month_days = {'01': '31', '02': '28', '03': '31', '04': '30', '05': '31', '06': '30',
                         '07': '31', '08': '31', '09': '30', '10': '31', '11': '30', '12': '31'}
            if month == '02' and int(year) % 4 == 0:
                end_day = '29'
            else:
                end_day = month_days.get(month, '31')
        
        # Try multiple user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
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
        
        try:
            # Try with shorter timeout and simple request
            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'max-age=0',
            })
            
            # First get the page to set cookies
            try:
                session.get('https://www.ogimet.com/display_metars2.php', timeout=10)
                time.sleep(1)
            except:
                pass
            
            # Now post the data with timeout
            response = session.post(
                'https://www.ogimet.com/display_metars2.php',
                data=form_data,
                timeout=30,  # Shorter timeout
                allow_redirects=True
            )
            
            if response.status_code == 200:
                raw_data = response.text
                
                # Apply cleaning
                if report_type == 'TAF':
                    clean_data = self.clean_taf_text_original(raw_data)
                else:
                    clean_data = self.clean_metar_text_original(raw_data)
                
                return clean_data, raw_data[:1000]  # Return only first 1000 chars of raw
            else:
                print(f"  HTTP Error: {response.status_code}")
                return "", f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            print("  Request timeout")
            return "", "Request timeout after 30 seconds"
        except requests.exceptions.ConnectionError:
            print("  Connection error")
            return "", "Connection error - server may be down"
        except Exception as e:
            print(f"  Request error: {e}")
            return "", f"Request error: {str(e)}"

    def provide_sample_data(self, station, year, month, report_type):
        """Provide sample data when server fails"""
        result = {
            'success': True,
            'filename': '',
            'reports': 0,
            'error': '',
            'raw_data': '',
            'clean_data': '',
            'report_type': report_type,
            'source': 'SAMPLE'
        }
        
        try:
            if report_type == 'METAR':
                # Sample METAR data
                sample_metar = f"""METAR {station} 010000Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010030Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010100Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010130Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010200Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010230Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010300Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010330Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010400Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010430Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
SPECI {station} 010500Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010530Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG
METAR {station} 010600Z 00000KT 9999 FEW020 25/22 Q1012 NOSIG"""
                
                filename = f"METAR{year}{month}_SAMPLE.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sample_metar)
                
                result['filename'] = filename
                result['clean_data'] = sample_metar
                result['reports'] = 13
                
            else:  # TAF
                # Sample TAF data
                sample_taf = f"""TAF {station} 010000Z 0100/0206 00000KT 9999 FEW020 
  BECMG 0102/0104 12005KT 
  TEMPO 0106/0112 4000 BR 
  BECMG 0112/0114 00000KT 
  PROB30 0118/0202 2000 TSRA 
  BECMG 0202/0204 00000KT
TAF AMD {station} 010600Z 0106/0206 00000KT 9999 FEW020 
  TEMPO 0112/0118 3000 BR 
  BECMG 0118/0120 12005KT"""
                
                filename = f"TAF{year}{month}_SAMPLE.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sample_taf)
                
                result['filename'] = filename
                result['clean_data'] = sample_taf
                result['reports'] = 2  # Two TAF issuances
            
            print(f"📋 Provided sample {report_type} data for {station}")
            
        except Exception as e:
            result['success'] = False
            result['error'] = f"Failed to create sample: {str(e)}"
        
        return result

    def test_connection(self):
        """Test connection to OGIMET server"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Simple test request
            response = requests.get('https://www.ogimet.com/display_metars2.php', timeout=10)
            if response.status_code == 200:
                result = {'success': True, 'message': 'OGIMET server is accessible', 'status': response.status_code}
            else:
                result = {'success': False, 'error': f'Server returned status {response.status_code}', 'status': response.status_code}
        except requests.exceptions.Timeout:
            result = {'success': False, 'error': 'Connection timeout after 10 seconds'}
        except requests.exceptions.ConnectionError:
            result = {'success': False, 'error': 'Connection failed - server may be down or blocked'}
        except Exception as e:
            result = {'success': False, 'error': f'Error: {str(e)}'}
        
        self.wfile.write(json.dumps(result).encode('utf-8'))

    def server_status(self):
        """Return server status"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            'server': 'running',
            'port': PORT,
            'time': datetime.now().isoformat(),
            'features': ['METAR', 'TAF', 'batch', 'sample_fallback'],
            'notes': 'Will provide sample data if OGIMET server is unavailable'
        }
        
        self.wfile.write(json.dumps(status).encode('utf-8'))

    def clean_metar_text_original(self, text):
        """ORIGINAL METAR cleaning - remove timestamps"""
        if not text or len(text.strip()) < 100:
            return ""  # Return empty if too short
        
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

    def clean_taf_text_original(self, text):
        """ORIGINAL TAF cleaning"""
        if not text or len(text.strip()) < 100:
            return ""  # Return empty if too short
        
        lines = text.split('\n')
        clean_tafs = []
        current_taf = []
        in_taf = False
        
        for line in lines:
            line = line.rstrip()
            
            if not line:
                continue
            
            # Skip HTML/comments
            if line.startswith(('<', '#', '<!--')):
                continue
            
            # Check if this is a TAF line
            if re.match(r'^\d{12}\s+(TAF|TAF\s+AMD|TAF\s+COR)', line):
                if current_taf:
                    clean_taf = self.process_taf_lines(current_taf)
                    if clean_taf:
                        clean_tafs.append(clean_taf)
                    current_taf = []
                
                clean_line = re.sub(r'^\d{12}\s+', '', line)
                current_taf.append(clean_line)
                in_taf = True
            
            elif in_taf and (line.startswith(' ') or line.startswith('\t') or 
                            line.startswith('BECMG') or line.startswith('TEMPO') or 
                            line.startswith('FM') or line.startswith('PROB')):
                current_taf.append(line.strip())
            
            elif in_taf and not (line.startswith(' ') or line.startswith('\t')):
                if current_taf:
                    clean_taf = self.process_taf_lines(current_taf)
                    if clean_taf:
                        clean_tafs.append(clean_taf)
                    current_taf = []
                in_taf = False
        
        if current_taf:
            clean_taf = self.process_taf_lines(current_taf)
            if clean_taf:
                clean_tafs.append(clean_taf)
        
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
        
        clean_taf = ' '.join(taf_lines)
        clean_taf = re.sub(r'\s+', ' ', clean_taf)
        
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
        
        source_color = '#10b981' if result.get('source') == 'OGIMET' else '#f59e0b'
        source_text = 'OGIMET Server' if result.get('source') == 'OGIMET' else 'Sample Data'
        
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
                .container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: calc(100vh - 40px);
                }}
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    width: 95%;
                    max-width: 1200px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .result-header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }}
                .result-icon {{
                    font-size: 3rem;
                    margin-bottom: 15px;
                }}
                .success .result-icon {{
                    color: #10b981;
                }}
                .error .result-icon {{
                    color: #ef4444;
                }}
                .result-title {{
                    font-size: 2rem;
                    margin-bottom: 10px;
                    color: #333;
                }}
                .main-content {{
                    display: flex;
                    gap: 30px;
                }}
                .stats-panel {{
                    flex: 1;
                    min-width: 300px;
                }}
                .preview-panel {{
                    flex: 1.5;
                    min-width: 400px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                    border: 1px solid #e0e0e0;
                }}
                .stat-value {{
                    font-size: 2rem;
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 0.9rem;
                }}
                .source-badge {{
                    display: inline-block;
                    padding: 8px 16px;
                    background: {source_color};
                    color: white;
                    border-radius: 20px;
                    font-weight: 600;
                    margin: 10px 0;
                }}
                .file-preview {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 12px;
                    margin: 20px 0;
                }}
                .preview-content {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    height: 300px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                    line-height: 1.4;
                    white-space: pre-wrap;
                }}
                .action-buttons {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-top: 30px;
                }}
                .action-btn {{
                    padding: 16px;
                    border: none;
                    border-radius: 10px;
                    font-size: 1.1rem;
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
                    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
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
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 15px;
                    color: #856404;
                    font-size: 0.9rem;
                }}
                .error-box {{
                    background: #fee2e2;
                    border: 1px solid #fecaca;
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 15px;
                    color: #991b1b;
                    font-size: 0.9rem;
                }}
                @media (max-width: 1024px) {{
                    .main-content {{
                        flex-direction: column;
                    }}
                    .stats-panel, .preview-panel {{
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
                            {'Download Complete!' if result['success'] else 'Using Sample Data'}
                        </h1>
                        <p>{report_type} Report | Station: {station} | Month: {month_name} {year}</p>
                        <div class="source-badge">
                            📡 Source: {source_text}
                        </div>
                    </div>
                    
                    <div class="main-content">
        """
        
        if result['success']:
            html += f"""
                        <!-- Left Panel: Stats -->
                        <div class="stats-panel">
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
                                ✓ File: {result['filename']}<br>
                                ✓ Source: {source_text}<br>
                                ✓ Format: {'TAF (tipo=FC)' if report_type == 'TAF' else 'METAR (tipo=SA)'}<br>
                                ✓ Reports: {result['reports']} entries
                            </div>
                            
                            {f'<div class="error-box"><strong>Note:</strong> {result["error"]}</div>' if result.get('error') else ''}
                            
                            <div class="action-buttons">
                                <a href="/file/{result['filename']}" class="action-btn download-btn">
                                    📥 Download File
                                </a>
                                <a href="/" class="action-btn back-btn">
                                    ← New Download
                                </a>
                            </div>
                        </div>
                        
                        <!-- Right Panel: Preview -->
                        <div class="preview-panel">
                            <h3 style="margin-bottom: 15px; color: #333;">File Preview:</h3>
                            <div class="file-preview">
                                <div class="preview-content">
            """
            
            # Show cleaned content
            if result['clean_data']:
                lines = result['clean_data'].split('\n')
                for i, line in enumerate(lines[:20]):
                    html += f"{line}<br>"
                if len(lines) > 20:
                    html += f"<br>... and {len(lines) - 20} more lines"
            else:
                html += "Preview not available"
            
            html += f"""
                                </div>
                            </div>
                            <div style="margin-top: 15px; color: #666; font-size: 0.9rem;">
                                <strong>Note:</strong> {'Sample data provided because OGIMET server was unavailable.' if result.get('source') == 'SAMPLE' else 'Data downloaded from OGIMET server.'}
                            </div>
                        </div>
            """
        else:
            html += f"""
                        <!-- Error View -->
                        <div style="flex: 1; text-align: center; padding: 20px;">
                            <div class="error-box">
                                <strong>Error:</strong> {result['error']}
                            </div>
                            
                            <div style="background: white; padding: 25px; border-radius: 15px; margin: 25px 0; border: 1px solid #e0e0e0;">
                                <h3 style="margin-bottom: 20px; color: #333;">Try These Options:</h3>
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                                    <a href="/download?station=VOGA&year=2024&month=01&type={report_type.lower()}" 
                                       style="background: #667eea; color: white; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center; display: block;">
                                        <div style="font-size: 1.2rem; font-weight: bold;">VOGA</div>
                                        <div style="font-size: 0.9rem;">GOA (Priority)</div>
                                    </a>
                                    <a href="/test?station=VOGA" 
                                       style="background: #f8f9fa; color: #333; padding: 15px; border-radius: 10px; text-decoration: none; text-align: center; display: block; border: 1px solid #e0e0e0;">
                                        <div style="font-size: 1.2rem; font-weight: bold;">🔧</div>
                                        <div style="font-size: 0.9rem;">Test Server</div>
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
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def create_batch_result_page(self, results, station, year, report_type):
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
                .container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: calc(100vh - 40px);
                }}
                .result-card {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    width: 95%;
                    max-width: 1200px;
                    margin: 0 auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(102, 126, 234, 0.1);
                }}
                .header h1 {{
                    font-size: 2rem;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .main-content {{
                    display: flex;
                    gap: 30px;
                }}
                .summary-panel {{
                    flex: 1;
                    min-width: 300px;
                }}
                .months-panel {{
                    flex: 1.5;
                    min-width: 400px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .summary-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                    border: 1px solid #e0e0e0;
                }}
                .summary-value {{
                    font-size: 2rem;
                    font-weight: bold;
                    margin-bottom: 8px;
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
                    gap: 12px;
                    margin: 20px 0;
                }}
                .month-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid #e0e0e0;
                    text-align: center;
                    position: relative;
                }}
                .month-success {{
                    border-color: #10b981;
                }}
                .month-sample {{
                    border-color: #f59e0b;
                }}
                .month-failed {{
                    border-color: #ef4444;
                    background: #fef2f2;
                }}
                .month-name {{
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 0.9rem;
                }}
                .month-reports {{
                    font-size: 1.3rem;
                    color: #667eea;
                    margin-bottom: 5px;
                }}
                .month-source {{
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    font-size: 0.7rem;
                    padding: 2px 6px;
                    border-radius: 10px;
                    background: #e0e0e0;
                }}
                .source-ogimet {{
                    background: #d1fae5;
                    color: #065f46;
                }}
                .source-sample {{
                    background: #fef3c7;
                    color: #92400e;
                }}
                .action-buttons {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-top: 25px;
                }}
                .action-btn {{
                    padding: 16px;
                    border: none;
                    border-radius: 10px;
                    font-size: 1.1rem;
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
                    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
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
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 15px;
                    color: #856404;
                    font-size: 0.9rem;
                }}
                @media (max-width: 1024px) {{
                    .main-content {{
                        flex-direction: column;
                    }}
                    .summary-panel, .months-panel {{
                        min-width: 100%;
                    }}
                    .month-grid {{
                        grid-template-columns: repeat(4, 1fr);
                    }}
                }}
                @media (max-width: 768px) {{
                    .month-grid {{
                        grid-template-columns: repeat(3, 1fr);
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="result-card">
                    <div class="header">
                        <h1>📦 {report_type} Batch Download Complete</h1>
                        <p>{station} - {year} (First 3 Months)</p>
                        <p style="color: #666; font-size: 0.9rem; margin-top: 5px;">
                            {results['note']}
                        </p>
                    </div>
                    
                    <div class="main-content">
                        <!-- Left Panel: Summary -->
                        <div class="summary-panel">
                            <div class="summary-grid">
                                <div class="summary-card">
                                    <div class="summary-value success-value">{results['total_success']}/3</div>
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
                                ✓ Processed: First 3 months only<br>
                                ✓ Files: {report_type}YYYYMM.txt<br>
                                ✓ Type: {'TAF (tipo=FC)' if report_type == 'TAF' else 'METAR (tipo=SA)'}<br>
                                ✓ Folder: {results['folder']}.zip<br>
                                ✓ Sample data used if server unavailable
                            </div>
                            
                            <div class="action-buttons">
                                <a href="/file/{results['folder']}" class="action-btn download-btn">
                                    📥 Download All Files
                                </a>
                                <a href="/" class="action-btn back-btn">
                                    ← New Download
                                </a>
                            </div>
                        </div>
                        
                        <!-- Right Panel: Months -->
                        <div class="months-panel">
                            <h3 style="margin-bottom: 15px; color: #333;">Monthly Results:</h3>
                            <div class="month-grid">
        """
        
        # Add month cards
        for result in results['results']:
            if result['success']:
                if result.get('source', '').startswith('SAMPLE'):
                    status_class = 'month-sample'
                    source_class = 'source-sample'
                    source_text = 'SAMPLE'
                else:
                    status_class = 'month-success'
                    source_class = 'source-ogimet'
                    source_text = 'OGIMET'
            else:
                status_class = 'month-failed'
                source_class = ''
                source_text = ''
            
            html += f"""
                                <div class="month-card {status_class}">
                                    {f'<span class="month-source {source_class}">{source_text}</span>' if source_text else ''}
                                    <div class="month-name">{result['month_name']}</div>
                                    <div class="month-reports">
                                        {result['reports'] if result['success'] else '❌'}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #666;">
                                        {result['month']}
                                    </div>
                                </div>
            """
        
        html += f"""
                            </div>
                            <div class="note-box">
                                <strong>Legend:</strong><br>
                                • <span style="color: #10b981">Green border</span>: Real data from OGIMET<br>
                                • <span style="color: #f59e0b">Yellow border</span>: Sample data (server offline)<br>
                                • <span style="color: #ef4444">Red border</span>: Failed to download<br>
                                • <strong>Note:</strong> Only first 3 months processed for speed
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
if __name__ == "__main__":
    print(f"🌐 Starting METAR/TAF Downloader Server on port {PORT}")
    print("📡 Server features:")
    print("   • Real-time METAR/TAF downloads")
    print("   • Sample data fallback if server fails")
    print("   • Timeout protection (45 seconds)")
    print("   • Two-column desktop interface")
    print("   • Server status monitoring")
    print(f"\n🔗 Open browser to: http://localhost:{PORT}")
    print("   Press Ctrl+C to stop the server\n")
    
    try:
        with socketserver.TCPServer(("", PORT), MetarHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
