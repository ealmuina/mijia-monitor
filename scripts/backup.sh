#!/bin/bash

# copy to local backups folder
cd "$HOME/mijia/" || exit
today=$(date '+%Y_%m_%d__%H_%M_%S')
cp "mijia.db" "$HOME/backups/mijia/mijia_$today.db"

# backup to gdrive
sleep 1
gdrive push -quiet -destination "/" "$HOME/backups/mijia"

# delete archives older than 7 days from disk
sleep 1
find "$HOME/backups/mijia/" -type f -mtime +7 -exec rm {} \;
