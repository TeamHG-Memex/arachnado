# -*- coding: utf-8 -*-
"""
Tests for configuration loading and parsing.
"""
from __future__ import absolute_import
import os
import tempfile
import unittest

from arachnado.config import load_config, ensure_bool


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading and parsing."""

    def test_resume_on_start_default_value(self):
        """Test that resume_on_start has a default value."""
        opts = load_config()
        self.assertIn('arachnado', opts)
        self.assertIn('resume_on_start', opts['arachnado'])
        # The default value should be "1" (as string) from defaults.conf
        self.assertEqual(opts['arachnado']['resume_on_start'], '1')

    def test_resume_on_start_as_boolean(self):
        """Test that resume_on_start can be converted to boolean."""
        opts = load_config()
        # Before ensure_bool, it should be a string
        self.assertEqual(opts['arachnado']['resume_on_start'], '1')
        
        # After ensure_bool, it should be a boolean
        ensure_bool(opts, 'arachnado', 'resume_on_start')
        self.assertIsInstance(opts['arachnado']['resume_on_start'], bool)
        self.assertTrue(opts['arachnado']['resume_on_start'])

    def test_resume_on_start_can_be_disabled(self):
        """Test that resume_on_start can be set to False via config file."""
        # Create a temporary config file with resume_on_start = 0
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write('[arachnado]\n')
            f.write('resume_on_start = 0\n')
            temp_config = f.name

        try:
            opts = load_config([temp_config])
            ensure_bool(opts, 'arachnado', 'resume_on_start')
            self.assertFalse(opts['arachnado']['resume_on_start'])
        finally:
            os.unlink(temp_config)

    def test_resume_on_start_can_be_overridden(self):
        """Test that resume_on_start can be overridden via command-line."""
        # Override with True
        overrides = [['arachnado', 'resume_on_start', True]]
        opts = load_config(overrides=overrides)
        ensure_bool(opts, 'arachnado', 'resume_on_start')
        self.assertTrue(opts['arachnado']['resume_on_start'])

        # Override with False
        overrides = [['arachnado', 'resume_on_start', False]]
        opts = load_config(overrides=overrides)
        ensure_bool(opts, 'arachnado', 'resume_on_start')
        self.assertFalse(opts['arachnado']['resume_on_start'])


if __name__ == '__main__':
    unittest.main()
