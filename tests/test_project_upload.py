# -*- coding: utf-8 -*-
import os
import tempfile
import shutil
import unittest
import zipfile

from arachnado.utils.projects import ProjectManager


class TestProjectManager(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.projects_dir = os.path.join(self.test_dir, 'projects')
        self.project_manager = ProjectManager(self.projects_dir)
    
    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_scrapy_project_zip(self, project_name='testproject'):
        """Create a test Scrapy project zip file."""
        project_dir = os.path.join(self.test_dir, project_name)
        os.makedirs(project_dir)
        
        # Create scrapy.cfg
        scrapy_cfg = os.path.join(project_dir, 'scrapy.cfg')
        with open(scrapy_cfg, 'w') as f:
            f.write('[settings]\n')
            f.write('default = {}.settings\n'.format(project_name))
        
        # Create project package
        package_dir = os.path.join(project_dir, project_name)
        os.makedirs(package_dir)
        
        # Create __init__.py
        with open(os.path.join(package_dir, '__init__.py'), 'w') as f:
            f.write('')
        
        # Create spiders directory
        spiders_dir = os.path.join(package_dir, 'spiders')
        os.makedirs(spiders_dir)
        
        # Create spiders/__init__.py
        with open(os.path.join(spiders_dir, '__init__.py'), 'w') as f:
            f.write('')
        
        # Create a test spider
        with open(os.path.join(spiders_dir, 'example.py'), 'w') as f:
            f.write('import scrapy\n\n')
            f.write('class ExampleSpider(scrapy.Spider):\n')
            f.write('    name = "example"\n')
            f.write('    start_urls = ["http://example.com"]\n')
        
        # Create zip file
        zip_path = os.path.join(self.test_dir, '{}.zip'.format(project_name))
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.test_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def test_extract_zip_project(self):
        """Test extracting a zip project."""
        zip_path = self._create_test_scrapy_project_zip('myproject')
        
        project_path = self.project_manager.extract_project(zip_path, 'myproject')
        
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(os.path.join(project_path, 'myproject', 'scrapy.cfg')))
    
    def test_get_project_spider_packages(self):
        """Test getting spider packages from a project."""
        zip_path = self._create_test_scrapy_project_zip('testproj')
        
        self.project_manager.extract_project(zip_path, 'testproj')
        spider_packages = self.project_manager.get_project_spider_packages('testproj')
        
        self.assertIsInstance(spider_packages, list)
        self.assertGreater(len(spider_packages), 0)
        self.assertTrue(any('spiders' in pkg for pkg in spider_packages))
    
    def test_list_projects(self):
        """Test listing projects."""
        zip_path1 = self._create_test_scrapy_project_zip('project1')
        zip_path2 = self._create_test_scrapy_project_zip('project2')
        
        self.project_manager.extract_project(zip_path1, 'project1')
        self.project_manager.extract_project(zip_path2, 'project2')
        
        projects = self.project_manager.list_projects()
        
        self.assertEqual(len(projects), 2)
        self.assertIn('project1', projects)
        self.assertIn('project2', projects)
    
    def test_delete_project(self):
        """Test deleting a project."""
        zip_path = self._create_test_scrapy_project_zip('delproject')
        
        self.project_manager.extract_project(zip_path, 'delproject')
        self.assertIn('delproject', self.project_manager.list_projects())
        
        self.project_manager.delete_project('delproject')
        self.assertNotIn('delproject', self.project_manager.list_projects())
    
    def test_replace_existing_project(self):
        """Test replacing an existing project."""
        zip_path = self._create_test_scrapy_project_zip('replaceproject')
        
        # Extract first time
        project_path1 = self.project_manager.extract_project(zip_path, 'replaceproject')
        
        # Extract again - should replace
        project_path2 = self.project_manager.extract_project(zip_path, 'replaceproject')
        
        self.assertEqual(project_path1, project_path2)
        # Should only have one project
        projects = self.project_manager.list_projects()
        self.assertEqual(projects.count('replaceproject'), 1)
    
    def test_unsupported_file_format(self):
        """Test that unsupported file format raises an error."""
        # Create a non-archive file
        text_file = os.path.join(self.test_dir, 'test.txt')
        with open(text_file, 'w') as f:
            f.write('This is not an archive')
        
        with self.assertRaises(ValueError):
            self.project_manager.extract_project(text_file, 'badproject')


if __name__ == '__main__':
    unittest.main()
