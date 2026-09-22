-- Shared, campaign-scoped persistence for Kadamba gameplay and UI.
-- Modding.OpenSaveData is shared across campaigns, so every key is prefixed
-- with immutable setup data that remains stable across save/load.

if KadambaState == nil then
	local State = {}
	local rawSave = Modding.OpenSaveData()

	local function SafePreGameNumber(name)
		local getter = PreGame and PreGame[name]
		if type(getter) ~= "function" then return nil end
		local ok, value = pcall(getter)
		return ok and tonumber(value) or nil
	end

	local function SafeNetworkNumber(name)
		local getter = Network and Network[name]
		if type(getter) ~= "function" then return nil end
		local ok, value = pcall(getter)
		return ok and tonumber(value) or nil
	end

	local function SafePreGameString(name)
		local getter = PreGame and PreGame[name]
		if type(getter) ~= "function" then return nil end
		local ok, value = pcall(getter)
		return ok and value ~= nil and tostring(value) or nil
	end

	local function MakeHasher()
		local hash = 5381
		local function Mix(value)
			if type(value) == "string" then
				for index = 1, #value do
					hash = (hash * 65599 + string.byte(value, index) + 97) % 2147483647
				end
			else
				hash = (hash * 65599 + (tonumber(value) or 0) + 97) % 2147483647
			end
		end
		return Mix, function() return math.floor(hash) end
	end

	local function CampaignFingerprint()
		local width, height = Map.GetGridSize()
		local mix, result = MakeHasher()
		mix(width)
		mix(height)
		mix(Game.GetGameSpeedType())
		mix(SafePreGameNumber("GetWorldSize") or -1)
		mix(SafePreGameNumber("GetEra") or -1)
		mix(SafePreGameString("GetMapScript") or "")

		local mapSeed = SafePreGameNumber("GetMapSeed")
		local syncSeed = SafePreGameNumber("GetSyncRandSeed")
			or SafeNetworkNumber("GetSynchRandSeed")
		local rerollsOnLoad = GameOptionTypes
			and GameOptionTypes.GAMEOPTION_NEW_RANDOM_SEED
			and Game.IsOption(GameOptionTypes.GAMEOPTION_NEW_RANDOM_SEED)

		mix(mapSeed ~= nil and 1 or 0)
		if mapSeed ~= nil then mix(mapSeed) end
		mix(syncSeed ~= nil and not rerollsOnLoad and 1 or 0)
		if syncSeed ~= nil and not rerollsOnLoad then mix(syncSeed) end

		local maxMajors = GameDefines.MAX_MAJOR_CIVS or GameDefines.MAX_CIV_PLAYERS
		for playerID = 0, maxMajors - 1 do
			local player = Players[playerID]
			if player and player:IsEverAlive() then
				mix(playerID)
				mix(player:GetCivilizationType())
				mix(player:GetLeaderType())
			end
		end

		return tostring(width) .. "x" .. tostring(height) .. "_" .. tostring(result())
	end

	local prefix = "KADAMBA_" .. CampaignFingerprint() .. "_"

	local function PlayerKey(name, playerID)
		return prefix .. name .. "_" .. tostring(playerID)
	end

	function State.GetNumber(name, playerID, defaultValue)
		local value = tonumber(rawSave.GetValue(PlayerKey(name, playerID)))
		if value == nil then return defaultValue end
		return value
	end

	function State.SetNumber(name, playerID, value)
		rawSave.SetValue(PlayerKey(name, playerID), tostring(value))
	end

	function State.GetMomentumUntilTurn(playerID)
		return State.GetNumber("MomentumUntilTurn", playerID, -1)
	end

	function State.SetMomentumUntilTurn(playerID, turn)
		State.SetNumber("MomentumUntilTurn", playerID, turn)
	end

	function State.GetTradeRemainder(playerID)
		return State.GetNumber("TradeGoldRemainder", playerID, 0)
	end

	function State.SetTradeRemainder(playerID, value)
		State.SetNumber("TradeGoldRemainder", playerID, value)
	end

	function State.GetLastTradePayoutTurn(playerID)
		return State.GetNumber("LastTradePayoutTurn", playerID, -1)
	end

	function State.SetLastTradePayoutTurn(playerID, turn)
		State.SetNumber("LastTradePayoutTurn", playerID, turn)
	end

	function State.GetCampaignPrefix()
		return prefix
	end

	KadambaState = State
	print("KADAMBA STATE NAMESPACE " .. prefix)
end
