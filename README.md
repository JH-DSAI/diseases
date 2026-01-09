# Disease Dashboard

A FastAPI web application for visualizing and analyzing US disease surveillance data.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.0-009688.svg)](https://fastapi.tiangolo.com/)
[![UV](https://img.shields.io/badge/uv-Package%20Manager-blueviolet)](https://docs.astral.sh/uv/)
[![Just](https://img.shields.io/badge/just-Task%20Runner-orange)](https://github.com/casey/just)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933.svg)](https://nodejs.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1.3+-yellow.svg)](https://duckdb.org/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0.8-3366CC.svg)](https://htmx.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/JH-DSAI/diseases/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-77%25-yellow.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>app</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py">database.py</a></td><td>331</td><td>105</td><td>68%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L39-L40">39&ndash;40</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L46-L55">46&ndash;55</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L121">121</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L126">126</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L130-L131">130&ndash;131</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L140-L141">140&ndash;141</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L153-L154">153&ndash;154</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L320">320</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L399">399</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L464">464</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L622-L623">622&ndash;623</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L626-L627">626&ndash;627</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L699">699</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L804-L855">804&ndash;855</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L889-L971">889&ndash;971</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L993-L1013">993&ndash;1013</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/dependencies.py">dependencies.py</a></td><td>16</td><td>1</td><td>94%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/dependencies.py#L23">23</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py">main.py</a></td><td>68</td><td>28</td><td>59%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L25-L30">25&ndash;30</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L46">46</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L49">49</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L70-L103">70&ndash;103</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L119-L120">119&ndash;120</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L133">133</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/utils.py">utils.py</a></td><td>10</td><td>10</td><td>0%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/utils.py#L3-L41">3&ndash;41</a></td></tr><tr><td colspan="5"><b>app/etl</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py">base.py</a></td><td>65</td><td>12</td><td>82%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L69-L71">69&ndash;71</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L77-L82">77&ndash;82</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L149">149</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L162">162</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L181-L184">181&ndash;184</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/config.py">config.py</a></td><td>13</td><td>1</td><td>92%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/config.py#L14">14</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/schema.py">schema.py</a></td><td>20</td><td>1</td><td>95%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/schema.py#L12">12</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/storage.py">storage.py</a></td><td>33</td><td>18</td><td>45%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/storage.py#L27-L32">27&ndash;32</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/storage.py#L59-L79">59&ndash;79</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/storage.py#L85">85</a></td></tr><tr><td colspan="5"><b>app/etl/normalizers</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/normalizers/fips.py">fips.py</a></td><td>6</td><td>6</td><td>0%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/normalizers/fips.py#L9-L94">9&ndash;94</a></td></tr><tr><td colspan="5"><b>app/etl/transformers</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py">nndss.py</a></td><td>160</td><td>11</td><td>93%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L141">141</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L196-L197">196&ndash;197</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L203-L204">203&ndash;204</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L263">263</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L268">268</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L296-L298">296&ndash;298</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L361">361</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py">tracker.py</a></td><td>116</td><td>14</td><td>88%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L69-L70">69&ndash;70</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L83-L84">83&ndash;84</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L98-L99">98&ndash;99</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L102-L103">102&ndash;103</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L153">153</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L155">155</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L203-L204">203&ndash;204</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L224">224</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L237">237</a></td></tr><tr><td colspan="5"><b>app/middleware</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/middleware/auth.py">auth.py</a></td><td>53</td><td>1</td><td>98%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/middleware/auth.py#L105">105</a></td></tr><tr><td colspan="5"><b>app/routers</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py">api.py</a></td><td>90</td><td>28</td><td>69%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L64-L66">64&ndash;66</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L83-L85">83&ndash;85</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L117-L119">117&ndash;119</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L161-L163">161&ndash;163</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L192-L194">192&ndash;194</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L243-L245">243&ndash;245</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L267-L294">267&ndash;294</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/html_api.py">html_api.py</a></td><td>56</td><td>14</td><td>75%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/html_api.py#L127-L130">127&ndash;130</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/html_api.py#L148-L159">148&ndash;159</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/html_api.py#L177-L181">177&ndash;181</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/html_api.py#L209-L214">209&ndash;214</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/pages.py">pages.py</a></td><td>29</td><td>9</td><td>69%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/pages.py#L106-L126">106&ndash;126</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/sql_api.py">sql_api.py</a></td><td>58</td><td>31</td><td>47%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/sql_api.py#L60-L76">60&ndash;76</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/sql_api.py#L82-L84">82&ndash;84</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/sql_api.py#L107-L122">107&ndash;122</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/sql_api.py#L145-L158">145&ndash;158</a></td></tr><tr><td><b>TOTAL</b></td><td><b>1270</b></td><td><b>290</b></td><td><b>77%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->

## Tech Stack

- **Backend**: FastAPI 0.121.0, Python 3.11+
- **Database**: DuckDB 
- **Frontend**:
  - HTMX 2.0.8 
  - Alpine.js 3.15.0 
  - Tailwind CSS + DaisyUI 5.0.0 
  - D3.js v7 

## Project Structure

```
disease-dashboard/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # DuckDB connection & data loading
│   ├── dependencies.py      # FastAPI dependencies
│   ├── models.py            # Pydantic models
│   ├── etl/                 # ETL pipeline
│   │   ├── base.py          # Base ETL classes
│   │   ├── transformers/    # Data transformers (NNDSS, tracker)
│   │   └── normalizers/     # Data normalization (geo, disease names)
│   ├── routers/
│   │   ├── api.py           # JSON API endpoints
│   │   ├── html_api.py      # HTML fragment endpoints
│   │   └── pages.py         # HTML page routes
│   ├── static/
│   │   ├── css/             # CSS source files
│   │   ├── dist/            # Built assets (auto-generated)
│   │   └── js/              # JavaScript source & components
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # Test suite (api/, etl/, html/)
├── us_disease_tracker_data/ # Disease tracker data (CSV)
├── nndss_data/              # NNDSS surveillance data
├── docs/                    # Documentation
├── justfile                 # Development task runner
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package installer
- [just](https://github.com/casey/just) command runner
- Node.js 18+ and npm

#### Data prerequisites
- [tracker data](https://github.com/JH-DSAI/us_disease_tracker_data) JHU data, updated periodically.
- [NNDSS data](https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/x9gk-5huc/about_data) CDC data, updated weekly. Click "export" to download as a CSV.

### About the data prerequisites

The app supports two modes for data loading:

#### Local Development (default)
Data is loaded from local directories. No Azure configuration needed.

- The tracker data is in a private repo, ask JHU team for access, it should be cloned into the root dir of this repo.
  - `git clone git@github.com:JH-DSAI/us_disease_tracker_data.git` should be fine.
  - e.g: `./us_disease_tracker_data/data/states/ID/20251121-123820_ID_Michael-Schnaubelt.csv`

- The NNDSS data should be exported as a CSV and put in a dir called `/nndss_data` also in the root dir of this repo.
See the project structure above.
  - e.g. `./nndss_data/NNDSS_Weekly_Data_20251121.csv`

#### Remote Deployment (Azure Blob Storage)
For deployed environments, data can be loaded from Azure Blob Storage. Set these in your `.env`:

```bash
AZURE_STORAGE_ACCOUNT="your-storage-account"
AZURE_STORAGE_KEY="your-storage-key"
DATA_URI="az://your-container/us_disease_tracker_data"
NNDSS_DATA_URI="az://your-container/nndss_data"
```

When `DATA_URI` or `NNDSS_DATA_URI` are set, the app uses Azure Blob Storage instead of local files. This uses [fsspec](https://filesystem-spec.readthedocs.io/) + [adlfs](https://github.com/fsspec/adlfs) for service-agnostic cloud storage access.


### Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

### Running the Application

Install Node.js dependencies first: `npm install`

```bash
just dev
```

This builds frontend assets and starts the development server.

The application will be available at:
- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Authentication

The application uses API key authentication. To access protected endpoints:

1. **Web Browser**: The application will check for API keys in the Authorization header
2. **API Requests**: Include the API key in the Authorization header:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/diseases
   ```

**Development Mode**: If no API keys are configured in `.env`, the application allows all access.

## API Endpoints

### Public Endpoints

- `GET /health` - Basic health check (unauthenticated)

### Protected Endpoints (require API key)

- `GET /` - Landing page with disease overview
- `GET /disease/{disease_name}` - Disease-specific detail page
- `GET /api/health` - Detailed health check with database status
- `GET /api/diseases` - List all tracked diseases
- `GET /api/stats` - Summary statistics across all data

## Data

The application loads disease surveillance data from CSV files in the `us_disease_tracker_data/data/states/` directory. Currently tracking:

- **Measles**: Viral respiratory infection
- **Pertussis**: Whooping cough
- **Meningococcus**: Bacterial meningitis

Data includes:
- Temporal trends (weekly/monthly)
- Geographic distribution (state, regional, county levels)
- Age group stratification
- Case confirmation status
- Disease subtypes (e.g., meningococcus serotypes)

## Development

The project uses [just](https://github.com/casey/just) for development tasks. Run `just --list` to see available commands.

Frontend assets are built with Vite (Tailwind CSS, HTMX, Alpine.js, D3.js). Source files are in `app/static/css/` and `app/static/js/`.

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
