#!/bin/python3

# Differences from ENOWARS
# -- no SLA
# -- constant +1 for attack
# -- defense +1 only in case of a successfull attack

import json
import math
import os

import time
import copy
import sys

### Handle arguments
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
			  'service_SLA'		: [],
			  'service_attack'	: {}, # service
			  'service_defense'	: {}
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
numberOfRounds = 170 # total number of rounds in ecsc 2022
	
numberOfTeams = 0
with open(teamIdsFile, 'r') as f: # open in readonly mode
	teamsIds = json.loads(f.read())
	teamsIds = [ids["user_id"] for ids in teamsIds]
	numberOfTeams = len(teamsIds)

	teams = dict(zip(teamsIds, [(copy.deepcopy(teamStatus))for i in range(0,len(teamsIds))]))
	scores["scores"] = [{"tickId": -1, "teams": copy.deepcopy(teams)} for i in range(0, numberOfRounds)]

#########################################################

## NO sla in defcon scoring
'''
# Parsing file for getting SLA data
SLAFile = "enowars5_SLA.json"
with open(SLAFile, 'r') as f: # open in readonly mode
	roundStatuses = json.loads(f.read())

	for status in roundStatuses:
		teamId = status["TeamId"]
		serviceId = status["ServiceId"]
		gameRoundId = status["GameRoundId"]
		status = status["Status"]

		scores["scores"][gameRoundId]["tickId"] = gameRoundId
		scores["scores"][gameRoundId]["teams"][teamId]["id"] = teamId

		if status == 1:
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"].append(1)
		elif status == 2:
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"].append(0.5)
#################################################################
'''

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
	flagRoundOffset = 0 # submission["FlagRoundOffset"] TODO fix

	roundScores = scores["scores"][flagRoundId]
	teamsScores = roundScores["teams"]

	attackerScore = roundScores["teams"][attackerId]
	attackerScore['id'] = attackerId
	victimScore = roundScores["teams"][victimId]
	victimScore['id'] = victimId

	if flagRoundOffset not in attackerScore['service_attack']:
		attackerScore['service_attack'][flagRoundOffset] = [1]
	else:
		attackerScore['service_attack'][flagRoundOffset].append(1)
	
	services_attacked_this_tick = services_attacked_in_ticks[flagRoundId]
	if serviceId not in services_attacked_this_tick:
		services_attacked_this_tick[serviceId] =  [flagRoundOffset]
		for tmpTeamId, tmpTeamScore in teamsScores.items():
			tmpTeamScore['id'] = tmpTeamId
			tmpTeamScore['service_defense'][serviceId] = [flagRoundOffset]
	elif flagRoundOffset not in services_attacked_this_tick[serviceId]:
		services_attacked_this_tick[serviceId].append(flagRoundOffset)
		for tmpTeamId, tmpTeamScore in teamsScores.items():
			tmpTeamScore['service_defense'][serviceId].append(flagRoundOffset)
	# else already added to attacked services

	if serviceId in victimScore['service_defense']:
		if flagRoundOffset in victimScore['service_defense'][serviceId]:
			victimScore['service_defense'][serviceId].remove(flagRoundOffset)


t4 = time.time()
if print_info:
	print("time taken in step 2 is: " + str(t4 - t3))
t5 = time.time()


for i in range(0, len(scores["scores"])):
	for j in scores["scores"][i]["teams"]:		
		# Defense
		for service, offsets in scores["scores"][i]["teams"][j]["service_defense"].items():
			scores["scores"][i]["teams"][j]["DEFENSE"] +=  len(offsets)

		# Attack
		attack = 0
		for service, offsets in scores["scores"][i]["teams"][j]["service_attack"].items():
			scores["scores"][i]["teams"][j]["ATTACK"] += len(offsets)

		scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i]["teams"][j]["ATTACK"] + scores["scores"][i]["teams"][j]["DEFENSE"]
			
		if i > 0:
			scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i-1]["teams"][j]["Total"] + scores["scores"][i]["teams"][j]["Total"]
			scores["scores"][i]["teams"][j]["DEFENSE"] += scores["scores"][i-1]["teams"][j]["DEFENSE"]
			scores["scores"][i]["teams"][j]["ATTACK"] += scores["scores"][i-1]["teams"][j]["ATTACK"]

t6 = time.time()
if print_info:
	print("time taken in step 3 is: " + str(t6 - t5))

last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
sortedIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)

if print_ranks_only:
	print("Defcon")
	for i in range(0, len(sortedIds)):
		print("{:3d} / {}".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]]))
else:
	print("TEAM (ID/Country) | ATTACK | DEFENSE | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{} / {} | {} | {} | {} ".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]], 
			round(last_tick_scores[sortedIds[i]]["ATTACK"], 2), 
			round(last_tick_scores[sortedIds[i]]["DEFENSE"], 2), 
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))

