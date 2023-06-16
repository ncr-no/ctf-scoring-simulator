cd ../top10-scores-output/

files = ls;
files = string(files(3:end, :));

for i=1:length(files)
    grid on
    fid=fopen(files(i));
    C=textscan(fid, "%f %f");
    fclose(fid);
    YR=cell2mat(C);
    YR(:,2) = datenum(datetime(YR(:,2),'ConvertFrom','epochtime','Epoch', '1970-01-01', "TicksPerSecond",1000,'Format','HH:mm:ss.SSSS'));
    plot(YR(:,2), YR(:,1));
    hold on
end

xlabel("Time (h)")
ylabel("Scores")
datetick('x')
legend(files);
cd ../matlab-scripts
