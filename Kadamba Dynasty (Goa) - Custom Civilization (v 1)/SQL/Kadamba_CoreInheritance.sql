-- Clone the installed Brave New World Temple and Swordsman definitions.
-- This preserves base-game and compatible schema fields that a hand-written
-- partial row would otherwise silently omit.

-- --------------------------------------------------------------------------
-- Kadamba Temple
-- --------------------------------------------------------------------------

DROP TABLE IF EXISTS temp.KadambaTempleClone;
CREATE TEMP TABLE KadambaTempleClone AS
SELECT * FROM Buildings WHERE Type = 'BUILDING_TEMPLE';

UPDATE KadambaTempleClone
SET ID = NULL,
    Type = 'BUILDING_KADAMBA_TEMPLE',
    Description = 'TXT_KEY_BUILDING_KADAMBA_TEMPLE',
    Civilopedia = 'TXT_KEY_BUILDING_KADAMBA_TEMPLE_PEDIA',
    Strategy = 'TXT_KEY_BUILDING_KADAMBA_TEMPLE_STRATEGY',
    Help = 'TXT_KEY_BUILDING_KADAMBA_TEMPLE_HELP',
    WonderProductionModifier = COALESCE(WonderProductionModifier, 0) + 10,
    PortraitIndex = 0,
    IconAtlas = 'KADAMBA_ICON_ATLAS';

INSERT INTO Buildings SELECT * FROM KadambaTempleClone;
DROP TABLE KadambaTempleClone;

INSERT INTO Building_YieldChanges (BuildingType, YieldType, Yield)
SELECT 'BUILDING_KADAMBA_TEMPLE', YieldType, Yield
FROM Building_YieldChanges
WHERE BuildingType = 'BUILDING_TEMPLE';

-- Apply the unique +1 Culture on top of any Culture a compatible base Temple
-- may already provide.
INSERT INTO Building_YieldChanges (BuildingType, YieldType, Yield)
SELECT 'BUILDING_KADAMBA_TEMPLE', 'YIELD_CULTURE', 0
WHERE NOT EXISTS (
    SELECT 1 FROM Building_YieldChanges
    WHERE BuildingType = 'BUILDING_KADAMBA_TEMPLE'
      AND YieldType = 'YIELD_CULTURE'
);
UPDATE Building_YieldChanges
SET Yield = Yield + 1
WHERE BuildingType = 'BUILDING_KADAMBA_TEMPLE'
  AND YieldType = 'YIELD_CULTURE';

INSERT INTO Building_ClassesNeededInCity (BuildingType, BuildingClassType)
SELECT 'BUILDING_KADAMBA_TEMPLE', BuildingClassType
FROM Building_ClassesNeededInCity
WHERE BuildingType = 'BUILDING_TEMPLE';

INSERT INTO Building_Flavors (BuildingType, FlavorType, Flavor)
SELECT 'BUILDING_KADAMBA_TEMPLE', FlavorType, Flavor
FROM Building_Flavors
WHERE BuildingType = 'BUILDING_TEMPLE';

INSERT INTO Building_Flavors (BuildingType, FlavorType, Flavor)
SELECT 'BUILDING_KADAMBA_TEMPLE', 'FLAVOR_CULTURE', 10
WHERE NOT EXISTS (
    SELECT 1 FROM Building_Flavors
    WHERE BuildingType = 'BUILDING_KADAMBA_TEMPLE'
      AND FlavorType = 'FLAVOR_CULTURE'
);
INSERT INTO Building_Flavors (BuildingType, FlavorType, Flavor)
SELECT 'BUILDING_KADAMBA_TEMPLE', 'FLAVOR_WONDER', 15
WHERE NOT EXISTS (
    SELECT 1 FROM Building_Flavors
    WHERE BuildingType = 'BUILDING_KADAMBA_TEMPLE'
      AND FlavorType = 'FLAVOR_WONDER'
);
INSERT INTO Building_Flavors (BuildingType, FlavorType, Flavor)
SELECT 'BUILDING_KADAMBA_TEMPLE', 'FLAVOR_MILITARY_TRAINING', 5
WHERE NOT EXISTS (
    SELECT 1 FROM Building_Flavors
    WHERE BuildingType = 'BUILDING_KADAMBA_TEMPLE'
      AND FlavorType = 'FLAVOR_MILITARY_TRAINING'
);

INSERT INTO Building_DomainFreeExperiences
    (BuildingType, DomainType, Experience)
VALUES
    ('BUILDING_KADAMBA_TEMPLE', 'DOMAIN_LAND', 5);

-- --------------------------------------------------------------------------
-- Forest Guard
-- --------------------------------------------------------------------------

DROP TABLE IF EXISTS temp.KadambaForestGuardClone;
CREATE TEMP TABLE KadambaForestGuardClone AS
SELECT * FROM Units WHERE Type = 'UNIT_SWORDSMAN';

UPDATE KadambaForestGuardClone
SET ID = NULL,
    Type = 'UNIT_KADAMBA_FOREST_GUARD',
    Description = 'TXT_KEY_UNIT_KADAMBA_FOREST_GUARD',
    Civilopedia = 'TXT_KEY_UNIT_KADAMBA_FOREST_GUARD_PEDIA',
    Strategy = 'TXT_KEY_UNIT_KADAMBA_FOREST_GUARD_STRATEGY',
    Help = 'TXT_KEY_UNIT_KADAMBA_FOREST_GUARD_HELP',
    Cost = 70,
    UnitFlagIconOffset = 0,
    PortraitIndex = 0,
    IconAtlas = 'KADAMBA_UNIT_ATLAS',
    UnitFlagAtlas = 'KADAMBA_UNIT_FLAG_ATLAS';

INSERT INTO Units SELECT * FROM KadambaForestGuardClone;
DROP TABLE KadambaForestGuardClone;

INSERT INTO Unit_AITypes (UnitType, UnitAIType)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', UnitAIType
FROM Unit_AITypes
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO Unit_ClassUpgrades (UnitType, UnitClassType)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', UnitClassType
FROM Unit_ClassUpgrades
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO Unit_ResourceQuantityRequirements (UnitType, ResourceType, Cost)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', ResourceType, Cost
FROM Unit_ResourceQuantityRequirements
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO Unit_Flavors (UnitType, FlavorType, Flavor)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', FlavorType, Flavor
FROM Unit_Flavors
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO UnitGameplay2DScripts (UnitType, SelectionSound, FirstSelectionSound)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', SelectionSound, FirstSelectionSound
FROM UnitGameplay2DScripts
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO Unit_FreePromotions (UnitType, PromotionType)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', PromotionType
FROM Unit_FreePromotions
WHERE UnitType = 'UNIT_SWORDSMAN';

INSERT INTO Unit_FreePromotions (UnitType, PromotionType)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', 'PROMOTION_KADAMBA_WOODLAND_DEFENDER'
WHERE NOT EXISTS (
    SELECT 1 FROM Unit_FreePromotions
    WHERE UnitType = 'UNIT_KADAMBA_FOREST_GUARD'
      AND PromotionType = 'PROMOTION_KADAMBA_WOODLAND_DEFENDER'
);
INSERT INTO Unit_FreePromotions (UnitType, PromotionType)
SELECT 'UNIT_KADAMBA_FOREST_GUARD', 'PROMOTION_WOODSMAN'
WHERE NOT EXISTS (
    SELECT 1 FROM Unit_FreePromotions
    WHERE UnitType = 'UNIT_KADAMBA_FOREST_GUARD'
      AND PromotionType = 'PROMOTION_WOODSMAN'
);
