#include <string>
#include <vector>
#include <ctime>

// not used atm
//#define MAX_NUMBER_OF_CHALLENGES 20
//#define MAX_NUMBER_OF_CHALLENGE_TYPES 5

#pragma once

struct PlayerSubmission
{
    int challengeId;
    std::string flag;
    double score;          // score awarded to the player for this challenge
    time_t submissionTime;

    PlayerSubmission(
            int challengeId,
            double score,
            time_t submissionTime
        )
        : challengeId(challengeId)
        , score(score)
        , submissionTime()
    { }
};

struct PlayerScore
{
    double score;       // scores calculated by CTF based on scoring formula
    time_t time;        // time associated with score calculation
                        // it can be different from submission times

    PlayerScore(double score, time_t time)
        : score(score)
        , time(time)
    { }
};

class Player
{
public:
    std::vector<std::string> skills;                        // user's skills, to be filled by the user
    std::vector<PlayerSubmission> m_vecPlayerSubmissions;   // flags submitted by the player, sorted by time, filled by the user

    std::vector<PlayerScore> m_vecPlayerScores;
    int m_playerID = 0;                                     // player id assigned by the CTF. (maybe needed later)

    int totalScore = 0;

    Player() = default;

    // not anymore used in submissions-based design
    Player(
            const std::vector<std::string>& skills,
            const std::vector<PlayerSubmission>& vecPlayerSubmissions,
            const int playerID
        )
        :
        skills(skills),
        m_vecPlayerSubmissions(vecPlayerSubmissions),
        m_playerID(playerID)
    { }

    Player(const Player& p)
    {
        skills = p.skills;
        m_vecPlayerSubmissions = p.m_vecPlayerSubmissions;
        m_playerID = p.m_playerID;
    }

    bool operator < (const Player& obj)
    {
        return totalScore < obj.totalScore;
    }

    bool operator > (const Player& obj)
    {
        return totalScore > obj.totalScore;
    }

    // Use it to add a submission to the player
    // it also calls the UpdateScore function to update scores-vec and current-score
    void AddSubmission(const int challengeId, const double score, const time_t time);

    // sets the score if challenge is found in player submissions
    // also calls the function to update scores-vector and current-score
    bool SetScore(const int challengeId, const double score, const time_t time);

    // sums the submissions and updates score with time
    // also updates the totalScore variable
    void UpdateScore(const time_t time);      // sums all scores and adds result to m_vecPlayerScores
};
