-- PostgreSQL example; assumes one observation per UTC hour per region.
-- Target is current-hour demand; all predictors use historical observations.
-- Pandas twin: src/energy_ml/features.py (shift / shift(1).rolling(24)).
-- PARTITION BY region_id: lags must not cross regions.
SELECT region_id, timestamp, demand_mw AS target_demand_mw,
       LAG(demand_mw, 1) OVER w AS demand_lag_1h,
       LAG(demand_mw, 24) OVER w AS demand_lag_24h,
       LAG(demand_mw, 168) OVER w AS demand_lag_168h,
       -- 1 PRECEDING excludes the current row (same as Pandas shift(1) then rolling).
       AVG(demand_mw) OVER (
           PARTITION BY region_id ORDER BY timestamp
           ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
       ) AS rolling_mean_24h
FROM electricity_demand
WINDOW w AS (PARTITION BY region_id ORDER BY timestamp);
