cd "$HOME/mijia-monitor/" || exit
# Backup DB
backup_dir=$(jq -r '.backup_dir' config.json)
cp mijia.db $backup_dir
