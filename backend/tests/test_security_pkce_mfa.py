"""
Unit Tests for Kestrel Shield — PKCE, RFC 6238 TOTP MFA, and Rate Limiting
Uses Python Standard Library unittest for zero-dependency execution.
"""
import time
import unittest
import asyncio
from app.core.security import compute_pkce_challenge, verify_pkce
from app.core.totp import generate_totp_secret, generate_totp_code, verify_totp_code, generate_totp_uri
from app.core.rate_limiter import SlidingWindowRateLimiter
from fastapi import HTTPException


class TestSecurityPkceMfa(unittest.TestCase):

    def test_pkce_s256_verification(self):
        """Verify standard RFC 7636 S256 code challenge generation and validation."""
        verifier = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
        challenge = compute_pkce_challenge(verifier)

        self.assertIsNotNone(challenge)
        self.assertTrue(len(challenge) > 20)
        self.assertTrue(verify_pkce(verifier, challenge, method="S256"))
        self.assertFalse(verify_pkce("wrong_verifier_12345678901234567890", challenge, method="S256"))

    def test_totp_rfc6238_generation_and_drift(self):
        """Verify RFC 6238 TOTP code generation, verification, and clock drift allowance."""
        secret = generate_totp_secret()
        self.assertEqual(len(secret), 32)

        # Generate current code
        now = time.time()
        code = generate_totp_code(secret, for_time=now)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        # Valid in current window
        self.assertTrue(verify_totp_code(secret, code))

        # Valid within ±1 drift interval (30s)
        drifted_code = generate_totp_code(secret, for_time=now - 25)
        self.assertTrue(verify_totp_code(secret, drifted_code, window=1))

        # Invalid code rejected
        self.assertFalse(verify_totp_code(secret, "000000" if code != "000000" else "999999"))

    def test_totp_uri_format(self):
        """Verify otpauth:// URI formatting for authenticator apps."""
        secret = "JBSWY3DPEHPK3PXP"
        uri = generate_totp_uri(secret, "trader@kestrel.com", "Kestrel Trading")
        self.assertTrue(uri.startswith("otpauth://totp/Kestrel%20Trading%3Atrader%40kestrel.com?"))
        self.assertIn("secret=JBSWY3DPEHPK3PXP", uri)
        self.assertIn("issuer=Kestrel+Trading", uri)

    def test_sliding_window_rate_limiter(self):
        """Verify rate limiter blocks requests exceeding threshold."""
        limiter = SlidingWindowRateLimiter()
        key = "test_ip_192_168_1_1"

        async def run_test():
            for _ in range(3):
                allowed = await limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
                self.assertTrue(allowed)

            with self.assertRaises(HTTPException) as cm:
                await limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
            self.assertEqual(cm.exception.status_code, 429)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
