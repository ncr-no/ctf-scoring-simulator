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
			  'service_attack'	: {},
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

## NO sla in defcon scoring
'''
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
		elif status == 2:
			scores["scores"][gameRoundId]["teams"][teamId]["service_SLA"].append(0.5)
#################################################################
'''

t2 = time.time()
if print_info:
	print("time taken in step 1: " + str(t2-t1))

t3 = time.time()

f = open("data/enowars5_sorted_by_time.json","r")
submittedFlagsJson = json.loads(f.read())


services_attacked_in_ticks = [{} for i in range(0,numberOfRounds+1)]
for submission in submittedFlagsJson:
	serviceId = submission["ServiceId"]
	attackerId = submission["AttackerId"]
	victimId = submission["OwnerId"]
	roundId = submission["RoundId"]
	flagRoundId = submission["FlagRoundId"]
	flagRoundOffset = submission["RoundOffset"]
	
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
		for teamId, teamScore in teamsScores.items():
			teamScore['id'] = teamId
			teamScore['service_defense'][serviceId] = [flagRoundOffset]
	elif flagRoundOffset not in services_attacked_this_tick[serviceId]:
		services_attacked_this_tick[serviceId].append(flagRoundOffset)
		for teamId, teamScore in teamsScores.items():
			teamScore['service_defense'][serviceId].append(flagRoundOffset)

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
		print("{:3d}".format(sortedIds[i]))
else:
	print("TEAM (ID) | ATTACK | DEFENSE | TOTAL")
	for i in range(0, len(sortedIds)):
		print("{} | {} | {} | {} ".format(sortedIds[i], 
			round(last_tick_scores[sortedIds[i]]["ATTACK"], 2), 
			round(last_tick_scores[sortedIds[i]]["DEFENSE"], 2), 
			round(last_tick_scores[sortedIds[i]]["Total"], 2)))



