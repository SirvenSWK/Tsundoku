# Tsundoku

Tsundoku is a local desktop app for turning free-form notes into tasks and events. It uses Groq for AI organization, stores your accepted plans on this computer, and can export scheduled items to your Google Calendar when you choose.

## Run locally

Install Python 3.14 or later and [uv](https://docs.astral.sh/uv/), then run:

```powershell
uv sync
uv run tsundoku
```

The app opens directly into the local workspace. To use the shared AI demo, set `TSUNDOKU_AI_PROXY_URL` in a local `.env` file using `.env.example` as a template. The endpoint URL is public; never put a Groq key in this file for a distributed demo.

## Limited AI demo setup (maintainer)

The desktop app calls a Vercel function at `api/organize.ts`. That function calls Groq and enforces usage limits with Upstash Redis. It does not store the submitted note. The desktop app stores accepted tasks and events locally.

1. Push this project, including `api/organize.ts` and `vercel.json`, to GitHub. Keep `.env` untracked; it is ignored by Git.
2. In Vercel, create a project by importing the GitHub repository. Use the repository root and the **Other** framework preset. Deploy once.
3. Add an Upstash Redis database and connect it to the Vercel project. Copy its REST URL and REST token from the Upstash database settings.
4. In Vercel project settings, add these Environment Variables for Production:

   - `GROQ_API_KEY` — the maintainer's Groq key
   - `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` — Upstash REST credentials; Vercel KV's `KV_REST_API_URL` and write-enabled `KV_REST_API_TOKEN` are also accepted.

   Optional limit variables default to 10 requests per IP per day, 100 total requests per UTC day, 3,000 characters per note, and 1,000 generated tokens per request: `DEMO_IP_DAILY_LIMIT`, `DEMO_GLOBAL_DAILY_LIMIT`, `DEMO_MAX_INPUT_CHARS`, and `DEMO_MAX_OUTPUT_TOKENS`.
5. Redeploy after adding the variables. The endpoint will be `https://<your-vercel-project>.vercel.app/api/organize`.
6. Put that public endpoint URL into `.env` as `TSUNDOKU_AI_PROXY_URL` for local development. Before distributing a desktop build, set `DEFAULT_AI_PROXY_URL` in `src/tsundoku/models/settings.py` to the same endpoint and rebuild the app. Users won't enter a Groq key.

The proxy fails closed if Redis is unavailable, so the app won't call Groq without checking its limits. The limits cap request volume and output size; they are not a precise dollar-spend meter. The text users submit travels through Vercel to Groq, while their saved task data stays local.

## Google Calendar OAuth setup (maintainer)

1. In Google Cloud Console, create a project and enable the Google Calendar API.
2. Configure the OAuth consent screen for your account.
3. Create an OAuth client with application type **Desktop app** and download its JSON file.
4. For local development, set `GOOGLE_OAUTH_CLIENT_FILE` to that JSON file's path. To provide it with a source build, place it at `src/tsundoku/Data/google_oauth_client.json` before packaging.

After the maintainer configures OAuth once, users click **Log into Google Calendar** and sign in through their system browser. They do not select or find a credentials file. Google requires each desktop app to have registered OAuth credentials; its client setup is described in the [Calendar API quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python).

On first connection, Tsundoku asks to read calendars you can access and to create a calendar owned by the app. It imports visible event occurrences into the local calendar and creates or reuses a separate **Tsundoku** calendar in Google Calendar. Imported events are marked as imports and aren't written back. Events and tasks you choose to export go into the Tsundoku calendar; syncing an exported item again updates its existing Google event. Timed tasks use their saved duration or 60 minutes if none was specified; timed events default to 60 minutes. All-day items use one calendar day. Reconnecting imports newly found events without duplicating existing ones.

The OAuth client must be created by the maintainer in Google Cloud; it cannot be safely invented or shared by the app. A desktop OAuth client ID is public by design, so bundling the downloaded Desktop app client JSON simplifies setup for users but does not make the client secret confidential. The client JSON is intentionally not committed to the repository.

To revoke Tsundoku's local authorization, use **Disconnect** in Settings. This removes the locally stored token; you can also revoke access from your Google Account.

## Data and privacy

Tasks, settings, OAuth credentials, and tokens are stored locally in the per-user application-data directory. Existing task/settings JSON files in the old project data folder are copied to the new location the first time the app loads them. There is no hosted Tsundoku user interface or task database. If the limited AI demo proxy is configured, text submitted for AI organization passes through the Vercel function to Groq; otherwise local development can use `GROQ_API_KEY` from the environment.
