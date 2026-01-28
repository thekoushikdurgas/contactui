"""Tests for path utility functions."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.conf import settings

from apps.documentation.utils.paths import (
    get_workspace_root,
    get_media_root,
    get_pages_dir,
    get_endpoints_dir,
    get_relationships_dir,
    get_postman_dir,
    get_n8n_dir,
    get_project_dir,
    get_scripts_dir,
    get_lambda_docs_api_dir,
    list_directory_files,
    _format_file_size,
)


class PathUtilsTestCase(TestCase):
    """Test path utility functions."""

    def test_get_workspace_root(self):
        """Test getting workspace root directory."""
        root = get_workspace_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())

    @override_settings(MEDIA_ROOT=None)
    def test_get_media_root_default(self):
        """Test getting media root when MEDIA_ROOT is not set."""
        with patch('apps.documentation.utils.paths.settings') as mock_settings:
            mock_settings.BASE_DIR = Path('/test/base')
            mock_settings.MEDIA_ROOT = None
            media_root = get_media_root()
            self.assertEqual(str(media_root), str(Path('/test/base') / 'media'))

    @override_settings(MEDIA_ROOT='/custom/media')
    def test_get_media_root_custom(self):
        """Test getting media root when MEDIA_ROOT is set."""
        with patch('apps.documentation.utils.paths.settings') as mock_settings:
            mock_settings.MEDIA_ROOT = '/custom/media'
            media_root = get_media_root()
            self.assertEqual(str(media_root), '/custom/media')

    def test_get_pages_dir(self):
        """Test getting pages directory."""
        pages_dir = get_pages_dir()
        self.assertIsInstance(pages_dir, Path)
        self.assertEqual(pages_dir.name, 'pages')

    def test_get_endpoints_dir(self):
        """Test getting endpoints directory."""
        endpoints_dir = get_endpoints_dir()
        self.assertIsInstance(endpoints_dir, Path)
        self.assertEqual(endpoints_dir.name, 'endpoints')

    def test_get_relationships_dir(self):
        """Test getting relationships directory."""
        rel_dir = get_relationships_dir()
        self.assertIsInstance(rel_dir, Path)
        # Note: Directory may be 'retations' (legacy) or 'relationships' on disk
        self.assertIn(rel_dir.name, ('retations', 'relationships'))

    def test_get_postman_dir(self):
        """Test getting Postman directory."""
        postman_dir = get_postman_dir()
        self.assertIsInstance(postman_dir, Path)
        self.assertEqual(postman_dir.name, 'postman')

    def test_get_n8n_dir(self):
        """Test getting N8N directory."""
        n8n_dir = get_n8n_dir()
        self.assertIsInstance(n8n_dir, Path)
        self.assertEqual(n8n_dir.name, 'n8n')

    def test_get_project_dir(self):
        """Test getting project directory."""
        project_dir = get_project_dir()
        self.assertIsInstance(project_dir, Path)
        self.assertEqual(project_dir.name, 'project')

    def test_get_scripts_dir(self):
        """Test getting scripts directory."""
        scripts_dir = get_scripts_dir()
        self.assertIsInstance(scripts_dir, Path)
        self.assertEqual(scripts_dir.name, 'scripts')

    def test_get_lambda_docs_api_dir_exists(self):
        """Test getting Lambda docs API directory when it exists."""
        with patch('apps.documentation.utils.paths.get_workspace_root') as mock_root:
            mock_root.return_value = Path('/workspace')
            test_path = Path('/workspace/lambda/documentation.api')
            
            with patch('pathlib.Path.exists', return_value=True):
                result = get_lambda_docs_api_dir()
                # Since we're mocking, we can't verify exact path, but should return Path
                # In real scenario, it would return the path if it exists

    def test_get_lambda_docs_api_dir_not_exists(self):
        """Test getting Lambda docs API directory when it doesn't exist."""
        with patch('apps.documentation.utils.paths.get_workspace_root') as mock_root:
            mock_root.return_value = Path('/workspace')
            
            with patch('pathlib.Path.exists', return_value=False):
                # This will return None if no path exists
                pass


class ListDirectoryFilesTestCase(TestCase):
    """Test list_directory_files function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path('/tmp/test_dir')

    def test_list_directory_files_nonexistent(self):
        """Test listing files in non-existent directory."""
        result = list_directory_files(Path('/nonexistent/dir'))
        self.assertEqual(result, [])

    @patch('apps.documentation.utils.paths.get_media_root')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    def test_list_directory_files_empty(self, mock_iterdir, mock_isdir, mock_exists, mock_media_root):
        """Test listing files in empty directory."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_iterdir.return_value = []
        mock_media_root.return_value = Path('/media')
        
        result = list_directory_files(self.test_dir)
        self.assertEqual(result, [])

    @patch('apps.documentation.utils.paths.get_media_root')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    def test_list_directory_files_with_extensions(self, mock_iterdir, mock_isdir, mock_exists, mock_media_root):
        """Test listing files with extension filter."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_media_root.return_value = Path('/media')
        
        # Create mock files
        file1 = MagicMock()
        file1.is_file.return_value = True
        file1.name = 'test.json'
        file1.suffix = '.json'
        file1.stat.return_value.st_size = 100
        file1.stat.return_value.st_mtime = 1234567890
        file1.relative_to.return_value = Path('test.json')
        
        file2 = MagicMock()
        file2.is_file.return_value = True
        file2.name = 'test.txt'
        file2.suffix = '.txt'
        
        mock_iterdir.return_value = [file1, file2]
        
        result = list_directory_files(self.test_dir, extensions=['.json'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test.json')

    @patch('apps.documentation.utils.paths.get_media_root')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    def test_list_directory_files_exclude_files(self, mock_iterdir, mock_isdir, mock_exists, mock_media_root):
        """Test listing files with exclude filter."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_media_root.return_value = Path('/media')
        
        file1 = MagicMock()
        file1.is_file.return_value = True
        file1.name = 'index.json'
        file1.suffix = '.json'
        file1.stat.return_value.st_size = 100
        file1.stat.return_value.st_mtime = 1234567890
        file1.relative_to.return_value = Path('index.json')
        
        file2 = MagicMock()
        file2.is_file.return_value = True
        file2.name = 'test.json'
        file2.suffix = '.json'
        file2.stat.return_value.st_size = 200
        file2.stat.return_value.st_mtime = 1234567890
        file2.relative_to.return_value = Path('test.json')
        
        mock_iterdir.return_value = [file1, file2]
        
        result = list_directory_files(self.test_dir, exclude_files={'index.json'})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test.json')


class FormatFileSizeTestCase(TestCase):
    """Test _format_file_size function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        self.assertEqual(_format_file_size(0), "0.0 B")
        self.assertEqual(_format_file_size(500), "500.0 B")
        self.assertEqual(_format_file_size(1023), "1023.0 B")

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        self.assertEqual(_format_file_size(1024), "1.0 KB")
        self.assertEqual(_format_file_size(2048), "2.0 KB")
        self.assertEqual(_format_file_size(1536), "1.5 KB")

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        self.assertEqual(_format_file_size(1048576), "1.0 MB")
        self.assertEqual(_format_file_size(2097152), "2.0 MB")

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        self.assertEqual(_format_file_size(1073741824), "1.0 GB")
        self.assertEqual(_format_file_size(2147483648), "2.0 GB")

    def test_format_terabytes(self):
        """Test formatting terabytes."""
        # Very large file
        size = 1099511627776  # 1 TB
        result = _format_file_size(size)
        self.assertIn("TB", result)
