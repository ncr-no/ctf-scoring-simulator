# Scoring simulator for CTFs
This simulator will be used to simulate/plot scores of teams/players based on different scoring algorithms used. The scoring system will support both Jeopardy and Attack-Defence style CTFs. It will take in as input submissions from teams based on time and output the teams scores by times. The output can then be used to plot the scores.

## Jeopardy Simulator
The simulator functioning can be divided into three phases:
### Initialization
In the initializaiton phase, all different kinds of inputs are added to the CTF class (by the user). These include:
	a. Challenges [flags, points, types, ?? (not all may not be needed) ]
	b. players info [# of players, ??]
	c. submissions with times [who submitted what at what time]
	d. scoring algorithm to use

### Processing
In the processing phase, the simulator will go over all the submissions by time. While doing so it will fill up the scores of players by time based on the scoring formula set in the initialization phase.

### Output
This phase is indistinguishable from the user's point of view. After all submissions have been processed in the previous phase, the simulator will write scores including times from all players into an output file that can be plotted using an external tool.



## Jeorpardy Simulator - Structure

Classes & sub-classes:
* CTF: CTF will have challenges (A), players (A), submissions (A), scoring algorithms (M).
* Challenges: challengeID, flags, points, maxPoints, numberOfCorrectSolutions
* Players: 
	* playerID
	* playerScores [pair(score, time)]
	* playerSubmissions [challengeID, score, time, flag (not really needed)] (updated while processing)
	* some helper functions to fill the above
* Submissions: playerID, challengeID, flag, time
* scoring routine: !!TODO!! 
