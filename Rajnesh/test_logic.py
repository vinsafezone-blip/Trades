import unittest
from trading_logic import check_candle_size, get_atm_strike_price, check_breakout

class TestTradingLogic(unittest.TestCase):

    def test_check_candle_size(self):
        # Test case where candle size is within range
        candle_in_range = {'high': 44000, 'low': 43750} # size = 250
        self.assertTrue(check_candle_size(candle_in_range))

        # Test case where candle size is below range
        candle_below_range = {'high': 44000, 'low': 43900} # size = 100
        self.assertFalse(check_candle_size(candle_below_range))

        # Test case where candle size is above range
        candle_above_range = {'high': 44000, 'low': 43600} # size = 400
        self.assertFalse(check_candle_size(candle_above_range))

        # Test case for edge value 130 - should be False
        candle_edge_130 = {'high': 44130, 'low': 44000} # size = 130
        self.assertFalse(check_candle_size(candle_edge_130))

        # Test case for edge value 300 - should be False
        candle_edge_300 = {'high': 44300, 'low': 44000} # size = 300
        self.assertFalse(check_candle_size(candle_edge_300))

        # Test case just inside the lower bound
        candle_just_above_130 = {'high': 44131, 'low': 44000} # size = 131
        self.assertTrue(check_candle_size(candle_just_above_130))

        # Test case just inside the upper bound
        candle_just_below_300 = {'high': 44299, 'low': 44000} # size = 299
        self.assertTrue(check_candle_size(candle_just_below_300))

    def test_get_atm_strike_price(self):
        # Test with a price that should round down
        self.assertEqual(get_atm_strike_price(44340), 44300)
        # Test with a price that should round up
        self.assertEqual(get_atm_strike_price(44360), 44400)
        # Test with a price that is exactly on a strike
        self.assertEqual(get_atm_strike_price(44300), 44300)
        # Test with a price at the midpoint
        self.assertEqual(get_atm_strike_price(44350), 44400)

    def test_check_breakout(self):
        candle = {'high': 44000, 'low': 43800}

        # Test for breakout above high
        self.assertEqual(check_breakout(44001, candle), 'high')
        # Test for breakout below low
        self.assertEqual(check_breakout(43799, candle), 'low')
        # Test for no breakout
        self.assertIsNone(check_breakout(43900, candle))
        # Test for price exactly at high
        self.assertIsNone(check_breakout(44000, candle))
        # Test for price exactly at low
        self.assertIsNone(check_breakout(43800, candle))

if __name__ == '__main__':
    unittest.main()
