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

def send_email(recipients, subject, body, attachment_path=None, config=None, cc=None, bcc=None):
    """
    Send an email with optional attachment to multiple recipients
    
    Args:
        recipients (str or list): Recipient email address(es)
        subject (str): Email subject
        body (str): Email body
        attachment_path (str, optional): Path to attachment file
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
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                message.attach(part)
        
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

def send_stock_report(ticker, recipients, file_path, data=None, cc=None, bcc=None):
    """
    Send a stock report via email to multiple recipients
    
    Args:
        ticker (str): Stock ticker symbol
        recipients (str or list): Recipient email address(es)
        file_path (str): Path to the report file
        data (dict, optional): Stock data to include in the email body
        cc (str or list, optional): CC email address(es)
        bcc (str or list, optional): BCC email address(es)
        
    Returns:
        bool: True if successful, False otherwise
    """
    subject = f"Stock Analysis Report: {ticker} - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Create email body
    body = [
        f"Stock Analysis Report for {ticker}",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "This is an automated report from your Stock Data Scraper application.",
        ""
    ]
    
    # Add key metrics if data is provided
    if data:
        body.append("Key Metrics:")
        body.append("-----------")
        
        # Add a few important metrics if available
        metrics = [
            ("P/E Ratio", "P/E Ratio"),
            ("Forward P/E", "Forward P/E"),
            ("PEG Ratio", "PEG Ratio"),
            ("EPS", "EPS"),
            ("ROE", "ROE"),
            ("Current Price", "Current Price"),
            ("RSI", "RSI (14)")
        ]
        
        for label, key_prefix in metrics:
            for data_key in data.keys():
                if key_prefix in data_key:
                    body.append(f"{label}: {data[data_key]}")
                    break
        
        body.append("")
    
    body.append("Please find the detailed report attached.")
    body.append("")
    body.append("--")
    body.append("Stock Data Scraper")
    
    # Debug info
    print(f"Sending with environment variables:")
    print(f"SMTP Server: {os.environ.get('FINANCE_SMTP_SERVER')}")
    print(f"Sender Email: {os.environ.get('FINANCE_SENDER_EMAIL')}")
    print(f"Password Set: {'Yes' if os.environ.get('FINANCE_SENDER_PASSWORD') else 'No'}")
    
    return send_email(
        recipients=recipients,
        subject=subject,
        body="\n".join(body),
        attachment_path=file_path,
        cc=cc,
        bcc=bcc
    )