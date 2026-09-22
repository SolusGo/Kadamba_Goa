print("KADAMBA TRAIT LOADED")

local State = KadambaState
local iCiv = GameInfoTypes.CIVILIZATION_KADAMBA
local iCoastalBuilding = GameInfoTypes.BUILDING_KADAMBA_COASTAL_BONUS
local iJungleBuilding = GameInfoTypes.BUILDING_KADAMBA_JUNGLE_BONUS
local iMomentumBuilding = GameInfoTypes.BUILDING_KADAMBA_SCHOLAR_MOMENTUM
local iCivilService = GameInfoTypes.TECH_CIVIL_SERVICE
local iFriendlyPromotion = GameInfoTypes.PROMOTION_KADAMBA_FRIENDLY_LANDS

-- Intentionally fixed across game speeds: each technology grants eight turns.
local MOMENTUM_TURNS = 8
local TRADE_BONUS_PERCENT = 0.25

local function IsKadamba(player)
	return player and player:IsAlive() and player:GetCivilizationType() == iCiv
end

local function IsEligibleLandCombatUnit(unit)
	return unit ~= nil
		and unit:IsCombatUnit()
		and unit:GetDomainType() == DomainTypes.DOMAIN_LAND
end

local function ReconcileCity(city, ownerIsKadamba, hasCivilService, momentumActive)
	city:SetNumRealBuilding(
		iCoastalBuilding,
		ownerIsKadamba and city:IsCoastal() and 1 or 0)
	city:SetNumRealBuilding(
		iJungleBuilding,
		ownerIsKadamba and hasCivilService and 1 or 0)
	city:SetNumRealBuilding(
		iMomentumBuilding,
		ownerIsKadamba and momentumActive and 1 or 0)
end

local function ReconcileCities(playerID)
	local player = Players[playerID]
	if player == nil or not player:IsAlive() then return end

	local ownerIsKadamba = IsKadamba(player)
	local hasCivilService = ownerIsKadamba
		and Teams[player:GetTeam()]:IsHasTech(iCivilService)
	local momentumActive = ownerIsKadamba
		and Game.GetGameTurn() <= State.GetMomentumUntilTurn(playerID)

	for city in player:Cities() do
		ReconcileCity(city, ownerIsKadamba, hasCivilService, momentumActive)
	end
end

local function ReconcileUnit(playerID, unitID)
	local player = Players[playerID]
	if player == nil then return end
	local unit = player:GetUnitByID(unitID)
	if unit == nil then return end

	local shouldHavePromotion = IsKadamba(player)
		and IsEligibleLandCombatUnit(unit)
	if unit:IsHasPromotion(iFriendlyPromotion) ~= shouldHavePromotion then
		unit:SetHasPromotion(iFriendlyPromotion, shouldHavePromotion)
	end
end

local function ReconcileUnits(playerID)
	local player = Players[playerID]
	if player == nil or not player:IsAlive() then return end
	local ownerIsKadamba = IsKadamba(player)

	for unit in player:Units() do
		local shouldHavePromotion = ownerIsKadamba
			and IsEligibleLandCombatUnit(unit)
		if unit:IsHasPromotion(iFriendlyPromotion) ~= shouldHavePromotion then
			unit:SetHasPromotion(iFriendlyPromotion, shouldHavePromotion)
		end
	end
end

local function ApplyTradeBonus(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return 0 end

	local currentTurn = Game.GetGameTurn()
	if State.GetLastTradePayoutTurn(playerID) == currentTurn then
		return 0
	end

	local totalRaw = 0
	for _, route in ipairs(player:GetTradeRoutes()) do
		local gold = (route.FromGPT or 0) / 100
		totalRaw = totalRaw + (gold * TRADE_BONUS_PERCENT)
	end

	local newTotal = State.GetTradeRemainder(playerID) + totalRaw
	local payout = math.floor(newTotal)
	State.SetTradeRemainder(playerID, newTotal - payout)
	State.SetLastTradePayoutTurn(playerID, currentTurn)

	if payout > 0 then
		player:ChangeGold(payout)
	end
	return payout
end

local function RefreshPlayer(playerID)
	ReconcileCities(playerID)
	ReconcileUnits(playerID)
end

local function OnPlayerDoTurn(playerID)
	-- Every player is reconciled so transferred units and captured cities cannot
	-- retain Kadamba-only state under a foreign owner.
	RefreshPlayer(playerID)
	ApplyTradeBonus(playerID)
end

local function OnTechResearched(teamID, techID)
	for playerID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
		local player = Players[playerID]
		if IsKadamba(player) and player:GetTeam() == teamID then
			State.SetMomentumUntilTurn(
				playerID,
				Game.GetGameTurn() + MOMENTUM_TURNS - 1)
			ReconcileCities(playerID)
		end
	end
end

local function OnUnitCreated(playerID, unitID)
	ReconcileUnit(playerID, unitID)
end

local function OnUnitUpgraded(playerID, oldUnitID, newUnitID)
	ReconcileUnit(playerID, newUnitID)
end

local function OnUnitConverted(oldPlayerID, newPlayerID, oldUnitID, newUnitID)
	ReconcileUnit(newPlayerID, newUnitID)
end

local function OnCityFounded(playerID, x, y)
	ReconcileCities(playerID)
end

local function OnCityCaptureComplete(oldOwnerID, isCapital, x, y, newOwnerID)
	ReconcileCities(oldOwnerID)
	ReconcileCities(newOwnerID)
end

local function Initialize()
	for playerID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
		RefreshPlayer(playerID)
	end
end

GameEvents.TeamTechResearched.Add(OnTechResearched)
GameEvents.PlayerDoTurn.Add(OnPlayerDoTurn)

if GameEvents.UnitCreated ~= nil then
	GameEvents.UnitCreated.Add(OnUnitCreated)
elseif Events.SerialEventUnitCreated ~= nil then
	Events.SerialEventUnitCreated.Add(OnUnitCreated)
end
if GameEvents.UnitUpgraded ~= nil then
	GameEvents.UnitUpgraded.Add(OnUnitUpgraded)
end
if GameEvents.UnitConverted ~= nil then
	GameEvents.UnitConverted.Add(OnUnitConverted)
end
if GameEvents.PlayerCityFounded ~= nil then
	GameEvents.PlayerCityFounded.Add(OnCityFounded)
end
if GameEvents.CityCaptureComplete ~= nil then
	GameEvents.CityCaptureComplete.Add(OnCityCaptureComplete)
end

Events.SequenceGameInitComplete.Add(Initialize)
