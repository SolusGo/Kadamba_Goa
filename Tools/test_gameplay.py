"""Deterministic regression model for Kadamba lifecycle invariants.

This does not emulate the Civ V engine. validate_mod.py separately checks that
the shipped Lua and database actions implement the constants and hooks modeled
here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPOSITORY_ROOT / "Kadamba Dynasty (Goa) - Custom Civilization (v 1)"


@dataclass
class SaveStore:
    values: dict[str, float] = field(default_factory=dict)

    def key(self, campaign: str, name: str, player_id: int) -> str:
        return f"KADAMBA_{campaign}_{name}_{player_id}"

    def get(self, campaign: str, name: str, player_id: int, default: float) -> float:
        return self.values.get(self.key(campaign, name, player_id), default)

    def set(self, campaign: str, name: str, player_id: int, value: float) -> None:
        self.values[self.key(campaign, name, player_id)] = value


@dataclass
class City:
    coastal: bool
    coastal_dummy: int = 0
    jungle_dummy: int = 0
    momentum_dummy: int = 0


@dataclass
class Unit:
    land: bool
    combat: bool
    friendly_promotion: bool = False
    woodland_defender: bool = False


@dataclass
class Player:
    player_id: int
    kadamba: bool
    gold: int = 0
    civil_service: bool = False
    routes_from_gpt: list[int] = field(default_factory=list)
    cities: list[City] = field(default_factory=list)
    units: list[Unit] = field(default_factory=list)


class KadambaModel:
    MOMENTUM_TURNS = 8
    TRADE_BONUS = 0.25

    def __init__(self, campaign: str, store: SaveStore, players: list[Player]):
        self.campaign = campaign
        self.store = store
        self.players = {player.player_id: player for player in players}
        self.turn = 0

    def momentum_until(self, player_id: int) -> int:
        return int(self.store.get(
            self.campaign, "MomentumUntilTurn", player_id, -1))

    def research_technology(self, player_id: int) -> None:
        player = self.players[player_id]
        if not player.kadamba:
            return
        self.store.set(
            self.campaign,
            "MomentumUntilTurn",
            player_id,
            self.turn + self.MOMENTUM_TURNS - 1,
        )
        self.reconcile_cities(player)

    def reconcile_cities(self, player: Player) -> None:
        momentum = player.kadamba and self.turn <= self.momentum_until(player.player_id)
        for city in player.cities:
            city.coastal_dummy = int(player.kadamba and city.coastal)
            city.jungle_dummy = int(player.kadamba and player.civil_service)
            city.momentum_dummy = int(momentum)

    @staticmethod
    def reconcile_units(player: Player) -> None:
        for unit in player.units:
            unit.friendly_promotion = player.kadamba and unit.land and unit.combat

    def trade_payout(self, player: Player) -> int:
        if not player.kadamba:
            return 0
        last_turn = int(self.store.get(
            self.campaign, "LastTradePayoutTurn", player.player_id, -1))
        if last_turn == self.turn:
            return 0
        raw = sum(value / 100 for value in player.routes_from_gpt) * self.TRADE_BONUS
        remainder = self.store.get(
            self.campaign, "TradeGoldRemainder", player.player_id, 0)
        total = raw + remainder
        payout = int(total // 1)
        self.store.set(
            self.campaign, "TradeGoldRemainder", player.player_id, total - payout)
        self.store.set(
            self.campaign, "LastTradePayoutTurn", player.player_id, self.turn)
        player.gold += payout
        return payout

    def player_do_turn(self, player_id: int) -> int:
        player = self.players[player_id]
        self.reconcile_cities(player)
        self.reconcile_units(player)
        return self.trade_payout(player)


checks_run = 0


def check(name: str, condition: bool) -> None:
    global checks_run
    assert condition, name
    checks_run += 1
    print(f"PASS {checks_run:02d}: {name}")


def main() -> None:
    store = SaveStore()
    human = Player(0, True, routes_from_gpt=[800], cities=[City(True)])
    ai = Player(1, True, routes_from_gpt=[400], cities=[City(False)])
    foreign = Player(2, False, routes_from_gpt=[1200], cities=[City(True)])
    model = KadambaModel("campaign-A", store, [human, ai, foreign])

    check("human Kadamba turn pays Trade Gold once", model.player_do_turn(0) == 2)
    check("AI Kadamba turn pays Trade Gold once", model.player_do_turn(1) == 1)
    check("non-Kadamba turn pays no Trade Gold", model.player_do_turn(2) == 0)
    check("duplicate processing on the same turn is idempotent", model.player_do_turn(0) == 0)

    fractional = Player(3, True, routes_from_gpt=[100])
    fraction_model = KadambaModel("campaign-A", store, [fractional])
    check("fractional Trade Gold is retained", fraction_model.player_do_turn(3) == 0
          and store.get("campaign-A", "TradeGoldRemainder", 3, -1) == 0.25)
    fraction_model.turn = 1
    fraction_model.player_do_turn(3)
    fraction_model.turn = 2
    fraction_model.player_do_turn(3)
    fraction_model.turn = 3
    check("fractional Trade Gold eventually pays", fraction_model.player_do_turn(3) == 1)

    reloaded = KadambaModel("campaign-A", store, [fractional])
    reloaded.turn = 4
    reloaded.player_do_turn(3)
    check("save/reload preserves the fractional remainder",
          store.get("campaign-A", "TradeGoldRemainder", 3, -1) == 0.25)
    clean_campaign = KadambaModel("campaign-B", store, [fractional])
    check("a new campaign cannot inherit an old remainder",
          store.get("campaign-B", "TradeGoldRemainder", 3, 0) == 0)

    model.turn = 20
    model.research_technology(0)
    check("technology research begins Momentum", human.cities[0].momentum_dummy == 1)
    check("Momentum uses the intended eight-turn inclusive expiry",
          model.momentum_until(0) == 27)
    model.turn = 27
    model.player_do_turn(0)
    check("Momentum remains active on its eighth turn",
          human.cities[0].momentum_dummy == 1)
    model.turn = 28
    model.player_do_turn(0)
    check("Momentum expires for a human Kadamba", human.cities[0].momentum_dummy == 0)

    model.turn = 30
    model.research_technology(1)
    model.turn = 38
    model.player_do_turn(1)
    check("Momentum expires for an AI Kadamba", ai.cities[0].momentum_dummy == 0)
    model.turn = 40
    model.research_technology(0)
    first_until = model.momentum_until(0)
    model.turn = 43
    model.research_technology(0)
    check("another technology refreshes rather than stacks Momentum",
          first_until == 47 and model.momentum_until(0) == 50)

    active_city = City(False)
    human.cities.append(active_city)
    model.player_do_turn(0)
    check("a new city during Momentum receives the dummy", active_city.momentum_dummy == 1)
    model.turn = 51
    expired_city = City(False)
    human.cities.append(expired_city)
    model.player_do_turn(0)
    check("a new city after Momentum does not receive the dummy",
          expired_city.momentum_dummy == 0)
    check("a coastal Kadamba city receives its dummy", human.cities[0].coastal_dummy == 1)
    check("an inland Kadamba city does not receive the coastal dummy",
          active_city.coastal_dummy == 0)

    captured = human.cities.pop(0)
    foreign.cities.append(captured)
    model.player_do_turn(2)
    check("city ownership change strips Kadamba-only dummy state",
          (captured.coastal_dummy, captured.jungle_dummy, captured.momentum_dummy) == (0, 0, 0))
    human.civil_service = True
    model.player_do_turn(0)
    check("Civil Service activates Jungle Production", active_city.jungle_dummy == 1)
    later_city = City(True)
    human.cities.append(later_city)
    model.player_do_turn(0)
    check("a new city after Civil Service receives the Jungle dummy",
          later_city.jungle_dummy == 1)

    land = Unit(True, True)
    civilian = Unit(True, False)
    naval = Unit(False, True)
    air = Unit(False, True)
    human.units.extend([land, civilian, naval, air])
    model.player_do_turn(0)
    check("Kadamba land combat units receive the friendly-land promotion",
          land.friendly_promotion)
    check("civilian, naval, and air units do not receive the promotion",
          not civilian.friendly_promotion and not naval.friendly_promotion
          and not air.friendly_promotion)
    upgraded = Unit(True, True, woodland_defender=True)
    human.units.append(upgraded)
    model.player_do_turn(0)
    check("an upgraded Kadamba unit keeps both persistent promotions",
          upgraded.friendly_promotion and upgraded.woodland_defender)
    human.units.remove(upgraded)
    foreign.units.append(upgraded)
    model.player_do_turn(2)
    check("a transferred Kadamba unit loses the ownership promotion",
          not upgraded.friendly_promotion and upgraded.woodland_defender)
    captured_foreign = Unit(True, True)
    human.units.append(captured_foreign)
    model.player_do_turn(0)
    check("a captured foreign unit entering Kadamba ownership gains the promotion",
          captured_foreign.friendly_promotion)

    sql = (PROJECT_ROOT / "SQL" / "Kadamba_CoreInheritance.sql").read_text(
        encoding="utf-8-sig"
    )
    xml = (PROJECT_ROOT / "XML" / "Kadamba_GameData.xml").read_text(
        encoding="utf-8-sig"
    )
    trait = (PROJECT_ROOT / "Lua" / "KadambaTrait.lua").read_text(
        encoding="utf-8-sig"
    )
    panel = (PROJECT_ROOT / "UI" / "KadambaBonusPanel.lua").read_text(
        encoding="utf-8-sig"
    )
    check("Kadamba Temple requires the base Temple prerequisite classes",
          "Building_ClassesNeededInCity" in sql and "BUILDING_TEMPLE" in sql)
    check("Kadamba Temple clones normal Temple functionality",
          "CREATE TEMP TABLE KadambaTempleClone" in sql
          and "SELECT * FROM Buildings" in sql)
    check("Forest Guard clones expected Swordsman functionality",
          "CREATE TEMP TABLE KadambaForestGuardClone" in sql
          and "SELECT * FROM Units" in sql)
    check("Forest Guard's Woodland Defender persists through upgrades",
          "<LostWithUpgrade>false</LostWithUpgrade>" in xml
          and "PROMOTION_KADAMBA_WOODLAND_DEFENDER" in sql)
    check("AI recognizes the Temple and Forest Guard through flavors",
          "Building_Flavors" in sql and "Unit_Flavors" in sql
          and "<Leader_Flavors>" in xml)
    check("UI failure cannot disable core gameplay",
          "KadambaBonusPanel" not in trait
          and all(token not in panel for token in (
              "ChangeGold", "SetNumRealBuilding", "SetHasPromotion")))

    assert checks_run == 32, f"expected 32 regression checks, ran {checks_run}"
    print("All 32 Kadamba gameplay regression checks passed.")


if __name__ == "__main__":
    main()
