# -*- coding: utf-8 -*-
"""
Example custom spider for Arachnado.

This spider demonstrates how to create a custom spider that:
- Inherits from ArachnadoSpider for better integration
- Uses the domain parameter provided by Arachnado
- Accepts custom arguments
- Implements custom parsing logic
"""
from __future__ import absolute_import
import scrapy
from arachnado.spider import ArachnadoSpider


class ExampleCustomSpider(ArachnadoSpider):
    """
    An example custom spider that extracts specific elements from pages.
    
    This spider can be used with Arachnado by:
    1. Installing this package or adding it to PYTHONPATH
    2. Configuring spider_packages in arachnado.conf:
       [arachnado.scrapy]
       spider_packages = examples.custom_spiders
    3. Starting a crawl with: spider://example
    """
    name = 'example'
    
    custom_settings = {
        'DEPTH_LIMIT': 5,
        'DOWNLOAD_DELAY': 1,
    }
    
    def __init__(self, max_pages=None, *args, **kwargs):
        """
        Initialize the spider.
        
        Args:
            max_pages: Optional limit on number of pages to crawl
        """
        super(ExampleCustomSpider, self).__init__(*args, **kwargs)
        self.max_pages = int(max_pages) if max_pages else None
        self.pages_crawled = 0
    
    def start_requests(self):
        """
        Generate initial requests.
        
        The 'domain' attribute is set by Arachnado and contains
        the URL to start crawling from.
        """
        self.logger.info(
            "Starting example spider for domain: %s (crawl_id: %s)",
            self.domain, self.crawl_id
        )
        
        # Add http:// scheme if not present
        url = self.domain
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        yield scrapy.Request(url, self.parse, dont_filter=True)
    
    def parse(self, response):
        """
        Parse a page and extract data.
        
        This example extracts:
        - Page URL
        - Page title
        - All links
        - All headings (h1, h2, h3)
        """
        # Check if we've reached the page limit
        if self.max_pages and self.pages_crawled >= self.max_pages:
            self.logger.info("Reached max_pages limit: %d", self.max_pages)
            return
        
        self.pages_crawled += 1
        
        # Extract data from the page
        item = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'h1': response.css('h1::text').getall(),
            'h2': response.css('h2::text').getall(),
            'h3': response.css('h3::text').getall(),
            'links': [
                {
                    'url': link.url,
                    'text': link.text,
                }
                for link in response.css('a')
            ],
        }
        
        yield item
        
        # Follow links if within depth limit
        if self.max_pages is None or self.pages_crawled < self.max_pages:
            for link in response.css('a::attr(href)').getall():
                # Only follow links to the same domain
                yield response.follow(link, self.parse)


class SimpleSpider(scrapy.Spider):
    """
    A simpler example that doesn't inherit from ArachnadoSpider.
    
    This still works with Arachnado, but you need to handle
    the domain parameter manually.
    
    Usage: spider://simple
    """
    name = 'simple'
    
    def start_requests(self):
        # The domain parameter is passed as a spider argument
        domain = getattr(self, 'domain', 'http://example.com')
        
        if not domain.startswith(('http://', 'https://')):
            domain = 'http://' + domain
        
        yield scrapy.Request(domain, self.parse)
    
    def parse(self, response):
        """Extract just the title and URL."""
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
        }
