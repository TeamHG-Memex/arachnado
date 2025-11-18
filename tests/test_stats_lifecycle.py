# -*- coding: utf-8 -*-
"""
Unit test for EventedStatsCollector to verify the PeriodicCallback lifecycle.

This test ensures that the bug where log_count/DEBUG keeps increasing after 
a job is finished has been fixed. The bug was caused by starting the 
PeriodicCallback twice (once in __init__ and once in open_spider), which 
caused orphaned callbacks that continued running after close_spider.
"""
import time
import unittest
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.spiders import Spider

from arachnado.stats import EventedStatsCollector


class TestEventedStatsCollector(unittest.TestCase):
    """Test EventedStatsCollector lifecycle management."""

    def test_task_not_started_in_init(self):
        """Test that the PeriodicCallback is not started in __init__."""
        settings = Settings()
        crawler = Crawler(Spider, settings)
        stats = EventedStatsCollector(crawler)
        
        # The task should not be running after initialization
        self.assertFalse(
            stats._task.is_running(),
            "PeriodicCallback should not be running after __init__"
        )

    def test_task_started_on_spider_open(self):
        """Test that the PeriodicCallback is started when spider opens."""
        settings = Settings()
        crawler = Crawler(Spider, settings)
        stats = EventedStatsCollector(crawler)
        spider = Spider(name='test')
        
        # Start the spider
        stats.open_spider(spider)
        
        # The task should now be running
        self.assertTrue(
            stats._task.is_running(),
            "PeriodicCallback should be running after open_spider"
        )
        
        # Cleanup
        stats.close_spider(spider, 'finished')

    def test_task_stopped_on_spider_close(self):
        """Test that the PeriodicCallback is stopped when spider closes."""
        settings = Settings()
        crawler = Crawler(Spider, settings)
        stats = EventedStatsCollector(crawler)
        spider = Spider(name='test')
        
        # Start and then stop the spider
        stats.open_spider(spider)
        stats.close_spider(spider, 'finished')
        
        # Give a moment for the stop to take effect
        time.sleep(0.2)
        
        # The task should not be running after close
        self.assertFalse(
            stats._task.is_running(),
            "PeriodicCallback should not be running after close_spider"
        )


if __name__ == '__main__':
    unittest.main()
