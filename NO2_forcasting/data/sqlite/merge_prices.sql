
-- Prevent duplicates (recommended)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_price
ON electricity_prices_historical(zone, timestamp);

-- Merge new data
INSERT OR IGNORE INTO electricity_prices_historical (zone, timestamp, price_eur_per_mwh)
SELECT zone, timestamp, price_eur_per_mwh
FROM electricity_prices_daily;

-- Optional: clear daily table after merge
-- DELETE FROM electricity_prices_daily;
  