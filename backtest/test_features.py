import pandas as pd
import sys
sys.path.append('.')

from feature_engineer import engineer_features

print("✅ Loading data...")

df = pd.read_csv('../data/usdjpy_m1.csv')
print(f"✅ Loaded {len(df):,} candles")
print(f"Columns: {df.columns.tolist()}")

print("\n🔧 Engineering features on 60-candle window...")
features = engineer_features(df, lookback=60)

print(f"✅ Success! Engineered features shape: {features.shape}")

features.to_csv('features_test_60candle.csv', index=True)
print("💾 Saved to: backtest/features_test_60candle.csv")

print("\nPreview of key indicators (last 5 rows):")
key_cols = ['ma_9', 'ma_20', 'ma_100', 'ma_200', 'bb_mid', 'stoch_k', 'atr_14', 'session', 'htf_bias']
print(features[key_cols].tail(5))
