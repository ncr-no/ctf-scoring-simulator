#include <iostream>
#include "CTF.h"
#include <iomanip>
#include <assert.h>


//#define ENABLE_COMPARISONS

float CompareThroughDissimilarityIndex(const CTF::leaderboard l1, const CTF::leaderboard l2)
{
    // how many players have their positions changed going from one leaderboard to the other
    // this is done only for the top 20 players
    // get a players position in leaderboard
    // get position in leaderboard2
    // compare positions: if changed -> inc difference
    // return difference / 20 * 100

    assert(!(l1.size() < 20 || l2.size() < 20), "The two leaderboards should have at least 20 players");


    float difference = 0;
    for (int i = 0; i < 20; ++i)
    {
        const int playerId = l1[i].first;
        const auto it = std::find_if(
            l2.begin(),
            l2.end(),
            [&playerId](const auto& p) {return p.first == playerId; }
        );

        int position2 = it - l2.begin();
        if (position2 != i)
        {
            difference++;
        }
    }

    return (difference / 20.000) * 100.00;
}


float CompareThroughDifferenceInRank(const CTF::leaderboard l1, const CTF::leaderboard l2)
{
    assert(!(l1.size() < 30 || l2.size() < 30), "The two leaderboards should have at least 30 players");

    float cummulativeChange = 0;
    for (int i = 1; i <= 20; ++i)
    {
        const int playerId = l1[i - 1].first;
        const auto it = std::find_if(
            l2.begin(),
            l2.end(),
            [&playerId](const auto& p) {return p.first == playerId; }
        );

        assert(it != l2.end(), "Could not find player from leaderboard 1 in leaderboard 2");
        int position2 = it - l2.begin() + 1;

        float change = ((float)(position2 - i) / (float)i) * 100.000;  // adding percentage differences in ranks
        // Higher ranks have more weightage since i is small for top ranks

        cummulativeChange += (change); // abs?
    }

    return (cummulativeChange / 20.0000); // avg chagne
}


float CompareThroughDifferenceInScore(const CTF::leaderboard l1, const CTF::leaderboard l2)
{

    assert(!(l1.size() < 30 || l2.size() < 30), "The two leaderboards should have at least 30 players");

    float cummulativeChange = 0;
    for (int i = 1; i <= 20; ++i)
    {
        const int playerId = l1[i - 1].first;
        const auto it = std::find_if(
            l2.begin(),
            l2.end(),
            [&playerId](const auto& p) {return p.first == playerId; }
        );

        assert(it != l2.end(), "Could not find player from leaderboard 1 in leaderboard 2");
        int score2 = it->second;

        float change = ((float)(score2 - l1[i - 1].second) / (float)l1[i - 1].second) * 100.000;

        cummulativeChange += (change); // why not abs?
    }

    return cummulativeChange / 20.0000;
}


int main()
{
    std::string file = "dc2021_logs.txt";
    std::vector<std::string> filenames;
    filenames.emplace_back(std::string("pwn2win_logs.txt"));
    filenames.emplace_back(std::string("dc2021_logs.txt"));
    filenames.emplace_back(std::string("dc2020_logs.txt"));
    filenames.emplace_back(std::string("dc2019_logs.txt"));

    const std::string scoringFormula("defcon");
    std::cout << "Comparing different scoring algorithms.\n";
    std::cout << "ScoringFormula being used = " + scoringFormula + "\n\n\n";

    std::vector<CTF::CTFScoringStyle> scoringStyles;
    scoringStyles.emplace_back(CTF::CTFScoringStyle::CTFSS_Static);
    scoringStyles.emplace_back(CTF::CTFScoringStyle::CTFSS_DynamicBasedOnTotalSolutions);
    scoringStyles.emplace_back(CTF::CTFScoringStyle::CTFSS_DynamicBasedOnPreviousSolutions);

    std::vector <CTF::leaderboard> leaderboards;
    leaderboards.resize(scoringStyles.size());

    std::vector<std::vector<float>> values;
    values.resize(scoringStyles.size(), std::vector<float>(scoringStyles.size()));


    for (const auto file : filenames)
    {
        for (int i = 0; i < scoringStyles.size(); ++i)
        {
            CTF pwnCTF(scoringStyles[i], scoringFormula);
            std::cout << "Processing log file \"" + file + "\"...\n";
            if (!pwnCTF.ParseFileAndInit(("data\\") + file))
            {
                std::cout << "Parsing failed. Aborting!\n";
                return -1;
            }
            std::cout << "Parsing Done\n\n";

            std::cout << "Running...\n";
            pwnCTF.Run();
            std::cout << "Done!\n\n";

            std::cout << "Output scores...\n";
            leaderboards[i] = pwnCTF.OutputScores();
            std::cout << "Done!\n--------------------------------------\n\n\n";
        }


#ifdef ENABLE_COMPARISONS
        std::cout << "Comparing top 20 of the leaderboard - CompareThroughDissimilarityIndex\n";

        std::cout << "                     | static               | Dynamic-Total-Sol    | Dynamic-Previous-Sol \n";

        for (int i = 0; i < scoringStyles.size(); ++i)
        {
            std::cout << std::setw(20) << CTF::PrintScoringStyle(scoringStyles[i]);
            for (int j = 0; j < scoringStyles.size(); ++j)
            {
                std::cout << " | " << std::setw(20) <<
                    CompareThroughDissimilarityIndex(leaderboards[i], leaderboards[j]);
                values[i][j] += CompareThroughDissimilarityIndex(leaderboards[i], leaderboards[j]);
            }
            std::cout << "\n";
        }
#endif // ENABLE_COMPARISONS

    }


#ifdef ENABLE_COMPARISONS
    std::cout << "Average comparison scores------------------------";
    std::cout << "\n\n\n\n                     | static               | Dynamic-Total-Sol    | Dynamic-Previous-Sol \n";
    for (int i = 0; i < 3; ++i)
    {
        std::cout << std::setw(20) << CTF::PrintScoringStyle(scoringStyles[i]);
        for (int j = 0; j < 3; ++j)
        {
            std::cout << " | " << std::setw(20) << values[i][j] / 4.00;
        }
        std::cout << "\n";
    }
#endif // ENABLE_COMPARISONS

}
