#!/bin/python3

# might not be exact due to few confusions
# num_online_teams: does it number of teams playing the CTF or number of teams that have a particular service up during a round
import json
import math
import os

import time
import copy
import sys

### Handle CL arguments
print_info = False
if "-i" in sys.argv:
	print_info = True

print_ranks_only = False
if "-r" in sys.argv:
	print_ranks_only = True

teamStatus = {'id'	   			:-1,
			  'ATTACK' 			: 0,
			  'DEFENSE'			: 0, 
			  'SLA'				: 0,
			  'service_SLA'		: [0 for i in range(0,15)],
			  'service_attack'	: {},
			  'service_defense'	: {},
			  "DEFENSEWOSLA": 0,
			  'Total'			: 0,
			  'Rank'			: 1
			 }

scores = {'scores':[
				{'tickId': -1,
		  		 'teams'  : { },
		  		 'roundDefenseStatus':{}
			  	}
			  	]
		 } 

t1 = time.time()

# teams id <-> countries
teamsIdsToCountries = {}
teamsIdsToCountriesFile = "data/ecsc-2022_registration_team.json"
with open(teamsIdsToCountriesFile, 'r') as f: # open in readonly mode
	teamsIdsAndCountriesFileData = json.loads(f.read())
	for teamData in teamsIdsAndCountriesFileData:
		teamCountry = teamData["country"]
		if teamCountry != "":
			teamCountry = teamCountry.split("/")
			teamCountry = teamCountry[len(teamCountry) - 1]
			teamCountry = teamCountry[0:2]
		else:
			teamCountry = "NOP"
		teamsIdsToCountries[teamData["user_id"]] = teamCountry

# preparing output based on number of rounds and teamIds
teamIdsFile = "data/ecsc-2022_registration_team.json"

numberOfRounds = 170
	
numberOfTeams = 0
with open(teamIdsFile, 'r') as f: # open in readonly mode
	teamsIds = json.loads(f.read())
	teamsIds = [ids["user_id"] for ids in teamsIds]
	numberOfTeams = len(teamsIds)

	teams = dict(zip(teamsIds, [(copy.deepcopy(teamStatus))for i in range(0,len(teamsIds))]))
	scores["scores"] = [{"tickId": -1, "teams": copy.deepcopy(teams), "roundDefenseStatus": {}} for i in range(0, numberOfRounds)]

numberOfTeams -= 1 #removing NOP team
#########################################################

# Parsing file for getting SLA data
SLAFile = "data/ecsc-2022_SLA.json"
with open(SLAFile, 'r') as f: # open in readonly mode
	roundStatuses = json.loads(f.read())

	for status in roundStatuses:
		teamId = status["team_id"]
		serviceId = status["service_id"]
		gameRoundId = status["tick"]
		status = status["status"]

		scores["scores"][gameRoundId]["tickId"] = gameRoundId
		scores["scores"][gameRoundId]["teams"][teamId]["id"] = teamId

		if status == 0: # assuming 0 to be OK
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"][serviceId] = 1
#################################################################

t2 = time.time()
if print_info:
	print("time taken in step 1: " + str(t2-t1))
t3 = time.time()

f = open("data/ecsc-2022_scoring_flag.json","r")
allStoredFlags = json.loads(f.read())
allIds = [storedFlag["id"] for storedFlag in allStoredFlags]
allStoredFlags = dict(zip(allIds, allStoredFlags))

f = open("data/ecsc-2022_scoring_capture.json","r")
capturedFlags = json.loads(f.read())

previousRoundId = 0
services_attacked_in_ticks = [{} for i in range(0,numberOfRounds+1)]
for submission in capturedFlags:
	flagId = submission["flag_id"]
	attackerId = submission["capturing_team_id"]
	roundId = submission["tick"]

	# find flagId in storedFlags
	flagData = allStoredFlags[flagId]

	serviceId = flagData["service_id"]
	victimId = flagData["protecting_team_id"]
	flagRoundId = flagData["tick"]
	flagRoundOffset = 0

	roundScores = scores["scores"][flagRoundId]

	attackerScore = roundScores["teams"][attackerId]
	victimScore = roundScores["teams"][victimId]

	if serviceId not in victimScore["service_defense"]:
		victimScore["service_defense"][serviceId] = {flagRoundOffset:1}
	else:
		victimScore["service_defense"][serviceId][flagRoundOffset] += 1


	if victimId not in attackerScore["service_attack"]:
		attackerScore["service_attack"][victimId] = { serviceId: flagRoundOffset}
	elif serviceId not in attackerScore["service_attack"][victimId]:
		attackerScore["service_attack"][victimId][serviceId] = flagRoundOffset
	else:
		raise Exception("How did it get here?")

	roundDefenseStatus = roundScores["roundDefenseStatus"]
	if serviceId not in roundDefenseStatus:
		roundDefenseStatus[serviceId] = numberOfTeams
		roundDefenseStatus[serviceId] -= 1 # remove current attacked team
	elif victimScore["service_defense"][serviceId][flagRoundOffset] == 1: # current victim attacked for the first time
		roundDefenseStatus[serviceId] -= 1 

########################################################################
	if roundId != previousRoundId:
		for i in range(0, roundId):
			roundDefenseStatus = scores["scores"][i]["roundDefenseStatus"]
			for j in scores["scores"][i]["teams"]:
				#SLA
				scores["scores"][i]["teams"][j]["SLA"] = sum(scores["scores"][i]["teams"][j]["service_SLA"])

				# update all previous defense scores
				defense = 0
				defenseWOSLA = 0
				for tmpServiceId in range(1, 15): # services are from 1 to 14
					if tmpServiceId not in scores["scores"][i]["teams"][j]["service_defense"]:
						if tmpServiceId not in roundDefenseStatus or roundDefenseStatus[tmpServiceId] == 0:
							defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1 + 1.5)
							defenseWOSLA += 1 + 1.5
						else:
							defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1 + (1.5*(1/roundDefenseStatus[tmpServiceId]))) # max((((0 - 0.5) / (20 * 20)) * (roundDefenseStatus[tmpServiceId] ** 2) + 0.5), 0)) 
							defenseWOSLA += (1 + (1.5*(1/roundDefenseStatus[tmpServiceId])))

				
				scores["scores"][i]["teams"][j]["DEFENSE"] = defense
				scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] = defenseWOSLA
		
				# Attack
				attack = 0
				for tmpVictimId, tmpVictimFlags in scores["scores"][i]["teams"][j]["service_attack"].items():
					for tmpServiceId, tmpFlagOffset in tmpVictimFlags.items():
						tmpCaptureCount = scores["scores"][i]["teams"][tmpVictimId]["service_defense"][tmpServiceId][tmpFlagOffset] 
						attack += 1 + (0.5 * (1 / tmpCaptureCount)) #max((((0 - 10) / (20 * 20)) * (tmpCaptureCount ** 2) + 10),0) # (0.5 * (1 / tmpCaptureCount))
						if scores["scores"][i-1]["teams"][tmpVictimId]["Rank"] > scores["scores"][i-1]["teams"][j]["Rank"]: 
							attack += (1/(scores["scores"][i-1]["teams"][tmpVictimId]["Rank"] - scores["scores"][i-1]["teams"][j]["Rank"])**2)
						else:
							attack += 1
				scores["scores"][i]["teams"][j]["ATTACK"] = attack

				if i > 0:
					scores["scores"][i]["teams"][j]["DEFENSE"] +=  scores["scores"][i-1]["teams"][j]["DEFENSE"]
					scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] +=  scores["scores"][i-1]["teams"][j]["DEFENSEWOSLA"]
					scores["scores"][i]["teams"][j]["SLA"] +=  scores["scores"][i-1]["teams"][j]["SLA"]
					scores["scores"][i]["teams"][j]["ATTACK"] +=  scores["scores"][i-1]["teams"][j]["ATTACK"]
				scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i]["teams"][j]["ATTACK"] + scores["scores"][i]["teams"][j]["DEFENSE"] + scores["scores"][i]["teams"][j]["SLA"]

		# compute new ranks for this round

		sortedScores = dict(sorted(scores["scores"][roundId-1]["teams"].items(), key=lambda teamScore: teamScore[1]["Total"], reverse=True))

		rank = 1
		firstRankId = next(iter(sortedScores))
		lastScore = sortedScores[firstRankId]["Total"]
		for tmpScore in sortedScores.values():
			if tmpScore["Total"] != lastScore:
				rank += 1
				lastScore = tmpScore["Total"]
			tmpScore["Rank"] = rank

		scores["scores"][roundId-1]["teams"] = sortedScores		
				
		previousRoundId = roundId
########################################################################

# This is for the final round
for i in range(0, numberOfRounds):
	roundDefenseStatus = scores["scores"][i]["roundDefenseStatus"]	
	for j in scores["scores"][i]["teams"]:
		# SLA
		scores["scores"][i]["teams"][j]["SLA"] = sum(scores["scores"][i]["teams"][j]["service_SLA"])

		# Defense
		defense = 0
		defenseWOSLA = 0
		for tmpServiceId in range(1, 15): # services are from 1 to 14
			if tmpServiceId not in scores["scores"][i]["teams"][j]["service_defense"]:
				if tmpServiceId not in roundDefenseStatus or roundDefenseStatus[tmpServiceId] == 0:
					defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1 + 1.5)
					defenseWOSLA += 1 + 1.5
				else:
					defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1 + (1.5*(1/roundDefenseStatus[tmpServiceId]))) #max((((0 - 0.5) / (20 * 20)) * (roundDefenseStatus[tmpServiceId] ** 2) + 0.5), 0))
					defenseWOSLA += (1 + (1.5*(1/roundDefenseStatus[tmpServiceId])))

		scores["scores"][i]["teams"][j]["DEFENSE"] = defense
		scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] = defenseWOSLA

		# Attack
		attack = 0
		for tmpVictimId, tmpVictimFlags in scores["scores"][i]["teams"][j]["service_attack"].items():
			for tmpServiceId, tmpFlagOffset in tmpVictimFlags.items():
				tmpCaptureCount = scores["scores"][i]["teams"][tmpVictimId]["service_defense"][tmpServiceId][tmpFlagOffset] 
				attack += 1 + (0.5 * (1 / tmpCaptureCount)) #max((((0 - 10) / (20 * 20)) * (tmpCaptureCount ** 2) + 10),0) # (0.5 * (1 / tmpCaptureCount))
				if scores["scores"][i-1]["teams"][tmpVictimId]["Rank"] > scores["scores"][i-1]["teams"][j]["Rank"]: 
					attack += (1/(scores["scores"][i-1]["teams"][tmpVictimId]["Rank"] - scores["scores"][i-1]["teams"][j]["Rank"])**2)
				else:
					attack += 1
		scores["scores"][i]["teams"][j]["ATTACK"] = attack

		if i > 0:
			scores["scores"][i]["teams"][j]["DEFENSE"] +=  scores["scores"][i-1]["teams"][j]["DEFENSE"]
			scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] +=  scores["scores"][i-1]["teams"][j]["DEFENSEWOSLA"]
			scores["scores"][i]["teams"][j]["SLA"] +=  scores["scores"][i-1]["teams"][j]["SLA"]
			scores["scores"][i]["teams"][j]["ATTACK"] +=  scores["scores"][i-1]["teams"][j]["ATTACK"]
			scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i]["teams"][j]["ATTACK"] + scores["scores"][i]["teams"][j]["DEFENSE"] + scores["scores"][i]["teams"][j]["SLA"]

t4 = time.time()
if print_info:
	print("time taken in step 2: " + str(t4-t3))
t5 = time.time()

last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
sortedIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)

if print_ranks_only:
	print("CyberChallengeIt")
	for i in range(0, len(sortedIds)):
		print("{:3d}/{}".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]]))
else:
	print("Proportional scoring")
	print("TEAM (ID/Country) | SLA | ATTACK | DEFENSE | DEFENSE W/O SLA | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{}/{} | {} | {} | {} | {} | {}".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]],
			last_tick_scores[sortedIds[i]]["SLA"],
			round(last_tick_scores[sortedIds[i]]["ATTACK"], 2),
			round(last_tick_scores[sortedIds[i]]["DEFENSE"], 2),
			round(last_tick_scores[sortedIds[i]]["DEFENSEWOSLA"],2),
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))
