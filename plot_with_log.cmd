@ECHO OFF
SET hr=%time:~0,2%
IF "%hr:~0,1%" equ " " set hr=0%hr:~1,1%
SET DATETIME=Log_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%hr%%time:~3,2%%time:~6,2%
SET LOG_FILE=logs/%DATETIME%.log
IF NOT EXIST logs MKDIR logs
powershell ".\chia_plot.exe -n 1 -r 16 -u 256 -t T:\ChiaTemp\ -d R:\ChiaPlots\ -p poolkey -f farmerkey | tee '%LOG_FILE%'"
PAUSE
