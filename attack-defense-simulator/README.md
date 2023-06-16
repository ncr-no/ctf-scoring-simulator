# AD-scoring-simulator
The two sub-directories contain Python scripts for two different data sets. Separate scripts are written because of the difference in data structures of Enowars and ECSC SQL dumps. The Python scripts can be used to apply the following scoring formulas to these datasets:
1. CyberChallengeIT
2. Defcon 2021
3. Enowars
4. iCTF
5. Saarland 
6. ECSC

In addition, some more scripts are added to the ECSC repo that contains some experimental scoring formulas.

The data for Enowars was exported from the SQL dumps at https://github.com/enowars/ctf-dumps. However, the ECSC data is not available publicly and is not published in this repo for this reason. The following are examples of the psql commands used for exporting SQL data as JSON:  
`\copy (select json_agg(row_to_json(foo)) from (select "FlagServiceId","FlagOwnerId","FlagRoundId","FlagRoundOffset","AttackerTeamId","RoundId" from "SubmittedFlags" order by "Timestamp") AS foo) to './enowars5_sorted_by_time.json';`  

`\copy (select json_agg(row_to_json(foo)) from (select "FlagServiceId" AS "ServiceId","FlagOwnerId" AS "OwnerId","FlagRoundId","FlagRoundOffset" AS "RoundOffset","AttackerTeamId" AS "AttackerId","RoundId" from "SubmittedFlags" order by "Timestamp") AS foo) to './enowars5_sorted_by_time.json';`


