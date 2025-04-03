#!/usr/bin/env python3
"""
Main entry point for the job application bot.
"""
import asyncio
import logging
import argparse
import re
import sys
from utils.logging_utils import setup_logging
from services.browser_service import browse_with_proxy
from config.settings import PROXIES

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def validate_lever_url(url):
    """
    Validate that the URL is a proper Lever job application URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        str: The validated URL if valid
        
    Raises:
        argparse.ArgumentTypeError: If the URL is invalid
    """
    # Pattern for Lever job application URLs
    pattern = r'^https://jobs\.lever\.co/[a-zA-Z0-9-_]+/[a-zA-Z0-9-]+/apply$'
    
    if not re.match(pattern, url):
        raise argparse.ArgumentTypeError(
            "Invalid Lever job URL format. URL must be in the format: "
            "https://jobs.lever.co/company/job-id/apply"
        )
    return url

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Lever Job Application Bot')
    parser.add_argument(
        '--url', 
        type=validate_lever_url,
        required=True,
        help='Target Lever job application URL (https://jobs.lever.co/company/job-id/apply)'
    )
    return parser.parse_args()

async def main():
    """Main function to run the job application bot."""
    # Parse arguments
    args = parse_arguments()
    target_url = args.url
    
    logger.info(f"Starting job application process for URL: {target_url}")
    
    is_success = False
    for proxy in PROXIES:
        try:
            logger.info(f"Attempting with proxy: {proxy['server']}")
            await browse_with_proxy(proxy, target_url)
            is_success = True
            break 
        except Exception as e:
            logger.warning(f"Failed with proxy {proxy['server']}: {str(e)}")
            logger.warning("Trying next proxy...")
            continue
    
    if is_success:
        logger.info("Successfully completed the job application process.")
    else:
        logger.error("All proxies have been tried without success.")

if __name__ == "__main__":
    asyncio.run(main())