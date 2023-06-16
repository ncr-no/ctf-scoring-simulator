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

# Attack, Defense, SLA, and Dyn part ---> each give 25% scores
# SLA point only given when the service is up i.e. status = 0

teamStatus = {'id'	   			:-1,
			  'ATTACK' 			: 0,
			  'DEFENSE'			: 0, 
			  'SLA'				: 0,
			  'service_SLA'		: [0 for i in range(0,15)],
			  'service_attack'	: {},
			  'service_defense'	: {},
			  'is_service_defended': {}
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
teamsIdsToCountriesFile = "ecsc-2022_registration_team.json"
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
# need following two files for this
#roundIdsFile = "enowars5_RoundsIds.json"
teamIdsFile = "ecsc-2022_registration_team.json"

numberOfRounds = 170
	
numberOfTeams = 0
with open(teamIdsFile, 'r') as f: # open in readonly mode
	teamsIds = json.loads(f.read())
	teamsIds = [ids["user_id"] for ids in teamsIds]
	numberOfTeams = len(teamsIds)

	teams = dict(zip(teamsIds, [(copy.deepcopy(teamStatus))for i in range(0,len(teamsIds))]))
	scores["scores"] = [{"tickId": -1, "teams": copy.deepcopy(teams), "roundDefenseStatus": {}} for i in range(0, numberOfRounds)]

numberOfTeams -=1 # removing the nop team
#print(numberOfTeams)
#########################################################

servicesFile = "ecsc-2022_scoring_service.json"

serviceToServiceGroupDict = {}
with open(servicesFile, 'r') as f: # open in readonly mode
	servicesFileJson = json.loads(f.read())
	serviceIds = [tmpService["id"] for tmpService in servicesFileJson]
	serviceGroupIds = [tmpService["service_group_id"] for tmpService in servicesFileJson]
	serviceToServiceGroupDict = dict(zip(serviceIds, serviceGroupIds))


# Parsing file for getting SLA data
SLAFile = "ecsc-2022_SLA.json"
with open(SLAFile, 'r') as f: # open in readonly mode
	roundStatuses = json.loads(f.read())

	for status in roundStatuses:
		teamId = status["team_id"]
		serviceId = status["service_id"]
		gameRoundId = status["tick"]
		status = status["status"]

		scores["scores"][gameRoundId]["tickId"] = gameRoundId
		scores["scores"][gameRoundId]["teams"][teamId]["id"] = teamId

		if status == 0:
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
	bonus = flagData["bonus"]

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
		raise exception("How did it get here?")

	roundDefenseStatus = roundScores["roundDefenseStatus"]
	if serviceId not in roundDefenseStatus:
		roundDefenseStatus[serviceId] = numberOfTeams
		roundDefenseStatus[serviceId] -= 1 # remove current attacked team
	elif victimScore["service_defense"][serviceId][flagRoundOffset] == 1: # current victim attacked for the first time
		roundDefenseStatus[serviceId] -= 1 # 

		

'''
########################################################################
	if roundId != previousRoundId:
		for i in range(0, roundId):
			for j in scores["scores"][i]["teams"]:
				#SLA
				scores["scores"][i]["teams"][j]["SLA"] = scores["scores"][i-1]["teams"][j]["SLA"]
				+ sum(scores["scores"][i]["teams"][j]["service_SLA"]) * (numberOfTeams)**0.5
			
				# update all previous defense scores
				defense = 0
				for service, offset in scores["scores"][i]["teams"][j]["service_defense"].items():
					for flagOffset, lostFlagCount in offset.items():
						defense -= lostFlagCount ** 0.75
				scores["scores"][i]["teams"][j]["DEFENSE"] = defense

				attack = 0
				for victimId, victimFlags in scores["scores"][i]["teams"][j]["service_attack"].items():
					for serviceId, flagInfo in victimFlags.items():
						for flagOffset, count in flagInfo.items():
							attack += (1 + (1 /count))
				scores["scores"][i]["teams"][j]["ATTACK"] = attack

		# sum defense scores and add to last tick scoreboard
		for k in scores["scores"][i]["teams"]:
			scores["scores"][previousRoundId]["teams"][k]["Scoreboard_Defense"] = sum([tick_scores["teams"][k]["DEFENSE"] for tick_scores in scores['scores'][0:roundId]])
			scores["scores"][previousRoundId]["teams"][k]["Scoreboard_Attack"] = sum([tick_scores["teams"][k]["ATTACK"] for tick_scores in scores['scores'][0:roundId]])

		previousRoundId = roundId
########################################################################
'''


t4 = time.time()

#print("time taken in step 2 is: " + str(t4 - t3))

'''
########################################################################
for i in range(0, len(scores["scores"])):
	for teamId, teamScore in scores["scores"][i]["teams"].items():
		scores["scores"][i]["teams"][teamId]["SLA"] = sum(scores["scores"][i]["teams"][teamId]["service_SLA"]) * (numberOfTeams)**0.5
		
		if i > 1:
			scores["scores"][i]["teams"][teamId]["SLA"] +=  scores["scores"][i-1]["teams"][teamId]["SLA"]
########################################################################
'''


# Now we have all the data we need about SLA, attack and defense. 
# Next step is to calculate the scores using FAUST formula

t5 = time.time()


for i in range(0, len(scores["scores"])):
	roundDefenseStatus = scores["scores"][i]["roundDefenseStatus"]
	#print(roundDefenseStatus)
	#exit()
	for j in scores["scores"][i]["teams"]:

		# SLA
		scores["scores"][i]["teams"][j]["SLA"] = sum(scores["scores"][i]["teams"][j]["service_SLA"])
		

		# Defense
		defense = 0
		defenseWOSLA = 0
		for tmpServiceId in range(1, 15): # services are from 1 to 14
			if tmpServiceId not in scores["scores"][i]["teams"][j]["service_defense"]:
				if tmpServiceId not in roundDefenseStatus or roundDefenseStatus[tmpServiceId] == 0:
					defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1)
					defenseWOSLA += 1
				else:
					defense += scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] * (1 +(0.5*(1/roundDefenseStatus[tmpServiceId])))
					defenseWOSLA += (1 + (0.5*(1/roundDefenseStatus[tmpServiceId])))
				

		#defense = 0
		#for tmpServiceId, tmpOffsetInfo in scores["scores"][i]["teams"][j]["service_defense"].items():
		#	for tmpFlagOffset, tmpLostFlagCount in tmpOffsetInfo.items():
		#		if scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId] == 1:
		#			defense -= (tmpLostFlagCount ** 0.75)  #(tmpLostFlagCount/numberOfTeams + 0.5) * scores["scores"][i]["teams"][j]["service_SLA"][tmpServiceId]
		#		else:
		#			defense -= numberOfTeams ** 0.75
		scores["scores"][i]["teams"][j]["DEFENSE"] = defense
		scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] = defenseWOSLA

		# Attack
		attack = 0
		for tmpVictimId, tmpVictimFlags in scores["scores"][i]["teams"][j]["service_attack"].items():
			for tmpServiceId, tmpFlagOffset in tmpVictimFlags.items():
				tmpCaptureCount = scores["scores"][i]["teams"][tmpVictimId]["service_defense"][tmpServiceId][tmpFlagOffset] 
				attack += 1 + max((((0 - 10) / (20 * 20)) * (tmpCaptureCount ** 2) + 10),0) # (0.5 * (1 / tmpCaptureCount))
		scores["scores"][i]["teams"][j]["ATTACK"] = attack

		if i > 0:
			scores["scores"][i]["teams"][j]["DEFENSEWOSLA"] += scores["scores"][i-1]["teams"][j]["DEFENSEWOSLA"]
			scores["scores"][i]["teams"][j]["DEFENSE"] +=  scores["scores"][i-1]["teams"][j]["DEFENSE"] 
			scores["scores"][i]["teams"][j]["SLA"] +=  scores["scores"][i-1]["teams"][j]["SLA"]
			scores["scores"][i]["teams"][j]["ATTACK"] +=  scores["scores"][i-1]["teams"][j]["ATTACK"]
			scores["scores"][i]["teams"][j]["Total"] =  scores["scores"][i]["teams"][j]["ATTACK"] + scores["scores"][i]["teams"][j]["DEFENSE"] + scores["scores"][i]["teams"][j]["SLA"]
			

t6 = time.time()
#print("time taken is {}".format(t6 - t5))
#print(scores["scores"][numberOfRounds - 1]["teams"][1] )
last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
for teamId, tmpTeam in last_tick_scores.items():
	del tmpTeam["service_attack"]
	del tmpTeam["service_defense"]
	del tmpTeam["service_SLA"]
	del tmpTeam["is_service_defended"]

print(last_tick_scores)
ourIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)
print("ourIds")
print(ourIds)
print("\n\n")


print("ECSC")
print("TEAM (ID/Country) | SLA | ATTACK | DEFENSE | DEFENSE W/O SLA | TOTAL")
for i in range(0, len(ourIds)):
	print("{} / {} | {} | {} | {} | {} | {}".format(ourIds[i], teamsIdsToCountries[ourIds[i]], 
		last_tick_scores[ourIds[i]]["SLA"], 
		round(last_tick_scores[ourIds[i]]["ATTACK"], 2), 
		round(last_tick_scores[ourIds[i]]["DEFENSE"], 2), 
		round(last_tick_scores[ourIds[i]]["DEFENSEWOSLA"],2), 
		round(last_tick_scores[ourIds[i]]["Total"], 2)))

exit()


last_tick_scores = scores["scores"][numberOfRounds - 1]["teams"]
last_tick_scores_arr = [score["Total"] for score in scores["scores"][numberOfRounds - 1]["teams"].values()]
last_tick_scores_arr = sorted(last_tick_scores_arr, reverse=True)
ourIds = sorted(last_tick_scores.keys(), key=lambda x: last_tick_scores[x]["Total"], reverse=True)
print("ourIds")
print(ourIds)
print("\n\n")

'''
IDs = []
scoreboardFilename = "scoreboard535.json"
with open(scoreboardFilename, 'r') as f:
	scoreboardFile = json.loads(f.read())


	IDs = [team["teamId"] for team in scoreboardFile["teams"][:]]
	print(dict(zip(ourIds, IDs)))

print("Rank | enowars5 ranking | new calcs")
for i in range(0, len(IDs)):
	print("{:3d}. | {:3d}              | {}".format(i+1, IDs[i], ourIds[i]))
'''

print("Rank | playerIds")
for i in range(0, len(ourIds)):
	print("{:3d}. | {:3d}              | {}".format(i+1, ourIds[i], last_tick_scores_arr[i]))
exit()

print(json.dumps(scores["scores"][535]["teams"]))
#print(json.dumps(scores))
exit()


##################################################
'''
# first calculating SLA and defense scores because it's easier
for roundScores in scores["scores"]:
	for teamScores in roundScores["teams"]:
		teamScores["SLA"] = sum(teamScores["service_SLA"]) * (numberOfTeams)**0.5
		
		defense = 0
		for service_defense in teamScores["service_defense"]:
			defense -= service_defense ** 0.75
		teamScores["DEFENSE"] =  defense

t6 = time.time()
print("time take in step 3 is: {}".format(t6-t5))

t7 = time.time()
'''
# Now for attack scores
# TODO

'''
# totaling
final_scores_us = {'teams': [{"id": -1, "Attack": -1, "Defense": -1, "SLA": -1, "Total": -1} for i in range(0,numberOfTeams)]}
for i in scores["scores"][1]["teams"].values():
	#final_scores_us['teams'][i-1]["Attack"] = sum([tick_scores["teams"][i-1]["ATTACK"] for tick_scores in scores['scores'][:]])
	final_scores_us['teams'][i]["Defense"] = scores["scores"][numberOfRounds - 1]["teams"][i]["DEFENSE"]
	final_scores_us['teams'][i]["SLA"] = scores['scores'][numberOfRounds - 1]["teams"][i]["SLA"]
	final_scores_us['teams'][i]["Attack"] = scores['scores'][numberOfRounds - 1]["teams"][i]["Attack"]
	final_scores_us['teams'][i]["Total"] = scores['scores'][numberOfRounds - 1]["teams"][i]["DEFENSE"] + scores['scores'][numberOfRounds - 1]["teams"][i]["SLA"] + scores['scores'][numberOfRounds - 1]["teams"][i]["Attack"]
	final_scores_us['teams'][i]["id"] = i


print(json.dumps(final_scores_us))
exit()
'''
### code below apparently does not work
last_tick_scores = scores["scores"][535]["teams"]

leaderboard_us = [{"team-id":-1, "score": -1} for i  in range(0,numberOfTeams)]
totals_us = [team_score["Total"] for team_score in final_scores_us['teams'][:]]
for i in range(0, len(leaderboard_us)):
	maximum  = max(totals_us)
	index = totals_us.index(maximum)
	leaderboard_us[i] = {"team-id": index+1, "score":totals_us[index]}
	totals_us[index] = -1

print(json.dumps(leaderboard_us))


t8 = time.time()
print("time take in step 4 is: {}".format(t8-t7))



