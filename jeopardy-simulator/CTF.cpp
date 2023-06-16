#include "CTF.h"

#include <iostream>
#include <cmath>
#include <fstream>
#include <direct.h>
#include <errno.h>
#include <algorithm>
#include <iomanip>


void CTF::AddFlagSubmission(const Submission& flagSubmission)
{
    m_vecFlagSubmissions.push_back(flagSubmission);
}

void CTF::AddChallenge(const Challenge& ctfChallenge)
{
    m_mapChallenges[ctfChallenge.challengeId] = ctfChallenge;
}

std::string CTF::PrintScoringStyle(CTFScoringStyle scoringStyle)
{
    switch (scoringStyle)
    {
    case CTFScoringStyle::CTFSS_Static:
        return "static";
    case CTFScoringStyle::CTFSS_DynamicBasedOnPreviousSolutions:
        return "Dynamic-Previous-Sol";
    case CTFScoringStyle::CTFSS_DynamicBasedOnTotalSolutions:
        return "Dynamic-Total-Sol";
    default:
        throw("Unexpected scoring style");
    }
}

bool CTF::ParseFileAndInit(std::string filename)
{
    std::ifstream inputFile(filename);
    if (! inputFile.is_open())
    {
        std::cout << "Error: unable to open input log file\n";
        return false;
    }

    std::string line;
    int maxTeamNumber = 0, maxChallengeNumber = 0;
    int challengeId, teamId;
    std::time_t timeOfSubmission;
    while (inputFile >> challengeId >> teamId >> timeOfSubmission)
    {
        Submission tempSubmission;
        tempSubmission.challengeId = challengeId;
        tempSubmission.playerId = teamId;
        tempSubmission.time = timeOfSubmission;
        m_vecFlagSubmissions.emplace_back(tempSubmission);

        maxTeamNumber = teamId > maxTeamNumber ? teamId : maxTeamNumber;
        maxChallengeNumber = challengeId > maxChallengeNumber ? challengeId : maxChallengeNumber;
    }
    inputFile.close();


    // add players and challenges
    {
        AddPlayers(maxTeamNumber + 1);
        CTF::Challenge tempChallenge;
        tempChallenge.challengeId = 1;
        tempChallenge.maxScore = 500;
        tempChallenge.score = 500;
        tempChallenge.numberOfCorrectSolutions = 0;
        AddChallenge(tempChallenge);
        while (maxChallengeNumber >= 0)
        {
            tempChallenge.challengeId = maxChallengeNumber;
            AddChallenge(tempChallenge);
            maxChallengeNumber--;
        }
    }

    return true;
}

void CTF::AddPlayer(const Player& ctfPlayer)
{
    m_mapPlayers[ctfPlayer.m_playerID] = ctfPlayer;
}

void CTF::AddPlayers(unsigned int number)
{
    for (unsigned int i = 0; i < number; i++)
    {
        Player tempPlayer;
        tempPlayer.m_playerID = i;
        m_mapPlayers[i] = tempPlayer;
    }
}

double Pwn2winFormula(const int numberOfSolutions)
{
    // taken from pwn2win Github
    // https://github.com/pwn2winctf/nizkctf-v2/blob/ee1e302779aeb70f027edb97aeb68dfb575a0c75/src/utils.ts
    double minScore = 50;
    double K = 80;
    double V = 3;
    double score = std::max(floor(500 -
        (K * log2((numberOfSolutions + V) / (1 + V)))), minScore); // pwn2win
    return score;
}

double DefconOOOFormula(const int numberOfSolutions)
{
    double score = 100 + (500 - 100) / (1 + 0.08 * numberOfSolutions * log(1 * numberOfSolutions)); // defcon OOO
    return score;
}

double CtfdFormula(const int numberOfSolutions)
{
    double minimum = 100;
    double initial = 500;
    double decay = 20;
    double score = ((minimum - initial) / (decay * decay)) * (numberOfSolutions * numberOfSolutions) + initial;
    return std::max(score, minimum);
}

double WatevrCTFFormula(const int numberOfSolutions)
{
    double score = round(10 + 490 / (1 + (numberOfSolutions - 1) / 12));
    return score;
}

double StaticFormula(const int numberOfSolutions)
{
    return numberOfSolutions < 5
        ? 1500
        : numberOfSolutions < 15
            ? 750
            : numberOfSolutions < 25
                ? 250
                : 100;
}


// find challenge
// set fixed points acc. to no. of solves
// find player
// add score to player
// update score for all players
void CTF::ProcessStaticPoints(const Submission& submissionToProcess)
{
    auto& challengeInfo = m_mapChallenges[submissionToProcess.challengeId];
    challengeInfo.numberOfCorrectSolutions++; // add current solution to total

    const double newChallengeScore = StaticFormula(challengeInfo.numberOfCorrectSolutions);
    challengeInfo.maxScore = newChallengeScore; // no use but still doing for correctness

    auto& submissionPlayer = m_mapPlayers[submissionToProcess.playerId];
    submissionPlayer.AddSubmission(submissionToProcess.challengeId, newChallengeScore, submissionToProcess.time);

    for (auto& mapIt : m_mapPlayers)
    {
        auto& player = mapIt.second;
        if (player.m_playerID == submissionPlayer.m_playerID)
        {
            continue;
        }

        player.SetScore(challengeInfo.challengeId, newChallengeScore, submissionToProcess.time);
    }
}

double ScoreCalculationFormulaSelection(const int numberOfCorrectSolutions, const std::string scoringFormula)
{
    if (scoringFormula == "defcon")
    {
        return DefconOOOFormula(numberOfCorrectSolutions);
    }
    else if (scoringFormula == "pwn2win")
    {
        return Pwn2winFormula(numberOfCorrectSolutions);
    }
    else if (scoringFormula == "ctfd")
    {
        return CtfdFormula(numberOfCorrectSolutions);
    }
    else if (scoringFormula == "watevr")
    {
        return WatevrCTFFormula(numberOfCorrectSolutions);
    }
    else
    {
        std::cout << "Scoring formula not supported.\nPlease add the new scoring formula to score calculation function.\n";
        throw("Error!");
    }
}

// find challenge
// update number of solutions
// calculate challenge score
// update score for all players that submitted it
void CTF::ProcessTotalSolutionsDynamicPoints(const Submission& submissionToProcess)
{
    auto& challengeInfo = m_mapChallenges[submissionToProcess.challengeId];
    challengeInfo.numberOfCorrectSolutions++; // add current solution to total

    const double newChallengeScore =
        ScoreCalculationFormulaSelection(challengeInfo.numberOfCorrectSolutions, m_strScoringFormula);

    auto& submissionPlayer = m_mapPlayers[submissionToProcess.playerId];
    submissionPlayer.AddSubmission(submissionToProcess.challengeId, newChallengeScore, submissionToProcess.time);

    for (auto& mapIt : m_mapPlayers)
    {
        auto& player = mapIt.second;
        if (player.m_playerID == submissionPlayer.m_playerID)
        {
            continue;
        }

        player.SetScore(challengeInfo.challengeId, newChallengeScore, submissionToProcess.time);
    }
}

// find challenge
// update number of solutions
// calculate challenge score
// update score for all players that submitted it
void CTF::ProcessPreviousSolutionsDynamicPoints(const Submission& submissionToProcess)
{
    auto& challengeInfo = m_mapChallenges[submissionToProcess.challengeId];
    challengeInfo.numberOfCorrectSolutions++; // add current solution to total

    const double newChallengeScore =
        ScoreCalculationFormulaSelection(challengeInfo.numberOfCorrectSolutions, m_strScoringFormula);

    auto& submissionPlayer = m_mapPlayers[submissionToProcess.playerId];
    submissionPlayer.AddSubmission(submissionToProcess.challengeId, newChallengeScore, submissionToProcess.time);
}

void CTF::PrintChallengesStatistics()
{
    std::vector<std::pair<int, Challenge>> tempChallengeVector;
    for (auto& it : m_mapChallenges)
    {
        tempChallengeVector.push_back(it);
    }

    std::sort(tempChallengeVector.begin(), tempChallengeVector.end(), [](auto a, auto b)
        {
            return a.second.numberOfCorrectSolutions > b.second.numberOfCorrectSolutions;
        });

    for (auto challenge : tempChallengeVector)
    {
        std::cout << "challenge-id" << challenge.first
            << ", number of solutions:" << challenge.second.numberOfCorrectSolutions << std::endl;
    }

}


// go through submissions
// update scores of players based on chosen algo
bool CTF::Run()
{
    for (auto submission : m_vecFlagSubmissions)
    {
        switch (m_scoringConfiguration)
        {
        case CTFScoringStyle::CTFSS_Static:
            ProcessStaticPoints(submission);
            break;
        case CTFScoringStyle::CTFSS_DynamicBasedOnTotalSolutions:
            ProcessTotalSolutionsDynamicPoints(submission);
            break;
        case CTFScoringStyle::CTFSS_DynamicBasedOnPreviousSolutions:
            ProcessPreviousSolutionsDynamicPoints(submission);
            break;
        default:
            break;
        }
    }
    return true;
}

CTF::leaderboard CTF::OutputScores()
{
    // get top-10 players
    for (const auto& mapIt : m_mapPlayers)
    {
        const auto& player = mapIt.second;

        for (int i = 0; i < m_topTen.size(); ++i)
        {
            if (player.totalScore > m_topTen[i].second)
            {
                // shift positions
                for (int j = m_topTen.size() - 1; j > i; --j)
                {
                    m_topTen[j].first = m_topTen[j - 1].first;
                    m_topTen[j].second = m_topTen[j - 1].second;
                }

                // add current position
                m_topTen[i].first = player.m_playerID;
                m_topTen[i].second = player.totalScore;

                // break
                break;
            }
        }
    }
    ////////////////////


    // make directory for output
    std::string outputDirectory = "top10-scores-output";
    if (_mkdir(outputDirectory.c_str()) != -1)
    {
        std::cout << "Info: Output directory created\n";
    }
    else if (errno == EEXIST)
    {
        std::cout << "Info: Output directory already exists\n";
    }
    else
    {
        std::cout << "Error: Unable to create output directory. Abort!\n";
        return std::vector<std::pair<int, int>>();
    }
    /////////////////////////////


    // TODO: rank based on timings. Two possible ways of doing it i.e. score-first, total commulative solving time
    // TODO: can also add option for first-blood points
    // TODO: print based on input from CL i.e. how many ranks to print

    // write top-10 to outputfiles and print leaderboard
    std::cout << "Leaderboard:\n";
    std::vector<std::string> table_header = { "Player-id","Score","Solves" };
    std::cout << table_header[0] << "   " << table_header[1] << "   " << table_header[2] << std::endl;

    for (const auto& rank : m_topTen)
    {
        const auto& player = m_mapPlayers[rank.first];
        std::string filename = outputDirectory + "/player-" + std::to_string(player.m_playerID) + ".txt";
        std::ofstream outputFile(filename.c_str());

        std::cout << std::setw(table_header[0].size()) << std::right << player.m_playerID << " | "
            << std::setw(table_header[1].size()) << rank.second << " | "
            << std::setw(table_header[2].size()) << std::left << player.m_vecPlayerSubmissions.size() << std::endl;

        for (auto scores : player.m_vecPlayerScores)
        {
            outputFile << scores.score << " " << scores.time << "\n";
        }
        outputFile.close();
    }
    ////////////////////////////////////////////////////
    return m_topTen;
}
