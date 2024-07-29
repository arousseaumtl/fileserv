import sys
import os
import random
import string
import unittest
import time

from tokens import Tokens

class TestTokens(unittest.TestCase):
    
    def setUp(self):
        self.validity_period_seconds = 5
        self.client_info = "client_ip:192.168.1.1;user_agent:TestAgent"
        self.file_path = "testfile.txt"
        self.unique_string = Tokens.generate_client_secret(self.client_info)
        self.token = Tokens.generate_signed_token(self.validity_period_seconds, self.unique_string, self.file_path)

    def test_generate_and_validate_token_immediately(self):
        print("\nTesting if token is valid immediately after generation")
        self.assertTrue(Tokens.validate_token(self.token, self.unique_string, self.file_path), "Token should be valid immediately after generation")

    def test_generate_and_validate_token_within_validity(self):
        print("Testing if token is still valid within the validity period (after 3 seconds)")
        time.sleep(3)
        self.assertTrue(Tokens.validate_token(self.token, self.unique_string, self.file_path), "Token should still be valid within the validity period")

    def test_generate_and_validate_token_after_expiry(self):
        print("Testing if token is invalid after the validity period")
        time.sleep(self.validity_period_seconds)
        self.assertFalse(Tokens.validate_token(self.token, self.unique_string, self.file_path), "Token should be invalid after the validity period")

    def test_tampered_token(self):
        print("Testing if a tampered token is invalid")
        tampered_token = self.token[:-8] + ''.join(random.choice(string.ascii_uppercase) for _ in range(8))
        self.assertFalse(Tokens.validate_token(tampered_token, self.unique_string, self.file_path), "Tampered token should be invalid")

if __name__ == '__main__':
    unittest.main(verbosity=2)
