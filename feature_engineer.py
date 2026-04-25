import pandas as pd
import numpy as np
from ta.volatility import BollingerBands, AverageTrueRange
from ta.momentum import StochasticOscillator

def engineer_features(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """
    Feature engineering tailored for EdgeFlow-Trader + your usdjpy_m1.csv format.
    Combines your exact MT4 setup with useful AlphaScan features.
    """
    df = df.copy()

    # === Create proper datetime index from Date + Timestamp ===
    df['timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Timestamp'])
    df.set_index('timestamp', inplace=True)

    # Use consistent column names (capitalized like your file)
    o, h, l, c = 'Open', 'High', 'Low', 'Close'

    # === Candle Anatomy ===
    df['body_size'] = (df[c] - df[o]).abs()
    df['upper_wick'] = df[h] - df[[c, o]].max(axis=1)
    df['lower_wick'] = df[[c, o]].min(axis=1) - df[l]
    df['candle_range'] = df[h] - df[l]
    df['bullish'] = (df[c] > df[o]).astype(int)

    # Engulfing
    df['prev_open'] = df[o].shift(1)
    df['prev_close'] = df[c].shift(1)
    df['engulfing'] = (
        ((df[c] > df[o]) & (df['prev_close'] < df['prev_open']) &
         (df[o] < df['prev_close']) & (df[c] > df['prev_open'])) |
        ((df[c] < df[o]) & (df['prev_close'] > df['prev_open']) &
         (df[o] > df['prev_close']) & (df[c] < df['prev_open']))
    ).astype(int)

    # === Core MT4 Indicators ===
    df['ma_9']   = df[c].rolling(window=9).mean()
    df['ma_20']  = df[c].rolling(window=20).mean()
    df['ma_100'] = df[c].rolling(window=100).mean()
    df['ma_200'] = df[c].rolling(window=200).mean()

    # Bollinger Bands (20, 2)
    bb = BollingerBands(close=df[c], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mid']   = bb.bollinger_mavg()
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    df['percent_b'] = (df[c] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # Stochastic (5,3,3)
    stoch = StochasticOscillator(high=df[h], low=df[l], close=df[c], window=5, smooth_window=3)
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()

    # ATR(14)
    atr = AverageTrueRange(high=df[h], low=df[l], close=df[c], window=14)
    df['atr_14'] = atr.average_true_range()

    # Trend & Bias
    df['above_ma9'] = (df[c] > df['ma_9']).astype(int)
    df['ma9_slope'] = df['ma_9'].diff()

    df['htf_bias'] = 0
    df.loc[(df[c] > df['ma_100']) & (df[c] > df['ma_200']), 'htf_bias'] = 1
    df.loc[(df[c] < df['ma_100']) & (df[c] < df['ma_200']), 'htf_bias'] = -1

    # MA Alignment
    def ma_alignment(row):
        if row['ma_9'] > row['ma_20'] > row['ma_100'] > row['ma_200']:
            return 1
        elif row['ma_9'] < row['ma_20'] < row['ma_100'] < row['ma_200']:
            return -1
        return 0
    df['ma_alignment'] = df.apply(ma_alignment, axis=1)

    # Time & Session
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek

    def get_session(h):
        if 0 <= h < 6:   return "Asia"
        elif 6 <= h < 12: return "London"
        elif 12 <= h < 18: return "New York"
        else:            return "Overlap"
    df['session'] = df['hour'].apply(get_session)

    # MA9 Hold Duration
    hold = []
    counter = 0
    prev_above = df['above_ma9'].iloc[0] if not df.empty else 0
    for above in df['above_ma9']:
        if above == prev_above:
            counter += 1
        else:
            counter = 1
            prev_above = above
        hold.append(counter if above else -counter)
    df['ma9_hold_duration'] = hold

    # Cleanup
    df.drop(columns=['prev_open', 'prev_close'], errors='ignore', inplace=True)
    df.dropna(inplace=True)

    return df


if __name__ == "__main__":
    df = pd.read_csv('../data/usdjpy_m1.csv')
    features = engineer_features(df, lookback=60)
    features.to_csv('features_test_60candle.csv', index=True)
    print(f"✅ Feature engineering complete. Shape: {features.shape}")
    key_cols = ['ma_9', 'ma_20', 'ma_100', 'ma_200', 'bb_mid', 'stoch_k', 'atr_14', 'session', 'htf_bias']
    print(features[key_cols].tail(5))
