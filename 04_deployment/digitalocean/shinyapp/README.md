# Deploy Shiny App (Marketstack EOD Explorer) to DigitalOcean

This folder contains the Shiny for Python app from `02_productivity/shinyapp`, packaged for deployment on DigitalOcean App Platform using Docker.

## Contents

- `app.py` – Shiny UI and server logic
- `api_client.py` – Marketstack EOD API client
- `requirements.txt` – Python dependencies
- `Dockerfile` – Container build for App Platform

## Prerequisites

- Marketstack API key (from [marketstack.com](https://marketstack.com))
- DigitalOcean account and App Platform access
- Repo (e.g. GitHub) with this folder at a path App Platform can use (e.g. `04_deployment/digitalocean/shinyapp`)

## Deploy on App Platform

1. **Create an app** in DigitalOcean App Platform and connect your repo.
2. **Set the source directory** to the path that contains this folder (e.g. `04_deployment/digitalocean/shinyapp`), or the repo root and ensure the build context includes this directory.
3. **Use Docker** as the build type; App Platform will use the `Dockerfile` in this folder.
4. **Add environment variables** in the App Platform dashboard:
   - `TEST_API_KEY2` or `MARKETSTACK_API_KEY` = your Marketstack API key  
   (Do not commit the key; set it only in the dashboard.)
5. **Deploy.** The app will listen on the port App Platform provides (default 8000 in the Dockerfile).

## Run locally with Docker

```bash
cd 04_deployment/digitalocean/shinyapp
docker build -t shiny-eod .
docker run -p 8000:8000 -e TEST_API_KEY2=your_key_here shiny-eod
```

Then open `http://localhost:8000`.

## Run locally without Docker

From the project root:

```bash
cd 02_productivity/shinyapp
pip install -r requirements.txt
# Set TEST_API_KEY2 or MARKETSTACK_API_KEY in .env or environment
shiny run --reload app.py
```
