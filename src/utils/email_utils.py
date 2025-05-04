"""
Email utilities for sending financial reports
"""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate
# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def setup_email_config():
    """
    Set up email configuration
    
    Returns:
        dict: Dictionary with email configuration
    """
    config = {
        "smtp_server": os.environ.get("FINANCE_SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("FINANCE_SMTP_PORT", 587)),
        "sender_email": os.environ.get("FINANCE_SENDER_EMAIL", ""),
        "sender_password": os.environ.get("FINANCE_SENDER_PASSWORD", ""),
        "use_tls": os.environ.get("FINANCE_USE_TLS", "True").lower() == "true"
    }
    
    return config

def validate_email_config(config):
    """
    Validate email configuration
    
    Args:
        config (dict): Email configuration
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["smtp_server", "smtp_port", "sender_email", "sender_password"]
    
    for field in required_fields:
        if not config.get(field):
            logger.warning(f"Missing required email configuration: {field}")
            return False
    
    return True

def parse_email_list(email_string):
    """
    Parse a comma-separated list of email addresses
    
    Args:
        email_string (str): Comma-separated list of email addresses
        
    Returns:
        list: List of email addresses
    """
    if not email_string:
        return []
        
    # Split by comma and strip whitespace
    emails = [email.strip() for email in email_string.split(",")]
    
    # Filter out empty strings
    return [email for email in emails if email]

def send_email(recipients, subject, body, attachment_paths=None, config=None, cc=None, bcc=None, is_html=False):
    """
    Send an email with optional attachments to multiple recipients
    
    Args:
        recipients (str or list): Recipient email address(es)
        subject (str): Email subject
        body (str): Email body
        attachment_paths (list, optional): List of paths to attachment files
        config (dict, optional): Email configuration. If None, will use environment variables.
        cc (str or list, optional): CC email address(es)
        bcc (str or list, optional): BCC email address(es)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config:
        config = setup_email_config()
    
    if not validate_email_config(config):
        return False
    
    # Convert string recipient to list if needed
    if isinstance(recipients, str):
        recipients = parse_email_list(recipients)
    
    # Convert CC and BCC to lists if needed
    if isinstance(cc, str):
        cc = parse_email_list(cc)
    elif cc is None:
        cc = []
        
    if isinstance(bcc, str):
        bcc = parse_email_list(bcc)
    elif bcc is None:
        bcc = []
    
    # Ensure we have at least one recipient
    if not recipients and not cc and not bcc:
        logger.error("No recipients specified")
        return False
    
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = config["sender_email"]
        
        # Set To, CC, and BCC headers
        if recipients:
            message["To"] = ", ".join(recipients)
        if cc:
            message["Cc"] = ", ".join(cc)
        # BCC is not included in headers
        
        message["Subject"] = subject
        
        # Add body
        if is_html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
        
        # Add attachments if provided
        if attachment_paths:
            for path in attachment_paths:
                if os.path.exists(path):
                    with open(path, "rb") as attachment:
                        part = MIMEApplication(attachment.read(), Name=os.path.basename(path))
                        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
                        message.attach(part)
                else:
                    logger.warning(f"Attachment file not found: {path}")
        
        # Combine all recipients for actual sending
        all_recipients = list(recipients) + list(cc) + list(bcc)
        
        # Connect to server and send email
        if config["use_tls"]:
            context = ssl.create_default_context()
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(config["sender_email"], config["sender_password"])
                server.sendmail(config["sender_email"], all_recipients, message.as_string())
        else:
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.login(config["sender_email"], config["sender_password"])
                server.sendmail(config["sender_email"], all_recipients, message.as_string())
        
        logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def generate_metrics_table(data_dict, metrics=None, table_format="grid"):
    """
    Generate a simple text table of key metrics for multiple stocks
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        metrics (list, optional): List of metrics to include
        table_format (str, optional): Format of the table (e.g., "grid", "plain"). Defaults to "grid".
        
    Returns:
        str: Formatted table as string
    """
    if not metrics:
        metrics = [
            "P/E Ratio", "Forward P/E", "PEG Ratio", 
            "EPS", "ROE", "Profit Margin", 
            "Current Price", "RSI (14)"
        ]
     # Prepare the data for tabulation
    summary_data = []
    for ticker, data in data_dict.items():
        row = [ticker]  # Start with the ticker symbol
        for metric_name in metrics:
            # Perform a case-insensitive partial match for the metric
            value = next((data[key] for key in data if metric_name.lower() in key.lower()), "--")
            row.append(value)
        summary_data.append(row)
    
    # Add headers (Ticker + Metrics)
    headers = ["Ticker"] + metrics
    
    # Generate the formatted table using tabulate
    if summary_data:
        return tabulate(summary_data, headers=headers, tablefmt=table_format)
    else:
        return "No data available for metrics table."


def generate_html_metrics_table(all_data):
    """
    Generate an HTML table for key metrics.
    
    Args:
        all_data (dict): Dictionary with ticker symbols as keys and data dictionaries as values.
        
    Returns:
        str: HTML table as a string.
    """
    # Define the key metrics to include in the summary
    key_metrics = ["Ticker", "P/E Ratio", "Forward P/E", "PEG Ratio", "EPS", "ROE", "P/B Ratio", "P/S Ratio", "Profit Margin"]
    
    # Start the HTML table
    html = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    html += "<thead><tr>"
    for metric in key_metrics:
        html += f"<th style='padding: 8px; text-align: left;'>{metric}</th>"
    html += "</tr></thead><tbody>"
    
    # Add rows for each ticker
    for ticker, data in all_data.items():
        html += "<tr>"
        html += f"<td style='padding: 8px;'>{ticker}</td>"
        for metric in key_metrics[1:]:  # Skip "Ticker" as it's already added
            value = next((data[key] for key in data if metric in key), "--")
            html += f"<td style='padding: 8px;'>{value}</td>"
        html += "</tr>"
    
    html += "</tbody></table>"
    return html
def send_consolidated_report(tickers, report_paths, all_data, recipients, summary_path=None, cc=None, bcc=None):
    """
    Send a consolidated report email for multiple stocks using HTML formatting.
    
    Args:
        tickers (list): List of ticker symbols
        report_paths (dict): Dictionary with ticker symbols as keys and report file paths as values
        all_data (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        recipients (str or list): Recipient email address(es)
        summary_path (str, optional): Path to summary report file
        cc (str or list, optional): CC email address(es)
        bcc (str or list, optional): BCC email address(es)
        
    Returns:
        bool: True if successful, False otherwise
    """
    subject = f"Stock Analysis Report: {', '.join(tickers)} - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Generate the HTML table for key metrics
    metrics_table_html = generate_html_metrics_table(all_data)
    
    # Create the HTML email body
    body = f"""
    <html>
        <body>
            <h2>Stock Analysis Report</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>This is an automated report from your Stock Data Scraper application.</p>
            
            <h3>Key Metrics Summary</h3>
            {metrics_table_html}
            
            <h3>Individual Stock Highlights</h3>
            <ul>
    """
    
    # Add individual stock highlights
    for ticker, data in all_data.items():
        body += f"<li><strong>{ticker}:</strong><ul>"
        metrics = [
            ("P/E Ratio", "P/E Ratio"),
            ("Forward P/E", "Forward P/E"),
            ("EPS", "EPS"),
            ("ROE", "ROE"),
            ("Current Price", "Current Price")
        ]
        for label, key_prefix in metrics:
            for data_key in data.keys():
                if key_prefix in data_key:
                    body += f"<li>{label}: {data[data_key]}</li>"
                    break
        body += "</ul></li>"
    
    body += """
            </ul>
            <p>Please find the detailed reports attached.</p>
    """
    
    # Add note about summary report if available
    if summary_path:
        body += "<p>A summary comparison report is also attached.</p>"
    
    body += """
            <p>--<br>Stock Data Scraper</p>
        </body>
    </html>
    """
    
    # Prepare attachments - include both individual reports and summary
    attachments = list(report_paths.values())
    if summary_path:
        attachments.append(summary_path)
    
    # Debug info
    print(f"Sending consolidated report with {len(attachments)} attachments")
    print(f"Recipients: {recipients}")
    
    # Send email
    print(f"DEBUGG CC email to: {cc}")
    return send_email(
        recipients=recipients,
        subject=subject,
        body=body,
        attachment_paths=attachments,
        cc=cc,
        bcc=bcc,
        is_html=True  # Indicate that the email body is HTML
    )