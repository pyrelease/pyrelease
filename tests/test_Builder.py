from __future__ import print_function
import os
import unittest


from pyrelease.builder import Builder
from pyrelease.pyrelease import PyPackage


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(os.path.dirname(__file__))
        target = os.path.join(self.test_dir, 'testcases', 'base_test.py')
        self.package = PyPackage(target)
        self.builder = Builder(package=self.package)

    def tearDown(self):
        try:
            os.rmdir(self.builder.build_dir)
        except OSError:
            pass

    def test_verbose(self):
        self.assertEqual(self.builder.verbose, False)
        self.assertEqual(os.path.basename(self.builder.file_name), "base_test.py")

    def test_use_test_server(self):
        self.assertTrue(self.builder.use_test_server)
        self.builder.use_test_server = False
        self.assertFalse(self.builder.use_test_server)

    def test_build_dir(self):
        self.assertEqual(os.path.basename(self.builder.build_dir), "base_test.0.1.1")

    def test_create_build_dir(self):
        self.builder.build_dir = os.path.join(self.test_dir, "build_test_dir")
        self.assertEqual(os.path.exists(self.builder.build_dir), False)
        self.builder.create_build_dir()
        self.assertEqual(os.path.exists(self.builder.build_dir), True)

    def test_build_readme(self):
        self.builder.create_build_dir()
        self.builder.build_readme()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'README.rst')))

    def test_build_manifest(self):
        self.builder.create_build_dir()
        self.builder.build_manifest()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'MANIFEST.in')))

    def test_build_setup(self):
        self.builder.create_build_dir()
        self.builder.build_setup()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'setup.py')))

    def test_build_license(self):
        self.builder.create_build_dir()
        self.builder.build_license()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'LICENSE.md')))

    def test_build_requirements(self):
        self.builder.create_build_dir()
        self.builder.build_requirements()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'requirements.txt')))

    def test_build_package(self):
        self.builder.create_build_dir()
        self.builder.build_package()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'base_test.py')))

    def test_make_all(self):
        self.builder.create_build_dir()
        self.builder.make_all()
        path = self.builder.build_dir
        self.assertTrue(os.path.isfile(os.path.join(path, 'README.rst')))
        self.assertTrue(os.path.isfile(os.path.join(path, 'MANIFEST.in')))
        self.assertTrue(os.path.isfile(os.path.join(path, 'setup.py')))
        self.assertTrue(os.path.isfile(os.path.join(path, 'LICENSE.md')))
        self.assertTrue(os.path.isfile(os.path.join(path, 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(path, 'base_test.py')))
