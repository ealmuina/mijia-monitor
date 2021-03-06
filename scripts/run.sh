cd "$HOME/mijia-monitor/" || exit
(
  echo "venv/bin/python mijia.py > log_mijia.txt"
  echo "venv/bin/python bot.py 2> log_bot.txt"
  echo "venv/bin/celery -A tasks worker --loglevel=info > log_celery.txt"
  echo "venv/bin/celery -A tasks beat --loglevel=info > log_celery_beat.txt"
) | parallel
