# CrowdWisdom Video Ad Agent — Hermes Multi-Agent System

> **Internship Assessment** · CrowdWisdom Trading · Marketing Lead (AI Agents)

A cinematic video ad generation system powered by **3 AI agents** orchestrated in a **Hermes Kanban** pipeline. The system automatically researches winning ads, extracts marketing insights, creates compelling scripts, and renders a professional 30–60 second video ad for [crowdwisdomtrading.com](https://crowdwisdomtrading.com).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HERMES KANBAN ORCHESTRATOR                        │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  ADS MANAGER     │  │  SCRIPT AGENT    │  │  VIDEO AGENT     │   │
│  │  AGENT           │→ │                  │→ │                  │   │
│  │                  │  │                  │  │                  │   │
│  │ • Apify scraper  │  │ • Pain analysis  │  │ • Frame gen      │   │
│  │ • Meta Ads Lib   │  │ • Tavily search  │  │ • FFmpeg compose │   │
│  │ • Best ads JSON  │  │ • 3-type scripts │  │ • Color grading  │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Agents

### 1. 📊 Ads Manager Agent
- Scrapes Meta Ads Library via **Apify** (`apify/facebook-ads-scraper`)
- Searches for top-performing trading/finance ads (last 30 days)
- Scores ads by relevance, longevity, and engagement signals
- Extracts ICP pain points and marketing concepts
- **Output:** `output/ads/winning_ads.json`, `output/ads/marketing_insights.json`

### 2. ✍️ Script Agent
- Uses **Tavily** to research identified pains and ICP in real-time
- Leverages CrowdWisdom unique data (crowd signals, accuracy stats)
- Creates **3 cinematic scripts**:
  - `Type A` — Pain-first hook ("Are you tired of...")
  - `Type B` — Data-proof hook ("83% of retail traders lose because...")
  - `Type C` — Transformation hook ("What if the crowd already knew the answer?")
- Each script includes: visual hook, voiceover, scene descriptions, CTA
- **Output:** `output/scripts/ad_scripts.json`

### 3. 🎬 Video Agent
- Generates cinematic frames with PIL (dark, moody, financial aesthetic)
- Renders real trading charts with matplotlib
- Applies **Ken Burns** zoom effects, fade transitions
- Mixes voiceover narration (gTTS) with dramatic background music
- Applies Hollywood-style **teal-orange color grading** via FFmpeg
- **Output:** `output/videos/crowdwisdom_ad_v1.mp4`, `_v2.mp4`, `_v3.mp4`

---

## Setup

### Prerequisites
- Python 3.10+
- FFmpeg ([download](https://ffmpeg.org/download.html) → add to PATH)
- Node.js 18+ (optional, for Remotion renderer)

### Install
```bash
git clone https://github.com/YOUR_USERNAME/crowdwisdom-video-agent
cd crowdwisdom-video-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your keys
```

### Run
```bash
# Full pipeline (all 3 agents + Kanban UI)
python main.py

# Run individual agents
python main.py --agent ads       # Only Ads Manager Agent
python main.py --agent script    # Only Script Agent (needs ads output)
python main.py --agent video     # Only Video Agent (needs script output)

# Use saved data (skip scraping)
python main.py --use-cache

# Verbose mode
python main.py --verbose
```

---

## API Keys Required

| Service | Purpose | Free? |
|---------|---------|-------|
| [OpenRouter](https://openrouter.ai) | LLM backbone (Claude 3.5 Sonnet) | ✅ Free tier |
| [Apify](https://apify.com) | Meta Ads Library scraping | ✅ Free $5 credits |
| [Tavily](https://tavily.com) | Real-time search | ✅ Free 1k/month |
| [Exa](https://exa.ai) | Neural search (optional) | ✅ Free tier |

---

## Output

```
output/
├── ads/
│   ├── winning_ads.json          # Raw scraped ads
│   └── marketing_insights.json  # Extracted concepts & pain points
├── scripts/
│   └── ad_scripts.json          # 3 video ad scripts (storyboard format)
└── videos/
    ├── crowdwisdom_ad_v1.mp4    # Pain-first hook video
    ├── crowdwisdom_ad_v2.mp4    # Data-proof hook video
    └── crowdwisdom_ad_v3.mp4    # Transformation hook video
```

---

## Evaluation Criteria

- ✅ **3 Working Agents** — AdsManager, Script, Video
- ✅ **Hermes Kanban** — Rich terminal Kanban board showing pipeline
- ✅ **Apify** — Meta Ads Library scraper integrated
- ✅ **Tavily** — Real-time ICP research
- ✅ **Cinematic Output** — "Wow" factor via color grading, charts, animation
- ✅ **GitHub Ready** — Clean repo, .env.example, full README
- ✅ **JSON Outputs** — Human-readable ads and scripts saved to disk

---

## Submission

Repository by: [YOUR NAME]  
Contact: gilad@crowdwisdomtrading.com

**API Tokens for re-running (provided separately by email)**
