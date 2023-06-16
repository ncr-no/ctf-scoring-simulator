% parser for defcon-quals ctf json log file
% creates a generic and simple output file that is easy-to-parse in c++
% run it in the matlab-scripts folder

fname = "../data/dcquals_2020.json";
fid = fopen(fname);
raw = fread(fid);
fclose(fid);
str = char(raw');
data=jsondecode(str);

challenges=[""];
teams=[""];

% clear the file if it already exists
writelines("", "../data/logs.txt","WriteMode","overwrite");

matrix = [];
for i=1:length(data.message.solves)
    challengeNum = 1;
    if startsWith(data.message.solves{i}{1}, "speedrun")
        continue
    end

    this_challenge = convertCharsToStrings(data.message.solves{i}{1});
    if ismember(this_challenge, challenges)
        challengeNum = find(challenges==this_challenge);
    else
        challenges = [challenges this_challenge];
        challengeNum = find(challenges==this_challenge);
    end

    teamNum = 1;
    this_team = convertCharsToStrings(data.message.solves{i}{2});
    if ismember(this_team, teams)
        teamNum = find(teams==this_team);
    else
        teams = [teams this_team];
        teamNum = find(teams==this_team);
    end

    matrix=[matrix; challengeNum teamNum data.message.solves{i}{3}];
end

matrix = sortrows(matrix, 3);

for i=1:length(matrix)
    line=int2str(matrix(i,1)) + " " + int2str(matrix(i,2)) + " " + int2str(matrix(i,3));
    writelines(line, "../data/dc2020_logs.txt", "WriteMode","append");
end

