#!/usr/bin/env python3
"""
WA Government Job Ad Scraper
Scrapes job listings and downloads attachments (PDFs, Word docs, etc.)
"""

import os
import re
import json
import time
import hashlib
import logging
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 1.5
ATTACHMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.rtf', '.odt', '.txt'}


class JobScraper:
    def __init__(self, output_dir: str = 'scraped_jobs', delay: float = DELAY_BETWEEN_REQUESTS):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
        })
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'pages').mkdir(exist_ok=True)
        (self.output_dir / 'attachments').mkdir(exist_ok=True)
        
        # Track progress
        self.results = []
        
    def sanitise_filename(self, name: str, max_length: int = 100) -> str:
        """Create a safe filename from a string."""
        # Remove or replace invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe = re.sub(r'\s+', '_', safe)
        safe = re.sub(r'_+', '_', safe)
        safe = safe.strip('_.')
        
        if len(safe) > max_length:
            safe = safe[:max_length]
        
        return safe or 'unnamed'
    
    def extract_advert_id(self, url: str) -> str:
        """Extract the AdvertID from the URL."""
        match = re.search(r'AdvertID=(\d+)', url)
        return match.group(1) if match else hashlib.md5(url.encode()).hexdigest()[:10]
    
    def fetch_page(self, url: str) -> tuple[str | None, requests.Response | None]:
        """Fetch a webpage and return its HTML content."""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text, response
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None, None
    
    def find_attachments(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """Find all downloadable attachments on the page."""
        attachments = []
        
        # Look for links that might be attachments
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if it's a document link
            parsed = urlparse(full_url)
            path_lower = parsed.path.lower()
            
            # Check file extension
            is_attachment = any(path_lower.endswith(ext) for ext in ATTACHMENT_EXTENSIONS)
            
            # Also check for download links or document-related URLs
            if not is_attachment:
                if 'download' in href.lower() or 'attachment' in href.lower():
                    is_attachment = True
                elif 'document' in href.lower() and ('id=' in href.lower() or 'file' in href.lower()):
                    is_attachment = True
            
            if is_attachment:
                link_text = link.get_text(strip=True) or 'attachment'
                attachments.append({
                    'url': full_url,
                    'link_text': link_text,
                    'original_href': href
                })
        
        return attachments
    
    def download_attachment(self, url: str, save_dir: Path, prefix: str = '') -> dict | None:
        """Download an attachment and save it."""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()
            
            # Determine filename
            filename = None
            
            # Check Content-Disposition header
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                match = re.search(r'filename[*]?=["\']?(?:UTF-8\'\')?([^"\';\n]+)', cd)
                if match:
                    filename = unquote(match.group(1))
            
            # Fall back to URL path
            if not filename:
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path)
            
            # If still no filename, create one from content type
            if not filename or filename == '':
                content_type = response.headers.get('Content-Type', '')
                ext = '.bin'
                if 'pdf' in content_type:
                    ext = '.pdf'
                elif 'word' in content_type or 'msword' in content_type:
                    ext = '.doc'
                elif 'openxmlformats' in content_type and 'word' in content_type:
                    ext = '.docx'
                filename = f'attachment{ext}'
            
            # Sanitise and add prefix
            safe_filename = self.sanitise_filename(filename)
            if prefix:
                safe_filename = f"{prefix}_{safe_filename}"
            
            filepath = save_dir / safe_filename
            
            # Handle duplicates
            counter = 1
            original_stem = filepath.stem
            while filepath.exists():
                filepath = save_dir / f"{original_stem}_{counter}{filepath.suffix}"
                counter += 1
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {filepath.name}")
            return {
                'filename': filepath.name,
                'path': str(filepath),
                'size_bytes': filepath.stat().st_size,
                'url': url
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    
    def extract_job_content(self, soup: BeautifulSoup) -> dict:
        """Extract structured content from the job page."""
        content = {
            'title': '',
            'full_text': '',
            'sections': {}
        }
        
        # Try to find the job title
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            content['title'] = title_elem.get_text(strip=True)
        
        # Extract the main content area
        # WA Jobs portal typically has content in specific divs
        main_content = soup.find('div', {'class': re.compile(r'content|main|job', re.I)})
        if not main_content:
            main_content = soup.find('main') or soup.find('article') or soup.body
        
        if main_content:
            content['full_text'] = main_content.get_text(separator='\n', strip=True)
            
            # Try to extract labelled sections (e.g., "Position Title:", "Agency:", etc.)
            for text in main_content.stripped_strings:
                if ':' in text and len(text) < 200:
                    parts = text.split(':', 1)
                    if len(parts) == 2 and len(parts[0]) < 50:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value:
                            content['sections'][key] = value
        
        return content
    
    def scrape_job(self, url: str, job_title: str = '', row_index: int = 0) -> dict:
        """Scrape a single job listing."""
        result = {
            'url': url,
            'job_title': job_title,
            'row_index': row_index,
            'success': False,
            'error': None,
            'content': {},
            'attachments': [],
            'html_file': None
        }
        
        advert_id = self.extract_advert_id(url)
        safe_title = self.sanitise_filename(job_title) if job_title else f'job_{advert_id}'
        
        logger.info(f"[{row_index}] Scraping: {job_title or url}")
        
        # Fetch the page
        html, response = self.fetch_page(url)
        if not html:
            result['error'] = 'Failed to fetch page'
            return result
        
        # Parse the page
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save the HTML
        html_filename = f"{advert_id}_{safe_title}.html"
        html_path = self.output_dir / 'pages' / html_filename
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        result['html_file'] = str(html_path)
        
        # Extract content
        result['content'] = self.extract_job_content(soup)
        
        # Find and download attachments
        attachments = self.find_attachments(soup, url)
        attachment_dir = self.output_dir / 'attachments' / f"{advert_id}_{safe_title}"
        
        if attachments:
            attachment_dir.mkdir(parents=True, exist_ok=True)
            
            for att in attachments:
                time.sleep(0.5)  # Small delay between attachment downloads
                downloaded = self.download_attachment(
                    att['url'], 
                    attachment_dir,
                    prefix=advert_id
                )
                if downloaded:
                    downloaded['link_text'] = att['link_text']
                    result['attachments'].append(downloaded)
        
        result['success'] = True
        return result
    
    def scrape_from_excel(self, excel_path: str, url_column: str = 'Job URL', 
                          title_column: str = 'Job Title', limit: int = None,
                          start_from: int = 0):
        """Scrape all jobs from an Excel file."""
        logger.info(f"Loading jobs from {excel_path}")
        
        df = pd.read_excel(excel_path)
        total_jobs = len(df)
        
        if limit:
            df = df.iloc[start_from:start_from + limit]
        else:
            df = df.iloc[start_from:]
        
        logger.info(f"Scraping {len(df)} jobs (starting from {start_from}, total: {total_jobs})")
        
        for idx, row in df.iterrows():
            url = row.get(url_column, '')
            title = row.get(title_column, '')
            
            if not url or pd.isna(url):
                logger.warning(f"[{idx}] Skipping row with no URL")
                continue
            
            result = self.scrape_job(url, title, idx)
            self.results.append(result)
            
            # Save progress periodically
            if len(self.results) % 10 == 0:
                self.save_results()
            
            # Delay between requests
            time.sleep(self.delay)
        
        # Final save
        self.save_results()
        self.generate_summary()
        
        return self.results
    
    def save_results(self):
        """Save scraping results to JSON."""
        results_path = self.output_dir / 'scrape_results.json'
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Saved results to {results_path}")
    
    def generate_summary(self):
        """Generate a summary report."""
        successful = sum(1 for r in self.results if r['success'])
        failed = sum(1 for r in self.results if not r['success'])
        total_attachments = sum(len(r['attachments']) for r in self.results)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_jobs': len(self.results),
            'successful': successful,
            'failed': failed,
            'total_attachments': total_attachments,
            'failed_urls': [r['url'] for r in self.results if not r['success']]
        }
        
        summary_path = self.output_dir / 'summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"SCRAPING COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Total jobs processed: {len(self.results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Attachments downloaded: {total_attachments}")
        logger.info(f"Results saved to: {self.output_dir}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Scrape WA Government job ads')
    parser.add_argument('excel_file', help='Path to Excel file with job URLs')
    parser.add_argument('-o', '--output', default='scraped_jobs', help='Output directory')
    parser.add_argument('-l', '--limit', type=int, help='Limit number of jobs to scrape')
    parser.add_argument('-s', '--start', type=int, default=0, help='Start from row number')
    parser.add_argument('-d', '--delay', type=float, default=1.5, help='Delay between requests (seconds)')
    parser.add_argument('--url-column', default='Job URL', help='Column name containing URLs')
    parser.add_argument('--title-column', default='Job Title', help='Column name containing job titles')
    
    args = parser.parse_args()
    
    scraper = JobScraper(output_dir=args.output, delay=args.delay)
    scraper.scrape_from_excel(
        args.excel_file,
        url_column=args.url_column,
        title_column=args.title_column,
        limit=args.limit,
        start_from=args.start
    )


if __name__ == '__main__':
    main()
