#!/usr/bin/env python3
"""
Keep-Alive Service for Render.com Free Tier
Pings the server every 10 minutes to prevent spin-down
"""
import requests
import time
from datetime import datetime
import logging

# Configuration
SERVER_URL = "https://finance-web-scrapper.onrender.com"
PING_INTERVAL = 600  # 10 minutes in seconds (Render spins down after 15 min inactivity)
HEALTH_ENDPOINT = "/health"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ping_server():
    """Send a ping to the server health endpoint"""
    try:
        url = f"{SERVER_URL}{HEALTH_ENDPOINT}"
        logger.info(f"Pinging server: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"✓ Server is alive - Status: {response.status_code}")
            return True
        else:
            logger.warning(f"⚠ Server responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("✗ Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("✗ Connection error - Server might be spinning up")
        return False
    except Exception as e:
        logger.error(f"✗ Error pinging server: {e}")
        return False


def keep_alive():
    """Main loop to keep server alive"""
    logger.info("=" * 60)
    logger.info("Keep-Alive Service Started")
    logger.info(f"Server URL: {SERVER_URL}")
    logger.info(f"Ping Interval: {PING_INTERVAL} seconds ({PING_INTERVAL/60} minutes)")
    logger.info("=" * 60)
    
    ping_count = 0
    success_count = 0
    
    while True:
        try:
            ping_count += 1
            logger.info(f"\n--- Ping #{ping_count} ---")
            
            if ping_server():
                success_count += 1
            
            logger.info(f"Success rate: {success_count}/{ping_count} ({(success_count/ping_count)*100:.1f}%)")
            logger.info(f"Next ping in {PING_INTERVAL/60} minutes...")
            
            # Sleep until next ping
            time.sleep(PING_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("Keep-Alive Service Stopped")
            logger.info(f"Total pings: {ping_count}")
            logger.info(f"Successful pings: {success_count}")
            logger.info(f"Success rate: {(success_count/ping_count)*100:.1f}%")
            logger.info("=" * 60)
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.info("Continuing...")
            time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    keep_alive()
