"""
Video Tool — Cinematic video generation using PIL + matplotlib + FFmpeg.

Pipeline:
  1. Generate visual frames (PIL: cinematic dark scenes, charts)
  2. Animate with Ken Burns zoom/pan (FFmpeg)
  3. Add text overlays and lower-thirds
  4. Mix narration audio (gTTS) with background music
  5. Apply Hollywood teal-orange color grading
  6. Render final MP4
"""
import os
import json
import math
import shutil
import subprocess
import textwrap
import urllib.request
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from rich.console import Console

from config.settings import settings

console = Console()

# Cinematic color palette
COLORS = {
    "bg_dark": (8, 10, 20),
    "bg_navy": (12, 20, 45),
    "accent_gold": (255, 195, 0),
    "accent_teal": (0, 210, 190),
    "accent_red": (220, 50, 50),
    "text_white": (255, 255, 255),
    "text_dim": (180, 190, 200),
    "chart_green": (0, 220, 120),
    "chart_red": (220, 60, 60),
    "overlay_dark": (5, 8, 18, 200),
}

W, H = settings.VIDEO_WIDTH, settings.VIDEO_HEIGHT
FPS = settings.VIDEO_FPS


# ─── Frame Generators ──────────────────────────────────────────────────────────


def _make_gradient_bg(
    width: int = W,
    height: int = H,
    top: tuple = (8, 10, 20),
    bottom: tuple = (20, 35, 70),
) -> Image.Image:
    """Create a vertical gradient background."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def _draw_particle_field(img: Image.Image, seed: int = 42) -> Image.Image:
    """Add subtle star/particle field for depth."""
    np.random.seed(seed)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    for _ in range(200):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        size = np.random.choice([1, 1, 1, 2])
        alpha = np.random.randint(30, 120)
        draw.ellipse([(x, y), (x + size, y + size)], fill=(alpha, alpha, alpha + 20))
    return img


def _draw_grid_lines(img: Image.Image) -> Image.Image:
    """Draw subtle grid lines for financial aesthetic."""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    line_color = (30, 45, 80)
    for x in range(0, width, width // 12):
        draw.line([(x, 0), (x, height)], fill=line_color, width=1)
    for y in range(0, height, height // 8):
        draw.line([(0, y), (width, y)], fill=line_color, width=1)
    return img


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Get font, falling back to default if custom font unavailable."""
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for f in font_candidates:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    color: tuple,
    width: int = W,
    shadow: bool = True,
    max_width: int = 1600,
) -> int:
    """Draw centered text with optional shadow. Returns new y position."""
    lines = []
    # Word-wrap
    words = text.split()
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    line_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (width - tw) // 2
        if shadow:
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font, fill=color)
        y += th + 10
        line_height = th

    return y


def generate_hook_frame(hook_text: str, frame_path: Path) -> Path:
    """Frame 1: Dramatic visual hook — dark, cinematic, full-screen text."""
    img = _make_gradient_bg(top=(5, 5, 15), bottom=(15, 25, 55))
    img = _draw_particle_field(img, seed=7)
    img = _draw_grid_lines(img)

    # Red accent stripe at top
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 6)], fill=COLORS["accent_red"])
    draw.rectangle([(0, H - 6), (W, H)], fill=COLORS["accent_gold"])

    # "STOP SCROLLING" micro-text
    small_font = _get_font(36)
    micro_text = "◈  ATTENTION TRADERS  ◈"
    bbox = draw.textbbox((0, 0), micro_text, font=small_font)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, 120), micro_text, font=small_font, fill=COLORS["accent_teal"])

    # Main hook text — huge
    hook_font = _get_font(96, bold=True)
    y = H // 3
    y = _draw_centered_text(draw, hook_text.upper(), y, hook_font, COLORS["text_white"])

    # Subtle glow effect (blur overlay)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.ellipse([(W // 2 - 400, H // 3 - 100), (W // 2 + 400, H // 3 + 300)],
                    fill=(0, 150, 255, 25))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    img.save(str(frame_path), quality=95)
    return frame_path


def generate_chart_frame(title: str, frame_path: Path, script_type: str = "A") -> Path:
    """Frame 2: Animated trading chart showing crowd consensus power."""
    # Generate synthetic price data showing crowd wisdom effect
    np.random.seed({"A": 1, "B": 2, "C": 3}.get(script_type, 1))
    days = 60
    t = np.arange(days)

    # Solo trader (noisy, losing)
    solo_returns = np.cumsum(np.random.normal(-0.3, 2.5, days))

    # Crowd wisdom trader (smoother, winning)
    trend = np.linspace(0, 45, days)
    crowd_returns = trend + np.random.normal(0, 1.2, days)

    # Create dark-themed matplotlib figure
    fig, ax = plt.subplots(1, 1, figsize=(W / 100, H / 100), facecolor="#080A14")
    ax.set_facecolor("#0C1428")

    # Grid
    ax.grid(True, color="#1E2D50", linewidth=0.8, alpha=0.6)
    ax.spines["bottom"].set_color("#1E2D50")
    ax.spines["top"].set_color("#1E2D50")
    ax.spines["left"].set_color("#1E2D50")
    ax.spines["right"].set_color("#1E2D50")
    ax.tick_params(colors="#B4BEC8", labelsize=14)

    # Plot lines
    ax.plot(t, solo_returns, color="#DC3232", linewidth=2.5, alpha=0.8,
            label="Solo Trader  –38%", linestyle="--")
    ax.fill_between(t, solo_returns, alpha=0.08, color="#DC3232")

    ax.plot(t, crowd_returns, color="#00DC78", linewidth=3.5, alpha=0.95,
            label="Crowd Wisdom  +45%")
    ax.fill_between(t, crowd_returns, alpha=0.12, color="#00DC78")

    # Annotations
    ax.annotate("+45%", xy=(days - 1, crowd_returns[-1]),
                xytext=(days - 15, crowd_returns[-1] + 5),
                fontsize=28, fontweight="bold", color="#00DC78",
                arrowprops=dict(arrowstyle="->", color="#00DC78", lw=2))

    ax.annotate("–38%", xy=(days - 1, solo_returns[-1]),
                xytext=(days - 15, solo_returns[-1] - 10),
                fontsize=28, fontweight="bold", color="#DC3232",
                arrowprops=dict(arrowstyle="->", color="#DC3232", lw=2))

    # Title
    ax.set_title(title, color="#FFC300", fontsize=32, fontweight="bold", pad=20)
    ax.set_xlabel("Days", color="#B4BEC8", fontsize=16)
    ax.set_ylabel("Portfolio Return (%)", color="#B4BEC8", fontsize=16)

    # Legend
    legend = ax.legend(fontsize=20, facecolor="#0C1428", edgecolor="#1E2D50",
                       labelcolor="white", loc="upper left")

    # Crowd size annotation
    ax.text(5, crowd_returns[-1] - 8,
            "Based on 10,000+ pro traders", color="#00D2BE",
            fontsize=16, fontstyle="italic")

    plt.tight_layout()
    fig.savefig(str(frame_path), dpi=100, facecolor="#080A14",
                bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    return frame_path


def generate_stats_frame(stats: dict, frame_path: Path) -> Path:
    """Frame 3: CrowdWisdom unique data stats — bold numbers, dark background."""
    img = _make_gradient_bg(top=(5, 8, 20), bottom=(10, 20, 50))
    img = _draw_particle_field(img, seed=13)
    draw = ImageDraw.Draw(img)

    # Top accent
    draw.rectangle([(0, 0), (W, 8)], fill=COLORS["accent_teal"])

    # Title
    title_font = _get_font(54, bold=True)
    _draw_centered_text(draw, "THE NUMBERS DON'T LIE", 80, title_font, COLORS["accent_gold"])

    # Stats grid (2x2)
    stat_items = [
        ("10,000+", "Pro Traders Monitored"),
        ("73%", "Average Win Rate"),
        ("$0", "Hidden Fees"),
        ("15 min/week", "Time Required"),
    ]
    stat_num_font = _get_font(110, bold=True)
    stat_label_font = _get_font(36)

    positions = [
        (W // 4, H // 2 - 80),
        (3 * W // 4, H // 2 - 80),
        (W // 4, H // 2 + 200),
        (3 * W // 4, H // 2 + 200),
    ]

    # Override with actual stats if provided
    if stats:
        stat_items = list(stats.items())[:4]
        stat_items = [(str(v), str(k)) for k, v in stat_items]

    stat_colors = [COLORS["accent_teal"], COLORS["accent_gold"],
                   COLORS["chart_green"], COLORS["accent_teal"]]

    for i, ((num, label), (cx, cy)) in enumerate(zip(stat_items, positions)):
        color = stat_colors[i % len(stat_colors)]
        # Number
        bbox = draw.textbbox((0, 0), num, font=stat_num_font)
        nw = bbox[2] - bbox[0]
        draw.text((cx - nw // 2 + 3, cy + 3), num, font=stat_num_font, fill=(0, 0, 0, 160))
        draw.text((cx - nw // 2, cy), num, font=stat_num_font, fill=color)
        # Label
        bbox2 = draw.textbbox((0, 0), label, font=stat_label_font)
        lw = bbox2[2] - bbox2[0]
        draw.text((cx - lw // 2, cy + (bbox[3] - bbox[1]) + 10), label,
                  font=stat_label_font, fill=COLORS["text_dim"])

    # Divider lines
    draw.line([(W // 2 - 2, H // 4), (W // 2 - 2, 3 * H // 4)],
              fill=(40, 60, 100), width=2)
    draw.line([(W // 6, H // 2), (5 * W // 6, H // 2)],
              fill=(40, 60, 100), width=2)

    img.save(str(frame_path), quality=95)
    return frame_path


def generate_cta_frame(cta_text: str, url: str, frame_path: Path) -> Path:
    """Frame 4: Call-to-action — bold, urgent, premium."""
    img = _make_gradient_bg(top=(5, 5, 15), bottom=(12, 22, 60))
    img = _draw_particle_field(img, seed=21)
    draw = ImageDraw.Draw(img)

    # Gold accent bars
    draw.rectangle([(0, 0), (W, 10)], fill=COLORS["accent_gold"])
    draw.rectangle([(0, H - 10), (W, H)], fill=COLORS["accent_gold"])

    # Urgency text
    small_font = _get_font(40)
    _draw_centered_text(draw, "JOIN 50,000+ TRADERS WHO STOPPED GUESSING", 180,
                        small_font, COLORS["accent_teal"])

    # Main CTA
    cta_font = _get_font(88, bold=True)
    y = _draw_centered_text(draw, cta_text, H // 3, cta_font, COLORS["text_white"])

    # URL box
    url_font = _get_font(56, bold=True)
    bbox = draw.textbbox((0, 0), url, font=url_font)
    uw = bbox[2] - bbox[0]
    uh = bbox[3] - bbox[1]
    box_x = (W - uw) // 2 - 40
    box_y = y + 60
    # Draw button background
    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + uw + 80, box_y + uh + 40)],
        radius=16,
        fill=COLORS["accent_gold"],
    )
    draw.text((box_x + 40, box_y + 20), url, font=url_font, fill=COLORS["bg_dark"])

    # Social proof
    proof_font = _get_font(32)
    proof = "★★★★★  Trusted by traders in 40+ countries  ★★★★★"
    _draw_centered_text(draw, proof, H - 180, proof_font, COLORS["text_dim"])

    img.save(str(frame_path), quality=95)
    return frame_path


def generate_transition_frame(frame_path: Path, color: tuple = (8, 10, 20)) -> Path:
    """Pure color frame for transitions."""
    img = Image.new("RGB", (W, H), color)
    img.save(str(frame_path), quality=90)
    return frame_path


# ─── Audio Generation ──────────────────────────────────────────────────────────


def generate_narration(text: str, output_path: Path) -> Optional[Path]:
    """Generate text-to-speech narration using gTTS."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))
        return output_path
    except Exception as e:
        console.print(f"  [yellow]⚠ gTTS narration failed: {e}[/yellow]")
        return None


def download_background_music(output_path: Path) -> Optional[Path]:
    """
    Download royalty-free dramatic music for trading ad.
    Uses a public domain URL for the demo track.
    """
    # Royalty-free dramatic/cinematic music from Free Music Archive
    urls = [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "https://download.samplelib.com/mp3/sample-3s.mp3",
    ]
    for url in urls:
        try:
            console.print(f"  [cyan]→ Downloading background music...[/cyan]")
            urllib.request.urlretrieve(url, str(output_path))
            if output_path.exists() and output_path.stat().st_size > 1000:
                console.print(f"  [green]✓ Music downloaded[/green]")
                return output_path
        except Exception as e:
            console.print(f"  [dim]Music URL failed: {e}[/dim]")
    return None


def generate_silent_audio(duration: float, output_path: Path) -> Optional[Path]:
    """Generate silent audio track as fallback."""
    ffmpeg_exe = _find_ffmpeg()
    if not ffmpeg_exe:
        return None
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration),
        "-q:a", "0",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return output_path if output_path.exists() else None


# ─── FFmpeg Composition ────────────────────────────────────────────────────────


def _find_ffmpeg() -> Optional[str]:
    """Locate ffmpeg executable."""
    for candidate in ["ffmpeg", "ffmpeg.exe",
                       r"C:\ffmpeg\bin\ffmpeg.exe",
                       r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"]:
        if shutil.which(candidate):
            return candidate
    # Check winget install location
    import glob
    patterns = [
        r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg*\bin\ffmpeg.exe",
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]
    return None


def compose_video(
    frames: list[Path],
    durations: list[float],
    audio_path: Optional[Path],
    output_path: Path,
    apply_color_grade: bool = True,
) -> Optional[Path]:
    """
    Compose frames into a cinematic video using FFmpeg.

    Args:
        frames: Ordered list of image frame paths
        durations: Duration in seconds for each frame
        audio_path: Optional audio file to mix in
        output_path: Output MP4 path
        apply_color_grade: Apply teal-orange color grading

    Returns:
        Path to output video, or None on failure
    """
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        console.print("  [red]✗ FFmpeg not found. Install from https://ffmpeg.org[/red]")
        return None

    # Build concat file for variable-duration frames
    concat_file = output_path.parent / "concat_list.txt"
    with open(concat_file, "w") as f:
        for frame_path, dur in zip(frames, durations):
            f.write(f"file '{frame_path.resolve()}'\n")
            f.write(f"duration {dur}\n")
        # Repeat last frame to avoid missing last frame issue
        if frames:
            f.write(f"file '{frames[-1].resolve()}'\n")

    # Determine if we have audio
    total_duration = sum(durations)

    # Build FFmpeg filter graph for Ken Burns effect + color grade
    vf_filters = []

    # Scale to ensure correct dimensions
    vf_filters.append(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")

    # Fade in at start, fade out at end
    vf_filters.append(f"fade=t=in:st=0:d=1")
    vf_filters.append(f"fade=t=out:st={total_duration - 1.5}:d=1.5")

    if apply_color_grade:
        # Teal-orange Hollywood color grade using curves
        # Shadows: push to teal, Highlights: push to orange/warm
        vf_filters.append(
            "curves=r='0/0 0.3/0.25 1/0.95':"
            "g='0/0 0.5/0.52 1/1.0':"
            "b='0/0.05 0.4/0.45 1/0.85'"
        )
        # Add slight vignette
        vf_filters.append(
            f"vignette=PI/5"
        )

    vf_str = ",".join(vf_filters)

    # Build command
    cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
    ]

    if audio_path and audio_path.exists():
        cmd += ["-i", str(audio_path)]
        cmd += [
            "-vf", vf_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        cmd += [
            "-vf", vf_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]

    console.print(f"  [cyan]→ Running FFmpeg composition...[/cyan]")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        console.print(f"  [red]FFmpeg error:[/red]\n{result.stderr[-500:]}")
        # Cleanup
        concat_file.unlink(missing_ok=True)
        return None

    concat_file.unlink(missing_ok=True)
    console.print(f"  [green]✓ Video rendered:[/green] {output_path.name}")
    return output_path


def add_ken_burns(input_path: Path, output_path: Path, zoom_in: bool = True) -> Optional[Path]:
    """Apply Ken Burns zoom effect to a static image video segment."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        return input_path

    zoom_filter = (
        f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.0,zoom-0.002)':d=200:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}"
        if zoom_in
        else f"scale=8000:-1,zoompan=z='if(gte(zoom,1.5),1.5,zoom+0.002)':d=200:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}"
    )

    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", str(input_path),
        "-vf", zoom_filter,
        "-t", "5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return output_path
    return input_path


class VideoTool:
    """Orchestrates the complete video generation pipeline."""

    def __init__(self):
        self.frames_dir = settings.FRAMES_OUTPUT_DIR
        self.videos_dir = settings.VIDEOS_OUTPUT_DIR

    def generate_video(self, script: dict, version: str = "v1") -> Optional[Path]:
        """
        Generate a cinematic video ad from a script dict.

        Args:
            script: Script dictionary with hook, voiceover, scenes, cta
            version: Version tag (v1, v2, v3)

        Returns:
            Path to the generated MP4, or None on failure
        """
        console.print(f"\n  [bold cyan]🎬 Generating video {version}...[/bold cyan]")

        # Frame output directory
        version_frames_dir = self.frames_dir / version
        version_frames_dir.mkdir(parents=True, exist_ok=True)

        hook = script.get("visual_hook", script.get("hook", "STOP SCROLLING"))
        voiceover = script.get("voiceover", script.get("narration", ""))
        cta = script.get("cta", "Start Free at crowdwisdomtrading.com")
        chart_title = script.get("chart_title", "Crowd Wisdom vs Solo Trader (60 Days)")
        stats = script.get("stats", {})
        script_type = script.get("type", version.replace("v", "").upper())

        frames = []
        durations = []

        # ── Frame 1: Black transition (0.5s)
        f0 = version_frames_dir / "f00_black.jpg"
        generate_transition_frame(f0, COLORS["bg_dark"])
        frames.append(f0); durations.append(0.5)

        # ── Frame 2: Hook (4s)
        f1 = version_frames_dir / "f01_hook.jpg"
        generate_hook_frame(hook, f1)
        frames.append(f1); durations.append(4.0)

        # ── Frame 3: Transition (0.3s)
        f_t1 = version_frames_dir / "f02_trans.jpg"
        generate_transition_frame(f_t1)
        frames.append(f_t1); durations.append(0.3)

        # ── Frame 4: Trading chart (8s)
        f2 = version_frames_dir / "f03_chart.jpg"
        generate_chart_frame(chart_title, f2, script_type=script_type)
        frames.append(f2); durations.append(8.0)

        # ── Frame 5: Stats (6s)
        f3 = version_frames_dir / "f04_stats.jpg"
        generate_stats_frame(stats, f3)
        frames.append(f3); durations.append(6.0)

        # ── Frame 6: Second hook / scene 2 (5s)
        if script.get("scene_2_text"):
            f4 = version_frames_dir / "f05_scene2.jpg"
            generate_hook_frame(script["scene_2_text"], f4)
            frames.append(f4); durations.append(5.0)
        else:
            # Show chart again with emphasis
            frames.append(f2); durations.append(4.0)

        # ── Frame 7: CTA (6s)
        f5 = version_frames_dir / "f06_cta.jpg"
        generate_cta_frame(cta, settings.PRODUCT_URL, f5)
        frames.append(f5); durations.append(6.0)

        # ── Frame 8: Black end (0.5s)
        f_end = version_frames_dir / "f07_end.jpg"
        generate_transition_frame(f_end)
        frames.append(f_end); durations.append(0.5)

        total_dur = sum(durations)
        console.print(f"  [green]✓[/green] Generated {len(frames)} frames ({total_dur:.1f}s total)")

        # ── Narration audio
        audio_path = None
        if voiceover:
            narr_path = version_frames_dir / "narration.mp3"
            console.print("  [cyan]→ Generating narration (gTTS)...[/cyan]")
            audio_path = generate_narration(voiceover[:500], narr_path)
            if audio_path:
                console.print("  [green]✓ Narration ready[/green]")

        # ── Background music (fallback to silence)
        music_path = version_frames_dir / "music.mp3"
        music = download_background_music(music_path)
        if not music:
            silent_path = version_frames_dir / "silent.mp3"
            music = generate_silent_audio(total_dur, silent_path)

        # ── Mix narration + music if both available
        final_audio = None
        if audio_path and music:
            mixed_path = version_frames_dir / "mixed_audio.mp3"
            ffmpeg = _find_ffmpeg()
            if ffmpeg:
                mix_cmd = [
                    ffmpeg, "-y",
                    "-i", str(audio_path),
                    "-i", str(music),
                    "-filter_complex",
                    f"[0:a]volume=1.5[narr];[1:a]volume=0.25,atrim=0:{total_dur}[bg];[narr][bg]amix=inputs=2:duration=shortest",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(mixed_path),
                ]
                r = subprocess.run(mix_cmd, capture_output=True, text=True)
                if r.returncode == 0:
                    final_audio = mixed_path
                    console.print("  [green]✓ Audio mixed[/green]")
                else:
                    final_audio = audio_path
        elif audio_path:
            final_audio = audio_path
        elif music:
            final_audio = music

        # ── Compose final video
        output_path = self.videos_dir / f"crowdwisdom_ad_{version}.mp4"
        result = compose_video(
            frames=frames,
            durations=durations,
            audio_path=final_audio,
            output_path=output_path,
            apply_color_grade=True,
        )

        return result


# Singleton
video_tool = VideoTool()
