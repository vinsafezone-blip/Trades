import pandas as pd
import datetime as dt
from trading_logic import check_candle_size

def run_backtest(kite, instrument_token, start_date, end_date, sl_points, target_points):
    """
    Runs a backtest of the trading strategy over a given period.
    """

    # Fetch historical data for the entire period
    try:
        historical_data = kite.historical_data(instrument_token, start_date, end_date, "5minute")
        if not historical_data:
            return None, None
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    except Exception as e:
        print(f"Error fetching historical data for backtest: {e}")
        return None, None

    trades = []

    # Group data by day
    daily_groups = df.groupby(df['date'].dt.date)

    for day, daily_data in daily_groups:
        # Get the first 5-minute candle
        first_candle_time = dt.time(9, 15)
        day_start_time = dt.datetime.combine(day, first_candle_time)
        first_candle = daily_data[daily_data['date'] == day_start_time]

        if first_candle.empty:
            continue

        first_candle = first_candle.iloc[0]

        candle_dict = {
            'high': first_candle['high'],
            'low': first_candle['low']
        }

        if not check_candle_size(candle_dict):
            continue

        entry_price = 0
        trade_type = None
        stop_loss = 0
        target = 0

        # Check for breakout in the rest of the day's candles
        for _, candle in daily_data[daily_data['date'] > day_start_time].iterrows():
            if not trade_type: # If not in a trade
                if candle['high'] > first_candle['high']:
                    entry_price = first_candle['high']
                    trade_type = 'BUY'
                    stop_loss = entry_price - sl_points
                    target = entry_price + target_points
                elif candle['low'] < first_candle['low']:
                    entry_price = first_candle['low']
                    trade_type = 'SELL'
                    stop_loss = entry_price + sl_points
                    target = entry_price - target_points

                if trade_type:
                    trades.append({
                        'date': day,
                        'entry_price': entry_price,
                        'trade_type': trade_type,
                        'sl': stop_loss,
                        'target': target,
                        'exit_price': 0,
                        'pnl': 0
                    })

            else: # If in a trade
                if trade_type == 'BUY':
                    if candle['low'] <= stop_loss:
                        trades[-1]['exit_price'] = stop_loss
                        trades[-1]['pnl'] = stop_loss - entry_price
                        break # Exit for the day
                    elif candle['high'] >= target:
                        trades[-1]['exit_price'] = target
                        trades[-1]['pnl'] = target - entry_price
                        break # Exit for the day
                elif trade_type == 'SELL':
                    if candle['high'] >= stop_loss:
                        trades[-1]['exit_price'] = stop_loss
                        trades[-1]['pnl'] = entry_price - stop_loss
                        break # Exit for the day
                    elif candle['low'] <= target:
                        trades[-1]['exit_price'] = target
                        trades[-1]['pnl'] = entry_price - target
                        break # Exit for the day

    summary = {
        'total_trades': len(trades),
        'profitable_trades': len([t for t in trades if t['pnl'] > 0]),
        'loss_making_trades': len([t for t in trades if t['pnl'] < 0]),
        'total_pnl': sum(t['pnl'] for t in trades)
    }

    return summary, trades
