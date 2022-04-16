#!/bin/bash

# copy to local backups folder
cd "$HOME/mijia-monitor/" || exit
today=$(date '+%Y_%m_%d__%H_%M_%S')
cp "mijia.db" "$HOME/backups/mijia-monitor/mijia_$today.db"

# backup to gdrive
sleep 1
gdrive push -quiet -destination "/" "$HOME/backups/mijia-monitor"

# delete archives older than 7 days from disk
sleep 1
find "$HOME/backups/mijia-monitor/" -type f -mtime +7 -exec rm {} \;
