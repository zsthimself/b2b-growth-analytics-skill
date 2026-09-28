# -*- coding: utf-8 -*-
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.google_api import mask_secrets
from core.cpl_ledger import CPLLedger


class TestCoreUtilities(unittest.TestCase):
    def test_mask_secrets(self):
        sample_log = "Error with Authorization: Bearer mock_access_token_12345 and developer-token: SecretDevToken12345"
        masked = mask_secrets(sample_log)
        self.assertNotIn("mock_access_token_12345", masked)
        self.assertNotIn("SecretDevToken12345", masked)
        self.assertIn("Bearer ***", masked)
        self.assertIn("developer-token: ***", masked)

    def test_cpl_ledger_calculation(self):
        inquiries = [
            {"seq": 1, "date": "2026-09-20", "channel": "Form", "is_valid": True, "country": "US"},
            {"seq": 2, "date": "2026-09-21", "channel": "WhatsApp", "is_valid": True, "country": "ES"},
            {"seq": 3, "date": "2026-09-22", "channel": "无效/推销", "is_valid": False, "country": "Unknown"},
        ]
        stats = CPLLedger.calculate_cpl_metrics(ad_spend_usd=100.0, inquiries=inquiries)
        self.assertEqual(stats["total_raw_leads"], 3)
        self.assertEqual(stats["valid_leads_count"], 2)
        self.assertEqual(stats["cpl_usd"], 50.0)
        self.assertEqual(stats["channel_distribution"]["Form"], 1)
        self.assertEqual(stats["channel_distribution"]["WhatsApp"], 1)
        self.assertEqual(stats["country_distribution"]["US"], 1)
        self.assertEqual(stats["country_distribution"]["ES"], 1)


if __name__ == "__main__":
    unittest.main()
