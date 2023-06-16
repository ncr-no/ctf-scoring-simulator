# Jeopardy Scoring Simulator

This code can be used to apply different scoring algorithms to the logs generated from an actual CTF. 

# Usage

The repo consists of a C++ visual studio project, Matlab scripts, and some old CTF data found on GitHub. 

1. Visual Studio Project  
The visual studio project contains the source code for the Jeopardy scoring simulator. The code allows the usage of different data logs, CTF algorithm (check CTF::CTFScoringStyle), and decay functions (in ScoreCalculationFormulaSelection in CTF.cpp).
The code can also be used for comparing different scoring algorithms or decay functions by uncommenting the #define ENABLE_COMPARISONS.

3. matlab-scripts  
The Matlab scripts can be used to convert JSON data from CTFs to simple text files that can be parsed by the C++ simulator. 
The script plottingScript can be used to plot the output generated from the Jeopardy simulator in a CTF-like manner.

4. data  
Contains JSON and converted data from https://github.com/o-o-overflow/scoring-playground/ and https://github.com/pwn2winctf/nizkctf-audit-trail.
