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

def send_email(recipients, subject, body, attachment_paths=None, config=None, cc=None, bcc=None):
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

def generate_metrics_table(data_dict, metrics=None):
    """
    Generate a simple text table of key metrics for multiple stocks
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        metrics (list, optional): List of metrics to include
        
    Returns:
        str: Formatted table as string
    """
    if not metrics:
        metrics = [
            "P/E Ratio", "Forward P/E", "PEG Ratio", 
            "EPS", "ROE", "Profit Margin", 
            "Current Price", "RSI (14)"
        ]
    
    # Extract data for each ticker
    table_data = {}
    for ticker, data in data_dict.items():
        ticker_data = {"Ticker": ticker}
        
        # Find relevant metrics from different sources
        for metric_name in metrics:
            for key, value in data.items():
                if metric_name in key:
                    ticker_data[metric_name] = value
                    break
        
        table_data[ticker] = ticker_data
    
    # Convert to DataFrame
    if table_data:
        df = pd.DataFrame([v for v in table_data.values()])
        return df.to_string(index=False)
    else:
        return "No data available for metrics table."

def send_consolidated_report(tickers, report_paths, all_data, recipients, summary_path=None, cc=None, bcc=None):
    """
    Send a consolidated report email for multiple stocks
    
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
    
    # Create email body
    body = [
        f"Stock Analysis Report for {len(tickers)} stocks: {', '.join(tickers)}",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "This is an automated report from your Stock Data Scraper application.",
        "",
        "KEY METRICS SUMMARY",
        "===================="
    ]
    
    # Add metrics table
    metrics_table = generate_metrics_table(all_data)
    body.append(metrics_table)
    body.append("")
    
    # Add individual stock highlights
    body.append("INDIVIDUAL STOCK HIGHLIGHTS")
    body.append("=========================")
    
    for ticker, data in all_data.items():
        body.append(f"\n{ticker}:")
        
        # Add key metrics if available
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
                    body.append(f"  • {label}: {data[data_key]}")
                    break
    
    body.append("\nPlease find the detailed reports attached.")
    
    # Add note about summary report if available
    if summary_path:
        body.append("\nA summary comparison report is also attached.")
    
    body.append("")
    body.append("--")
    body.append("Stock Data Scraper")
    
    # Prepare attachments - include both individual reports and summary
    attachments = list(report_paths.values())
    if summary_path:
        attachments.append(summary_path)
    
    # Debug info
    print(f"Sending consolidated report with {len(attachments)} attachments")
    print(f"Recipients: {recipients}")
    
    # Send email
    return send_email(
        recipients=recipients,
        subject=subject,
        body="\n".join(body),
        attachment_paths=attachments,
        cc=cc,
        bcc=bcc
    )