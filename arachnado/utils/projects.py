# -*- coding: utf-8 -*-
"""
Utilities for managing uploaded Scrapy projects.
"""
from __future__ import absolute_import
import os
import sys
import logging
import shutil
import zipfile
import tarfile


logger = logging.getLogger(__name__)


class ProjectManager(object):
    """
    Manages uploaded Scrapy projects.
    """
    def __init__(self, projects_dir):
        """
        :param projects_dir: Directory where uploaded projects are stored
        """
        self.projects_dir = projects_dir
        if not os.path.exists(projects_dir):
            os.makedirs(projects_dir)
    
    def extract_project(self, file_path, project_name):
        """
        Extract an uploaded project archive to the projects directory.
        
        :param file_path: Path to the uploaded archive file
        :param project_name: Name to use for the extracted project
        :return: Path to the extracted project directory
        """
        project_path = os.path.join(self.projects_dir, project_name)
        
        # Remove existing project if it exists
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        
        os.makedirs(project_path)
        
        try:
            # Try to extract as zip file
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(project_path)
                logger.info("Extracted zip project %s to %s", project_name, project_path)
            # Try to extract as tar file
            elif tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(project_path)
                logger.info("Extracted tar project %s to %s", project_name, project_path)
            else:
                raise ValueError("Unsupported file format. Only zip and tar archives are supported.")
            
            return project_path
        except Exception as e:
            # Clean up on failure
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
            logger.error("Failed to extract project %s: %s", project_name, e)
            raise
    
    def get_project_spider_packages(self, project_name):
        """
        Get spider packages from an extracted project.
        
        :param project_name: Name of the project
        :return: List of spider package names
        """
        project_path = os.path.join(self.projects_dir, project_name)
        if not os.path.exists(project_path):
            return []
        
        spider_packages = []
        
        # Look for common spider package patterns
        # 1. Look for scrapy.cfg to identify project root
        scrapy_cfg = self._find_scrapy_cfg(project_path)
        if scrapy_cfg:
            # Parse scrapy.cfg to find the spider module
            spider_module = self._parse_spider_module_from_cfg(scrapy_cfg)
            if spider_module:
                spider_packages.append(spider_module)
        
        # 2. Fallback: Look for directories named 'spiders'
        if not spider_packages:
            for root, dirs, files in os.walk(project_path):
                if 'spiders' in dirs:
                    # Try to construct the package path
                    spiders_path = os.path.join(root, 'spiders')
                    if self._is_python_package(spiders_path):
                        # Convert file path to package name
                        rel_path = os.path.relpath(spiders_path, project_path)
                        package = rel_path.replace(os.sep, '.')
                        parent_package = package.rsplit('.', 1)[0] if '.' in package else None
                        if parent_package and self._is_python_package(os.path.join(project_path, parent_package.replace('.', os.sep))):
                            spider_packages.append(package)
        
        # Add project path to sys.path if we found spider packages
        if spider_packages and project_path not in sys.path:
            sys.path.insert(0, project_path)
            logger.info("Added %s to sys.path", project_path)
        
        return spider_packages
    
    def _find_scrapy_cfg(self, project_path):
        """Find scrapy.cfg file in the project."""
        for root, dirs, files in os.walk(project_path):
            if 'scrapy.cfg' in files:
                return os.path.join(root, 'scrapy.cfg')
        return None
    
    def _parse_spider_module_from_cfg(self, cfg_path):
        """Parse spider module name from scrapy.cfg."""
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser
        
        try:
            config = configparser.ConfigParser()
            config.read(cfg_path)
            if config.has_section('settings'):
                default_settings = config.get('settings', 'default')
                # default_settings is like 'myproject.settings'
                # spider module is typically 'myproject.spiders'
                base_module = default_settings.rsplit('.', 1)[0]
                return base_module + '.spiders'
        except Exception as e:
            logger.warning("Failed to parse scrapy.cfg: %s", e)
        return None
    
    def _is_python_package(self, path):
        """Check if a directory is a Python package."""
        return os.path.isdir(path) and os.path.exists(os.path.join(path, '__init__.py'))
    
    def list_projects(self):
        """
        List all uploaded projects.
        
        :return: List of project names
        """
        if not os.path.exists(self.projects_dir):
            return []
        return [d for d in os.listdir(self.projects_dir) 
                if os.path.isdir(os.path.join(self.projects_dir, d))]
    
    def delete_project(self, project_name):
        """
        Delete an uploaded project.
        
        :param project_name: Name of the project to delete
        """
        project_path = os.path.join(self.projects_dir, project_name)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
            logger.info("Deleted project %s", project_name)
