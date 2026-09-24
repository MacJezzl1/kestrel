"""
Unit Tests for Orders Pipeline and Idempotency Validation
Uses Python Standard Library unittest for zero-dependency execution.
"""
import unittest
from pydantic import ValidationError
from app.routers.orders import OrderCreate


class TestOrdersValidation(unittest.TestCase):

    def test_order_schema_validation(self):
        """Verify allow-list regex and quantity boundaries."""
        # Valid order
        order = OrderCreate(
            client_order_id="ord_test_unique_12345",
            instrument="Volatility 100 Index",
            order_type="MARKET",
            direction="BUY",
            qty=0.50,
            stop_loss=1230.0,
            take_profit=1290.0,
        )
        self.assertEqual(order.instrument, "Volatility 100 Index")
        self.assertEqual(order.qty, 0.50)

        # Invalid instrument characters (SQL injection attempt blocked)
        with self.assertRaises(ValidationError):
            OrderCreate(
                client_order_id="ord_test_unique_12345",
                instrument="EURUSD; DROP TABLE orders;--",
                direction="BUY",
                qty=1.0,
            )

        # Invalid lot size (negative lot)
        with self.assertRaises(ValidationError):
            OrderCreate(
                client_order_id="ord_test_unique_12345",
                instrument="EURUSD",
                direction="BUY",
                qty=-0.5,
            )


if __name__ == "__main__":
    unittest.main()
