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
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"].append(1)
#################################################################


t2 = time.time()
if print_info:
	print("time taken in step 1: " + str(t2-t1))
t3 = time.time()

f = open("data/enowars5_sorted_by_time.json","r")
submittedFlagsJson = json.loads(f.read())

previousRoundId = 1
for submission in submittedFlagsJson:
	serviceId = submission["ServiceId"]
	attackerId = submission["AttackerId"]
	victimId = submission["OwnerId"]
	roundId = submission["RoundId"]
	flagRoundId = submission["FlagRoundId"]
	flagRoundOffset = submission["RoundOffset"]

	if roundId > 535:
		continue
	roundScores = scores["scores"][flagRoundId]

	attackerScore = roundScores["teams"][attackerId]
	victimScore = roundScores["teams"][victimId]

	if serviceId not in victimScore["service_defense"]:
		victimScore["service_defense"][serviceId] = {flagRoundOffset:1}
	elif flagRoundOffset not in victimScore["service_defense"][serviceId]:
		victimScore["service_defense"][serviceId][flagRoundOffset] = 1 
	else:
		victimScore["service_defense"][serviceId][flagRoundOffset] += 1

	if victimId not in attackerScore["service_attack"]:
		attackerScore["service_attack"][victimId] = { serviceId: [flagRoundOffset]}
	elif serviceId not in attackerScore["service_attack"][victimId]:
		attackerScore["service_attack"][victimId][serviceId] = [flagRoundOffset]
	elif flagRoundOffset not in attackerScore["service_attack"][victimId][serviceId]:
		attackerScore["service_attack"][victimId][serviceId].append(flagRoundOffset) 

t4 = time.time()
if print_info:
	print("time taken in step 2: " + str(t4-t3))

t5 = time.time()


# Now we have all the data we need about SLA, attack and defense. 
# Next step is to calculate the scores using FAUST formula


for i in range(0, len(scores["scores"])):
	for j in scores["scores"][i]["teams"]:
		# SLA
		scores["scores"][i]["teams"][j]["SLA"] = sum(scores["scores"][i]["teams"][j]["service_SLA"]) * numberOfTeams ** 0.5
		
		# Defense
		defense = 0
		for service, offset in scores["scores"][i]["teams"][j]["service_defense"].items():
			for flagOffset, lostFlagCount in offset.items():
				defense -= pow(lostFlagCount, 0.5)
		scores["scores"][i]["teams"][j]["DEFENSE"] = defense

		# Attack
		attack = 0
		for tmpVictimId, tmpVictimFlags in scores["scores"][i]["teams"][j]["service_attack"].items():
			for tmpServiceId, tmpFlagOffsetList in tmpVictimFlags.items():
				for tmpOffset in tmpFlagOffsetList:
					tmpCaptureCount = scores["scores"][i]["teams"][tmpVictimId]["service_defense"][tmpServiceId][tmpOffset] 
					attack += (1 + (1 /tmpCaptureCount))
		scores["scores"][i]["teams"][j]["ATTACK"] = attack


		if i > 0:
			scores["scores"][i]["teams"][j]["DEFENSE"] =  scores["scores"][i-1]["teams"][j]["DEFENSE"] + defense
			scores["scores"][i]["teams"][j]["SLA"] +=  scores["scores"][i-1]["teams"][j]["SLA"]
			scores["scores"][i]["teams"][j]["ATTACK"] =  scores["scores"][i-1]["teams"][j]["ATTACK"] + attack
			scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i]["teams"][j]["ATTACK"] + scores["scores"][i]["teams"][j]["DEFENSE"] + scores["scores"][i]["teams"][j]["SLA"]
			

t6 = time.time()
if print_info:
	print("time taken in step 3: " + str(t6-t5))


last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
sortedIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)

if print_ranks_only:
	print("CyberChallengeIt")
	for i in range(0, len(sortedIds)):
		print("{:3d} ".format(sortedIds[i]))
else:
	print("TEAM (ID) | ATTACK | DEFENSE | SLA | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{} | {} | {} | {} | {} ".format(sortedIds[i], 
			round(last_tick_scores[sortedIds[i]]["ATTACK"], 2), 
			round(last_tick_scores[sortedIds[i]]["DEFENSE"], 2),
			round(last_tick_scores[sortedIds[i]]["SLA"], 2), 
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))
