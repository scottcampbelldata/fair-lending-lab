# Fair Lending Lab, VPS deployment

Target: Linux (Ubuntu 22.04 or 24.04), PostgreSQL 17, Python 3.12, nginx, systemd, certbot. No Docker.

Public API host (example): `fair-lending-api.scottcampbell.io`. Update everything in this doc to match the real hostname you point at the VPS.

The Next.js frontend ships to Cloudflare Pages, not the VPS. See `frontend/` for the build, and the project README for the DNS records.

## 1. One time host prep

Run as a sudoer once per host.

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip \
                    postgresql-17 postgresql-client-17 \
                    nginx certbot python3-certbot-nginx \
                    git build-essential
```

Create an unprivileged user that will own the app process, if you do not already have one:

```bash
sudo adduser --system --group --home /home/scott --shell /bin/bash scott
sudo mkdir -p /home/scott
sudo chown scott:scott /home/scott
```

## 2. Postgres bootstrap

Edit `bootstrap_db.sql`: replace `REPLACE_ME` with a strong random password (the same one you will paste into the app `.env`).

```bash
sudo -u postgres psql -f deploy/bootstrap_db.sql
```

Confirm the app role can log in:

```bash
PGPASSWORD='STRONG_PW_HERE' psql -h localhost -U flab_app -d fair_lending_lab -c '\conninfo'
```

## 3. Application install

```bash
sudo -u scott -H git clone https://github.com/scottcampbelldata/fair-lending-lab.git /home/scott/fair-lending-lab
cd /home/scott/fair-lending-lab/platform
sudo -u scott -H python3.12 -m venv .venv
sudo -u scott -H .venv/bin/pip install --upgrade pip wheel
sudo -u scott -H .venv/bin/pip install -e .
```

Write the prod `.env` (do NOT commit). Set CORS to the Cloudflare frontend hostname:

```bash
sudo -u scott -H tee /home/scott/fair-lending-lab/platform/.env <<'EOF'
PGHOST=localhost
PGPORT=5432
PGDATABASE=fair_lending_lab
PGUSER=flab_app
PGPASSWORD=STRONG_PW_HERE

FLAB_API_HOST=127.0.0.1
FLAB_API_PORT=8702
FLAB_DATA_DIR=/home/scott/fair-lending-lab/platform/data
FLAB_RANDOM_SEED=20260625
FLAB_LOG_LEVEL=INFO
FLAB_HMDA_YEAR=2023
FLAB_HMDA_STATE=MA
FLAB_CORS_ORIGINS=https://fair-lending.scottcampbell.io
EOF
sudo chmod 600 /home/scott/fair-lending-lab/platform/.env
```

Apply the schema and load the data. Use the installed `flab` console
entry point (the venv puts it on `.venv/bin/flab`):

```bash
sudo -u scott -H .venv/bin/flab db init
# or apply the schema directly with psql:
sudo -u scott -H psql "postgresql://flab_app:STRONG_PW_HERE@localhost/fair_lending_lab" -f flab/db/schema.sql

sudo -u scott -H .venv/bin/flab ingest hmda --year 2023 --state MA
sudo -u scott -H .venv/bin/flab ingest build-curated
sudo -u scott -H .venv/bin/flab analyze run-all
sudo -u scott -H .venv/bin/flab export-results --out data/processed/results.json
```

## 4. systemd

```bash
sudo cp deploy/flab-api.service /etc/systemd/system/flab-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now flab-api.service
sudo systemctl status flab-api.service --no-pager
```

Logs:

```bash
sudo journalctl -u flab-api.service -f
```

Verify the API responds locally:

```bash
curl -s http://127.0.0.1:8702/health
```

## 5. nginx and TLS

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/fair-lending-api.scottcampbell.io.conf
sudo ln -s /etc/nginx/sites-available/fair-lending-api.scottcampbell.io.conf /etc/nginx/sites-enabled/
sudo nginx -t

# Point fair-lending-api.scottcampbell.io at the VPS in DNS first (A record),
# then obtain the cert:
sudo certbot --nginx -d fair-lending-api.scottcampbell.io
sudo systemctl reload nginx

curl -s https://fair-lending-api.scottcampbell.io/health
```

## 6. Refresh schedule

The HMDA file is annual. Re-running the pipeline once per release is enough. A systemd timer is overkill; a one-line cron is fine:

```bash
sudo -u scott crontab -e
# refresh the analysis on the first of every month at 02:30 local
30 2 1 * * cd /home/scott/fair-lending-lab/platform && .venv/bin/python -m flab.cli analyze run-all >> /home/scott/fair-lending-lab/platform/data/cron.log 2>&1
```

## 7. Cloudflare Pages frontend

The frontend builds to a static export from `frontend/`:

```bash
cd /home/scott/fair-lending-lab/frontend
npm ci
NEXT_PUBLIC_API_BASE=https://fair-lending-api.scottcampbell.io npm run build
```

Upload the `out/` directory to Cloudflare Pages. Cloudflare project settings:
- Build command: `npm run build`
- Build output directory: `out`
- Root directory: `frontend`
- Environment variable: `NEXT_PUBLIC_API_BASE = https://fair-lending-api.scottcampbell.io`

DNS:
- `fair-lending.scottcampbell.io` CNAME to the Cloudflare Pages project hostname (e.g. `fair-lending-lab.pages.dev`).
- `fair-lending-api.scottcampbell.io` A record to the VPS IPv4 address. AAAA if you also have IPv6.

## 8. Rollback

```bash
sudo systemctl stop flab-api.service
cd /home/scott/fair-lending-lab
git checkout <previous_sha>
cd platform
.venv/bin/pip install -e .
sudo systemctl start flab-api.service
```

## 9. Smoke checks

```bash
curl -s https://fair-lending-api.scottcampbell.io/health
curl -s https://fair-lending-api.scottcampbell.io/api/overview | head -c 400
curl -s https://fair-lending-api.scottcampbell.io/api/hypotheses | head -c 400
```

Open the Cloudflare frontend URL in a browser, verify the dashboard shows the "what matters now" callout with live numbers and that all four tabs render real data.
