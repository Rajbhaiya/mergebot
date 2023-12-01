echo "Started"
git pull -f -q
pip install --no-cache-dir -r requirements.txt
python3 bot.py
