-- Optional SQL balance patch for Kadamba Dynasty.
-- Import this only if the XML version feels too strong.

UPDATE Buildings
SET WonderProductionModifier = 5
WHERE Type = 'BUILDING_KADAMBA_TEMPLE';

UPDATE Traits
SET TradeRouteResourceModifier = 15
WHERE Type = 'TRAIT_KADAMBA_SCHOLARS_DEFIANCE';

UPDATE Units
SET Cost = 75
WHERE Type = 'UNIT_KADAMBA_FOREST_GUARD';
