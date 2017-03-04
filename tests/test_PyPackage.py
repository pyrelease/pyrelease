from __future__ import print_function
import os
import unittest
from unittest.mock import mock_open


from pyrelease.pyrelease import PyPackage


class TestPyPackageWithMeta(unittest.TestCase):
    def setUp(self):
        self.scriptDir = os.path.abspath(os.path.dirname(__file__))
        self.testDataDir = os.path.join(self.scriptDir, 'testcases')
        self.package = PyPackage(os.path.join(self.testDataDir, "base_test.py"))

    def test_when_meta(self):
        self.assertIsNotNone(self.package.license)
        self.assertIsNotNone(self.package.version)
        self.assertNotEqual(self.package.description, "")
        self.assertEqual(self.package.find_packages, "")

    def test_name(self):
        self.assertEqual(self.package.name, "base_test")
        self.package.name = "New Name"
        self.assertEqual(self.package.name, "New Name")

    def test_find_packages(self):
        self.assertEqual(self.package.find_packages, "")

    def test_errors(self):
        self.assertIsNone(self.package.errors)

    def test_verbose(self):
        self.assertFalse(self.package.verbose)
        self.package.verbose = True
        self.assertTrue(self.package.verbose)

    def test_is_script(self):
        self.assertTrue(self.package.is_script)

    def test_is_single_file(self):
        self.assertTrue(self.package.is_single_file)

    def test_license(self):
        self.assertEqual(self.package.license, 'BSD-2')

    def test_version(self):
        self.assertEqual(self.package.version, "0.1.1")

    def test_description(self):
        self.assertEqual(self.package.description,
                         "MyMainClass docstring Description")

    def test_requirements(self):
        self.assertEqual(self.package.requirements,
                         ["click", "requests"])


class TestPyPackageNoMeta(unittest.TestCase):
    def setUp(self):
        self.scriptDir = os.path.abspath(os.path.dirname(__file__))
        self.testDataDir = os.path.join(self.scriptDir, 'testcases')
        self.package_no_meta = PyPackage(os.path.join(self.testDataDir, "no_meta.py"))

    def test_is_script(self):
        self.assertTrue(self.package_no_meta.is_script)

    def test_is_single_file(self):
        self.assertTrue(self.package_no_meta.is_single_file)

    def test_when_no_meta(self):
        self.assertIsNone(self.package_no_meta.license)
        self.assertIsNone(self.package_no_meta.version)
        self.assertEqual(self.package_no_meta.description, "")
        self.assertEqual(self.package_no_meta.find_packages, "")

    def test_license(self):
        self.assertIsNone(self.package_no_meta.license)

    def test_version(self):
        self.assertIsNone(self.package_no_meta.version)

    def test_description(self):
        self.assertEqual(self.package_no_meta.description, "")

    def test_requirements(self):
        self.assertEqual(self.package_no_meta.requirements, [])
