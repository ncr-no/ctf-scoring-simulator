% parser for pwn2win ctf json log file
% creates a generic and simple output file that is easy-to-parse in c++
% run it in the matlab-scripts folder

fname = "../data/pwn2win-logs.json";
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
for i=1:length(data)
    challengeNum = 1;
    this_challenge = convertCharsToStrings(data(i).challengeId);
    if ismember(this_challenge, challenges)
        challengeNum = find(challenges==this_challenge);
    else
        challenges = [challenges this_challenge];
        challengeNum = find(challenges==this_challenge);
    end

    teamNum = 1;
    this_team = convertCharsToStrings(data(i).teamId);
    if ismember(this_team, teams)
        teamNum = find(teams==this_team);
    else
        teams = [teams this_team];
        teamNum = find(teams==this_team);
    end

    matrix=[matrix; challengeNum teamNum data(i).moment];
end

matrix = sortrows(matrix, 3);

for i=1:length(matrix)
    line=int2str(matrix(i,1)) + " " + int2str(matrix(i,2)) + " " + int2str(matrix(i,3));
    writelines(line, "../data/pwn2win_logs.txt", "WriteMode","append");
end
