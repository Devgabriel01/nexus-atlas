-- NEXUS ATLAS — Database Initialization
-- Run this once after PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Ensure schema
CREATE SCHEMA IF NOT EXISTS nexus;

-- Seed default regions of interest
INSERT INTO regions (id, name, description, category, lat_min, lat_max, lon_min, lon_max, watch_level)
VALUES
  (gen_random_uuid()::text, 'Amazon Basin - Deforestation Zone', 'Rapid deforestation activity detected', 'forest', -10.0, 0.0, -65.0, -50.0, 'high'),
  (gen_random_uuid()::text, 'Arctic Sea Ice Edge', 'Seasonal monitoring zone', 'arctic', 70.0, 80.0, -30.0, 30.0, 'normal'),
  (gen_random_uuid()::text, 'Sahara Expansion Front', 'Desertification boundary', 'desert', 12.0, 20.0, -5.0, 20.0, 'medium'),
  (gen_random_uuid()::text, 'South China Sea', 'Maritime activity monitoring', 'ocean', 10.0, 22.0, 110.0, 125.0, 'high'),
  (gen_random_uuid()::text, 'Siberian Permafrost Zone', 'Methane release monitoring', 'arctic', 55.0, 70.0, 60.0, 120.0, 'medium'),
  (gen_random_uuid()::text, 'Nile Delta', 'Agricultural & urban expansion', 'urban', 30.0, 32.5, 30.0, 33.0, 'normal'),
  (gen_random_uuid()::text, 'Congo Rainforest', 'Carbon sink monitoring', 'forest', -5.0, 5.0, 15.0, 30.0, 'medium'),
  (gen_random_uuid()::text, 'Himalayan Glaciers', 'Glacial retreat analysis', 'arctic', 27.0, 35.0, 75.0, 95.0, 'high')
ON CONFLICT DO NOTHING;
