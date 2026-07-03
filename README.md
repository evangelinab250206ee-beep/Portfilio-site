# Vikas Portfolio — React App

A professional 3-page portfolio built with React + Vite.

## Pages
1. **Portfolio** (`/`) — Professional achievements, projects, skills, awards
2. **PM Vikas Tracker** (`/pm-vikas`) — Track PM scheme projects with milestones & dashboard
3. **Insights** (`/insights`) — PM knowledge quiz, scheme directory, tools stack

## Local Development

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Cross-Device Tracker Sync

The tracker can save to browser storage by itself, but browser storage is device-only. To see changes from another phone/laptop, connect the app to Supabase.

1. Create a free Supabase project.
2. Open Supabase SQL Editor and run:

```sql
create table if not exists public.tracker_records (
  id text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.tracker_records enable row level security;

create policy "Public tracker read"
on public.tracker_records
for select
to anon
using (true);

create policy "Public tracker write"
on public.tracker_records
for insert
to anon
with check (true);

create policy "Public tracker update"
on public.tracker_records
for update
to anon
using (true)
with check (true);
```

3. Add these environment variables locally in `.env` and in Vercel Project Settings:

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_SUPABASE_TABLE=tracker_records
```

4. Redeploy. After that, edits made on one device are saved online and loaded when another device opens or focuses the tracker.

## Deploy to Vercel (Free)

### Option 1 — Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# From the portfolio folder
vercel

# Follow the prompts:
# - Link to existing project? No
# - Project name: vikas-portfolio
# - Framework: Vite
# - Build command: npm run build
# - Output directory: dist
```

Your site will be live at `https://vikas-portfolio.vercel.app`

### Option 2 — GitHub + Vercel Dashboard

1. Push this folder to a GitHub repo:
   ```bash
   git init
   git add .
   git commit -m "Initial portfolio"
   git remote add origin https://github.com/YOUR_USERNAME/vikas-portfolio.git
   git push -u origin main
   ```

2. Go to https://vercel.com → **New Project**
3. Import your GitHub repo
4. Framework: **Vite**
5. Build command: `npm run build`
6. Output: `dist`
7. Click **Deploy** → Done!

### Option 3 — Vercel Web Upload

1. Run `npm run build` locally
2. Go to https://vercel.com → **New Project** → **Upload**
3. Drag and drop the `dist/` folder

## Customize

- **Personal info**: Edit `src/pages/Portfolio.jsx` — update name, bio, projects, awards
- **PM Projects**: Edit `src/pages/PMVikas.jsx` — update the `initialProjects` array
- **Colors**: Edit `src/index.css` — change CSS variables in `:root`
