import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from generate_excel import create_excel_dashboard

CASES_FILE = "datasets/cases.csv"
RESULTS_FILE = "datasets/rule_checker_results.csv"
AI_RESULTS_FILE = "datasets/ai_diagnosis_results.csv"
REVIEW_FILE = "datasets/responsible_ai_log.csv"
OUTPUT_FILE = "dashboard/index.html"

def generate_dashboard():
    """
    Generate an HTML dashboard and Excel dashboard from the CSV artifacts.
    """
    
    # Load data
    cases_df = pd.read_csv(CASES_FILE)
    results_df = pd.read_csv(RESULTS_FILE)
    ai_df = pd.read_csv(AI_RESULTS_FILE)
    review_df = pd.read_csv(REVIEW_FILE)
    
    # Calculate metrics
    total_cases = len(cases_df)
    successful_ai = (ai_df["status"] == "SUCCESS").sum()
    failed_ai = (ai_df["status"] != "SUCCESS").sum()
    
    rule_matches = (results_df["comparison"] == "MATCH").sum()
    rule_mismatches = (results_df["comparison"] == "MISMATCH").sum()
    rule_no_detection = (results_df["comparison"] == "NO_DETECTION").sum()
    
    human_reviews = len(review_df)
    review_accepted = (review_df["human_decision"] == "Accepted").sum()
    review_edited = (review_df["human_decision"] == "Edited").sum()
    
    match_rate = (rule_matches / total_cases * 100) if total_cases > 0 else 0
    correction_rate = (review_edited / human_reviews * 100) if human_reviews > 0 else 0
    
    # Severity breakdown
    severity_counts = cases_df["severity"].value_counts().to_dict()
    severity_html = "".join([
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(severity_counts.items())
    ])
    
    # Concept breakdown
    concept_counts = results_df["detected_concepts"].value_counts().head(10).to_dict()
    concept_html = "".join([
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)
    ])
    
    # Recent reviews
    recent_reviews = review_df.tail(5)
    recent_html = "".join([
        f"""<tr>
            <td>{row["case_id"]}</td>
            <td>{row["human_decision"]}</td>
            <td>{row["ai_confidence"]:.2f}</td>
            <td>{row["review_timestamp"]}</td>
        </tr>"""
        for _, row in recent_reviews.iterrows()
    ])
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetSega AI Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #134074 0%, #0b2545 100%);
            color: white;
            padding: 22px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .metric-card h3 {{
            font-size: 0.85em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-card .value {{
            font-size: 2.2em;
            font-weight: bold;
        }}
        
        .metric-card.accent {{
            background: linear-gradient(135deg, #0070d2 0%, #134074 100%);
        }}
        
        .metric-card.success {{
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }}
        
        .metric-card.warning {{
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        }}
        
        section {{
            margin-bottom: 40px;
        }}
        
        section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #134074;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        th {{
            background: #f5f5f5;
            color: #333;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background: #f9f9f9;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge.accepted {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.edited {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .badge.match {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        .badge.mismatch {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        footer {{
            background: #f5f5f5;
            color: #666;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>NetSega AI Dashboard</h1>
            <p>Cisco NetAcad VIP 2026 Submission • Network Troubleshooting with Responsible AI</p>
        </header>
        
        <div class="content">
            <section>
                <h2>📊 Key Performance Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Total Cases</h3>
                        <div class="value">{total_cases}</div>
                    </div>
                    <div class="metric-card success">
                        <h3>Successful AI Diagnoses</h3>
                        <div class="value">{successful_ai}</div>
                    </div>
                    <div class="metric-card">
                        <h3>Failed AI Diagnoses</h3>
                        <div class="value">{failed_ai}</div>
                    </div>
                    <div class="metric-card accent">
                        <h3>Rule Match Rate</h3>
                        <div class="value">{match_rate:.1f}%</div>
                    </div>
                    <div class="metric-card">
                        <h3>Human Reviews</h3>
                        <div class="value">{human_reviews}</div>
                    </div>
                    <div class="metric-card success">
                        <h3>Accepted Reviews</h3>
                        <div class="value">{review_accepted}</div>
                    </div>
                    <div class="metric-card warning">
                        <h3>Edited Reviews</h3>
                        <div class="value">{review_edited}</div>
                    </div>
                    <div class="metric-card warning">
                        <h3>Human Correction Rate</h3>
                        <div class="value">{correction_rate:.1f}%</div>
                    </div>
                </div>
            </section>
            
            <section>
                <h2>📈 Rule Checker Performance</h2>
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                    <tr>
                        <td><span class="badge match">MATCH</span></td>
                        <td>{rule_matches}</td>
                        <td>{rule_matches/total_cases*100:.1f}%</td>
                    </tr>
                    <tr>
                        <td><span class="badge mismatch">MISMATCH</span></td>
                        <td>{rule_mismatches}</td>
                        <td>{rule_mismatches/total_cases*100:.1f}%</td>
                    </tr>
                    <tr>
                        <td><span class="badge">NO DETECTION</span></td>
                        <td>{rule_no_detection}</td>
                        <td>{rule_no_detection/total_cases*100:.1f}%</td>
                    </tr>
                </table>
            </section>
            
            <section>
                <h2>🔍 Human Review Summary</h2>
                <table>
                    <tr>
                        <th>Decision</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                    <tr>
                        <td><span class="badge accepted">Accepted</span></td>
                        <td>{review_accepted}</td>
                        <td>{review_accepted/human_reviews*100:.1f}%</td>
                    </tr>
                    <tr>
                        <td><span class="badge edited">Edited</span></td>
                        <td>{review_edited}</td>
                        <td>{review_edited/human_reviews*100:.1f}%</td>
                    </tr>
                </table>
            </section>
            
            <section>
                <h2>⚠️ Cases by Severity</h2>
                <table>
                    <tr>
                        <th>Severity</th>
                        <th>Count</th>
                    </tr>
                    {severity_html}
                </table>
            </section>
            
            <section>
                <h2>🏷️ Top Detected Concepts</h2>
                <table>
                    <tr>
                        <th>Concept</th>
                        <th>Occurrences</th>
                    </tr>
                    {concept_html}
                </table>
            </section>
            
            <section>
                <h2>📋 Recent Review Records</h2>
                <table>
                    <tr>
                        <th>Case ID</th>
                        <th>Decision</th>
                        <th>Confidence</th>
                        <th>Timestamp</th>
                    </tr>
                    {recent_html}
                </table>
            </section>
        </div>
        
        <footer>
            <p>NetSega AI Dashboard • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Rule Checker: {RESULTS_FILE} | Human Review: {REVIEW_FILE}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
        
    # Generate Excel Dashboard
    create_excel_dashboard()
    
    print()
    print("NetSega AI Dashboard Generator")
    print("================================")
    print(f"HTML Dashboard generated : {OUTPUT_FILE}")
    print(f"Excel Dashboard generated: dashboard/NetSega_AI_Dashboard.xlsx")
    print(f"Total cases              : {total_cases}")
    print(f"Successful AI Diagnoses  : {successful_ai}")
    print(f"Failed AI Diagnoses      : {failed_ai}")
    print(f"Rule match rate          : {match_rate:.1f}%")
    print(f"Human reviews            : {human_reviews}")
    print(f"Accepted Reviews         : {review_accepted}")
    print(f"Edited Reviews           : {review_edited}")
    print(f"Human Correction Rate    : {correction_rate:.1f}%")
    print()

if __name__ == "__main__":
    generate_dashboard()
