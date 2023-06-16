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
			  'service_SLA'		: [0 for i in range(0,9)],
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


t1 = time.time()

# preparing output based on number of rounds and teamIds
# need following two files for this
roundIdsFile = "data/enowars5_RoundsIds.json"
teamIdsFile = "data/enowars5_TeamsIds.json"

numberOfRounds = 0
with open(roundIdsFile, 'r') as f:
	roundIds = json.loads(f.read())
	numberOfRounds = max([ids["Id"] for ids in roundIds])
	
numberOfTeams = 0
with open(teamIdsFile, 'r') as f: # open in readonly mode
	teamsIds = json.loads(f.read())
	teamsIds = [ids["Id"] for ids in teamsIds]
	numberOfTeams = len(teamsIds)

	teams = dict(zip(teamsIds, [(copy.deepcopy(teamStatus))for i in range(0,len(teamsIds))]))
	scores["scores"] = [{"tickId": -1, "teams": copy.deepcopy(teams)} for i in range(0, numberOfRounds+1)]
#########################################################

# Parsing file for getting SLA data
SLAFile = "data/enowars5_SLA.json"
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
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"][serviceId] = 1
#################################################################


t2 = time.time()
if print_info:
	print("time taken in step 1: " + str(t2-t1))
t3 = time.time()

f = open("data/enowars5_sorted_by_time.json","r")
submittedFlagsJson = json.loads(f.read())

for submission in submittedFlagsJson:
	serviceId = submission["ServiceId"]
	attackerId = submission["AttackerId"]
	victimId = submission["OwnerId"]
	roundId = submission["RoundId"]
	flagRoundId = submission["FlagRoundId"]
	flagRoundOffset = submission["RoundOffset"]

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
for i in range(0, len(scores["scores"])):
	for serviceId in range(1,9):
		# SLA
		teams_up = [team for team in scores["scores"][i]["teams"].values() if team["service_SLA"][serviceId] == 1]
		teams_down = [team for team in scores["scores"][i]["teams"].values() if team["service_SLA"][serviceId] == 0]

		point_income_from_down_teams =  0 if len(teams_up) == 0 else (len(teams_down) * 50) / len(teams_up)
		count_teamsup_zero = count_teamsup_zero + 1 if len(teams_up) == 0 else count_teamsup_zero

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
		print("{:3d}".format(sortedIds[i]))
else:
	print("TEAM (ID/Country) | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{} | {} ".format(sortedIds[i],
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))

