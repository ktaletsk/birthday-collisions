# Birthday Collisions, Live

[![Live demo on Railway](https://img.shields.io/badge/Live_demo-Railway-0B0D0E?logo=railway&logoColor=white)](https://birthday-collisions-production.up.railway.app/deck/)

An audience-powered presentation.
Fork of [Light2Dark/birthday-collisions](https://github.com/Light2Dark/birthday-collisions).

The original project turns the birthday paradox into an engaging marimo
presentation. This version keeps that story, then invites the room to submit
their birthdays while the presenter walks through the math. The slides update
as answers arrive, eventually revealing real collisions, near misses, and room
statistics.

## What changed

- A phone-friendly voting page asks for a birthday and an optional nickname.
- A small FastAPI app serves the voting page, API, and marimo presentation.
- The notebook reacts to the shared room state automatically.
- A pinned QR code and participant count stay visible throughout the deck.

## Run it

### Localhost: authoring and debugging

```bash
uv run main.py
```

Then open:

- presentation: <http://127.0.0.1:8010/deck/>
- audience form: <http://127.0.0.1:8010/join/demo>
- API docs: <http://127.0.0.1:8010/docs>

Open the audience form in one or more browser profiles and submit birthdays.
Reusing the same browser updates that browser's answer instead of adding
another participant.

For slide-only authoring in marimo's editor, use:

```bash
uv run marimo edit custom.py
```

Run `uv run main.py` again when you want to test the voting page and
presentation together.

### ngrok: one-off presentations

[Install ngrok](https://ngrok.com/docs/getting-started/) and connect your
account once. On macOS:

```bash
brew install ngrok
ngrok config add-authtoken YOUR_TOKEN
```

Then run the app and tunnel in separate terminals:

```bash
uv run main.py
```

```bash
ngrok http 8010
```

ngrok prints a temporary public URL. Append `/deck/` for the presentation or
`/join/demo` for the voting page. The presentation detects the forwarded URL
and puts it in the link and QR code, so `PUBLIC_URL` is not required.

The free ngrok service may show each audience member a one-time **Visit Site**
warning before opening the voting page.

### Railway: durable deployments

[Railway](https://docs.railway.com/guides/fastapi) provides a stable public URL
and redeploys when you push to GitHub:

1. Push the repository to GitHub.
2. In Railway, create a project with **Deploy from GitHub repo** and select the
   repository.
3. Open the service's **Settings → Networking** and choose
   **Generate Domain**.
4. Optionally set the healthcheck path to `/healthz`.

Railway's
[Python builder](https://railpack.com/languages/python/) detects
`pyproject.toml`, `uv.lock`, FastAPI, and uvicorn. It installs with uv and
starts the app on Railway's assigned port, so no custom build command, start
command, `HOST`, or `PORT` variable is needed.

After generating the domain, you can make the presentation URL explicit by
adding this service variable:

```text
PUBLIC_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
```

Keep the service at one replica. The current room store is in memory, so
restarts and redeployments clear the votes. “Durable” here means a stable
hosted URL, not persistent vote storage.

## How it works

This project combines a few lesser-known marimo features:

- [FastAPI support](https://docs.marimo.io/guides/deploying/programmatically/):
  `main.py` serves the voting page and API, then mounts the notebook in the
  same application with `marimo.create_asgi_app()`.
- [Slide support](https://docs.marimo.io/guides/apps/#slides-layout): the
  notebook runs as a presentation while marimo's reactive execution redraws
  results as votes arrive.

Together, they make something a little like Slido, but fully open source. The
FastAPI app and notebook share one thread-safe, in-memory room store; the
notebook checks it every second and updates the dependent slides.

The local defaults require no configuration. They can be overridden with:

```text
HOST=127.0.0.1
PORT=8010
VOTING_ROOM=demo
VOTE_REFRESH_INTERVAL=1s
```

`PUBLIC_URL` is optional; when unset, the join URL is inferred from the request.

The app must run with one worker because its room state is in memory. Restarting
the server clears the room.

## Tests

```bash
uv run pytest
```
