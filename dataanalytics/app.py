import os
import re
import pandas as pd
import numpy as np
import threading
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)

# Secret key for monitor access — set this in Render.com environment variables
MONITOR_KEY = os.environ.get('MONITOR_KEY', 'RAD_ADMIN_2024')

# Config directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
SPLIT_DIR = os.path.join(BASE_DIR, 'data', 'split')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
DB_JSON_DIR = os.path.join(BASE_DIR, 'db_json')

for directory in [RAW_DIR, SPLIT_DIR, PROCESSED_DIR, DB_JSON_DIR]:
    os.makedirs(directory, exist_ok=True)

DATA_LEARN_FILE = os.path.join(DB_JSON_DIR, 'data-learn.json')

@app.before_request
def log_device_data():
    if request.path in ['/', '/upload', '/split', '/reconcile']:
        device_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'action': request.path,
            'method': request.method
        }
        
        try:
            if os.path.exists(DATA_LEARN_FILE):
                with open(DATA_LEARN_FILE, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
                
            data.append(device_data)
            with open(DATA_LEARN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            pass # Silent fail for telemetry

# Helper: Normalize billing numbers
def normalize_billing(val):
    if not isinstance(val, str):
        return val
    val = val.strip().upper()
    match = re.match(r"^(([A-Z])[A-Z]+)/\2?(\d+)/(\d+)/(\d+)$", val)
    if match:
        prefix, first_letter, num1, num2, num3 = match.groups()
        return f"{prefix}/{num1}/{num2}/{num3.zfill(6)}"
    return val

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith(('.xlsx', '.xls')):
        # Save to data/raw/
        filename = "ZV64_IMT_2024_new.xlsx" # Keep standard name internally
        file_path = os.path.join(RAW_DIR, filename)
        file.save(file_path)
        return jsonify({
            'success': True,
            'message': f"File successfully uploaded and saved as '{filename}' in raw data directory."
        })
    else:
        return jsonify({'error': 'Invalid file format. Please upload an Excel (.xlsx or .xls) file.'}), 400

@app.route('/split', methods=['POST'])
def split_excel():
    excel_path = os.path.join(RAW_DIR, "ZV64_IMT_2024_new.xlsx")
    if not os.path.exists(excel_path):
        return jsonify({'error': 'Raw Excel file not found. Please upload the file first.'}), 400
    
    try:
        xls = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')
        exported_sheets = []
        for sheet_name, df in xls.items():
            safe_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_', '-')).strip()
            out_file = os.path.join(SPLIT_DIR, f"{safe_name}.csv")
            df.to_csv(out_file, index=False)
            exported_sheets.append(f"{safe_name}.csv")
            
        return jsonify({
            'success': True,
            'message': f"Excel successfully split into {len(exported_sheets)} sheets: {', '.join(exported_sheets)}"
        })
    except Exception as e:
        return jsonify({'error': f"Failed to split Excel: {str(e)}"}), 500

@app.route('/reconcile', methods=['POST'])
def run_reconciliation():
    pivot_path = os.path.join(SPLIT_DIR, "pivot.csv")
    if not os.path.exists(pivot_path):
        return jsonify({'error': "pivot.csv not found in split directory. Did you run Split Excel first?"}), 400
    
    try:
        # Load pivot skipping the first 5 header rows
        df = pd.read_csv(pivot_path, skiprows=5)
        
        # GL Side
        gl_df = df.iloc[:, [0, 1, 2]].dropna(subset=[df.columns[0]])
        gl_df.columns = ['Invoice_GL', 'GL_Qty', 'GL_Amount']
        gl_df['Invoice_GL'] = gl_df['Invoice_GL'].astype(str).str.strip()
        gl_df = gl_df[gl_df['Invoice_GL'] != 'Grand Total']
        
        # Bill Side
        bill_df = df.iloc[:, [6, 7, 8]].dropna(subset=[df.columns[6]])
        bill_df.columns = ['Invoice_Bill', 'Bill_Qty', 'Bill_Value']
        bill_df['Invoice_Bill'] = bill_df['Invoice_Bill'].astype(str).str.strip()
        bill_df = bill_df[bill_df['Invoice_Bill'] != 'Grand Total']
        
        all_invoices = sorted(list(set(gl_df['Invoice_GL']).union(set(bill_df['Invoice_Bill']))))
        
        records = []
        for inv in all_invoices:
            gl_row = gl_df[gl_df['Invoice_GL'] == inv]
            bill_row = bill_df[bill_df['Invoice_Bill'] == inv]
            
            in_gl = not gl_row.empty
            in_bill = not bill_row.empty
            
            gl_qty = gl_row['GL_Qty'].values[0] if in_gl else np.nan
            gl_amt = gl_row['GL_Amount'].values[0] if in_gl else np.nan
            
            bill_qty = bill_row['Bill_Qty'].values[0] if in_bill else np.nan
            bill_val = bill_row['Bill_Value'].values[0] if in_bill else np.nan
            
            diff_qty = np.nan
            diff_val = np.nan
            
            if in_gl and in_bill:
                diff_qty = abs(gl_qty) - bill_qty
                diff_val = abs(gl_amt) - bill_val
                
            if not in_gl:
                status = "Only in Bill (N#A in GL)"
            elif not in_bill:
                status = "Only in GL (N#A in Bill)"
            else:
                qty_disc = abs(diff_qty) > 0.01
                val_disc = abs(diff_val) > 0.01
                if qty_disc and val_disc:
                    status = "Qty & Value Discrepancy"
                elif qty_disc:
                    status = "Qty Discrepancy"
                elif val_disc:
                    status = "Value Discrepancy"
                else:
                    status = "Match"
                    
            records.append({
                'Invoice Number': inv,
                'Exists in GL': 'Yes' if in_gl else 'No',
                'Exists in Bill': 'Yes' if in_bill else 'No',
                'GL Quantity': round(gl_qty, 2) if pd.notnull(gl_qty) else gl_qty,
                'Bill Quantity': round(bill_qty, 2) if pd.notnull(bill_qty) else bill_qty,
                'Diff Quantity': round(diff_qty, 2) if pd.notnull(diff_qty) else diff_qty,
                'GL Net Value': round(gl_amt, 2) if pd.notnull(gl_amt) else gl_amt,
                'Bill Net Value': round(bill_val, 2) if pd.notnull(bill_val) else bill_val,
                'Diff Net Value': round(diff_val, 2) if pd.notnull(diff_val) else diff_val,
                'Status': status
            })
            
        result_df = pd.DataFrame(records)
        
        # Save results
        result_csv_path = os.path.join(PROCESSED_DIR, "result.csv")
        result_xlsx_path = os.path.join(PROCESSED_DIR, "result.xlsx")
        
        result_df.to_csv(result_csv_path, index=False)
        result_df.to_excel(result_xlsx_path, index=False, engine='openpyxl')
        
        # Generate ReconReport.html
        generate_html_report(result_df)
        
        summary = result_df['Status'].value_counts().to_dict()
        return jsonify({
            'success': True,
            'message': 'Reconciliation processed successfully!',
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': f"Failed to reconcile data: {str(e)}"}), 500

@app.route('/report')
def get_report():
    return send_from_directory(PROCESSED_DIR, 'ReconReport.html')

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id == '2024':
        return send_from_directory(SPLIT_DIR, '2024.csv', as_attachment=True)
    elif file_id == 'gl_2024_2':
        return send_from_directory(SPLIT_DIR, 'GL 2024 2.csv', as_attachment=True)
    elif file_id == 'pivot':
        return send_from_directory(SPLIT_DIR, 'pivot.csv', as_attachment=True)
    elif file_id == 'result':
        return send_from_directory(PROCESSED_DIR, 'result.xlsx', as_attachment=True)
    return jsonify({'error': 'File not found'}), 404



@app.route('/log_location', methods=['POST'])
def log_location():
    data = request.json
    
    # Get IP properly behind proxy
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_address = ip_address.split(',')[0].strip() if ip_address else 'Unknown'
    
    user_agent = request.headers.get('User-Agent', 'Unknown')
    action = data.get('action', 'Location & Battery Update')
        
    device_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'ip_address': ip_address,
        'user_agent': user_agent,
        'action': 'Location & Battery Update',
        'latitude': data.get('lat'),
        'longitude': data.get('lng'),
        'battery_level': data.get('battery_level'),
        'is_charging': data.get('is_charging')
    }
    
    try:
        if os.path.exists(DATA_LEARN_FILE):
            with open(DATA_LEARN_FILE, 'r', encoding='utf-8') as f:
                try:
                    file_data = json.load(f)
                except json.JSONDecodeError:
                    file_data = []
        else:
            file_data = []
            
        file_data.append(device_data)
        with open(DATA_LEARN_FILE, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=4)
    except Exception as e:
        pass
        
    return jsonify({'status': 'success'})

@app.route('/monitor')
def monitor():
    key = request.args.get('key', '')
    if key != MONITOR_KEY:
        return render_template('404.html'), 404
    return render_template('monitor.html')

@app.route('/warning')
def warning():
    return render_template('warning.html')

@app.route('/api/telemetry')
def api_telemetry():
    if os.path.exists(DATA_LEARN_FILE):
        try:
            with open(DATA_LEARN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

def generate_html_report(df):
    total_invoices = len(df)
    match_count = len(df[df['Status'] == 'Match'])
    only_bill_count = len(df[df['Status'] == 'Only in Bill (N#A in GL)'])
    only_gl_count = len(df[df['Status'] == 'Only in GL (N#A in Bill)'])
    discrepancy_count = len(df[df['Status'] == 'Qty & Value Discrepancy'])

    total_gl_qty = df['GL Quantity'].abs().sum()
    total_bill_qty = df['Bill Quantity'].sum()
    diff_qty = total_gl_qty - total_bill_qty

    total_gl_val = df['GL Net Value'].abs().sum()
    total_bill_val = df['Bill Net Value'].sum()
    diff_val = total_gl_val - total_bill_val

    top_disc = df[df['Status'] == 'Qty & Value Discrepancy'].copy()
    top_disc['Abs_Diff_Val'] = top_disc['Diff Net Value'].abs()
    top_disc = top_disc.sort_values(by='Abs_Diff_Val', ascending=False).head(5)

    disc_table_rows = ""
    for idx, row in top_disc.iterrows():
        disc_table_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; font-family: monospace; font-size: 0.9em; color: #1A1A1A;">{row['Invoice Number']}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; color: #E53E3E; font-weight: 500;">{row['GL Quantity']:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; color: #2B6CB0; font-weight: 500;">{row['Bill Quantity']:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; font-weight: 600; color: #2D3748;">{row['Diff Quantity']:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; color: #E53E3E; font-weight: 500;">{row['GL Net Value']:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; color: #2B6CB0; font-weight: 500;">{row['Bill Net Value']:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; font-weight: 600; color: #2D3748;">{row['Diff Net Value']:,.2f}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReconReport - McKinsey Corporate Style</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC;
            color: #1A1A1A;
            line-height: 1.5;
            padding: 40px;
            display: flex;
            justify-content: center;
        }}
        .report-container {{
            width: 100%;
            max-width: 1100px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
            padding: 50px;
            position: relative;
        }}
        .report-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 8px;
            background-color: #002D62;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 2px solid #002D62;
            padding-bottom: 20px;
            margin-bottom: 35px;
        }}
        .header-title h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 2.4em;
            font-weight: 700;
            color: #002D62;
            letter-spacing: -0.5px;
        }}
        .header-title p {{
            font-size: 0.95em;
            color: #4A607A;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
            margin-top: 5px;
        }}
        .header-meta {{
            text-align: right;
            font-size: 0.85em;
            color: #718096;
        }}
        .grid-kpi {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }}
        .kpi-card {{
            background: #F8FAFC;
            border-left: 4px solid #002D62;
            padding: 20px;
            border-top: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
        }}
        .kpi-card.alert {{
            border-left-color: #E53E3E;
        }}
        .kpi-label {{
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #718096;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #002D62;
        }}
        .kpi-card.alert .kpi-value {{
            color: #E53E3E;
        }}
        .kpi-subtext {{
            font-size: 0.8em;
            color: #718096;
            margin-top: 5px;
        }}
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.4em;
            color: #002D62;
            margin-bottom: 20px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 8px;
        }}
        .layout-body {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-bottom: 40px;
        }}
        .chart-box {{
            display: flex;
            flex-direction: column;
        }}
        .chart-container {{
            position: relative;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .table-container {{
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}
        th {{
            background-color: #002D62;
            color: #FFFFFF;
            text-align: left;
            padding: 10px;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
        }}
        .footer {{
            border-top: 1px solid #E2E8F0;
            padding-top: 20px;
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #718096;
        }}
        .legend-box {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 15px;
        }}
        .legend-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85em;
            padding: 8px 12px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
            margin-right: 8px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>

<div class="report-container">
    <div class="header">
        <div class="header-title">
            <h1>ReconReport</h1>
            <p>GL vs Billing Reconciliation Summary — FY 2024</p>
        </div>
        <div class="header-meta">
            <p><strong>Prepared for:</strong> My Love Rara</p>
            <p><strong>Run Date:</strong> 2026-06-26</p>
        </div>
    </div>

    <div class="grid-kpi">
        <div class="kpi-card">
            <div class="kpi-label">Total Invoices Analyzed</div>
            <div class="kpi-value">{total_invoices:,}</div>
            <div class="kpi-subtext">Unique billing references</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Perfect Match Rate</div>
            <div class="kpi-value">{match_count / total_invoices * 100:.1f}%</div>
            <div class="kpi-subtext">{match_count:,} matched references</div>
        </div>
        <div class="kpi-card alert">
            <div class="kpi-label">Total Discrepancies</div>
            <div class="kpi-value">{discrepancy_count + only_bill_count + only_gl_count}</div>
            <div class="kpi-subtext">{discrepancy_count} qty/val, {only_bill_count + only_gl_count} missing</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Net Value Variance</div>
            <div class="kpi-value">IDR {abs(diff_val):,.0f}</div>
            <div class="kpi-subtext">GL absolute vs Bill value</div>
        </div>
    </div>

    <div class="layout-body">
        <div class="chart-box">
            <h2 class="section-title">Reconciliation Breakdown</h2>
            <div class="chart-container">
                <canvas id="statusChart"></canvas>
            </div>
            <div class="legend-box">
                <div class="legend-item">
                    <div style="display: flex; align-items: center;">
                        <div class="legend-color" style="background-color: #002D62;"></div>
                        <span>Perfect Match</span>
                    </div>
                    <strong>{match_count} ({match_count / total_invoices * 100:.1f}%)</strong>
                </div>
                <div class="legend-item">
                    <div style="display: flex; align-items: center;">
                        <div class="legend-color" style="background-color: #4A607A;"></div>
                        <span>Only in Bill (N#A in GL)</span>
                    </div>
                    <strong>{only_bill_count} ({only_bill_count / total_invoices * 100:.1f}%)</strong>
                </div>
                <div class="legend-item">
                    <div style="display: flex; align-items: center;">
                        <div class="legend-color" style="background-color: #CBD5E0;"></div>
                        <span>Only in GL (N#A in Bill)</span>
                    </div>
                    <strong>{only_gl_count} ({only_gl_count / total_invoices * 100:.1f}%)</strong>
                </div>
                <div class="legend-item">
                    <div style="display: flex; align-items: center;">
                        <div class="legend-color" style="background-color: #E53E3E;"></div>
                        <span>Qty & Value Discrepancy</span>
                    </div>
                    <strong>{discrepancy_count} ({discrepancy_count / total_invoices * 100:.1f}%)</strong>
                </div>
            </div>
        </div>

        <div class="chart-box">
            <h2 class="section-title">Aggregated Volumes</h2>
            <div style="margin-bottom: 25px; margin-top: 15px;">
                <p style="font-size: 0.75em; text-transform: uppercase; color: #718096; font-weight: 600; margin-bottom: 5px;">Total Quantity Comparison</p>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-size: 0.9em;">GL Quantity (Abs)</span>
                    <strong style="font-size: 1.1em; color: #002D62;">{total_gl_qty:,.2f}</strong>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-size: 0.9em;">Billed Quantity</span>
                    <strong style="font-size: 1.1em; color: #4A607A;">{total_bill_qty:,.2f}</strong>
                </div>
                <div style="height: 8px; background: #E2E8F0; width: 100%; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; background: #002D62; width: 100%;"></div>
                </div>
            </div>

            <div style="margin-bottom: 25px;">
                <p style="font-size: 0.75em; text-transform: uppercase; color: #718096; font-weight: 600; margin-bottom: 5px;">Total Value Comparison</p>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-size: 0.9em;">GL Net Value (Abs)</span>
                    <strong style="font-size: 1.1em; color: #002D62;">{total_gl_val:,.2f}</strong>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-size: 0.9em;">Billed Net Value</span>
                    <strong style="font-size: 1.1em; color: #4A607A;">{total_bill_val:,.2f}</strong>
                </div>
                <div style="height: 8px; background: #E2E8F0; width: 100%; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; background: #4A607A; width: 95%;"></div>
                </div>
            </div>

            <div style="padding: 20px; background: #FFF5F5; border: 1px solid #FED7D7; border-left: 4px solid #E53E3E; margin-top: 10px;">
                <p style="font-size: 0.85em; font-weight: 600; color: #9B2C2C; margin-bottom: 5px;">Reconciliation Note</p>
                <p style="font-size: 0.8em; color: #C53030;">A total variance of <strong>IDR {abs(diff_val):,.2f}</strong> exists between General Ledger and Billing systems. Key drives include consolidated invoices containing double-billed volumes (e.g. Contract duplicates).</p>
            </div>
        </div>
    </div>

    <div>
        <h2 class="section-title">Top 5 Discrepancies by Net Value</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="padding: 10px;">Invoice Number</th>
                        <th style="padding: 10px; text-align: right;">GL Qty</th>
                        <th style="padding: 10px; text-align: right;">Bill Qty</th>
                        <th style="padding: 10px; text-align: right;">Diff Qty</th>
                        <th style="padding: 10px; text-align: right;">GL Net Value</th>
                        <th style="padding: 10px; text-align: right;">Bill Net Value</th>
                        <th style="padding: 10px; text-align: right;">Diff Value</th>
                    </tr>
                </thead>
                <tbody>
                    {disc_table_rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        <p>&copy; RAD tech system</p>
    </div>
</div>

<script>
    const ctx = document.getElementById('statusChart').getContext('2d');
    new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: ['Match', 'Only in Bill', 'Only in GL', 'Discrepancy'],
            datasets: [{{
                data: [{match_count}, {only_bill_count}, {only_gl_count}, {discrepancy_count}],
                backgroundColor: ['#002D62', '#4A607A', '#CBD5E0', '#E53E3E'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            cutout: '70%'
        }}
    }});
</script>

</body>
</html>
"""
    report_path = os.path.join(PROCESSED_DIR, 'ReconReport.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
