import unittest
import serve_latest_builds

class TestMaxVersionPicker(unittest.TestCase):

    def test_1(self):
        data = ['0137.002.020/', '0139.010.009/', '0139.011.009/']
        self.assertEqual(serve_latest_builds.find_latest_build(data), '0139.011.009/')

if __name__ == '__main__':
    unittest.main()