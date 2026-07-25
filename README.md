# Tsuyu-mi
[日本語](README_ja.md)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF.svg?logo=githubactions&logoColor=white)](https://github.com/unsolublesugar/tsuyu-mi/actions)<br>
![Raindrop.io](https://img.shields.io/badge/Raindrop.io-0B7ED0?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIi8+PC9zdmc+)
![Jinja2](https://img.shields.io/badge/Jinja2-B41717?logo=jinja&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)

![Tsuyu-mi](assets/images/screenshot.png)

Periodically fetches articles from a Raindrop.io collection, extracts their content, summarizes them with AI, and outputs a priority-ranked HTML dashboard.

> The name **Tsuyu-mi** comes from: Raindrop &rarr; *shizuku* (雫, droplet) &rarr; *tsuyu* (露, dew) &rarr; *tsuyu-mi* (露見, "seeing the dew").

## Purpose

Triage your "read later" articles saved in Raindrop — before reading the full text.

- **Read now** — timely or high-value
- **Defer** — interesting but not urgent
- **Drop** — safe to discard

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/unsolublesugar/tsuyu-mi.git
cd tsuyu-mi
```

### 2. Prepare the Python environment

> [!NOTE]
> Python 3.11 or later is required. [uv](https://docs.astral.sh/uv/) can install Python itself alongside dependencies.

```bash
# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"

# Using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Obtain API keys

This tool requires a **Raindrop.io API token** and an **LLM API key**.

#### Raindrop.io test token

1. Go to [Raindrop.io Integrations](https://app.raindrop.io/settings/integrations)
2. Click **Create new app** under "For Developers"
3. Enter an app name (e.g. `RaindropSummarizer`) and create it
4. Click the app → **Create test token**
5. Copy the displayed token

#### Collection ID

1. Open [Raindrop.io](https://app.raindrop.io)
2. Navigate to the target collection (e.g. "Unsorted")
3. Check the URL: `https://app.raindrop.io/my/{collection_id}` — the numeric part is the collection ID

#### LLM API key

Obtain an API key from one of the following providers:

**Google Gemini (recommended — has a free tier)**

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. **Create API Key** → **Create API key in new project**
3. Recommended model: `gemini-3.5-flash-lite`

> [!TIP]
> You may need to link a Google Cloud billing account and [enable the Gemini API](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com).

**OpenAI**

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. **Create new secret key**
3. Recommended model: `gpt-5.6-luna`

**Anthropic**

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. **Create Key**
3. Recommended model: `claude-haiku-4-5`

#### Recommended models (as of July 2026)

This tool does a 3-line summary plus 4-axis scoring, a few to a dozen articles per run. Expensive reasoning models are unnecessary, so the low-cost tier of each provider is recommended.

| Provider | `LLM_MODEL` | Reference price (input / output, per 1M tokens) | Notes |
|---|---|---|---|
| `gemini` | `gemini-3.5-flash-lite` | $0.30 / $2.50 | **Recommended.** Has a free tier |
| `openai` | `gpt-5.6-luna` | $1.00 / $6.00 | Cheapest tier of the GPT-5.6 family |
| `anthropic` | `claude-haiku-4-5` | $1.00 / $5.00 | Cheapest Claude tier |

For better triage quality, swap in a higher tier (`gemini-3.6-flash` / `gpt-5.6-terra` / `claude-sonnet-5`). Only `LLM_MODEL` changes — no code changes needed.

> [!NOTE]
> To cut costs further, Gemini also offers `gemini-2.5-flash-lite` ($0.10 / $0.40). Triage that requires reading full text and judging relatively tends to get coarse there, so validate with the recommended model first.

### 4. Configure environment variables

#### Local execution

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
RAINDROP_TOKEN=your-raindrop-token
RAINDROP_COLLECTION_ID=your-collection-id
LLM_PROVIDER=gemini
LLM_API_KEY=your-llm-api-key
LLM_MODEL=gemini-3.5-flash-lite
```

> [!WARNING]
> Never commit `.env` to the repository — it contains secrets.

#### GitHub Actions

Add the following to your repository: Settings → Secrets and variables → Actions → Repository secrets.

| Secret name | Value |
|---|---|
| `RAINDROP_TOKEN` | Raindrop.io API test token |
| `RAINDROP_COLLECTION_ID` | Target collection ID |
| `LLM_PROVIDER` | `gemini` / `openai` / `anthropic` |
| `LLM_API_KEY` | LLM API key |
| `LLM_MODEL` | Model name (e.g. `gemini-3.5-flash-lite`) |

### 5. Verify

```bash
# Test Raindrop API connectivity only (no LLM required)
python -m src fetch-only

# Summarize a small batch
MAX_SUMMARIZE_PER_RUN=3 python -m src run

# Full run
python -m src run
```

## Usage

```bash
# Full pipeline (fetch → extract → summarize → generate HTML)
python -m src run

# Dry run — preview target articles without processing
python -m src run --dry-run

# Verbose logging
python -m src run --verbose

# Fetch from Raindrop only
python -m src fetch-only

# Regenerate HTML
python -m src build-html

# Reprocess a specific article
python -m src reprocess --id 123456789

# Retry all failed articles
python -m src reprocess-failed
```

## Output

An article dashboard is generated at `docs/index.html`. Open it in a browser to review.

- Color-coded by priority (HIGH = red / MEDIUM = yellow / LOW = gray)
- Filter buttons to narrow by priority
- Each article shows a 3-line summary, read-now reason, defer reason, and keywords
- A score (`8/12`) sits next to the priority badge; hover it for the per-axis breakdown

## How priority is decided

Asking the LLM to pick `high` / `medium` / `low` directly skews everything toward **high** — every article here was bookmarked, so all of them are at least somewhat interesting. Instead the LLM only scores four axes from 0 to 3, and the conversion to a priority happens deterministically in code ([`src/priority.py`](src/priority.py)).

| Axis | What it measures |
|---|---|
| `novelty` | Is this a rehash of known material, or first-hand / original information? |
| `relevance` | How close is the topic to day-to-day engineering work and writing? |
| `depth` | Does the 3-line summary suffice, or is the full text needed? |
| `actionability` | Are there concrete steps, settings, or numbers you can use as-is? |

The 0–12 total maps to a priority with these thresholds:

| Priority | Condition |
|---|---|
| `high` | Total ≥ 10 **and** `depth` ≥ 2 |
| `medium` | Total 5–9 |
| `low` | Total ≤ 4 |
| Drop candidate | Total ≤ 2 |

The `depth` condition means an article can be novel and highly relevant yet still land in `medium` if the summary already covers it.

To make triage stricter or looser, tune the threshold constants in [`src/priority.py`](src/priority.py) (`HIGH_TOTAL_MIN` / `MEDIUM_TOTAL_MIN` / `HIGH_DEPTH_MIN` / `DROP_TOTAL_MAX`) rather than editing the prompt.

> [!NOTE]
> Older data without `scores`, or a response where the LLM failed to emit them, falls back to the `priority` the LLM returned.

## Configuration

| Environment variable | Description | Default |
|---|---|---|
| `RAINDROP_TOKEN` | Raindrop.io API test token | (required) |
| `RAINDROP_COLLECTION_ID` | Target collection ID | (required) |
| `LLM_PROVIDER` | `gemini` / `openai` / `anthropic` | `gemini` |
| `LLM_API_KEY` | LLM API key | (required) |
| `LLM_MODEL` | Model name | (required) |
| `MAX_SUMMARIZE_PER_RUN` | Max articles to summarize per run | `10` |
| `REQUEST_TIMEOUT_SECONDS` | HTTP request timeout (seconds) | `20` |
| `USER_AGENT` | HTTP User-Agent header | `Tsuyu-mi/0.1` |
| `OUTPUT_DIR` | HTML output directory | `docs` |
| `SITE_URL` | Public site URL used for absolute OGP URLs | `https://unsolublesugar.github.io/tsuyu-mi/` |
| `DATA_DIR` | Data storage directory | `data` |
| `STATE_DIR` | State management directory | `state` |
| `LOG_LEVEL` | Log level | `INFO` |

## Automated operation with GitHub Actions

### 1. Set up GitHub Secrets

See "4. Configure environment variables → GitHub Actions" above.

### 2. Enable GitHub Pages

Settings → Pages → Source: **GitHub Actions**

> [!IMPORTANT]
> Private repositories require **GitHub Pro** or higher to use GitHub Pages.

### 3. Execution schedule

- **Automatic**: Every 3 days at JST 7:00 (UTC 22:00)
- **Manual**: Run on demand from the Actions tab via "Run workflow"

Changes are auto-committed and pushed only when new content is generated.

## Testing

```bash
pytest
ruff check src/ tests/
```

### Contributing

Contributions are welcome! A few things that help keep the project healthy:

- Please make sure `pytest` passes before opening a pull request. PRs are merged once the test suite is green.
- When you change or fix behavior, please add or update tests to cover it.
- Running `ruff check src/ tests/` is appreciated — try not to add new lint warnings in the files you touch.

The suite includes some regression tests that guard against previously-fixed bugs — for example, [`tests/unit/test_main_fallback.py`](tests/unit/test_main_fallback.py) covers the fallback summarization path (X/Twitter posts, articles where extraction failed). Please fix the underlying code rather than removing these if they fail.

## License

[MIT](LICENSE)
