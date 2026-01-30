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
        
        # Process in smaller batches (2 months at a time)
        all_months = list(range(1, 13))
        batches = [all_months[i:i+2] for i in range(0, len(all_months), 2)]  # Changed from 3 to 2
        
        print(f"\n🚀 Starting {report_type} batch download for {station} {year}")
        print(f"📁 Saving to folder: {folder_name}")
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n📦 Batch {batch_idx + 1}/{len(batches)}")
            
            for month_num in batch:
                month = f"{month_num:02d}"
                month_name = month_names.get(month, f"Month {month}")
                
                if month == '02' and is_leap:
                    end_day = '29'
                else:
                    end_day = month_days.get(month, '31')
                
                print(f"  📅 {month_name} ({year}-{month})...", end="", flush=True)
                
                try:
                    # Increase timeout and retry logic
                    clean_data, _ = self.get_weather_data_with_retry(
                        station, year, month, report_type, end_day
                    )
                    
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
                        
                        print(f"✅ {report_count} reports saved")
                    else:
                        results.append({
                            'month': month,
                            'month_name': month_name,
                            'filename': '',
                            'reports': 0,
                            'success': False,
                            'error': f'No {report_type} data'
                        })
                        print("❌ No data found")
                        
                except Exception as e:
                    results.append({
                        'month': month,
                        'month_name': month_name,
                        'filename': '',
                        'reports': 0,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"❌ Error: {str(e)[:50]}...")
                
                # Increase delay between months
                print(f"    Waiting 2 seconds...")
                time.sleep(2)  # Increased delay
            
            # Longer delay between batches
            if batch_idx < len(batches) - 1:
                wait_time = 5
                print(f"\n    ⏳ Waiting {wait_time} seconds before next batch...")
                time.sleep(wait_time)
        
        print(f"\n🎉 Batch download completed!")
        print(f"   ✅ Successful: {sum(1 for r in results if r['success'])}/12 months")
        print(f"   📊 Total reports: {sum(r['reports'] for r in results if r['success']):,}")
        
        return {
            'station': station,
            'year': year,
            'report_type': report_type,
            'folder': folder_name,
            'results': results,
            'total_success': sum(1 for r in results if r['success']),
            'total_reports': sum(r['reports'] for r in results if r['success'])
        }

    def get_weather_data_with_retry(self, station, year, month, report_type='METAR', end_day=None, retries=3):
        """Get data with retry logic"""
        for attempt in range(retries):
            try:
                print(f"    Attempt {attempt + 1}/{retries}...", end="")
                clean_data, raw_data = self.get_weather_data(station, year, month, report_type, end_day)
                
                if clean_data and len(clean_data.strip()) > 0:
                    print("✅ Success")
                    return clean_data, raw_data
                else:
                    print("❌ No data")
                    if attempt < retries - 1:
                        time.sleep(3)  # Wait before retry
            
            except requests.exceptions.Timeout:
                print(f"⌛ Timeout")
                if attempt < retries - 1:
                    print(f"    Retrying in 5 seconds...")
                    time.sleep(5)
            
            except requests.exceptions.ConnectionError:
                print(f"🔌 Connection error")
                if attempt < retries - 1:
                    print(f"    Retrying in 10 seconds...")
                    time.sleep(10)
            
            except Exception as e:
                print(f"⚠️ Error: {str(e)[:30]}")
                if attempt < retries - 1:
                    print(f"    Retrying in 3 seconds...")
                    time.sleep(3)
        
        return "", "All retries failed"
