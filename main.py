import market_stats

bd=market_stats.BinanceData()
bd.download_data('BTCUSDT',interval='1d',startTime='2021-01-01',endTime='2025-01-01',save=True)