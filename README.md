# Grow-a-Garden Discord Bot

This project uses [GitHub Actions](https://docs.github.com/en/actions) to run a small Python script every 5 minutes.  
The script fetches stock + weather data from the [Grow-a-Garden API](https://gagapi.onrender.com) and posts updates into a Discord channel via a webhook.

## How it works
- GitHub Actions runs `bot.py` on a schedule.
- The script queries the API and builds a Discord embed.
- If new data is found, it posts into your server.

## Setup
1. Fork/clone this repository.
2. Add your Discord webhook URL under **Settings → Secrets and variables → Actions** as `DISCORD_WEBHOOK`.
3. (Optional) adjust polling rate or formatting inside `bot.py`.
4. Watch Discord light up with updates every 5 minutes.

## Notes
- Works with free GitHub Actions.  
- Public repo = unlimited minutes; private repo = 2000 free minutes/month.  
- All sensitive values (like your webhook) are stored in GitHub Secrets, never in code.

## License
[MIT](LICENSE)
