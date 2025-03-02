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

def send_email(recipient_email, subject, body, attachment_path=None, config=None):
    """
    Send an email with optional attachment
    
    Args:
        recipient_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        attachment_path (str, optional): Path to attachment file
        config (dict, optional): Email configuration. If None, will use environment variables.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config:
        config = setup_email_config()
    
    if not validate_email_config(config):
        return False
    
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = config["sender_email"]
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Add body
        message.attach(MIMEText(body, "plain"))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                message.attach(part)
        
        # Connect to server and send email
        if config["use_tls"]:
            context = ssl.create_default_context()
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(config["sender_email"], config["sender_password"])
                server.send_message(message)
        else:
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.login(config["sender_email"], config["sender_password"])
                server.send_message(message)
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_stock_report(ticker, recipient_email, file_path, data=None):
    """
    Send a stock report via email
    
    Args:
        ticker (str): Stock ticker symbol
        recipient_email (str): Recipient email address
        file_path (str): Path to the report file
        data (dict, optional): Stock data to include in the email body
        
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
    
    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body="\n".join(body),
        attachment_path=file_path
    )