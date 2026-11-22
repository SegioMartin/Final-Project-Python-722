# Do Major Events in Toronto Disrupt TTC Bus Service?

MMGMT 722 (Data Analytics using Python), Fall 2026, group project.

## 1. Problem and audience

Toronto hosts large events almost every week: Blue Jays games at Rogers Centre, Leafs and Raptors
games at Scotiabank Arena, Toronto FC at BMO Field, parades and festivals that close downtown streets,
and in 2026 six FIFA World Cup matches. TTC buses share the road with event traffic, road closures
and diversions.

**Audience:** TTC Service Planning and Operations, City of Toronto Transportation Services and
special-events staff, and event organizers.

**Why it matters:** if certain events, venues and hours reliably produce more bus disruptions,
TTC can plan for them in advance (extra buses, pre-planned diversions, rider alerts) instead of reacting.

**What the data can and cannot say.** The TTC dataset records *service incidents* (a delay or a gap
logged by staff with a cause code), not road speed or traffic volume. So we measure the effect of events
on **bus service disruptions**, not on "traffic" in general.

## 2. Research questions

1. On days and hours with major events, are bus delay incidents more frequent or longer than on
   comparable days without events?
2. Which event types (sports games, parades, festivals, World Cup matches) and which venues have the
   largest effect?
3. Is the effect concentrated on routes near the venue and in the hours around the event?
4. Which incident causes increase? Most relevant codes: `MFDV` (on diversion), `MFPR` (held by
   parades/marches), `MFUS` (unable to maintain schedule).

## 3. Data

Analysis period: **2025-01-01 to 2026-09-30** (full coverage of the TTC file).
All files are in `data/raw/` and were downloaded on **2026-11-21**. APIs and open-data feeds change
over time, so the project uses these saved snapshots, not live requests.

### TTC bus delays

| File | Content | Source |
|---|---|---|
| `TTC Bus Delay Data since 2025.csv` | 107,349 incidents, 2025-01-01 to 2026-09-30. Columns: Date, Line, Time, Day, Station, Code, Min Delay, Min Gap, Bound, Vehicle | [City of Toronto Open Data – TTC Bus Delay Data](https://open.toronto.ca/dataset/ttc-bus-delay-data/), portal version refreshed 2026-10-26 |
| `Code Descriptions.csv` | 46 incident codes and their meaning | same page |

"Min Delay" is the delay in minutes (not a minimum). We use only data since 2025 because older yearly
files have a different structure (Route, Location and a free-text Incident instead of Line, Station
and Code), and the 2025+ file already covers 21 months in one consistent format.
Licence: Open Government Licence – Toronto.

### Sports schedules (home game = event at the venue)

| File | Team, venue | Season | Source |
|---|---|---|---|
| `mlb_2025.json` | Blue Jays, Rogers Centre | 2025, incl. postseason and World Series | MLB Stats API: `https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=141&season=2025&gameType=R,F,D,L,W` |
| `mlb_2026.json` | Blue Jays, Rogers Centre | 2026 | same, `season=2026` |
| `nhl_2024_25.json` | Maple Leafs, Scotiabank Arena | 2024-25, incl. preseason and playoffs | NHL API: `https://api-web.nhle.com/v1/club-schedule-season/TOR/20242025` |
| `nhl_2025_26.json` | Maple Leafs, Scotiabank Arena | 2025-26 | same, `20252026` |
| `nba_2025.json` | Raptors, Scotiabank Arena | 2024-25 regular season | ESPN API: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/tor/schedule?season=2025` |
| `nba_2026.json` | Raptors, Scotiabank Arena | 2025-26 regular season | same, `season=2026` |
| `nba_2026_playoffs.json` | Raptors, Scotiabank Arena | 2026 playoffs | same, `season=2026&seasontype=3` |
| `tfc_2025.json` | Toronto FC, BMO Field | 2025 MLS season | ESPN API: `https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/teams/7318/schedule?season=2025` |
| `tfc_2026.json` | Toronto FC, BMO Field | 2026 MLS season | same, `season=2026` |

Notes:
- Each file contains home and away games (and preseason); home games are selected in `01_data_prep`.
- Game times in all three APIs are in **UTC** and must be converted to Toronto time
  (e.g. World Series Game 7 is stored as 2025-11-02 UTC but was played on the evening of 2025-11-01).
- The ESPN API is public but undocumented; the MLB and NHL APIs are public and need no key.
  All are used for non-commercial academic purposes only.

### Major city events

| File | Content | Source |
|---|---|---|
| `events_manual.csv` | 17 major events in the analysis period: Pride Parade, Caribbean Carnival Grand Parade, CNE, TIFF, Nuit Blanche, Waterfront Marathon, Santa Claus Parade, six FIFA World Cup 2026 matches at BMO Field | Compiled by hand. Every row has a `source_url`, and each date was checked against that page. Times are local Toronto time; empty when the source did not confirm a time. |

Blue Jays World Series home games are not in this file because they are already in `mlb_2025.json`.

### Weather

| File | Content | Source |
|---|---|---|
| `weather_2025.csv`, `weather_2026.csv` | Daily weather at Toronto Pearson (TORONTO INTL A, Climate ID 6158731, station ID 51459): temperature, rain, snowfall, precipitation, snow on ground | Environment and Climate Change Canada: `https://climate.weather.gc.ca/climate_data/bulk_data_e.html?format=csv&stationID=51459&Year=2025&Month=1&Day=14&timeframe=2&submit=Download+Data` (and `Year=2026`) |

Pearson is used instead of the Toronto City station because Toronto City does not report daily snowfall.
Licence: Open Government Licence – Canada.

Public holidays come from the Python package `holidays` (Ontario), so no file is needed.

## 4. Approach

1. **Event calendar.** One table of all events in the period: date, start time (Toronto time), venue,
   type (sports game, parade, festival, World Cup match).
2. **Event exposure.** Mark each TTC incident and each day as event or non-event, using the event date
   and a time window from 2 h before the start to 2 h after the end (end unknown → start + 3 h).
   The window is set in `01_data_prep` and varied in `04_verification`.
3. **Baseline.** Compare each event hour with hours of the same weekday type and hour of day outside any
   event window, not with all hours, because incidents depend strongly on weekday, hour and season.
4. **Weather control.** Weather is the main alternative explanation:
   - snow and heavy rain produce many incidents on their own (for example, the day with the most
     `MFDV` "on diversion" incidents, 2026-09-02, had 43 mm of rain, and the second, 2026-01-15,
     had 20 cm of snowfall);
   - events are seasonal (festivals and baseball in summer, hockey in winter), so event days and bad-weather
     days are not spread evenly over the year.

   Without a weather control we could attribute a weather effect to events, or hide a real event effect.
   We therefore join daily snowfall, precipitation, temperature and snow on ground to every day and
   (a) include them as controls in a regression together with weekday, month and holiday, and
   (b) check that the event effect holds when comparing only days with similar weather (e.g. dry days only).
5. **Location.** A route is "near a venue" if one of its stops is within 1 km of Rogers Centre, Scotiabank Arena
   or BMO Field. Stop coordinates come from the TTC GTFS feed (`scripts/clean_gtfs.py` cleans it into
   `data/processed/gtfs_*.csv`; `01_data_prep` adds the distances). The `Station` field is free text and is not used.
6. **Verification.** Placebo test (fake event dates should show no effect), alternative time windows,
   other model choices and dropping groups of hours (21 checks in `04_verification`).

## 5. Notebooks

Run them in order. Notebooks 02-04 read only files created by 01.

| Notebook | Purpose | Input → output |
|---|---|---|
| `notebooks/01_data_prep.ipynb` | Load and clean TTC data (types, date-time, duplicates, zero delays, outliers, cause codes, route numbers); build the event calendar (home games only, UTC → Toronto time, manual events); add weather and holidays; merge everything | `data/raw/*` → `data/processed/`: `incidents.csv` (1 row = incident), `events.csv` (event-day), `daily.csv` (day), `hourly.csv` (hour) |
| `notebooks/02_eda.ipynb` | How incidents behave in general, step by step: volume, delay size, hour of day, causes (and the April 2026 coding change), routes and places, weather and holidays, the event calendar, and what it means for the analysis. Each chart has a plain-language explanation | `data/processed/*` → charts |
| `notebooks/03_event_effect.ipynb` | Main question. Modelling table; matched comparison (event hours vs the usual for the same weekday and hour); Poisson regression with weekday, hour, month, weather, holiday and coding-period controls; near-venue test; diversions, long delays and delay minutes; cause groups; conclusions | `data/processed/*` → results, charts |
| `notebooks/04_verification.ipynb` | 21 robustness checks (event windows, model choices, dropped hours) and a fake-events test, with a verdict | `data/processed/*` → results |

**Before `01_data_prep`:** the raw TTC GTFS feed is **not in the repository** (326 MB, over GitHub's file limit).
Download the Toronto Open Data dataset "Merged GTFS - TTC Routes and Schedules" (feed version S1000544, valid 2026-11-01 to 2026-12-19)
and unzip it into `data/raw/Merged GTFS - TTC Routes and Schedules/`. Then run `uv run python scripts/clean_gtfs.py` once. It reduces the feed to the small `gtfs_*.csv` tables that `01_data_prep` reads.

## 5a. Main findings

- Major events did **not** raise bus incidents: baseball 1.03, hockey 0.96 and other events 0.95 (rate ratios, 1.0 = no difference), all within chance.
- **Basketball hours at Scotiabank Arena have about 9% fewer incidents** (0.91) and about 16% less delay time (0.84). This holds in all 21 checks and against fake events.
- A small rise for Toronto FC (1.09) is not reliable: it disappears when each weekday is matched separately.
- Routes near a venue show no sports effect. During parades, the World Cup and festivals there is a possible rise (1.22) that rests on 12 events and is only a lead.
- Weather and holidays move incidents much more than events do: heavy snow +81% on the day, a holiday -32%.

## 6. How to reproduce

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Clone the repository and go into its folder.
3. Run `uv sync`. It installs Python 3.13 if needed and creates `.venv` with the exact package
   versions from `uv.lock`.
4. Open the folder in VS Code (with the Python and Jupyter extensions), open a notebook,
   click **Select Kernel → Python Environments → .venv**.
   Without VS Code: `uv run --with jupyter jupyter lab`.
5. Run the notebooks in order: 01 → 02 → 03 → 04.

## 7. Team rules

- **One owner per notebook.** Only the owner edits it; others ask first. Notebooks are JSON files
  and are almost impossible to merge when two people change the same one.
- **`git pull` before you start, small commits, push often.**
- **Before every commit: Restart Kernel and Run All.** The notebook must run top to bottom without
  errors. Keep the outputs, so charts are visible on GitHub.
- **Never edit files in `data/raw/` by hand.** All cleaning is done in code. The only exception is
  `events_manual.csv`: a new row is allowed only with a working `source_url`.
- **`data/processed/` is not committed.** It is generated by `01_data_prep`; run it first.
- **Relative paths only**, e.g. `../data/raw/weather_2025.csv` (notebooks run from the `notebooks/` folder).
- **New packages only via `uv add <package>`**, then commit `pyproject.toml` and `uv.lock` together.
- **Readable code:** clear variable names, comments explaining the logic, no dead code
  (the course rubric checks this).
- **AI use:** write down substantive prompts and what you verified; the report needs an AI-use appendix.

## 8. Project structure

```
.
├── data/
│   ├── raw/            # original downloaded files (committed, never edited)
│   └── processed/      # files created by 01_data_prep (not committed)
├── notebooks/          # 01_data_prep, 02_eda, 03_event_effect, 04_verification
├── pyproject.toml      # project and package list
├── uv.lock             # exact package versions
├── .python-version     # Python 3.13
└── README.md
```
