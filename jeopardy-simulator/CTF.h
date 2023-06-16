#pragma once
#include "Player.h"

#include <vector>
#include <unordered_map>
#include <ctime>
#include <string>


// not used atm
//#define MAX_NUMBER_OF_PLAYERS 1000

class CTF
{
public:
    enum class CTFScoringStyle : uint8_t
    {
        CTFSS_Static = 0,
        CTFSS_DynamicBasedOnTotalSolutions = 1,
        CTFSS_DynamicBasedOnPreviousSolutions = 2,
    };

    struct Challenge
    {
        int challengeId;
        std::string flag;
        double score;     // current score
        double maxScore;  // max score set at the beginning
        int numberOfCorrectSolutions = 0;

        // maybe add type-of-challenges. (no use like skills in players)
    };

    struct Submission
    {
        int playerId;
        std::string flag;
        int challengeId;
        time_t time;
    };

    typedef std::vector<std::pair<int, int>> leaderboard;

private:
    std::vector<Submission> m_vecFlagSubmissions;
    std::unordered_map<int, Challenge> m_mapChallenges; // map "challengeId" <-> challenge
    std::unordered_map<int, Player> m_mapPlayers;       // map "playerId" <-> player
    leaderboard m_topTen;          // <team-id, points>
    CTFScoringStyle m_scoringConfiguration;             // scoring algorithm
    std::string m_strScoringFormula;                    // score decay formula

public:
    CTF(const CTFScoringStyle scoringConfiguration, const std::string strScoringFormula)
        : m_scoringConfiguration(scoringConfiguration)
        , m_strScoringFormula(strScoringFormula)
    {
        m_topTen.resize(50);
        for (auto& rank : m_topTen)
        {
            rank.first = 0;
            rank.second = 0;
        }
    }

    static std::string PrintScoringStyle(CTFScoringStyle scoringStyle);

    // Parse submissions file //////////////////////////
    bool ParseFileAndInit(std::string filename);
    ////////////////////////////////////////////////////

    // helper functions used for setup//////////////////
    void AddPlayer(const Player& ctfPlayer);

    void AddPlayers(unsigned int number);

    void AddFlagSubmission(const Submission& flagSubmission);

    void AddChallenge(const Challenge& ctfChallenge);
    ////////////////////////////////////////////////////

    // functions used for simulation/scoring////////////

    void ProcessStaticPoints(const Submission& submissionToProcess);

    void ProcessTotalSolutionsDynamicPoints(const Submission& submissionToProcess);

    void ProcessPreviousSolutionsDynamicPoints(const Submission& submissionToProcess);

    void PrintChallengesStatistics();

    // iterates over all submissions, add submissions to players,
    // adds and updates scores to players acc to scoring func selected
    bool Run();
    ////////////////////////////////////////////////////

    // Output //////////////////////////////////////////
    // iterates over all players, creates output file(s) for all players scores with time
    leaderboard OutputScores();
};
