#!/usr/bin/env python3
"""
Scrapy Website Content Extractor
Extracts content from a website URL using Scrapy and saves it to a JSON file.

Installation:
pip install scrapy

Usage:
python scrapy_extractor.py https://example.com
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
import sys
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

class WebContentSpider(scrapy.Spider):
    name = 'web_content'
    
    def __init__(self, start_url=None, output_file=None, *args, **kwargs):
        super(WebContentSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.output_file = output_file
        self.extracted_data = {}
        
    def start_requests(self):
        """Generate initial requests with custom headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                dont_filter=True,
                meta={'dont_retry': False}
            )
    
    def parse(self, response):
        """Parse the response and extract content"""
        try:
            base_url = response.url
            
            # Extract all content
            content = {
                'url': response.url,
                'extraction_date': datetime.now().isoformat(),
                'status_code': response.status,
                'title': self.extract_title(response),
                'meta_description': self.extract_meta_description(response),
                'meta_keywords': self.extract_meta_keywords(response),
                'headings': self.extract_headings(response),
                'paragraphs': self.extract_paragraphs(response),
                'links': self.extract_links(response, base_url),
                'images': self.extract_images(response, base_url),
                'text_content': self.extract_clean_text(response),
                'word_count': 0,
                'forms': self.extract_forms(response),
                'tables': self.extract_tables(response),
                'scripts': self.extract_scripts(response),
                'styles': self.extract_styles(response),
                'page_size': len(response.body),
                'encoding': response.encoding
            }
            
            # Calculate word count
            content['word_count'] = len(content['text_content'].split()) if content['text_content'] else 0
            
            # Store data
            self.extracted_data = content
            
            # Save to file
            self.save_to_json(content)
            
            # Print summary
            self.print_summary(content)
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            error_data = {
                'url': response.url,
                'error': f'Extraction failed: {str(e)}',
                'status_code': response.status,
                'extraction_date': datetime.now().isoformat()
            }
            self.extracted_data = error_data
            self.save_to_json(error_data)
    
    def extract_title(self, response):
        """Extract page title"""
        title = response.css('title::text').get()
        return title.strip() if title else ''
    
    def extract_meta_description(self, response):
        """Extract meta description"""
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        return meta_desc.strip() if meta_desc else ''
    
    def extract_meta_keywords(self, response):
        """Extract meta keywords"""
        meta_keywords = response.css('meta[name="keywords"]::attr(content)').get()
        return meta_keywords.strip() if meta_keywords else ''
    
    def extract_headings(self, response):
        """Extract all headings (h1-h6)"""
        headings = {}
        for i in range(1, 7):
            h_tags = response.css(f'h{i}::text').getall()
            headings[f'h{i}'] = [tag.strip() for tag in h_tags if tag.strip()]
        return headings
    
    def extract_paragraphs(self, response):
        """Extract all paragraph content"""
        paragraphs = response.css('p::text').getall()
        return [p.strip() for p in paragraphs if p.strip()]
    
    def extract_links(self, response, base_url):
        """Extract all links"""
        links = []
        for link in response.css('a'):
            href = link.css('::attr(href)').get()
            text = link.css('::text').get()
            
            if href:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                
                links.append({
                    'text': text.strip() if text else '',
                    'url': full_url,
                    'is_external': self.is_external_link(full_url, base_url)
                })
        
        return links
    
    def extract_images(self, response, base_url):
        """Extract all images"""
        images = []
        for img in response.css('img'):
            src = img.css('::attr(src)').get()
            alt = img.css('::attr(alt)').get()
            title = img.css('::attr(title)').get()
            
            if src:
                full_url = urljoin(base_url, src)
                images.append({
                    'src': full_url,
                    'alt': alt or '',
                    'title': title or ''
                })
        
        return images
    
    def extract_clean_text(self, response):
        """Extract clean text content"""
        # Remove script and style content
        text_content = response.css('body *:not(script):not(style)::text').getall()
        
        # Clean and join text
        clean_text = ' '.join([text.strip() for text in text_content if text.strip()])
        
        return clean_text
    
    def extract_forms(self, response):
        """Extract form information"""
        forms = []
        for form in response.css('form'):
            form_data = {
                'action': form.css('::attr(action)').get() or '',
                'method': (form.css('::attr(method)').get() or 'get').lower(),
                'inputs': []
            }
            
            for input_tag in form.css('input, textarea, select'):
                input_data = {
                    'type': input_tag.css('::attr(type)').get() or 'text',
                    'name': input_tag.css('::attr(name)').get() or '',
                    'placeholder': input_tag.css('::attr(placeholder)').get() or '',
                    'required': bool(input_tag.css('::attr(required)').get())
                }
                form_data['inputs'].append(input_data)
            
            forms.append(form_data)
        
        return forms
    
    def extract_tables(self, response):
        """Extract table data"""
        tables = []
        for table in response.css('table'):
            table_data = {'headers': [], 'rows': []}
            
            # Extract headers
            headers = table.css('th::text').getall()
            table_data['headers'] = [h.strip() for h in headers]
            
            # Extract rows
            for row in table.css('tr'):
                cells = row.css('td::text, th::text').getall()
                if cells:
                    row_data = [cell.strip() for cell in cells]
                    table_data['rows'].append(row_data)
            
            if table_data['rows']:  # Only add tables with content
                tables.append(table_data)
        
        return tables
    
    def extract_scripts(self, response):
        """Extract script tags information"""
        scripts = []
        for script in response.css('script'):
            src = script.css('::attr(src)').get()
            script_type = script.css('::attr(type)').get()
            
            script_info = {
                'src': src,
                'type': script_type,
                'inline': src is None
            }
            scripts.append(script_info)
        
        return scripts
    
    def extract_styles(self, response):
        """Extract stylesheet information"""
        styles = []
        for link in response.css('link[rel="stylesheet"]'):
            href = link.css('::attr(href)').get()
            media = link.css('::attr(media)').get()
            
            if href:
                styles.append({
                    'href': urljoin(response.url, href),
                    'media': media or 'all'
                })
        
        return styles
    
    def is_external_link(self, url, base_url):
        """Check if a link is external"""
        return urlparse(url).netloc != urlparse(base_url).netloc
    
    def save_to_json(self, content):
        """Save extracted content to JSON file"""
        if self.output_file:
            filename = self.output_file
        else:
            # Generate filename from URL
            parsed_url = urlparse(content.get('url', ''))
            domain = parsed_url.netloc.replace('www.', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"\nContent saved to: {filename}")
        except Exception as e:
            self.logger.error(f"Error saving file: {str(e)}")
    
    def print_summary(self, content):
        """Print extraction summary"""
        print(f"\n{'='*60}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"URL: {content['url']}")
        print(f"Status: {content['status_code']}")
        print(f"Title: {content['title']}")
        print(f"Word count: {content['word_count']}")
        print(f"Links found: {len(content['links'])}")
        print(f"Images found: {len(content['images'])}")
        print(f"Forms found: {len(content['forms'])}")
        print(f"Tables found: {len(content['tables'])}")
        print(f"Page size: {content['page_size']} bytes")
        print(f"Encoding: {content['encoding']}")
        print(f"{'='*60}")

def main():
    """Main function to run the extractor"""
    if len(sys.argv) < 2:
        print("Usage: python scrapy_extractor.py <URL> [output_file]")
        print("Example: python scrapy_extractor.py https://example.com")
        print("Example: python scrapy_extractor.py https://example.com output.json")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"Extracting content from: {url}")
    print("Using Scrapy for robust web scraping...")
    
    # Configure Scrapy settings
    settings = get_project_settings()
    settings.setdict({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for this scraper
        'DOWNLOAD_DELAY': 1,  # Delay between requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Randomize delay (0.5-1.5 * DOWNLOAD_DELAY)
        'CONCURRENT_REQUESTS': 1,  # Only one request at a time
        'COOKIES_ENABLED': True,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'WARNING',  # Reduce scrapy logging
        'RETRY_TIMES': 3,  # Retry failed requests
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 3,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    })
    
    # Create and run the spider
    process = CrawlerProcess(settings)
    process.crawl(WebContentSpider, start_url=url, output_file=output_file)
    process.start()

if __name__ == "__main__":
    main()