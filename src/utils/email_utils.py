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
            clean_value = value.replace(", ", "<br>")
            color = get_metric_color(metric, value)
            
            html += f'''
                <td style="padding: 15px; border-bottom: 1px solid #ecf0f1; color: {color}; font-weight: 500;">
                    {clean_value if clean_value != "--" else '<span style="color: #95a5a6;">--</span>'}
                </td>
            '''
        
        html += "</tr>"
    
    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return html

def generate_enhanced_technical_analysis_section(all_data):
    """
    Generate enhanced technical analysis section with visual indicators.
    """
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

    def format_volume(volume_str):
        """Format volume string with proper comma separation."""
        try:
            if volume_str == "--" or volume_str == "" or volume_str is None:
                return "--"
            # Remove any existing commas and convert to float, then to int
            clean_volume = str(volume_str).replace(',', '').replace(' ', '')
            volume_num = int(float(clean_volume))
            return f"{volume_num:,}"
        except (ValueError, TypeError):
            return str(volume_str) if volume_str not in ["--", "", None] else "--"

    def safe_get_data(data, key, default="--"):
        """Safely get data from dictionary with fallback."""
        return data.get(key, default) if data.get(key) not in [None, "", "--"] else default

    def find_matching_key(data, patterns):
        """Find the first key that matches any of the patterns."""
        for pattern in patterns:
            for key in data.keys():
                if pattern.lower() in key.lower():
                    return data[key]
        return "--"

    html = """
    <div style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: white; text-align: center; margin-bottom: 20px; font-size: 24px;">🔍 Technical Analysis Overview</h3>
    """
    
    # Debug: Print available keys for first ticker
    if all_data:
        first_ticker = list(all_data.keys())[0]
        print(f"DEBUG: Available keys for {first_ticker}:")
        for key in sorted(all_data[first_ticker].keys()):
            print(f"  - {key}")
    
    for ticker, data in all_data.items():
        # Use flexible key matching to find the right data
        current_price = find_matching_key(data, ['current price', 'price'])
        rsi_value = find_matching_key(data, ['rsi (14)', 'rsi'])
        rsi_signal = find_matching_key(data, ['rsi signal'])
        volume = find_matching_key(data, ['current volume', 'volume'])
        obv_trend = find_matching_key(data, ['obv trend', 'obv'])
        
        # Get moving average data
        ma10_value = find_matching_key(data, ['ma10 (technical)', 'ma10'])
        ma20_value = find_matching_key(data, ['ma20 (technical)', 'ma20'])
        ma50_value = find_matching_key(data, ['ma50 (technical)', 'ma50'])
        ma100_value = find_matching_key(data, ['ma100 (technical)', 'ma100'])
        
        ma10_signal = find_matching_key(data, ['ma10 signal'])
        ma20_signal = find_matching_key(data, ['ma20 signal'])
        ma50_signal = find_matching_key(data, ['ma50 signal'])
        ma100_signal = find_matching_key(data, ['ma100 signal'])

        
        # Get Exponential Moving Averages (EMA) if available. EMA is more responsive to recent price changes.
        ema12_value = find_matching_key(data, ['ema12 (technical)', 'ema10'])
        ema26_value = find_matching_key(data, ['ema26 (technical)', 'ema20'])
        ema50_value = find_matching_key(data, ['ema50 (technical)', 'ema50'])
        
        # Get Bollinger Bands if available
        bb_percentB_value = find_matching_key(data, ['BB %B (Technical)', 'BB %B']) # current price relative to the band
        bb_lower_value = find_matching_key(data, ['BB Lower Band (Technical)', 'BB Lower']) # formula = middle band - K*Standard Deviation where k = 2 default multipler
        bb_upper_value = find_matching_key(data, ['BB Upper Band (Technical)', 'BB Upper']) # formula = middle band + K*Standard Deviation where k = 2 default multipler
        bb_middle_value = find_matching_key(data, ['BB Middle (Technical)', 'BB Middle']) # equivalent to the 20-day SMA
        bb_signal_value = find_matching_key(data, ['BB Signal (Technical)', 'BB Signal']) # buy when price below lower band, sell when above upper band
        bb_width_value = find_matching_key(data, ['BB Width (Technical)', 'BB Width']) # relative width of the bands, wider bands indicate higher volatility. Low volatility often precede a breakout

        # Get additional technical indicators
        sharpe_ratio = find_matching_key(data, ['sharpe ratio'])
        sortino_ratio = find_matching_key(data, ['sortino ratio'])
        annual_return = find_matching_key(data, ['annualized return', 'annual return'])
        volatility = find_matching_key(data, ['annualized volatility', 'volatility'])
        
        html += f"""
        <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap;">
                <h4 style="color: #2c3e50; margin: 0; font-size: 20px;">
                    <span style="background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 8px 15px; border-radius: 20px; font-size: 16px;">
                        {ticker}
                    </span>
                </h4>
                <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">
                    ${current_price}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">📊 RSI Analysis</h5>
                    {get_rsi_visual(rsi_value)}
                    <div style="text-align: center; margin-top: 5px;">
                        {get_signal_badge(rsi_signal)}
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">📈 Volume & Momentum</h5>
                    <div style="margin-bottom: 8px;">
                        <strong>Volume:</strong> <span style="color: #3498db;">{format_volume(volume)}</span>
                    </div>
                    <div>
                        <strong>OBV Trend:</strong> {get_signal_badge(obv_trend)}
                    </div>
                </div>
                 <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">📉 Exponential Moving Averages</h5>
                    <div style="font-size: 12px; line-height: 1.4;">
                        <div><strong>BB Percent B(current price relative to the band) (<0 : oversold) (>1 : overbought):</strong> ${bb_percentB_value}</div>
                        <div><strong>BB Lower Band:</strong> ${bb_lower_value}</div>
                        <div><strong>BB Upper Band:</strong> ${bb_upper_value}</div>
                        <div><strong>BB Middle:</strong> ${bb_middle_value}</div>
                        <div><strong>BB Signal:</strong> ${bb_signal_value}</div>
                        <div><strong>BB Width:</strong> ${bb_width_value}</div>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">📉 Exponential Moving Averages</h5>
                    <div style="font-size: 12px; line-height: 1.4;">
                        <div><strong>EMA12:</strong> ${ema12_value}</div>
                        <div><strong>EMA26:</strong> ${ema26_value}</div>
                        <div><strong>EMA50:</strong> ${ema50_value}</div>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">📉 Moving Averages</h5>
                    <div style="font-size: 12px; line-height: 1.4;">
                        <div><strong>MA10:</strong> ${ma10_value} {get_signal_badge(ma10_signal)}</div>
                        <div><strong>MA20:</strong> ${ma20_value} {get_signal_badge(ma20_signal)}</div>
                        <div><strong>MA50:</strong> ${ma50_value} {get_signal_badge(ma50_signal)}</div>
                        <div><strong>MA100:</strong> ${ma100_value} {get_signal_badge(ma100_signal)}</div>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h5 style="color: #34495e; margin: 0 0 10px 0;">🎯 Performance Metrics</h5>
                    <div style="font-size: 12px; line-height: 1.4;">
                        <div><strong>Sharpe Ratio:</strong> <span style="color: #27ae60;">{sharpe_ratio}</span></div>
                        <div><strong>Sortino Ratio:</strong> <span style="color: #27ae60;">{sortino_ratio}</span></div>
                        <div><strong>Annual Return:</strong> <span style="color: #e74c3c;">{annual_return}</span></div>
                        <div><strong>Volatility:</strong> <span style="color: #f39c12;">{volatility}</span></div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

# 
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
    technical_analysis_html = generate_enhanced_technical_analysis_section(all_data)
    
    # Create the enhanced HTML email body
    body = f"""
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
            .alert {{
                background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .footer a {{
                color: #74b9ff;
                text-decoration: none;
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
                <div class="alert">
                    <h3 style="margin: 0 0 10px 0;">🚀 Market Intelligence Report Ready</h3>
                    <p style="margin: 0;">This comprehensive analysis includes market sentiment, technical indicators, and financial metrics for informed investment decisions.</p>
                </div>
                
                {cnn_metrics_html}
                
                {metrics_table_html}
                
                {technical_analysis_html}
                
                <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 25px; border-radius: 15px; margin: 20px 0; color: white; text-align: center;">
                    <h3 style="margin: 0 0 15px 0; font-size: 24px;">📎 Detailed Reports Attached</h3>
                    <p style="margin: 0; font-size: 16px;">Individual stock analysis reports and summary comparisons are included as attachments for deeper insights.</p>
                    {f'<p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">📋 Summary comparison report included</p>' if summary_path else ''}
                </div>
                
                <div style="background: #f8f9fa; border-left: 4px solid #6c5ce7; padding: 20px; margin: 20px 0;">
                    <h4 style="color: #2c3e50; margin: 0 0 10px 0;">ℹ️ Important Notes:</h4>
                    <ul style="color: #5d6d7e; margin: 0; padding-left: 20px;">
                        <li>All technical indicators are calculated based on recent market data</li>
                        <li>CNN Fear & Greed Index provides market sentiment context</li>
                        <li>Consider multiple factors before making investment decisions</li>
                        <li>Past performance does not guarantee future results</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <h3 style="margin: 0 0 10px 0;">📈 Stock Data Scraper Pro</h3>
                <p style="margin: 0; opacity: 0.8;">Powered by advanced financial analytics • <a href="https://money.cnn.com/data/fear-and-greed/">CNN Fear & Greed Index</a></p>
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
        body=body,
        attachment_paths=attachments,
        cc=cc,
        bcc=bcc,
        is_html=True
    )
