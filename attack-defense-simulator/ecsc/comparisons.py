#!/bin/python3

import re
import json
import math
import os

import time
import copy
import sys


def CompareThroughDissimilarityIndex(l1, l2):
	if len(l1) != len(l2):
		raise Exception("leaderboards lengths should be equal")

	difference = 0
	for teamId, teamInfo1 in l1.items():
		teamInfo2 = l2[teamId]
		if teamInfo1[0] != teamInfo2[0]: # comparing ranks
			difference +=1

	return (difference / len(l1)) * 100


def CompareThroughDifferenceInRank(l1, l2):
	if len(l1) != len(l2):
		raise Exception("leaderboards lengths should be equal")

	difference = 0
	totalPercentageChange = 0
	for teamId, teamInfo1 in l1.items():
		teamInfo2 = l2[teamId]
		change = (abs(teamInfo1[0] - teamInfo2[0]) * 100)/teamInfo1[0];
		totalPercentageChange += change

	return (totalPercentageChange / len(l1))

def CompareThroughDifferenceInScore(l1, l2):
	if len(l1) != len(l2):
		raise Exception("leaderboards lengths should be equal")

	difference = 0
	totalPercentageChange = 0
	for teamId, teamInfo1 in l1.items():
		teamInfo2 = l2[teamId]
		change = (abs(teamInfo1[1] - teamInfo2[1]) * 100)/teamInfo1[1];
		totalPercentageChange += change

	return (totalPercentageChange / len(l1))


ranksFileName = "ranks.txt"

# parsing input file
leaderboards = [{} for i in range(0,6)] # teamId: rank
scorings = []
with open(ranksFileName, 'r') as f: # open in readonly mode
	lines = f.readlines()
	strippedLine = re.split('\s+', lines[0])
	scorings.append(strippedLine[0])
	scorings.append(strippedLine[1])
	scorings.append(strippedLine[2])
	scorings.append(strippedLine[3])
	scorings.append(strippedLine[4])
	scorings.append(strippedLine[5])
	
	for i in range(1, len(lines)):
		line_stripped = re.split('\s+', lines[i])
		for j in range(0, len(line_stripped) - 1):
			commaSplitted = line_stripped[j].split(",")
			leaderboards[j][commaSplitted[0]] = [i, float(commaSplitted[1])]

# Dissimilarity index
for score in scorings:
	print(score + " | ", end="")
print("")
for i in range(0, len(scorings)):
	print(scorings[i], end="")
	for j in range(0, len(scorings)):
		print(" | {}".format(round(CompareThroughDissimilarityIndex(leaderboards[i], leaderboards[j]), 2)), end="")
	print("")

print("\n\nPercentage Difference in rank\n")
# Dissimilarity index
for score in scorings:
	print(score + " | ", end="")
print("")
for i in range(0, len(scorings)):
	print(scorings[i], end="")
	for j in range(0, len(scorings)):
		print(" | {}".format(round(CompareThroughDifferenceInRank(leaderboards[i], leaderboards[j]), 2)), end="")
	print("")


print("\n\nPercentage Difference in scores\n")
# Dissimilarity index
for score in scorings:
	print(score + " | ", end="")
print("")
for i in range(0, len(scorings)):
	print(scorings[i], end="")
	for j in range(0, len(scorings)):
		print(" | {}".format(round(CompareThroughDifferenceInScore(leaderboards[i], leaderboards[j]), 2)), end="")
	print("")
