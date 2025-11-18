# -*- coding: utf-8 -*-
"""
Tests for spider path-based filtering functionality.
"""
import unittest
from scrapy.http import HtmlResponse, Request
from arachnado.spider import CrawlWebsiteSpider


class TestCrawlWebsiteSpider(unittest.TestCase):
    """Test path-based filtering in CrawlWebsiteSpider"""
    
    def _create_spider(self, domain):
        """Helper to create a spider instance"""
        spider = CrawlWebsiteSpider()
        spider.domain = domain
        spider.crawl_id = 'test-crawl-id'
        spider.motor_job_id = 'test-motor-id'
        spider.state = {}
        return spider
    
    def _create_response(self, url, spider):
        """Helper to create a scrapy Response object"""
        request = Request(url)
        response = HtmlResponse(
            url=url,
            request=request,
            body=b'<html><body></body></html>',
            encoding='utf-8'
        )
        # Set required meta attributes
        response.meta['depth'] = 0
        return response
    
    def test_path_extraction_root_domain(self):
        """Test that root domain (no path) results in '/' as start_path"""
        spider = self._create_spider('example.com')
        response = self._create_response('http://example.com', spider)
        
        # Call parse_first to initialize state
        list(spider.parse_first(response))
        
        self.assertEqual(spider.state['start_path'], '/')
        self.assertEqual(spider.state['allow_domain'], 'example.com')
    
    def test_path_extraction_with_directory(self):
        """Test path extraction for directory-style URLs"""
        spider = self._create_spider('example.com/docs/api')
        response = self._create_response('http://example.com/docs/api', spider)
        
        # Call parse_first to initialize state
        list(spider.parse_first(response))
        
        # Should normalize to end with /
        self.assertEqual(spider.state['start_path'], '/docs/api/')
    
    def test_path_extraction_with_trailing_slash(self):
        """Test path extraction for URLs with trailing slash"""
        spider = self._create_spider('example.com/docs/api/')
        response = self._create_response('http://example.com/docs/api/', spider)
        
        # Call parse_first to initialize state
        list(spider.parse_first(response))
        
        self.assertEqual(spider.state['start_path'], '/docs/api/')
    
    def test_path_extraction_with_file(self):
        """Test path extraction for file-style URLs"""
        spider = self._create_spider('example.com/docs/api/index.html')
        response = self._create_response('http://example.com/docs/api/index.html', spider)
        
        # Call parse_first to initialize state
        list(spider.parse_first(response))
        
        # Should use parent directory
        self.assertEqual(spider.state['start_path'], '/docs/api/')
    
    def test_link_extractor_root_path(self):
        """Test that link extractor doesn't filter when path is root"""
        spider = self._create_spider('example.com')
        spider.state = {
            'allow_domain': 'example.com',
            'start_path': '/'
        }
        
        link_extractor = spider.link_extractor
        
        # For root path, allow pattern should be None
        self.assertIsNone(link_extractor.allow)
    
    def test_link_extractor_with_path(self):
        """Test that link extractor creates correct pattern for non-root paths"""
        spider = self._create_spider('example.com/docs/')
        spider.state = {
            'allow_domain': 'example.com',
            'start_path': '/docs/'
        }
        
        link_extractor = spider.link_extractor
        
        # Should have allow pattern
        self.assertIsNotNone(link_extractor.allow)
        # Pattern should start with escaped path
        self.assertEqual(link_extractor.allow, '^/docs/')


if __name__ == '__main__':
    unittest.main()
