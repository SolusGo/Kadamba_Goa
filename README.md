<div align="center">

# Kadamba Dynasty of Goa

### A custom civilization for Sid Meier's Civilization V: Brave New World

**Temples, trade, scholarship, and quiet strength on the Konkan coast.**

![Version](https://img.shields.io/badge/version-1-goldenrod)
![Status](https://img.shields.io/badge/status-alpha-darkgreen)
![Game](https://img.shields.io/badge/Civilization%20V-Brave%20New%20World-6b8e23)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

</div>

---

The **Kadamba Dynasty**, led by **Mayurasharma**, is a coastal-jungle civilization built around prosperous port cities, productive jungle interiors, temple culture, and defensive warfare. Its economy rewards careful settlement along the sea, while a well-timed technology path creates recurring bursts of building production across the empire.

The result is a flexible builder civilization with strong defensive tools. Kadamba is most comfortable growing behind wooded terrain, developing a network of coastal cities, and converting scientific progress into infrastructure, wonders, and long-term economic strength.

## Contents

- [Civilization overview](#civilization-overview)
- [Unique ability: Scholar's Defiance](#unique-ability-scholars-defiance)
- [Unique building: Kadamba Temple](#unique-building-kadamba-temple)
- [Unique unit: Forest Guard](#unique-unit-forest-guard)
- [How to play](#how-to-play)
- [Victory paths](#victory-paths)
- [Policy and empire synergies](#policy-and-empire-synergies)
- [Kadamba bonus panel](#kadamba-bonus-panel)
- [Reliability and AI behavior](#reliability-and-ai-behavior)
- [Installation and building](#installation-and-building)
- [Optional balance patch](#optional-balance-patch)
- [Compatibility and alpha notes](#compatibility-and-alpha-notes)
- [Project structure](#project-structure)

## Civilization overview

| Category | Details |
|---|---|
| **Civilization** | Kadamba Dynasty |
| **Leader** | Mayurasharma |
| **Unique Ability** | Scholar's Defiance |
| **Unique Building** | Kadamba Temple, replacing the Temple |
| **Unique Unit** | Forest Guard, replacing the Swordsman |
| **Start bias** | Ocean and Jungle |
| **Primary strengths** | Coastal economy, Culture, building production, wooded-terrain combat |
| **Secondary strengths** | Faith, Wonders, land-unit experience, defensive warfare |
| **Best terrain** | Coastal regions with workable Jungle and Forest |
| **Preferred victories** | Science, Culture, or Diplomacy; defensive Domination is also viable |

Kadamba begins with the standard Palace, Agriculture, and a Settler. Its start settings strongly encourage an ocean-adjacent capital in or near a jungle region.

The city list currently includes:

- Banavasi
- Gopakapattana
- Chandrapura
- Halsi
- Vainginim
- Konkanapura

## Unique ability: Scholar's Defiance

> **Coastal Cities gain +2 Gold and +1 Culture. After Civil Service, Jungle tiles worked by Kadamba cities yield +1 Production. Trade Routes generate +25% Gold. After discovering a technology, cities gain +15% Production toward buildings for 8 turns. Units receive +10% Combat Strength in friendly lands.**

Scholar's Defiance combines five bonuses that reinforce one another throughout the game.

### Coastal prosperity

Every coastal city receives:

- **+2 Gold** per turn
- **+1 Culture** per turn

This is a flat city yield, so it begins helping immediately and does not depend on population or worked tiles. The Gold helps pay building and unit maintenance, while the Culture makes a chain of coastal settlements much easier to develop.

The ability rewards expansion, but placement matters more than raw city count. A coastal city with poor food or production still takes time to become useful. Look for locations that combine sea access with rivers, hills, resources, Forest, or Jungle.

### Jungle production after Civil Service

Once **Civil Service** is researched, every worked Jungle tile in a Kadamba city produces **+1 Production**.

This changes the usual Jungle calculation. Instead of clearing every Jungle for immediate production or farms, Kadamba can preserve large areas and turn them into flexible long-term tiles. Later improvements and science bonuses can then sit on top of the extra Production.

Practical consequences:

- Avoid clearing all Jungle during the early game merely for short-term gains.
- Mark strong Jungle clusters for later population growth.
- Prioritize Civil Service when several cities can work multiple Jungle tiles.
- Jungle cities become excellent locations for infrastructure during Scholar Momentum.
- Forest does **not** receive the Production yield; Forest instead supports the Forest Guard's combat role.

### Trade-route income

Kadamba gains additional Gold equal to **25% of the Gold generated on its active trade routes**.

The bonus is implemented as a treasury payout at the beginning of each Kadamba player's turn. It works for human and AI players through `GameEvents.PlayerDoTurn`. Fractions are retained between turns rather than discarded. For example, a calculated bonus of 2.75 Gold pays 2 immediately and carries the remaining 0.75 forward.

Each campaign uses its own deterministic save-data namespace, so a remainder or Momentum timer from an older game cannot leak into a new campaign. The payout is also guarded by a per-player, per-turn marker: duplicate event processing cannot award the Gold twice.

Because this is a separate payout, the route-selection interface may continue to show the route's normal value. The Kadamba bonus panel reports the extra payout and its unrounded value.

To get the most from the bonus:

- Protect high-value routes rather than treating caravans and cargo ships as disposable.
- Favor profitable international routes when food or production routes are not urgently needed.
- Use coastal cities as safe cargo-ship hubs; sea routes generally have greater reach and strong income potential.
- Re-evaluate routes after new technologies, buildings, ideologies, or diplomatic changes improve their base Gold.

### Scholar Momentum

Every time Kadamba discovers a technology, all of its cities receive **+15% Production toward buildings for 8 turns**.

Important behavior:

- The duration includes the turn on which the technology is completed.
- Discovering another technology refreshes the window to eight turns.
- The modifier does not stack with itself.
- The effect applies empire-wide.
- The duration is a fixed eight game turns and is not scaled by game speed.

Momentum rewards planning the build queue around research completion. Expensive infrastructure should be prepared just before a technology finishes so that as much of its cost as possible is completed during the bonus window. In later eras, a strong science rate can keep Momentum active almost continuously.

### Defiance in friendly lands

Kadamba land combat units receive **+10% Combat Strength in friendly territory**.

The promotion is granted to existing and newly created land combat units when the trait refreshes, and it remains present through upgrades. This makes Kadamba difficult to dislodge from its own territory and particularly dangerous when its borders contain Forest or Jungle.

The bonus is defensive by nature: it does not help deep inside an enemy empire. Use roads, forts, citadels, ranged support, and wooded chokepoints to force opponents to fight where the modifier is active.

## Unique building: Kadamba Temple

The **Kadamba Temple** replaces the ordinary Temple and becomes available at **Philosophy**. Its database definition is cloned from the installed Brave New World Temple before Kadamba's unique effects are applied, preserving the normal Shrine requirement, purchase rules, Religion flavor, Faith yield, art metadata, and other base functionality.

| Statistic | Kadamba Temple |
|---|---:|
| Production cost | 100 |
| Gold maintenance | 2 per turn |
| Faith | +2 |
| Culture | +1 |
| Wonder production | +10% in this city |
| Experience for newly trained land units | +5 XP |

The Kadamba Temple keeps the core religious function of a Temple while adding three distinct roles.

### Culture and border growth

The additional Culture stacks naturally with the Culture from coastal cities. A coastal city with a Kadamba Temple therefore contributes **+2 Culture per turn** from civilization-specific effects before other buildings, specialists, or modifiers are counted.

### Wonder construction

Its **+10% Wonder Production** makes established Temple cities good candidates for wonder specialization. The effect is local, so Temples should be built early in cities that already have hills, production resources, internal production routes, or other Wonder bonuses.

Scholar Momentum and the Kadamba Temple serve complementary roles: Momentum accelerates the surrounding infrastructure, while the Temple improves the city's Wonder construction directly.

### Military training

Every newly trained land unit in a city with a Kadamba Temple receives **+5 XP**. The amount is modest on its own, but it combines with Barracks, Armories, Military Academies, policies, and other experience sources. Temple cities can therefore act as hybrid cultural, religious, and military centers.

## Unique unit: Forest Guard

The **Forest Guard** replaces the Swordsman. It is an early melee unit designed to control wooded territory and defend the Kadamba heartland. Its database row and auxiliary data are cloned from the installed Swordsman, preserving normal AI roles, flavors, Iron requirement, purchase settings, sounds, and upgrade behavior.

| Statistic | Forest Guard |
|---|---:|
| Required technology | Iron Working |
| Combat Strength | 14 |
| Production cost | 70 |
| Movement | 2 |
| Strategic resource | 1 Iron |
| Upgrades to | Longswordsman |
| Obsolete at | Steel |

Compared with the standard Brave New World Swordsman, the Forest Guard has the same base Combat Strength while costing slightly less to produce.

### Free promotions

**Woodland Defender**

- +20% Combat Strength when attacking in Forest or Jungle
- +20% Combat Strength when defending in Forest or Jungle
- The promotion is retained when the unit upgrades

**Woodsman**

- Improves movement through Forest and Jungle

These promotions turn rough wooded terrain from an obstacle into a road network and defensive screen. A Forest Guard fighting in Forest or Jungle inside friendly territory can benefit from both Woodland Defender and Scholar's Defiance, making it much stronger than its base value suggests.

### Tactical use

- Fortify Forest Guards on wooded hills, river crossings, and narrow approaches.
- Keep ranged units immediately behind them; the Guards absorb attacks while ranged fire does the damage.
- Use superior woodland movement to rotate injured units, flank invaders, and punish embarked or isolated enemies.
- Escort Workers and Settlers through unsettled Jungle regions.
- Preserve useful Forest and Jungle near exposed borders instead of clearing every tile.
- Upgrade experienced Guards rather than replacing them so Woodland Defender continues to contribute later in the game.

The Forest Guard is capable on offense when the battlefield is wooded, but it is not a universal rush unit. Open terrain and prolonged campaigns outside friendly borders remove much of Kadamba's advantage.

## How to play

### Opening: establish the coast

1. **Settle on the coast when the location is viable.** The capital immediately benefits from the coastal Gold and Culture, while sea access prepares it for cargo ships and naval infrastructure.
2. **Scout for a second coastal location with Jungle.** The ideal city contributes to the early coastal economy and becomes a productive Jungle city after Civil Service.
3. **Locate Iron.** Even if an early war is not planned, access to Iron allows Forest Guards to secure expansion routes and deter aggression.
4. **Preserve high-quality Jungle clusters.** Clear selectively for critical resources, city placement, farms, or emergency production—not by default.
5. **Build a stable economic base.** Scholar Momentum is strongest when cities already have enough population and raw Production to take advantage of its percentage modifier.

### Classical era: choose the order of power spikes

Kadamba has three important early-to-midgame technologies:

- **Iron Working** unlocks the Forest Guard.
- **Philosophy** unlocks the Kadamba Temple.
- **Civil Service** activates Jungle Production.

The correct order depends on the map.

- Under military pressure, take Iron Working early and establish Forest Guard chokepoints.
- With a productive capital and attractive Wonders, prioritize Philosophy and complete the Kadamba Temple.
- With several populous Jungle cities, accelerate toward Civil Service for the largest empire-wide economic gain.

Do not delay basic growth, happiness, or science solely to reach these technologies. The civilization scales through developed cities, not through a single isolated power spike.

### Medieval and Renaissance eras: compound the bonuses

This is where Kadamba's systems begin reinforcing each other:

- Civil Service turns preserved Jungle into productive land.
- Technology completions repeatedly trigger Scholar Momentum.
- Kadamba Temples add Culture and help selected cities compete for Wonders.
- Coastal cities support profitable cargo-ship routes.
- Upgraded Forest Guards remain strong defenders in wooded territory.

Use Momentum to complete Workshops, Universities, Markets, Harbors, and other infrastructure quickly. When possible, begin the expensive building shortly before research completes, then use the full eight-turn window to finish it.

### Industrial era and beyond: maintain momentum

Faster research makes the eight-turn production window easier to refresh. At this stage Kadamba can transition from a terrain-dependent early civilization into a broad economic engine.

- Keep science strong enough to maintain frequent technology completions.
- Use the building bonus to establish Factories, Public Schools, Research Labs, and ideology buildings.
- Continue protecting sea lanes; the trade bonus scales with the value of the underlying routes.
- Use upgraded Forest Guard veterans as durable defensive infantry.
- Concentrate Wonder attempts in cities with Kadamba Temples and strong base Production.

## Victory paths

| Victory | Suitability | Approach |
|---|---|---|
| **Science** | Excellent | Preserve Jungle, reach Civil Service, develop science buildings during Momentum, and use late-game research speed to keep the building modifier active. |
| **Culture** | Strong | Stack coastal Culture with Kadamba Temples, use specialized Temple cities for Wonders, and fund cultural development through trade. |
| **Diplomacy** | Strong | Build a broad coastal economy, maximize profitable routes, and convert the bonus Gold into city-state influence. |
| **Domination** | Situational | Defend efficiently with Forest Guards and the friendly-land modifier, then counterattack after an enemy has exhausted itself. Wooded maps are much more favorable. |
| **Religion** | Supportive, not specialized | Temples provide Faith and Culture, but the civilization has no direct Great Prophet, conversion, or religious-pressure bonus. Religion is best used to reinforce another victory plan. |

### Science victory

Science is the most natural long-term route. Jungle tiles can combine their Kadamba Production with later science improvements and buildings, reducing the normal tension between research terrain and city Production. Each technology then accelerates the construction of the next generation of scientific infrastructure.

The main risk is a slow start: preserved Jungle can limit early improvements before Civil Service. Balance long-term terrain value against immediate food and production needs.

### Culture victory

Flat Culture from coastal settlements and Kadamba Temples provides a reliable foundation. Choose one or two cities for Wonders instead of spreading production across the empire. Trade income can pay maintenance and support diplomatic agreements while the core cities focus on culture and tourism.

### Diplomatic victory

The coastal and trade-route Gold bonuses make city-state investment practical. A wide but disciplined network of coastal ports works well, provided happiness and defense remain under control. Protecting cargo ships is especially important because a pillaged route loses both its normal yield and the Kadamba bonus.

### Domination victory

Kadamba is better at **absorbing an attack and reversing it** than at crossing open terrain in an early all-in rush. Fight near your borders, use Forest Guards to hold wooded tiles, and attack after the opponent has lost units against your defensive modifiers.

## Policy and empire synergies

### Tradition

Tradition supports a compact empire with a powerful capital. It pairs well with a Wonder-focused Kadamba Temple and lets a smaller number of high-population cities work many productive Jungle tiles.

### Liberty

Liberty makes it easier to establish multiple coastal cities and multiply the flat Gold and Culture bonuses. Use it when the coastline offers several defensible settlement locations and sufficient happiness resources.

### Commerce and Exploration

Commerce strengthens the Gold economy, while Exploration is attractive on water-heavy maps with several ports. Either can reinforce the civilization's trade-and-coast identity.

### Rationalism

Rationalism supports the strongest late-game loop: faster research produces more technology completions, which refresh Scholar Momentum and accelerates the buildings that sustain science and production.

### Piety and Aesthetics

Piety can turn the Temple replacement into the center of a religious strategy. Aesthetics is the more direct choice for Culture Victory and benefits from the civilization's ability to construct cultural infrastructure quickly.

## Kadamba bonus panel

When the human player is Kadamba, an in-game panel displays the current state of the civilization's major bonuses:

- Number and combined yield of coastal cities
- Turns remaining on Scholar Momentum
- Whether the Civil Service Jungle bonus is active
- Expected next whole-Gold trade payout and the raw fractional bonus

The panel is an `InGameUIAddin` and appears near the upper-right portion of the interface. It automatically hides when the active player is not Kadamba.

The panel is presentation-only. Gold payouts, dummy buildings, promotions, timers, city ownership reconciliation, and AI processing all remain in the gameplay script if the panel fails to load.

## Reliability and AI behavior

The Alpha implementation includes lifecycle safeguards for normal single-player, AI-controlled Kadamba, hot-seat, and multiplayer contexts where the Civ V Lua events are supported:

- Every player's turn reconciles coastal, Jungle, and Momentum dummy buildings.
- Every player's turn grants or removes the friendly-land promotion according to current ownership and unit eligibility.
- Unit creation, upgrade, and conversion hooks apply promotion state promptly, with turn reconciliation as a safety net.
- City founding and capture hooks refresh dummy buildings promptly, with turn reconciliation as a safety net.
- Scholar Momentum expires authoritatively for both human and AI Kadamba.
- Trade income is campaign-scoped, fraction-preserving, and idempotent per player and turn.
- Mayurasharma has explicit leader flavors and major/minor civilization approach biases emphasizing defense, coastal growth, infrastructure, Gold, Culture, Religion, and Science over reckless conquest.
- The Kadamba Temple and Forest Guard inherit their base components' AI flavors.

Scholar Momentum intentionally remains **eight turns on every game speed**. This is a fixed design choice rather than an accidental omission; Quick games receive proportionally more value per technology than Epic or Marathon games.

## Installation and building

### Requirements

- Sid Meier's Civilization V
- Brave New World
- No other mods are declared as dependencies

### Build from the ModBuddy project

1. Clone or download this repository.
2. Open `Kadamba_Dynasty_Civ5_Mod.civ5sln` in the Civilization V SDK's ModBuddy.
3. Select the **Default**, **Deploy Only**, or **Package Only** configuration as needed.
4. Build the solution.
5. Start Civilization V and enable **Kadamba Dynasty (Goa) - Custom Civilization** in the Mods menu.

### Run validation and regression tests

With Python 3 installed, run these commands from the repository root:

```text
python Tools/validate_mod.py
python Tools/test_gameplay.py
```

The validator loads the project into a temporary copy of the local Brave New World core database. It checks project packaging, action order, VFS intent, Temple and Swordsman inheritance, Shrine and Iron requirements, promotions, AI data, localization, icon atlases, and DDS dimensions. It also reports any newly discovered base Temple or Swordsman auxiliary table that has not been explicitly reviewed.

The deterministic gameplay model contains 32 regression checks covering human and AI turns, payout idempotence, fractional persistence and campaign isolation, Momentum timing, city lifecycle, unit ownership and upgrades, inheritance, AI flavors, and UI/gameplay separation.

The repository tracks the source project rather than generated build products. ModBuddy's `Build`, `Packages`, `.civ5mod`, `.modinfo`, user-settings, and temporary files are intentionally excluded from Git.

### Existing built copy

If using a prebuilt folder, place the complete mod directory in:

```text
Documents\My Games\Sid Meier's Civilization 5\MODS
```

Then enable the mod from Civilization V's Mods menu before starting a game.

## Optional balance patch

`SQL/Kadamba_Balance_Optional.sql` is included in the project but is **not executed by the current ModBuddy actions**. It is intended as an optional starting point for a lower-powered variant.

The file currently makes these database changes when manually enabled after the core inheritance action:

- Reduces Kadamba Temple Wonder Production from 10% to 5%.
- Raises Forest Guard cost from 70 to 75 Production.

The playable 25% trade-Gold payout is controlled by `TRADE_BONUS_PERCENT` in `Lua/KadambaTrait.lua` and mirrored by the presentation-only UI. The old, misleading `TradeRouteResourceModifier` update has been removed because it did not change the scripted payout.

To activate the patch as part of a build, add it as an `UpdateDatabase` action in ModBuddy after `SQL/Kadamba_CoreInheritance.sql`. Review both Lua constants if a lower trade-Gold percentage is also desired.

## Compatibility and alpha notes

- The project is marked **Alpha** and affects saved games. Avoid removing it from a game in progress.
- Single-player, multiplayer, hot-seat, and macOS support are declared in the project metadata.
- Text is currently provided in English only.
- The civilization uses the Asian art style, the Indian civilization art definition, the Swordsman unit model, and Ramkhamhaeng's leader scene alongside its custom icons and static artwork.
- The bonus panel occupies a fixed interface location and may overlap with other UI mods that use the same area.
- Several trait effects are implemented through invisible buildings and promotions. Other mods that heavily replace city, unit, or turn-event behavior may require compatibility testing.
- No compatibility with major overhaul mods is claimed unless specifically tested.

## Project structure

```text
Kadamba_Goa/
├── Kadamba_Dynasty_Civ5_Mod.civ5sln
├── Kadamba Dynasty (Goa) - Custom Civilization (v 1)/
    ├── Kadamba_Dynasty_Civ5_Mod.civ5proj
    ├── Art/       # Civilization, leader, unit, map, and Dawn of Man textures
    ├── Lua/       # Campaign state, trait lifecycle, and Lua loader
    ├── SQL/       # Base-row inheritance and disabled optional balance patch
    ├── UI/        # In-game Kadamba bonus panel
    └── XML/       # Civilization data, units, buildings, promotions, and text
├── Tools/         # Database validator and deterministic gameplay tests
└── README.md
```

The active database actions load:

1. `XML/Kadamba_GameData.xml`
2. `SQL/Kadamba_CoreInheritance.sql`
3. `XML/Kadamba_Text.xml`

The active UI entry points load:

1. `Lua/KadambaLoader.lua`
2. `UI/KadambaBonusPanel.xml`

---

## Credits

**Author:** ThatOneYi  
**Special thanks:** Firaxis Games and the CivFanatics community

The Kadamba design draws on a realm associated with the western Deccan and Konkan region, expressed here through coastal prosperity, jungle development, temple culture, scholarship, and resilient defense.
