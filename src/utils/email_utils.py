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
    
def get_all_sources_data(data, metric):
    """
    Get all values for a metric from different sources.

    Args:
        data (dict): Dictionary containing all data.
        metric (str): The metric to retrieve (e.g., "P/E Ratio").

    Returns:
        str: Concatenated values from all sources.
    """
     # Filter keys that match the metric
    matching_keys = [key for key in data.keys() if metric in key]

    # Group and format the values
    values = []
    for key in matching_keys:
        # Extract the source from the key (e.g., "Finviz" from "EPS (TTM) (Finviz)")
        source = key.split('(')[-1][:-1] if '(' in key else "Unknown"
        # Format the value with the source and specific metric label
        specific_metric = key.replace(f" ({source})", "").strip()  # Remove source from key
        values.append(f"{specific_metric} ({source}): {data[key]}")

    return ", ".join(values) if values else "--"


def generate_enhanced_html_cnn_metrics_table(cnnMetricData):
    """
    Generate an HTML table for CNN data metrics with columns: Metric, Score, Rating.
    Args:
        cnnMetricData (dict): Dictionary with key Metric as keys and data dictionaries as values.
    Returns:
        str: HTML table as a string.
    """
    metric_meanings = {
        "fear_and_greed": "Composite gauge of market sentiment, ranging from 0 (extreme fear) to 100 (extreme greed).<br>Excessive fear indicates a bearish market, while excessive greed indicates a bullish market.",
        "fear_and_greed_historical": "Historical data of the Fear and Greed Index.",
        "market_momentum_sp500": "Market momentum (S&P 500). If S&P 500 stocks is well above their 125-day average<br>>50 indicates bullish sentiment and has strong momentum.",
        "market_momentum_sp125": "Market momentum (S&P 125 stocks above 125-day average).",
        "stock_price_strength": "Stock price strength (Ratio of stocks at 52-week highs vs lows).<br>>50 indicates more stocks at making 52 weeks highs compared to 52 weeks lows.",
        "stock_price_breadth": "Stock price breadth (volume of advancing vs. declining stocks)<br>>50 indicates more volume in advancing stocks than declining.",
        "put_call_options": "Measures ratio of bearish(put) to bullish (call) options (derivatives sentiment.<br>>50 indicates more call than put, bullish sentiment in market.",
        "market_volatility_vix": "Market volatility (VIX), higher VIX<br>>50 indicates more volatility in the market, more fearful than greed.",
        "market_volatility_vix_50": "Market volatility (VIX vs. 50-day average).",
        "junk_bond_demand": "Measures spread between junk bond and investment grade yield.<br>>50 indicates tight spread, indicating more demand for junk bonds, higher risk appetite. Bullish sentiment.",
        "safe_haven_demand": "Compares demand for stocks vs Treasuries.<br>>50 indicates higher demand for stocks than Treasuries, indicating bullish sentiment (Greed)."
    }

    def get_score_color(score_str):
        """Get color based on score value."""
        try:
            score = float(score_str)
            if score <= 25:
                return "#e74c3c"  # Red for extreme fear
            elif score <= 40:
                return "#f39c12"  # Orange for fear
            elif score <= 50:
                return "#f1c40f"  # Yellow for neutral
            elif score <= 70:
                return "#27ae60"  # Green for greed
            else:
                return "#2ecc71"  # Bright green for extreme greed
        except:
            return "#95a5a6"  # Gray for unknown

    def get_rating_badge(rating):
        """Generate styled rating badge."""
        color_map = {
            "Extreme Fear": "#e74c3c",
            "Fear": "#f39c12", 
            "Neutral": "#f1c40f",
            "Greed": "#27ae60",
            "Extreme Greed": "#2ecc71"
        }
        color = color_map.get(rating, "#95a5a6")
        return f'<span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">{rating}</span>'

    html = """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: white; text-align: center; margin-bottom: 20px; font-size: 24px;">📊 Market Sentiment Analysis</h3>
        <div style="background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <table style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white;">
                        <th style="padding: 15px; text-align: left; font-weight: 600;">Metric</th>
                        <th style="padding: 15px; text-align: left; font-weight: 600;">Interpretation</th>
                        <th style="padding: 15px; text-align: center; font-weight: 600;">Score</th>
                        <th style="padding: 15px; text-align: center; font-weight: 600;">Rating</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, (metric, values) in enumerate(cnnMetricData.items()):
        row_bg = "#f8f9fa" if i % 2 == 0 else "white"
        score = values.get('score', '--')
        rating = values.get('rating', '--')
        score_color = get_score_color(score)
        
        html += f"""
                    <tr style="background-color: {row_bg}; transition: background-color 0.3s ease;">
                        <td style="padding: 15px; font-weight: 600; color: #2c3e50; border-bottom: 1px solid #ecf0f1;">
                            {metric.replace('_', ' ').title()}
                        </td>
                        <td style="padding: 15px; color: #5d6d7e; font-size: 14px; border-bottom: 1px solid #ecf0f1;">
                            {metric_meanings.get(metric, '--')}
                        </td>
                        <td style="padding: 15px; text-align: center; border-bottom: 1px solid #ecf0f1;">
                            <span style="background-color: {score_color}; color: white; padding: 8px 15px; border-radius: 25px; font-weight: bold; font-size: 16px;">
                                {score}
                            </span>
                        </td>
                        <td style="padding: 15px; text-align: center; border-bottom: 1px solid #ecf0f1;">
                            {get_rating_badge(rating)}
                        </td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    return html


def generate_enhanced_html_metrics_table(all_data):
    """
    Generate an enhanced HTML table for key metrics with modern styling and visual indicators.
    """
    key_metrics = ["Ticker", "Current Price", "Analyst Price Target", "P/E Ratio", "Forward P/E", "PEG Ratio", "EPS", "ROE", "P/B Ratio", "P/S Ratio", "Profit Margin"]
    
    def get_metric_color(metric, value_str):
        """Get color coding for different metrics."""
        try:
            # Extract numeric value from string
            import re
            numbers = re.findall(r'-?\d+\.?\d*', value_str.replace('%', ''))
            if not numbers:
                return "#95a5a6"
            
            value = float(numbers[0])
            
            if "P/E" in metric:
                if value < 15: return "#27ae60"  # Good
                elif value < 25: return "#f39c12"  # Moderate
                else: return "#e74c3c"  # High
            elif "ROE" in metric or "Profit Margin" in metric:
                if value > 15: return "#27ae60"  # Good
                elif value > 5: return "#f39c12"  # Moderate
                else: return "#e74c3c"  # Low
            elif "PEG" in metric:
                if value < 1: return "#27ae60"  # Good
                elif value < 2: return "#f39c12"  # Moderate
                else: return "#e74c3c"  # High
        except:
            pass
        return "#34495e"  # Default

    html = """
    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: white; text-align: center; margin-bottom: 20px; font-size: 24px;">📈 Key Financial Metrics</h3>
        <div style="background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-width: 800px;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white;">
    """
    
    for metric in key_metrics:
        html += f'<th style="padding: 15px; text-align: left; font-weight: 600; white-space: nowrap;">{metric}</th>'
    
    html += """
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for i, (ticker, data) in enumerate(all_data.items()):
        row_bg = "#f8f9fa" if i % 2 == 0 else "white"
        html += f'<tr style="background-color: {row_bg}; transition: background-color 0.3s ease;">'
        
        # Ticker column with special styling
        html += f'''
            <td style="padding: 15px; border-bottom: 1px solid #ecf0f1;">
                <span style="background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                    {ticker}
                </span>
            </td>
        '''
        
        for metric in key_metrics[1:]:  # Skip ticker
            value = get_all_sources_data(data, metric)
            # Add bullet points for each line
            if value != "--":
                # Split by ", " (which is replaced by <br>), then join with <br>• 
                lines = value.split(", ")
                if len(lines) > 1:
                    clean_value = "• " + "<br>• ".join(lines)
                else:
                    clean_value = "• " + lines[0]
            else:
                clean_value = '<span style="color: #95a5a6;">--</span>'
            color = get_metric_color(metric, value)
            
            html += f'''
                <td style="padding: 15px; border-bottom: 1px solid #ecf0f1; color: {color}; font-weight: 500;">
                    {clean_value}
                </td>
            '''
    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return html

def generate_combined_analysis_section(all_data):
    """
    Generate a combined Technical and Sentiment Analysis section with side-by-side layout.
    Responsive design: side-by-side on wide screens, stacked on mobile.
    """
    if not all_data:
        return ""
    
    # Helper functions for Technical Analysis
    def get_signal_badge(signal):
        """Generate styled signal badge."""
        if not signal or signal == "--" or signal == "":
            return '<span style="color: #95a5a6;">--</span>'
        
        signal_lower = str(signal).lower()
        if "bullish" in signal_lower or "buy" in signal_lower:
            color = "#27ae60"
            icon = "📈"
        elif "bearish" in signal_lower or "sell" in signal_lower:
            color = "#e74c3c" 
            icon = "📉"
        elif "overbought" in signal_lower:
            color = "#f39c12"
            icon = "⚠️"
        elif "oversold" in signal_lower:
            color = "#3498db"
            icon = "💡"
        else:
            color = "#95a5a6"
            icon = "➖"
        
        return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 15px; font-size: 11px; font-weight: bold;">{icon} {signal}</span>'
    
    def get_rsi_visual(rsi_value):
        """Generate RSI visual indicator."""
        try:
            if rsi_value == "--" or rsi_value == "" or rsi_value is None:
                return '<span style="color: #95a5a6;">No RSI Data Available</span>'
            
            rsi = float(rsi_value)
            if rsi >= 70:
                color = "#e74c3c"
                status = "Overbought"
            elif rsi <= 30:
                color = "#3498db" 
                status = "Oversold"
            else:
                color = "#27ae60"
                status = "Normal"
            
            percentage = min(rsi, 100)
            return f'''
                <div style="background: #ecf0f1; border-radius: 10px; height: 20px; position: relative; margin: 5px 0;">
                    <div style="background: {color}; height: 100%; width: {percentage}%; border-radius: 10px; position: relative;">
                        <span style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); color: white; font-size: 11px; font-weight: bold;">
                            {rsi:.1f}
                        </span>
                    </div>
                    <div style="text-align: center; font-size: 11px; color: {color}; font-weight: bold; margin-top: 2px;">
                        {status}
                    </div>
                </div>
            '''
        except:
            return f'<span style="color: #95a5a6;">Invalid RSI: {rsi_value}</span>'
    
    def find_matching_key(data, patterns):
        """Find the first key that matches any of the patterns."""
        for pattern in patterns:
            for key in data.keys():
                if pattern.lower() in key.lower():
                    return data[key]
        return "--"
    
    # Helper functions for Sentiment Analysis
    def get_sentiment_color(score):
        """Get color based on sentiment score."""
        try:
            score_float = float(str(score).replace('%', '').replace('--', '0'))
            if score_float > 0.1:
                return "#27ae60"  # Green for positive
            elif score_float < -0.1:
                return "#e74c3c"  # Red for negative
            else:
                return "#f39c12"  # Orange for neutral
        except:
            return "#95a5a6"  # Gray for invalid
    
    def get_sentiment_emoji(label):
        """Get emoji based on sentiment label."""
        if "Positive" in str(label):
            return "😊"
        elif "Negative" in str(label):
            return "😟"
        else:
            return "😐"
    
    def get_trend_arrow(direction):
        """Get arrow based on trend direction."""
        if "Increasing" in str(direction):
            return "📈"
        elif "Decreasing" in str(direction):
            return "📉"
        else:
            return "➖"
    
    def safe_get_enhanced_value(data, patterns, default="--"):
        """Safely get enhanced sentiment data from dictionary."""
        for pattern in patterns:
            for key, value in data.items():
                if pattern.lower() in key.lower() and "enhanced" in key.lower():
                    return value
        return default
    
    def format_score(value, decimals=2):
        """Format score value with proper decimal places."""
        try:
            if value == "--" or value is None:
                return "--"
            return f"{float(value):.{decimals}f}"
        except:
            return str(value)
    
    def format_topics(topic_str):
        """Format topics for display."""
        if topic_str == "--" or not topic_str:
            return "No data"
        topics = str(topic_str).split(", ")
        return ", ".join(topics[:3]) if len(topics) > 3 else topic_str
    
    # Helper function for formatting volume
    def format_volume(volume_str):
        try:
            if volume_str == "--" or volume_str == "" or volume_str is None:
                return "--"
            clean_volume = str(volume_str).replace(',', '').replace(' ', '')
            volume_num = int(float(clean_volume))
            return f"{volume_num:,}"
        except (ValueError, TypeError):
            return str(volume_str) if volume_str not in ["--", "", None] else "--"
    
    # Start building the HTML
    html = """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: white; text-align: center; margin-bottom: 20px; font-size: 24px;">📊 Comprehensive Market Analysis</h3>
    """
    
    for ticker, data in all_data.items():
        # Extract Technical Analysis data
        current_price = find_matching_key(data, ['current price', 'price'])
        rsi_value = find_matching_key(data, ['rsi (14)', 'rsi'])
        rsi_signal = find_matching_key(data, ['rsi signal'])
        volume = find_matching_key(data, ['current volume', 'volume'])
        obv_trend = find_matching_key(data, ['obv trend', 'obv'])
        
        # Moving averages with signals
        ma10_value = find_matching_key(data, ['ma10 (technical)', 'ma10'])
        ma20_value = find_matching_key(data, ['ma20 (technical)', 'ma20'])
        ma50_value = find_matching_key(data, ['ma50 (technical)', 'ma50'])
        ma100_value = find_matching_key(data, ['ma100 (technical)', 'ma100'])

        ma10_signal = find_matching_key(data, ['ma10 signal'])
        ma20_signal = find_matching_key(data, ['ma20 signal'])
        ma50_signal = find_matching_key(data, ['ma50 signal'])
        ma100_signal = find_matching_key(data, ['ma100 signal'])

        # Exponential Moving Averages
        ema12_value = find_matching_key(data, ['ema12 (technical)', 'ema12'])
        ema26_value = find_matching_key(data, ['ema26 (technical)', 'ema26'])
        ema50_value = find_matching_key(data, ['ema50 (technical)', 'ema50'])
        
        # Bollinger Bands
        bb_percentB_value = find_matching_key(data, ['BB %B (Technical)', 'BB %B'])
        bb_lower_value = find_matching_key(data, ['BB Lower Band (Technical)', 'BB Lower'])
        bb_upper_value = find_matching_key(data, ['BB Upper Band (Technical)', 'BB Upper'])
        bb_middle_value = find_matching_key(data, ['BB Middle Band (Technical)', 'BB Middle'])
        bb_signal_value = find_matching_key(data, ['BB Signal (Technical)', 'BB Signal'])
        bb_width_value = find_matching_key(data, ['BB Width (%) (Technical)', 'BB Width'])
        
        # Performance metrics
        sharpe_ratio = find_matching_key(data, ['sharpe ratio'])
        sortino_ratio = find_matching_key(data, ['sortino ratio'])
        annual_return = find_matching_key(data, ['annualized return', 'annual return'])
        volatility = find_matching_key(data, ['annualized volatility', 'volatility'])
        
        # Extract Sentiment Analysis data
        overall_score = safe_get_enhanced_value(data, ['overall sentiment score'])
        overall_label = safe_get_enhanced_value(data, ['overall sentiment label'])
        confidence = safe_get_enhanced_value(data, ['sentiment confidence'])
        sentiment_strength = "Strong" if abs(float(overall_score) if overall_score != "--" else 0) > 0.5 else "Moderate" if abs(float(overall_score) if overall_score != "--" else 0) > 0.1 else "Weak"
        
        # Google Trends
        trends_interest = safe_get_enhanced_value(data, ['google trends interest'])
        trends_direction = safe_get_enhanced_value(data, ['trends direction'])
        avg_interest = safe_get_enhanced_value(data, ['avg interest'])
        
        # News Analysis
        news_articles = safe_get_enhanced_value(data, ['news articles analyzed'])
        news_sentiment = safe_get_enhanced_value(data, ['news sentiment score'])
        positive_news = safe_get_enhanced_value(data, ['positive news articles'])
        negative_news = safe_get_enhanced_value(data, ['negative news articles'])
        finbert_score = safe_get_enhanced_value(data, ['finbert news score'])
        
        # Reddit Analysis
        reddit_posts = safe_get_enhanced_value(data, ['reddit posts analyzed'])
        reddit_sentiment = safe_get_enhanced_value(data, ['reddit sentiment score'])
        reddit_score = safe_get_enhanced_value(data, ['reddit avg score'])
        reddit_comments = safe_get_enhanced_value(data, ['reddit avg comments'])
        positive_reddit = safe_get_enhanced_value(data, ['positive reddit posts'])
        
        # Topic Analysis
        topic1 = safe_get_enhanced_value(data, ['top topic 1 keywords'])
        topic2 = safe_get_enhanced_value(data, ['top topic 2 keywords'])
        doc_similarity = safe_get_enhanced_value(data, ['document similarity'])

        html += f"""
        <div style="background: white; border-radius: 15px; padding: 0; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden;">
            <!-- Header with Ticker -->
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #f8f9fa, white);">
                <span style="background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 12px 30px; border-radius: 30px; font-size: 22px; font-weight: bold; box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3); display: inline-block;">
                    {ticker} - ${current_price}
                </span>
            </div>
            
            <!-- Container for side-by-side layout - TRUE 50/50 Split -->
            <div style="display: flex; width: 100%; margin: 0;">
                
                <!-- Technical Analysis Section (Left - Exactly 50%) -->
                <div style="width: 50%; box-sizing: border-box;">
                    <div style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); padding: 20px; height: 100%;">
                        <h4 style="color: white; margin: 0 0 20px 0; text-align: center; font-size: 18px; font-weight: bold;">
                            🔍 Technical Analysis
                        </h4>
                        
                        <div style="background: white; border-radius: 8px; padding: 15px; max-height: 650px; overflow-y: auto;">
                            <!-- RSI Analysis -->
                            <div style="margin-bottom: 15px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">📊 RSI Analysis</h5>
                                {get_rsi_visual(rsi_value)}
                                <div style="text-align: center; margin-top: 5px;">
                                    {get_signal_badge(rsi_signal)}
                                </div>
                            </div>
                            
                            <!-- Volume & Momentum -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">📈 Volume & Momentum</h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>Volume: <strong style="color: #3498db;">{format_volume(volume)}</strong></div>
                                    <div>OBV Trend: {get_signal_badge(obv_trend)}</div>
                                </div>
                            </div>
                            
                            <!-- Bollinger Bands -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">🎯 Bollinger Bands</h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>BB %B: <strong>{bb_percentB_value}</strong></div>
                                    <div>BB Lower: <strong>${bb_lower_value}</strong></div>
                                    <div>BB Upper: <strong>${bb_upper_value}</strong></div>
                                    <div>BB Middle: <strong>${bb_middle_value}</strong></div>
                                    <div>BB Signal: {get_signal_badge(bb_signal_value)}</div>
                                    <div>BB Width: <strong>{bb_width_value}%</strong></div>
                                </div>
                            </div>
                            
                            <!-- Exponential Moving Averages -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">⚡ Exponential Moving Averages</h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>EMA12: <strong>${ema12_value}</strong></div>
                                    <div>EMA26: <strong>${ema26_value}</strong></div>
                                    <div>EMA50: <strong>${ema50_value}</strong></div>
                                </div>
                            </div>
                            
                            <!-- Simple Moving Averages -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">📉 Moving Averages</h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>MA10: <strong>${ma10_value}</strong> {get_signal_badge(ma10_signal)}</div>
                                    <div>MA20: <strong>${ma20_value}</strong> {get_signal_badge(ma20_signal)}</div>
                                    <div>MA50: <strong>${ma50_value}</strong> {get_signal_badge(ma50_signal)}</div>
                                    <div>MA100: <strong>${ma100_value}</strong> {get_signal_badge(ma100_signal)}</div>
                                </div>
                            </div>
                            
                            <!-- Performance Metrics -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">🎯 Performance Metrics</h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>Sharpe Ratio: <strong style="color: #27ae60;">{sharpe_ratio}</strong></div>
                                    <div>Sortino Ratio: <strong style="color: #27ae60;">{sortino_ratio}</strong></div>
                                    <div>Annual Return: <strong style="color: #e74c3c;">{annual_return}</strong></div>
                                    <div>Volatility: <strong style="color: #f39c12;">{volatility}</strong></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sentiment Analysis Section (Right - Exactly 50%) -->
                <div style="width: 50%; box-sizing: border-box;">
                    <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 20px; height: 100%;">
                        <h4 style="color: white; margin: 0 0 20px 0; text-align: center; font-size: 18px; font-weight: bold;">
                            🧠 Sentiment Analysis {get_sentiment_emoji(overall_label)}
                        </h4>
                        
                        <div style="background: white; border-radius: 8px; padding: 15px; max-height: 650px; overflow-y: auto;">
                            <!-- Overall Sentiment -->
                            <div style="margin-bottom: 15px; text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <span style="background-color: {get_sentiment_color(overall_score)}; color: white; padding: 8px 15px; border-radius: 20px; font-size: 14px; font-weight: bold;">
                                    {overall_label} ({format_score(overall_score, 3)})
                                </span>
                                <div style="font-size: 11px; color: #7f8c8d; margin-top: 8px;">
                                    Confidence: {format_score(confidence, 3)} | Strength: {sentiment_strength}
                                </div>
                            </div>
                            
                            <!-- Market Trends -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">
                                    📊 Market Trends (0-100) {get_trend_arrow(trends_direction)}
                                </h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>Latest Interest Level: <strong style="font-size: 16px; color: #2c3e50;">{trends_interest}</strong></div>
                                    <div>Average Interest Over Time: <strong>{format_score(avg_interest, 1)}</strong> | Interest Direction: <strong>{trends_direction}</strong></div>
                                    <div style="color: #7f8c8d; font-style: italic; margin-top: 5px;">
                                        📌 >50 = above avg attention
                                    </div>
                                </div>
                            </div>
                            
                            <!-- News Sentiment -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">
                                    📰 News Sentiment (-1 to +1)
                                </h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>Articles Analyzed: <strong>{news_articles}</strong></div>
                                    <div>VADER: <span style="color: {get_sentiment_color(news_sentiment)}; font-weight: bold;">{format_score(news_sentiment, 3)}</span></div>
                                    <div>FinBERT: <span style="color: {get_sentiment_color(finbert_score)}; font-weight: bold;">{format_score(finbert_score, 3)}</span></div>
                                    <div style="margin-top: 5px;">
                                        <span style="color: #27ae60;">✓ {positive_news}</span> | 
                                        <span style="color: #e74c3c;">✗ {negative_news}</span>
                                    </div>
                                    <div style="color: #7f8c8d; font-style: italic; margin-top: 5px;">
                                        📌 VADER: General | FinBERT: Financial AI<br>
                                        >0.05 = Positive | <-0.05 = Negative
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Reddit Analysis -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">
                                    🔴 Reddit Analysis (-1 to +1)
                                </h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div>Posts Analyzed: <strong>{reddit_posts}</strong></div>
                                    <div>Sentiment: <span style="color: {get_sentiment_color(reddit_sentiment)}; font-weight: bold;">{format_score(reddit_sentiment, 3)}</span></div>
                                    <div>Avg Upvotes: <strong>{format_score(reddit_score, 1)}</strong> | Comments: <strong>{format_score(reddit_comments, 1)}</strong></div>
                                    <div style="color: #7f8c8d; font-style: italic; margin-top: 5px;">
                                        📌 Upvotes: >1000=viral, 100-1000=popular<br>
                                        Sentiment: >0.3=Very Bullish | <-0.1=Bearish
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Key Topics -->
                            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <h5 style="color: #34495e; margin: 0 0 10px 0; font-size: 13px;">
                                    🏷️ Key Topics (AI-detected)
                                </h5>
                                <div style="font-size: 11px; line-height: 1.8;">
                                    <div><strong>Topic 1:</strong> {format_topics(topic1)}</div>
                                    <div><strong>Topic 2:</strong> {format_topics(topic2)}</div>
                                    <div>Doc Similarity: <strong>{format_score(doc_similarity, 3)}</strong></div>
                                    <div style="color: #7f8c8d; font-style: italic; margin-top: 5px;">
                                        📌 Shows current discussion themes
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Summary Bar at Bottom - Full Width -->
            <div style="padding: 20px; background: linear-gradient(to bottom, #f8f9fa, white); border-top: 2px solid #ecf0f1;">
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px; text-align: center;">
                    <div style="flex: 1; min-width: 120px;">
                        <div style="font-size: 11px; color: #95a5a6; text-transform: uppercase; font-weight: 600;">Technical Signal</div>
                        <div style="font-size: 15px; font-weight: bold; color: #2c3e50; margin-top: 5px;">
                            {rsi_signal if rsi_signal != "--" else "Neutral"}
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <div style="font-size: 11px; color: #95a5a6; text-transform: uppercase; font-weight: 600;">Sentiment Signal</div>
                        <div style="font-size: 15px; font-weight: bold; color: {get_sentiment_color(overall_score)}; margin-top: 5px;">
                            {overall_label}
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <div style="font-size: 11px; color: #95a5a6; text-transform: uppercase; font-weight: 600;">Market Trend</div>
                        <div style="font-size: 15px; font-weight: bold; color: #2c3e50; margin-top: 5px;">
                            {trends_direction}
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <div style="font-size: 11px; color: #95a5a6; text-transform: uppercase; font-weight: 600;">Combined Signal</div>
                        <div style="font-size: 15px; font-weight: bold; margin-top: 5px; padding: 5px 10px; border-radius: 20px; background: {'linear-gradient(135deg, #27ae60, #2ecc71)' if overall_label == 'Positive' and 'Bullish' in str(rsi_signal) else 'linear-gradient(135deg, #e74c3c, #c0392b)' if overall_label == 'Negative' and 'Bearish' in str(rsi_signal) else 'linear-gradient(135deg, #f39c12, #f1c40f)'}; color: white; display: inline-block;">
                            {'Strong Buy' if overall_label == 'Positive' and 'Bullish' in str(rsi_signal) else 'Strong Sell' if overall_label == 'Negative' and 'Bearish' in str(rsi_signal) else 'Hold/Mixed'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    html += """
    </div>
    
    <style>
        @media (max-width: 900px) {
            div[style*="display: flex"][style*="width: 100%"] {
                flex-direction: column !important;
            }
            div[style*="width: 50%"] {
                width: 100% !important;
            }
        }
    </style>
    """
    
    return html

def send_consolidated_report(tickers, report_paths, all_data, cnnMetricData, recipients, summary_path=None, cc=None, bcc=None):
    """
    Send a visually enhanced consolidated report email for multiple stocks using modern HTML formatting.
    
    Args:
        tickers (list): List of ticker symbols
        report_paths (dict): Dictionary with ticker symbols as keys and report file paths as values
        all_data (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        cnnMetricData (dict): Dictionary with CNN Fear and Greed Index data
        recipients (str or list): Recipient email address(es)
        summary_path (str, optional): Path to summary report file
        cc (str or list, optional): CC email address(es)
        bcc (str or list, optional): BCC email address(es)
        
    Returns:
        bool: True if successful, False otherwise
    """
    subject = f"📊 Stock Analysis Report: {', '.join(tickers)} - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Generate enhanced sections
    cnn_metrics_html = generate_enhanced_html_cnn_metrics_table(cnnMetricData)
    metrics_table_html = generate_enhanced_html_metrics_table(all_data)
    # Use the new combined analysis section instead of separate technical and sentiment
    combined_analysis_html = generate_combined_analysis_section(all_data)
    # Create the enhanced HTML email body
        
    email_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Analysis Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
                margin: 20px 0;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5rem;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            @media (max-width: 768px) {{
                body {{ padding: 10px; }}
                .header {{ padding: 20px 15px; }}
                .header h1 {{ font-size: 1.8rem; }}
                .content {{ padding: 20px 15px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Stock Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                <p>Automated Financial Intelligence Dashboard</p>
            </div>
            
            <div class="content">
                {cnn_metrics_html}
                
                {metrics_table_html}
                
                <!-- Combined Technical and Sentiment Analysis -->
                {combined_analysis_html}
                
                <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 25px; border-radius: 15px; margin: 20px 0; color: white; text-align: center;">
                    <h3 style="margin: 0 0 15px 0; font-size: 24px;">📎 Detailed Reports Attached</h3>
                    <p style="margin: 0; font-size: 16px;">Individual stock analysis reports and summary comparisons are included as attachments for deeper insights.</p>
                </div>
            </div>
            
            <div class="footer">
                <h3 style="margin: 0 0 10px 0;">📈 Stock Data Scraper Pro</h3>
                <p style="margin: 0; opacity: 0.8;">Powered by advanced financial analytics</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.6;">This is an automated report. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Prepare attachments
    attachments = list(report_paths.values())
    if summary_path:
        attachments.append(summary_path)
    
    # Debug info
    print(f"📧 Sending enhanced consolidated report with {len(attachments)} attachments")
    print(f"📬 Recipients: {recipients}")
    
    # Send email
    return send_email(
        recipients=recipients,
        subject=subject,
        body=email_body,
        attachment_paths=attachments,
        cc=cc,
        bcc=bcc,
        is_html=True
    )
