import unittest

suite = unittest.defaultTestLoader.discover("unittest","test_*.py")
runner = unittest.TextTestRunner()
runner.run(suite)