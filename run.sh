cd "$HOME/mijia-monitor/" || exit
(
  echo "python3 mijia.py";
  echo "python3 bot.py 2> log.txt"
) | parallel