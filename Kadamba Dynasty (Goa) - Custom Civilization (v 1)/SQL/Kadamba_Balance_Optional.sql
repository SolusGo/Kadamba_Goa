-- Optional SQL balance patch for Kadamba Dynasty.
-- This file is intentionally not an active UpdateDatabase action.
-- Enable it after Kadamba_CoreInheritance.sql to use the lower-power values.

UPDATE Buildings
SET WonderProductionModifier = 5
WHERE Type = 'BUILDING_KADAMBA_TEMPLE';

UPDATE Units
SET Cost = 75
WHERE Type = 'UNIT_KADAMBA_FOREST_GUARD';

-- The scripted Trade Route Gold percentage is defined by
-- TRADE_BONUS_PERCENT in Lua/KadambaTrait.lua and UI/KadambaBonusPanel.lua.
-- SQL cannot override that Lua constant, so no misleading trade update is
-- attempted here.
