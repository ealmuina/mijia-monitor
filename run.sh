cd "$HOME/mijia-monitor/" || exit
(
  echo "venv/bin/python mijia.py > log_mijia.txt";
  echo "venv/bin/python bot.py 2> log_bot.txt"
) | parallel