
import pandas as pd

def downsample(df, timeframe):
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)

    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }
    if 'volume' in df.columns:
        ohlc_dict['volume'] = 'sum'

    resampled = df.resample(timeframe).agg(ohlc_dict).dropna().reset_index()
    return resampled

def detect_swing_highs_lows(df, window=3):
    highs = df['high'].values
    lows = df['low'].values
    dates = df['datetime'].values

    swing_highs = []
    swing_lows = []

    for i in range(window, len(df) - window):
        local_high = highs[i]
        local_low = lows[i]
        is_high = all(local_high > highs[i - j] for j in range(1, window + 1)) and                   all(local_high > highs[i + j] for j in range(1, window + 1))
        is_low = all(local_low < lows[i - j] for j in range(1, window + 1)) and                  all(local_low < lows[i + j] for j in range(1, window + 1))

        if is_high:
            swing_highs.append((dates[i], local_high))
        if is_low:
            swing_lows.append((dates[i], local_low))

    return swing_highs, swing_lows

def get_support_resistance_zones(df, timeframes=['1h', '4h', '1d'], window=3, cluster_threshold=0.0015):
    raw_levels = []

    for tf in timeframes:
        tf_df = downsample(df, tf)
        highs, lows = detect_swing_highs_lows(tf_df, window=window)
        raw_levels.extend([price for _, price in highs])
        raw_levels.extend([price for _, price in lows])

    # Cluster similar levels together
    raw_levels.sort()
    clustered_zones = []

    for level in raw_levels:
        found = False
        for cluster in clustered_zones:
            if abs(level - cluster['level']) <= level * cluster_threshold:
                cluster['touches'] += 1
                cluster['members'].append(level)
                cluster['level'] = sum(cluster['members']) / len(cluster['members'])  # update average
                found = True
                break
        if not found:
            clustered_zones.append({
                'level': level,
                'touches': 1,
                'members': [level]
            })

    support = [z['level'] for z in clustered_zones if z['touches'] >= 2]
    resistance = [z['level'] for z in clustered_zones if z['touches'] >= 2]

    zones = {
        'support': support,
        'resistance': resistance,
        'scored_zones': clustered_zones
    }

    return zones
