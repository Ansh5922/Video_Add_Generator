"""
CrowdWisdom Video Ad Agent — Configuration & Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    # ── LLM ────────────────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"
    )

    # ── Data tools ─────────────────────────────────────────────────────────────
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    EXA_API_KEY: str = os.getenv("EXA_API_KEY", "")
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

    # ── Output ─────────────────────────────────────────────────────────────────
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    VIDEO_DURATION_SECONDS: int = int(os.getenv("VIDEO_DURATION_SECONDS", "45"))
    VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "24"))
    VIDEO_WIDTH: int = int(os.getenv("VIDEO_WIDTH", "1920"))
    VIDEO_HEIGHT: int = int(os.getenv("VIDEO_HEIGHT", "1080"))

    # ── Product context ─────────────────────────────────────────────────────────
    PRODUCT_NAME: str = "CrowdWisdom Trading"
    PRODUCT_URL: str = "crowdwisdomtrading.com"
    PRODUCT_NICHE: str = "trading signals, crowd intelligence, market analysis"
    TARGET_ICP: str = "retail traders, swing traders, investors aged 25-55"

    # ── Derived paths ──────────────────────────────────────────────────────────
    @property
    def ADS_OUTPUT_DIR(self) -> Path:
        return self.OUTPUT_DIR / "ads"

    @property
    def SCRIPTS_OUTPUT_DIR(self) -> Path:
        return self.OUTPUT_DIR / "scripts"

    @property
    def VIDEOS_OUTPUT_DIR(self) -> Path:
        return self.OUTPUT_DIR / "videos"

    @property
    def FRAMES_OUTPUT_DIR(self) -> Path:
        return self.OUTPUT_DIR / "frames"

    def ensure_dirs(self):
        """Create all output directories."""
        for d in [
            self.ADS_OUTPUT_DIR,
            self.SCRIPTS_OUTPUT_DIR,
            self.VIDEOS_OUTPUT_DIR,
            self.FRAMES_OUTPUT_DIR,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def validate(self):
        """Validate required keys are present."""
        errors = []
        if not self.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is required")
        if not self.APIFY_API_TOKEN:
            errors.append("APIFY_API_TOKEN is required")
        if not self.TAVILY_API_KEY:
            errors.append("TAVILY_API_KEY is required")
        if errors:
            raise ValueError(
                "Missing required configuration:\n" + "\n".join(f"  • {e}" for e in errors)
            )


settings = Settings()
