print("KADAMBA UI PANEL LOADED")

local iCiv = GameInfoTypes.CIVILIZATION_KADAMBA
local iCivilService = GameInfoTypes.TECH_CIVIL_SERVICE
local TRADE_BONUS_PERCENT = 0.25

local saveData = Modding.OpenSaveData()

function IsHumanKadamba()
	local playerID = Game.GetActivePlayer()
	local player = Players[playerID]
	return player and player:IsAlive() and player:GetCivilizationType() == iCiv
end

function GetMomentumTurnsLeft(playerID)
	local currentTurn = Game.GetGameTurn()
	local untilTurn = tonumber(saveData.GetValue("KadambaMomentum_" .. playerID) or "-1")

	local remaining = untilTurn - currentTurn + 1
	if remaining < 0 then remaining = 0 end

	return remaining
end

function CountCoastalCities(player)
	local count = 0
	for city in player:Cities() do
		if city:IsCoastal() then count = count + 1 end
	end
	return count
end

-- ?? FIXED TRADE DISPLAY
function GetTradeBonusReal(player, playerID)
	local totalRaw = 0

	for _, route in ipairs(player:GetTradeRoutes()) do
		local gold = (route.FromGPT or 0) / 100  -- ? FIX HERE
		totalRaw = totalRaw + (gold * TRADE_BONUS_PERCENT)
	end

	local key = "KadambaTradeGold_" .. playerID
	local stored = tonumber(saveData.GetValue(key) or "0")

	local realPayout = math.floor(totalRaw + stored)

	return realPayout, totalRaw
end

function UpdateKadambaPanel()
	local panel = Controls.KadambaPanel
	local label = Controls.BonusLabel

	if not IsHumanKadamba() then
		panel:SetHide(true)
		return
	end

	panel:SetHide(false)

	local playerID = Game.GetActivePlayer()
	local player = Players[playerID]
	local team = Teams[player:GetTeam()]

	local coastalCities = CountCoastalCities(player)
	local jungleActive = team:IsHasTech(iCivilService)
	local momentumTurns = GetMomentumTurnsLeft(playerID)

	local tradePayout, tradeRaw = GetTradeBonusReal(player, playerID)

	local text =
		"[ICON_GOLD] Coastal Cities: +" .. (coastalCities * 2) .. " Gold, +" .. coastalCities .. " Culture[NEWLINE]" ..
		"[ICON_PRODUCTION] Building Momentum: " .. momentumTurns .. " turns left[NEWLINE]" ..
		"[ICON_PRODUCTION] Jungle Production: " .. (jungleActive and "Active" or "Requires Civil Service") .. "[NEWLINE]" ..
		"[COLOR:255:215:0:255][ICON_GOLD] Trade Bonus: +" .. tradePayout .. " (" .. string.format("%.1f", tradeRaw) .. " raw)[ENDCOLOR]"

	label:SetText(text)
end

Events.ActivePlayerTurnStart.Add(UpdateKadambaPanel)
Events.SerialEventGameDataDirty.Add(UpdateKadambaPanel)
Events.SequenceGameInitComplete.Add(UpdateKadambaPanel)