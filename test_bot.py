import unittest
from config import setup_api_credentials

class TestConfig(unittest.TestCase):
    def test_api_credentials(self):
        """
        Testet das Laden der API-Schlüssel.
        """
        api_key, api_secret = setup_api_credentials()
        self.assertIsNotNone(api_key)
        self.assertIsNotNone(api_secret)

if __name__ == '__main__':
    unittest.main()