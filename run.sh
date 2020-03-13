cd "$HOME/mijia-monitor/" || exit
(
  echo "venv/bin/python mijia.py";
  echo "venv/bin/python bot.py 2> log.txt"
) | parallel