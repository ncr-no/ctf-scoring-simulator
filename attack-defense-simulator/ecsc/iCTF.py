#!/bin/python3

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
			  'service_attack'	: {}, # service
			  'service_defense'	: {},
			  'Total'			: 0
			 }

scores = {'scores':[
				{'tickId': -1,
		  		 'teams'  : { },
		  		 'roundDefenseStatus':{}
			  	}
			  	]
		 } 

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

t1 = time.time()

# preparing output based on number of rounds and teamIds
teamIdsFile = "data/ecsc-2022_registration_team.json"

numberOfRounds = 170

numberOfTeams = 0
with open(teamIdsFile, 'r') as f: # open in readonly mode
	teamsIds = json.loads(f.read())
	teamsIds = [ids["user_id"] for ids in teamsIds]
	numberOfTeams = len(teamsIds)

	teams = dict(zip(teamsIds, [(copy.deepcopy(teamStatus))for i in range(0,len(teamsIds))]))
	scores["scores"] = [{"tickId": -1, "teams": copy.deepcopy(teams)} for i in range(0, numberOfRounds)]

numberOfTeams -= 1 # removing NOP team

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
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"][serviceId]= 1
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

	attackerScore = roundScores["teams"][attackerId]
	victimScore = roundScores["teams"][victimId]

	if serviceId not in victimScore["service_defense"]:
		victimScore["service_defense"][serviceId] = {flagRoundOffset:[attackerId]}
	elif flagRoundOffset not in victimScore["service_defense"][serviceId]:
		victimScore["service_defense"][serviceId][flagRoundOffset] = [attackerId]
	else:
		victimScore["service_defense"][serviceId][flagRoundOffset].append(attackerId)

t4 = time.time()
if print_info:
	print("time taken in step 2: " + str(t4-t3))
t5 = time.time()

# Now we have all the data we need about SLA, attack and defense. 
# Next step is to calculate the scores using FAUST formula

count_teamsup_zero = 0
sumTotalPoints = 0
for i in range(0, len(scores["scores"])):
	for serviceId in range(0,15):
		# SLA
		teams_up = [team for team in scores["scores"][i]["teams"].values() if team["service_SLA"][serviceId] == 1]
		teams_down = [team for team in scores["scores"][i]["teams"].values() if team["service_SLA"][serviceId] == 0]

		point_income_from_down_teams =  0 if len(teams_up) == 0 else (len(teams_down) * 50) / len(teams_up)
		count_teamsup_zero = count_teamsup_zero + 1 if len(teams_up) == 0 else count_teamsup_zero

		sumTotalPoints += 50 * 34

		for team in teams_up:
			team["Total"] += point_income_from_down_teams

		for team in teams_up:
			if serviceId not in team["service_defense"] or 0 not in team["service_defense"][serviceId]:
				team["Total"] += 50
			else:
				point_income_from_exploit = 50 / len(team["service_defense"][serviceId][0])
				for exploiter in team['service_defense'][serviceId][0]:
					scores["scores"][i]["teams"][exploiter]["Total"] += point_income_from_exploit


#print(count_teamsup_zero)
#print("Sum total points: {}".format(sumTotalPoints))

for i in range(0, len(scores["scores"])):
	for j in scores["scores"][i]["teams"]:
		if i > 0:
			scores["scores"][i]["teams"][j]["Total"] += scores["scores"][i-1]["teams"][j]["Total"]	

t6 = time.time()
if print_info:
	print("time taken in step 3 is: " + str(t6 - t5))


last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
sortedIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)

if print_ranks_only:
	print("iCTF")
	for i in range(0, len(sortedIds)):
		print("{:3d} / {}".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]]))
else:
	print("TEAM (ID/Country) | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{} / {} | {} ".format(sortedIds[i], teamsIdsToCountries[sortedIds[i]],
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))



