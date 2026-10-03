---@diagnostic disable: undefined-global
-- Add the following to \Saved Games\DCS\Scripts\Export.lua
--dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])
--
-- NOTE: this version CHAINS LuaExportActivityNextEvent -- it saves and calls any
-- previously-registered handler (DCS-BIOS, TheWay, ModernF15E) before doing its
-- own send, so loading this last does not clobber their export hooks.

package.path = package.path .. ";.\\LuaSocket\\?.lua"
package.cpath = package.cpath .. ";.\\LuaSocket\\?.dll"

package.path = lfs.writedir() .. "?.lua;" .. package.path

-- all requires must come after updates to package.path


local socket = require("socket")

-- Define the UDPMulticastSender class
local UDPMulticastSender = {}
UDPMulticastSender.__index = UDPMulticastSender

-- Constructor
function UDPMulticastSender:new(multicast_group, port)
    local self = setmetatable({}, UDPMulticastSender)
    self.multicast_group = multicast_group
    self.port = port
    self.udp = socket.udp()
    self.udp:setpeername(multicast_group, port)
    self.udp:setoption("ip-multicast-ttl", 1)
    return self
end

-- Method to send data
function UDPMulticastSender:sendData(data)
    local success, err = self.udp:send(data)
    -- if not success then
    --     print("Error sending data: " .. err)
    -- else
    --     print("Data sent: " .. data)
    -- end
end

-- Method to close the UDP socket
function UDPMulticastSender:close()
    if self.udp then
        self.udp:close()
    end
end

local sender = UDPMulticastSender:new("239.255.61.21", 6121)

-- Save any previously-registered handler so we can chain it (good-citizen hook).
local DAM_PrevActivityNextEvent = LuaExportActivityNextEvent
local DAM_lastSend = -1

-- DCS Export functions

function LuaExportActivityNextEvent(t)
	-- Our own send cadence (~1 s). Track it separately so chaining a faster
	-- previous handler doesn't make us spam.
	local ourNext = t + 1

	-- Chain the previously-registered handler first, respecting its schedule.
	local nextT = ourNext
	if DAM_PrevActivityNextEvent then
		local ok, prevNext = pcall(DAM_PrevActivityNextEvent, t)
		if ok and type(prevNext) == "number" then
			nextT = math.min(nextT, prevNext)
		end
	end

	local function tableToString(tbl, prefix)
		prefix = prefix or ""
		local str = ""
		for k, v in pairs(tbl) do
			local newKey = prefix .. (prefix ~= "" and "." or "") .. tostring(k)
			if type(v) == "table" then
				str = str .. tableToString(v, newKey)
			else
				str = str .. newKey .. "=" .. tostring(v) .. ";"
			end
		end
		return str
	end

	-- Only build+send at our ~1 Hz cadence.
	if DAM_lastSend < 0 or (t - DAM_lastSend) >= 1.0 then
		DAM_lastSend = t

		-- Safe getter: call a LoGet* function, return nil on any error/absence so
		-- one bad/undefined export call can never break the whole export hook.
		local function G(fn)
			if type(fn) ~= "function" then return nil end
			local ok, v = pcall(fn)
			if ok then return v end
			return nil
		end

		-- Surface wind: sample the wind at the ground point directly below the
		-- aircraft, so the CARP SFC W/V can use the true surface-layer wind
		-- instead of the aircraft-altitude wind (LoGetVectorWindVelocity).
		-- Several candidate export functions are tried in order (which one is
		-- exposed varies by DCS build / MP export environment). DAM_Wind_status
		-- reports what happened so we can see it in the dump.
		-- Surface wind for the CARP SFC W/V: sample at ~10 m (33 ft, the standard
		-- surface-wind reference height) above the ground point below the aircraft,
		-- so SFC W/V uses the true surface-layer wind instead of the aircraft-
		-- altitude wind. LoGetWindAtPoint takes 3 numeric args (x, y, z world
		-- coords) and returns 3 numbers (vx, vy, vz). VALIDATED in-sim.
		local DAM_SurfaceWind = nil
		do
			local sd = G(LoGetSelfData)
			local asl = G(LoGetAltitudeAboveSeaLevel)
			local agl = G(LoGetAltitudeAboveGroundLevel)
			if type(sd) == "table" and type(sd.Position) == "table"
				and type(asl) == "number" and type(agl) == "number"
				and type(LoGetWindAtPoint) == "function" then
				local terrain = asl - agl                      -- ground elev under aircraft
				local ok, sx, sy, sz = pcall(LoGetWindAtPoint,
					sd.Position.x, terrain + 10.0, sd.Position.z)
				if ok and type(sx) == "number" and type(sy) == "number"
					and type(sz) == "number" then
					DAM_SurfaceWind = { x = sx, y = sy, z = sz }
				end
			end
		end

		local DcsAutoMateData = {
			-- Surface-layer wind below the aircraft (for CARP SFC W/V).
			DAM_SurfaceWind = DAM_SurfaceWind,
			--Ownship
			LoGetIndicatedAirSpeed = G(LoGetIndicatedAirSpeed), -- m/s
			LoGetVerticalVelocity = G(LoGetVerticalVelocity),
			LoGetTrueAirSpeed = G(LoGetTrueAirSpeed), -- m/s
			LoGetAltitudeAboveSeaLevel = G(LoGetAltitudeAboveSeaLevel),
			LoGetAltitudeAboveGroundLevel = G(LoGetAltitudeAboveGroundLevel),
			LoGetMachNumber = G(LoGetMachNumber),
			LoGetRadarAltimeter = G(LoGetRadarAltimeter),
			LoGetEngineInfo = G(LoGetEngineInfo),
			LoGetSelfData = G(LoGetSelfData),
			LoGetPayloadInfo = G(LoGetPayloadInfo),
			-- PROBE (temporary): route + nav info, to find the run-in leg course.
			LoGetRoute = G(LoGetRoute),
			LoGetNavigationInfo = G(LoGetNavigationInfo),
			LoGetWayPointInfo = G(LoGetWayPointInfo),
			LoGetMechInfo = G(LoGetMechInfo),
			LoGetHeightWithObjects = G(LoGetHeightWithObjects),
			LoGetFMData = G(LoGetFMData),

			-- Winds + pressure: useful for CARP INIT 3/5 (wind fields + altimeter).
			-- Enabled (were commented out in the stock export).
			LoGetVectorWindVelocity = G(LoGetVectorWindVelocity),
			LoGetWindWithTurbulence = G(LoGetWindWithTurbulence),
			LoGetBasicAtmospherePressure = G(LoGetBasicAtmospherePressure),
			LoGetMagneticYaw = G(LoGetMagneticYaw),
			LoGetAngleOfAttack = G(LoGetAngleOfAttack),

			--Always
			LoGetPilotName = G(LoGetPilotName),
			LoGetVersionInfo = G(LoGetVersionInfo),
			LoGetModelTime = G(LoGetModelTime),
			LoGetMissionStartTime = G(LoGetMissionStartTime),
		}

		local ok, dataString = pcall(tableToString, DcsAutoMateData)
		if ok and dataString then
			sender:sendData(dataString)
		end
	end

	return nextT
end
