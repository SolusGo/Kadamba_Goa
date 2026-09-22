print("KADAMBA TRAIT LOADED")

local iCiv = GameInfoTypes.CIVILIZATION_KADAMBA
local iCoastalBuilding = GameInfoTypes.BUILDING_KADAMBA_COASTAL_BONUS
local iJungleBuilding = GameInfoTypes.BUILDING_KADAMBA_JUNGLE_BONUS
local iMomentumBuilding = GameInfoTypes.BUILDING_KADAMBA_SCHOLAR_MOMENTUM
local iCivilService = GameInfoTypes.TECH_CIVIL_SERVICE
local iFriendlyPromotion = GameInfoTypes.PROMOTION_KADAMBA_FRIENDLY_LANDS

local MOMENTUM_TURNS = 8
local TRADE_BONUS_PERCENT = 0.25

local saveData = Modding.OpenSaveData()

function IsKadamba(player)
	return player and player:IsAlive() and player:GetCivilizationType() == iCiv
end

function GetMomentumUntilTurn(playerID)
	local val = saveData.GetValue("KadambaMomentum_" .. playerID)
	return val and tonumber(val) or -1
end

function SetMomentumUntilTurn(playerID, turn)
	saveData.SetValue("KadambaMomentum_" .. playerID, tostring(turn))
end

function ApplyCoastal(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return end

	for city in player:Cities() do
		city:SetNumRealBuilding(iCoastalBuilding, city:IsCoastal() and 1 or 0)
	end
end

function ApplyJungle(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return end

	local hasTech = Teams[player:GetTeam()]:IsHasTech(iCivilService)

	for city in player:Cities() do
		city:SetNumRealBuilding(iJungleBuilding, hasTech and 1 or 0)
	end
end

function ApplyMomentum(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return end

	local active = Game.GetGameTurn() <= GetMomentumUntilTurn(playerID)

	for city in player:Cities() do
		city:SetNumRealBuilding(iMomentumBuilding, active and 1 or 0)
	end
end

function ApplyFriendlyBonus(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return end

	for unit in player:Units() do
		if unit:IsCombatUnit() and unit:GetDomainType() == DomainTypes.DOMAIN_LAND then
			unit:SetHasPromotion(iFriendlyPromotion, true)
		end
	end
end

-- ?? FIXED TRADE BONUS
function ApplyTradeBonus(playerID)
	local player = Players[playerID]
	if not IsKadamba(player) then return end

	local totalRaw = 0

	for _, route in ipairs(player:GetTradeRoutes()) do
		local gold = (route.FromGPT or 0) / 100  -- ? FIX HERE
		totalRaw = totalRaw + (gold * TRADE_BONUS_PERCENT)
	end

	local key = "KadambaTradeGold_" .. playerID
	local stored = tonumber(saveData.GetValue(key) or "0")

	local newTotal = stored + totalRaw
	local payout = math.floor(newTotal)

	saveData.SetValue(key, tostring(newTotal - payout))

	if payout > 0 then
		player:ChangeGold(payout)
	end
end

function Refresh(playerID)
	ApplyCoastal(playerID)
	ApplyJungle(playerID)
	ApplyMomentum(playerID)
	ApplyFriendlyBonus(playerID)
end

function OnTech(teamID, techID)
	for playerID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
		local player = Players[playerID]

		if IsKadamba(player) and player:GetTeam() == teamID then
			local untilTurn = Game.GetGameTurn() + MOMENTUM_TURNS - 1
			SetMomentumUntilTurn(playerID, untilTurn)
			Refresh(playerID)
		end
	end
end

GameEvents.TeamTechResearched.Add(OnTech)

Events.ActivePlayerTurnStart.Add(function()
	local playerID = Game.GetActivePlayer()
	Refresh(playerID)
	ApplyTradeBonus(playerID)
end)

Events.SequenceGameInitComplete.Add(function()
	for i = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
		Refresh(i)
	end
end)