"""Validate Kadamba packaging, database inheritance, assets, and Lua contracts."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPOSITORY_ROOT / "Kadamba Dynasty (Goa) - Custom Civilization (v 1)"
PROJECT_PATH = PROJECT_ROOT / "Kadamba_Dynasty_Civ5_Mod.civ5proj"
XML_NAMESPACE = {"msb": "http://schemas.microsoft.com/developer/msbuild/2003"}

EXPECTED_ACTIONS = [
    "XML/Kadamba_GameData.xml",
    "SQL/Kadamba_CoreInheritance.sql",
    "XML/Kadamba_Text.xml",
]
EXPECTED_ENTRY_POINTS = {
    "Lua/KadambaLoader.lua",
    "UI/KadambaBonusPanel.xml",
}
BUILDING_AUXILIARY_COPIED = {
    "Building_ClassesNeededInCity",
    "Building_Flavors",
    "Building_YieldChanges",
}
UNIT_AUXILIARY_COPIED = {
    "UnitGameplay2DScripts",
    "Unit_AITypes",
    "Unit_ClassUpgrades",
    "Unit_Flavors",
    "Unit_ResourceQuantityRequirements",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def scalar(database: sqlite3.Connection, query: str, parameters: tuple = ()) -> int:
    row = database.execute(query, parameters).fetchone()
    require(row is not None, f"query returned no row: {query}")
    return int(row[0])


def row_dict(database: sqlite3.Connection, table: str, key: str, value: str) -> dict:
    cursor = database.execute(
        f"SELECT * FROM {quote_identifier(table)} WHERE {quote_identifier(key)} = ?",
        (value,),
    )
    row = cursor.fetchone()
    require(row is not None, f"missing {table}.{key}={value}")
    return dict(zip((item[0] for item in cursor.description), row))


def xml_value(value: str | None) -> object:
    if value is None:
        return ""
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered == "true":
        return 1
    if lowered == "false":
        return 0
    return stripped


def apply_game_data_xml(database: sqlite3.Connection, path: Path) -> None:
    root = ET.parse(path).getroot()
    require(root.tag == "GameData", f"unexpected XML root in {path.name}: {root.tag}")
    for table_node in root:
        table = table_node.tag
        for row in table_node.findall("Row"):
            values: dict[str, object] = {
                key: xml_value(value) for key, value in row.attrib.items()
            }
            for field in row:
                values[field.tag] = xml_value(field.text)
            columns = ", ".join(quote_identifier(column) for column in values)
            placeholders = ", ".join("?" for _ in values)
            database.execute(
                f"INSERT INTO {quote_identifier(table)} ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )


def project_actions(project: ET.ElementTree) -> list[str]:
    return [
        node.findtext("msb:FileName", "", XML_NAMESPACE).replace("\\", "/")
        for node in project.findall(".//msb:ModActions/msb:Action", XML_NAMESPACE)
        if node.findtext("msb:Type", "", XML_NAMESPACE) == "UpdateDatabase"
    ]


def project_entry_points(project: ET.ElementTree) -> set[str]:
    return {
        node.findtext("msb:FileName", "", XML_NAMESPACE).replace("\\", "/")
        for node in project.findall(".//msb:ModContent/msb:Content", XML_NAMESPACE)
    }


def project_content(project: ET.ElementTree) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for node in project.findall(".//msb:Content[@Include]", XML_NAMESPACE):
        relative = node.attrib["Include"].replace("\\", "/")
        imported = node.findtext("msb:ImportIntoVFS", "False", XML_NAMESPACE).lower() == "true"
        result[relative] = imported
    return result


def validate_packaging(project: ET.ElementTree) -> None:
    content = project_content(project)
    require(project_actions(project) == EXPECTED_ACTIONS, "database action order is incorrect")
    require(project_entry_points(project) == EXPECTED_ENTRY_POINTS, "UI entry points differ")

    for relative in content:
        require((PROJECT_ROOT / relative).is_file(), f"project file is missing: {relative}")

    runtime_files = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for folder in ("Art", "Lua", "SQL", "UI", "XML")
        for path in (PROJECT_ROOT / folder).rglob("*")
        if path.is_file()
    }
    require(runtime_files == set(content),
            f"project/source mismatch: {sorted(runtime_files ^ set(content))}")

    for relative, imported in content.items():
        expected = relative.startswith("Art/") or relative in {
            "Lua/KadambaState.lua",
            "Lua/KadambaTrait.lua",
        }
        require(imported == expected,
                f"unexpected VFS setting for {relative}: {imported}, expected {expected}")

    retired = [name for name in content if "KadambaFlag_" in name or "KadambaLogo_" in name]
    require(not retired, f"unused art remains packaged: {retired}")
    print(f"PASS packaging: {len(content)} project files, actions, entry points, and VFS")


def database_candidates() -> list[Path]:
    homes = {Path.home()}
    if os.environ.get("USERPROFILE"):
        homes.add(Path(os.environ["USERPROFILE"]))
    candidates = []
    for home in homes:
        candidates.append(
            home / "Documents" / "My Games" / "Sid Meier's Civilization 5"
            / "cache" / "Civ5CoreDatabase.db"
        )
    return candidates


def resolve_database(argument: str | None) -> Path:
    if argument:
        path = Path(argument).expanduser().resolve()
        require(path.is_file(), f"base database does not exist: {path}")
        return path
    for candidate in database_candidates():
        if candidate.is_file():
            return candidate
    raise AssertionError("Civ5CoreDatabase.db not found; pass --database PATH")


def tables_with_source_rows(database: sqlite3.Connection, column: str, source: str) -> set[str]:
    result: set[str] = set()
    tables = [
        row[0] for row in database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        columns = {row[1] for row in database.execute(
            f"PRAGMA table_info({quote_identifier(table)})"
        )}
        if column not in columns:
            continue
        try:
            if scalar(database,
                      f"SELECT COUNT(*) FROM {quote_identifier(table)} "
                      f"WHERE {quote_identifier(column)} = ?", (source,)):
                result.add(table)
        except sqlite3.Error:
            continue
    return result


def auxiliary_counter(
    database: sqlite3.Connection,
    table: str,
    key: str,
    value: str,
) -> Counter:
    columns = [
        row[1] for row in database.execute(f"PRAGMA table_info({quote_identifier(table)})")
        if row[1] != key and not (row[5] and row[1].lower() == "id")
    ]
    selected = ", ".join(quote_identifier(column) for column in columns)
    return Counter(database.execute(
        f"SELECT {selected} FROM {quote_identifier(table)} "
        f"WHERE {quote_identifier(key)} = ?", (value,)
    ))


def apply_project_database(
    database: sqlite3.Connection,
    project: ET.ElementTree,
) -> None:
    database.execute(
        "CREATE TABLE IF NOT EXISTS Language_en_US "
        "(Tag TEXT PRIMARY KEY, Text TEXT, Gender TEXT, Plurality TEXT)"
    )
    for relative in project_actions(project):
        path = PROJECT_ROOT / relative
        if path.suffix.lower() == ".sql":
            database.executescript(path.read_text(encoding="utf-8-sig"))
        else:
            apply_game_data_xml(database, path)
        print(f"PASS database action: {relative}")
    database.commit()


def validate_inheritance(database: sqlite3.Connection, snapshots: dict) -> None:
    temple = row_dict(database, "Buildings", "Type", "BUILDING_KADAMBA_TEMPLE")
    base_temple = snapshots["temple"]
    building_differences = {
        "ID", "Type", "Description", "Civilopedia", "Strategy", "Help",
        "WonderProductionModifier", "PortraitIndex", "IconAtlas",
    }
    for column, source_value in base_temple.items():
        if column not in building_differences:
            require(temple[column] == source_value,
                    f"Temple inheritance drift in {column}: {temple[column]} != {source_value}")
    require(temple["WonderProductionModifier"] ==
            (base_temple["WonderProductionModifier"] or 0) + 10,
            "Kadamba Temple Wonder bonus is not base +10")
    require(temple["Cost"] == 100 and temple["GoldMaintenance"] == 2,
            "Kadamba Temple core stats changed")

    shrine_count = scalar(
        database,
        "SELECT COUNT(*) FROM Building_ClassesNeededInCity "
        "WHERE BuildingType=? AND BuildingClassType=?",
        ("BUILDING_KADAMBA_TEMPLE", "BUILDINGCLASS_SHRINE"),
    )
    require(shrine_count == 1, "Kadamba Temple does not require exactly one Shrine")
    faith = scalar(database,
                   "SELECT COALESCE(SUM(Yield),0) FROM Building_YieldChanges "
                   "WHERE BuildingType=? AND YieldType='YIELD_FAITH'",
                   ("BUILDING_KADAMBA_TEMPLE",))
    culture = scalar(database,
                     "SELECT COALESCE(SUM(Yield),0) FROM Building_YieldChanges "
                     "WHERE BuildingType=? AND YieldType='YIELD_CULTURE'",
                     ("BUILDING_KADAMBA_TEMPLE",))
    require(faith == 2 and culture == 1, "Kadamba Temple yields are not +2 Faith/+1 Culture")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Building_DomainFreeExperiences "
                   "WHERE BuildingType=? AND DomainType='DOMAIN_LAND' AND Experience=5",
                   ("BUILDING_KADAMBA_TEMPLE",)) == 1,
            "Kadamba Temple land-unit XP is missing")

    guard = row_dict(database, "Units", "Type", "UNIT_KADAMBA_FOREST_GUARD")
    base_guard = snapshots["swordsman"]
    unit_differences = {
        "ID", "Type", "Description", "Civilopedia", "Strategy", "Help",
        "Cost", "UnitFlagIconOffset", "PortraitIndex", "IconAtlas", "UnitFlagAtlas",
    }
    for column, source_value in base_guard.items():
        if column not in unit_differences:
            require(guard[column] == source_value,
                    f"Forest Guard inheritance drift in {column}: {guard[column]} != {source_value}")
    require(guard["Cost"] == 70 and guard["Combat"] == 14,
            "Forest Guard intended cost/strength changed")

    for table in BUILDING_AUXILIARY_COPIED:
        source = auxiliary_counter(database, table, "BuildingType", "BUILDING_TEMPLE")
        target = auxiliary_counter(database, table, "BuildingType", "BUILDING_KADAMBA_TEMPLE")
        require(not (source - target), f"base Temple rows not preserved in {table}")
    for table in UNIT_AUXILIARY_COPIED:
        source = auxiliary_counter(database, table, "UnitType", "UNIT_SWORDSMAN")
        target = auxiliary_counter(database, table, "UnitType", "UNIT_KADAMBA_FOREST_GUARD")
        require(not (source - target), f"base Swordsman rows not preserved in {table}")

    require(scalar(database,
                   "SELECT COUNT(*) FROM Unit_ResourceQuantityRequirements "
                   "WHERE UnitType=? AND ResourceType='RESOURCE_IRON' AND Cost=1",
                   ("UNIT_KADAMBA_FOREST_GUARD",)) == 1,
            "Forest Guard Iron requirement is missing")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Unit_ClassUpgrades "
                   "WHERE UnitType=? AND UnitClassType='UNITCLASS_LONGSWORDSMAN'",
                   ("UNIT_KADAMBA_FOREST_GUARD",)) == 1,
            "Forest Guard upgrade path is missing")
    promotions = {
        row[0] for row in database.execute(
            "SELECT PromotionType FROM Unit_FreePromotions WHERE UnitType=?",
            ("UNIT_KADAMBA_FOREST_GUARD",),
        )
    }
    require({"PROMOTION_KADAMBA_WOODLAND_DEFENDER", "PROMOTION_WOODSMAN"} <= promotions,
            "Forest Guard promotions are incomplete")
    print("PASS Temple and Forest Guard full-row inheritance and auxiliary data")


def validate_database(database_path: Path, project: ET.ElementTree) -> None:
    source = sqlite3.connect(str(database_path))
    database = sqlite3.connect(":memory:")
    source.backup(database)
    source.close()

    snapshots = {
        "temple": row_dict(database, "Buildings", "Type", "BUILDING_TEMPLE"),
        "swordsman": row_dict(database, "Units", "Type", "UNIT_SWORDSMAN"),
    }
    building_tables = tables_with_source_rows(
        database, "BuildingType", "BUILDING_TEMPLE")
    unit_tables = tables_with_source_rows(database, "UnitType", "UNIT_SWORDSMAN")
    require(building_tables == BUILDING_AUXILIARY_COPIED,
            f"unreviewed base Temple auxiliary tables: "
            f"{sorted(building_tables ^ BUILDING_AUXILIARY_COPIED)}")
    require(unit_tables == UNIT_AUXILIARY_COPIED,
            f"unreviewed base Swordsman auxiliary tables: "
            f"{sorted(unit_tables ^ UNIT_AUXILIARY_COPIED)}")

    apply_project_database(database, project)
    for table, key, value in (
        ("Civilizations", "Type", "CIVILIZATION_KADAMBA"),
        ("Leaders", "Type", "LEADER_MAYURASHARMA"),
        ("Traits", "Type", "TRAIT_KADAMBA_SCHOLARS_DEFIANCE"),
        ("Buildings", "Type", "BUILDING_KADAMBA_TEMPLE"),
        ("Units", "Type", "UNIT_KADAMBA_FOREST_GUARD"),
    ):
        require(scalar(database,
                       f"SELECT COUNT(*) FROM {quote_identifier(table)} "
                       f"WHERE {quote_identifier(key)}=?", (value,)) == 1,
                f"{value} must exist exactly once")

    require(scalar(database,
                   "SELECT COUNT(*) FROM Civilization_BuildingClassOverrides "
                   "WHERE CivilizationType=? AND BuildingClassType=? AND BuildingType=?",
                   ("CIVILIZATION_KADAMBA", "BUILDINGCLASS_TEMPLE",
                    "BUILDING_KADAMBA_TEMPLE")) == 1,
            "Temple civilization override is incorrect")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Civilization_UnitClassOverrides "
                   "WHERE CivilizationType=? AND UnitClassType=? AND UnitType=?",
                   ("CIVILIZATION_KADAMBA", "UNITCLASS_SWORDSMAN",
                    "UNIT_KADAMBA_FOREST_GUARD")) == 1,
            "Forest Guard civilization override is incorrect")
    validate_inheritance(database, snapshots)

    require(scalar(database,
                   "SELECT COUNT(*) FROM Leader_Flavors WHERE LeaderType=?",
                   ("LEADER_MAYURASHARMA",)) >= 30,
            "Mayurasharma leader flavors are incomplete")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Leader_MajorCivApproachBiases WHERE LeaderType=?",
                   ("LEADER_MAYURASHARMA",)) == 7,
            "major-civilization approach biases are incomplete")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Leader_MinorCivApproachBiases WHERE LeaderType=?",
                   ("LEADER_MAYURASHARMA",)) == 5,
            "minor-civilization approach biases are incomplete")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Building_Flavors WHERE BuildingType=?",
                   ("BUILDING_KADAMBA_TEMPLE",)) >= 4,
            "Kadamba Temple AI flavors are incomplete")
    require(scalar(database,
                   "SELECT COUNT(*) FROM Unit_Flavors WHERE UnitType=?",
                   ("UNIT_KADAMBA_FOREST_GUARD",)) >= 2,
            "Forest Guard AI flavors are incomplete")
    print("PASS database identities, overrides, promotions, resources, and AI data")

    optional_sql = (PROJECT_ROOT / "SQL" / "Kadamba_Balance_Optional.sql").read_text(
        encoding="utf-8-sig"
    )
    database.executescript(optional_sql)
    require(row_dict(database, "Buildings", "Type", "BUILDING_KADAMBA_TEMPLE")
            ["WonderProductionModifier"] == 5,
            "optional balance patch does not set the Temple Wonder bonus to 5")
    require(row_dict(database, "Units", "Type", "UNIT_KADAMBA_FOREST_GUARD")["Cost"] == 75,
            "optional balance patch does not set the Forest Guard cost to 75")
    print("PASS disabled optional balance patch syntax and values")
    database.close()


def dds_dimensions(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()[:128]
    require(data[:4] == b"DDS ", f"not a DDS file: {path}")
    height, width = struct.unpack_from("<II", data, 12)
    return width, height, data[84:88]


def validate_assets_and_localization() -> None:
    game_data = ET.parse(PROJECT_ROOT / "XML" / "Kadamba_GameData.xml")
    text_data = ET.parse(PROJECT_ROOT / "XML" / "Kadamba_Text.xml")
    tags = {
        row.attrib["Tag"]
        for row in text_data.getroot().findall(".//Row")
        if "Tag" in row.attrib
    }
    required_keys: set[str] = set()
    for element in game_data.getroot().iter():
        # CivilopediaTag is a prefix used to group entries, not a localized row.
        if element.tag == "CivilopediaTag" or element.text is None:
            continue
        value = element.text.strip()
        if value.startswith("TXT_KEY_") and (
            "KADAMBA" in value or "MAYURASHARMA" in value
        ):
            required_keys.add(value)
    inheritance_sql = (PROJECT_ROOT / "SQL" / "Kadamba_CoreInheritance.sql").read_text(
        encoding="utf-8-sig"
    )
    required_keys.update(
        value for value in re.findall(r"TXT_KEY_[A-Z0-9_]+", inheritance_sql)
        if "KADAMBA" in value or "MAYURASHARMA" in value
    )
    require(required_keys <= tags,
            f"missing localization keys: {sorted(required_keys - tags)}")

    atlas_rows = game_data.getroot().findall("./IconTextureAtlases/Row")
    atlases: dict[str, set[int]] = {}
    for row in atlas_rows:
        atlas = row.findtext("Atlas", "")
        size = int(row.findtext("IconSize", "0"))
        filename = row.findtext("Filename", "")
        atlases.setdefault(atlas, set()).add(size)
        require((PROJECT_ROOT / filename).is_file(), f"atlas texture missing: {filename}")
    required_atlases = {
        "KADAMBA_ICON_ATLAS", "KADAMBA_ALPHA_ATLAS", "KADAMBA_LEADER_ATLAS",
        "KADAMBA_UNIT_ATLAS", "KADAMBA_UNIT_FLAG_ATLAS",
    }
    require(required_atlases <= set(atlases), "one or more custom icon atlases are missing")
    for atlas in required_atlases:
        require(atlases[atlas] == {32, 45, 64, 80, 128, 256},
                f"atlas sizes are incomplete for {atlas}: {sorted(atlases[atlas])}")

    map_path = PROJECT_ROOT / "Art" / "Map_Kadamba_360x412.dds"
    dom_path = PROJECT_ROOT / "Art" / "DOM_Kadamba.dds"
    require(dds_dimensions(map_path) == (360, 412, b"DXT5"),
            f"map DDS must be 360x412 DXT5, got {dds_dimensions(map_path)}")
    require(dds_dimensions(dom_path)[:2] == (1024, 768),
            f"Dawn of Man DDS must be 1024x768, got {dds_dimensions(dom_path)[:2]}")
    print("PASS localization, atlas references, and DDS dimensions/encoding")


def validate_lua_contracts() -> None:
    trait = (PROJECT_ROOT / "Lua" / "KadambaTrait.lua").read_text(encoding="utf-8-sig")
    state = (PROJECT_ROOT / "Lua" / "KadambaState.lua").read_text(encoding="utf-8-sig")
    panel = (PROJECT_ROOT / "UI" / "KadambaBonusPanel.lua").read_text(encoding="utf-8-sig")
    optional = (PROJECT_ROOT / "SQL" / "Kadamba_Balance_Optional.sql").read_text(
        encoding="utf-8-sig"
    )

    for snippet in (
        "GameEvents.PlayerDoTurn.Add(OnPlayerDoTurn)",
        "local MOMENTUM_TURNS = 8",
        "local TRADE_BONUS_PERCENT = 0.25",
        "State.GetLastTradePayoutTurn(playerID) == currentTurn",
        "State.SetLastTradePayoutTurn(playerID, currentTurn)",
        "GameEvents.UnitCreated.Add(OnUnitCreated)",
        "GameEvents.UnitUpgraded.Add(OnUnitUpgraded)",
        "GameEvents.UnitConverted.Add(OnUnitConverted)",
        "GameEvents.PlayerCityFounded.Add(OnCityFounded)",
        "GameEvents.CityCaptureComplete.Add(OnCityCaptureComplete)",
    ):
        require(snippet in trait, f"Lua lifecycle contract missing: {snippet}")
    require("ActivePlayerTurnStart" not in trait,
            "gameplay must not use ActivePlayerTurnStart")
    require(not re.search(r"(?m)^function\s+", trait),
            "KadambaTrait.lua exposes unnamespaced global functions")
    require(not re.search(r"(?m)^function\s+", panel),
            "KadambaBonusPanel.lua exposes unnamespaced global functions")
    require("KADAMBA_" in state and "CampaignFingerprint" in state,
            "campaign-scoped save namespace is missing")
    for forbidden in ("ChangeGold", "SetNumRealBuilding", "SetHasPromotion"):
        require(forbidden not in panel, f"UI mutates gameplay through {forbidden}")
    require("TradeRouteResourceModifier" not in optional,
            "optional SQL still claims to change Lua Trade Gold")

    compiler = shutil.which("luac") or shutil.which("luac5.1")
    if compiler:
        for relative in (
            "Lua/KadambaState.lua", "Lua/KadambaTrait.lua", "Lua/KadambaLoader.lua",
            "UI/KadambaBonusPanel.lua",
        ):
            subprocess.run([compiler, "-p", str(PROJECT_ROOT / relative)], check=True)
        print(f"PASS Lua syntax via {compiler}")
    else:
        print("NOTE Lua compiler unavailable; lifecycle/static contracts validated instead")
    print("PASS Lua lifecycle, persistence, idempotence, ownership, and UI separation")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", help="path to a clean BNW Civ5CoreDatabase.db")
    args = parser.parse_args()

    project = ET.parse(PROJECT_PATH)
    validate_packaging(project)
    database_path = resolve_database(args.database)
    print(f"Using base database: {database_path}")
    validate_database(database_path, project)
    validate_assets_and_localization()
    validate_lua_contracts()
    print("All Kadamba validation checks passed.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ET.ParseError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
