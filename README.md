# The AI Morning Gossip

A daily email digest of AI news, written up gossip-column style, pulled only
from a curated list of verified sources. Runs every morning at 7:00 AM IST
via GitHub Actions — no server of your own needed.

## Setup (about 10 minutes, one-time)

### 1. Create a private GitHub repo
- Go to github.com → New repository → make it **Private**.
- Upload these three files, keeping the folder structure:
  ```
  ai_gossip_digest.py
  .github/workflows/daily-ai-gossip.yml
  README.md
  ```
  (Easiest: drag-and-drop them into GitHub's web UI, or `git push` if you're
  comfortable with git.)

### 2. Get a Google AI Studio (Gemini) API key
- Go to aistudio.google.com/apikey → Create API key (if you already have
  one, just reuse it).
- Google AI Studio has a free tier; a once-a-day digest will likely stay
  within it, but check current Gemini API pricing/limits if you're unsure.

### 3. Get a Gmail "app password"
Regular Gmail passwords won't work for scripts. You need an app password:
1. Turn on 2-Step Verification on the Gmail account, if not already on:
   myaccount.google.com/security
2. Go to myaccount.google.com/apppasswords
3. Create a new app password (name it "AI Gossip Digest") → copy the
   16-character code it gives you.

### 4. Add secrets to your GitHub repo
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add these four:

| Secret name | Value |
|---|---|
| `GEMINI_API_KEY` | your Google AI Studio API key |
| `GMAIL_ADDRESS` | the Gmail address to send FROM |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 3 |
| `RECIPIENT_EMAIL` | the email address you want the digest sent TO |

### 5. Test it
Go to the **Actions** tab in your repo → "Daily AI Morning Gossip" →
**Run workflow** (this uses the `workflow_dispatch` trigger). Check your
inbox in a minute or two.

### 6. Done
From here it runs automatically every day at 7:00 AM IST. To change the
time, edit the `cron` line in `.github/workflows/daily-ai-gossip.yml`
(times are in UTC — IST is UTC+5:30).

## Customizing

- **Sources**: edit the `VERIFIED_SOURCES` list in `ai_gossip_digest.py` to
  add/remove trusted domains.
- **Tone/structure**: edit `SYSTEM_PROMPT` in the same file.
- **Model**: change `MODEL` if you want a cheaper/faster or more thorough
  model.
- **Multiple recipients**: change `RECIPIENT_EMAIL` in `send_email()` to
  accept a comma-separated list, or add more `sendmail` calls.

## Running it manually (optional, for testing on your own machine)

```bash
pip install requests
export GEMINI_API_KEY=AIza...
export GMAIL_ADDRESS=you@gmail.com
export GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
export RECIPIENT_EMAIL=you@gmail.com
python ai_gossip_digest.py
```
