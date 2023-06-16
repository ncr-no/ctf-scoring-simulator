#include "Player.h"

void Player::AddSubmission(const int challengeId, const double score, const time_t time)
{
    m_vecPlayerSubmissions.emplace_back(PlayerSubmission(challengeId, score, time));
    UpdateScore(time);
}

bool Player::SetScore(const int challengeId, const double score, const time_t time)
{
    for (auto& submission : m_vecPlayerSubmissions)
    {
        if (submission.challengeId == challengeId)
        {
            submission.score = score;
            UpdateScore(time);
            return true;
        }
    }
    return false;
}

void Player::UpdateScore(const time_t time)
{
    int score = 0;
    for (auto submission : m_vecPlayerSubmissions)
    {
        score += submission.score;
    }
    totalScore = score;
    m_vecPlayerScores.push_back(PlayerScore(score, time));
}
