#!/usr/bin/env python3
"""
FFmpeg Test Entrypoint for Progressive Builder Captions

This script runs the progressive builder captions algorithm using FFmpeg rendering.
It produces versioned outputs with Clip_FFmpeg_V1.mp4, Clip_FFmpeg_V2.mp4, etc.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from progressive_captions import SubtitleParser, CaptionGenerator, FFmpegGenerator

def setup_logging(log_file: str):
    """Setup logging to both file and console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def detect_fonts():
    """Detect available Poppins fonts"""
    fonts = {
        'Black': False,
        'Bold': False,
        'ExtraBold': False
    }
    
    # Check for fonts in current directory and outputs directory
    font_dirs = ['.', 'outputs']
    
    for font_dir in font_dirs:
        if os.path.exists(os.path.join(font_dir, 'Poppins-Black.ttf')):
            fonts['Black'] = True
        if os.path.exists(os.path.join(font_dir, 'Poppins-Bold.ttf')):
            fonts['Bold'] = True
        if os.path.exists(os.path.join(font_dir, 'Poppins-ExtraBold.ttf')):
            fonts['ExtraBold'] = True
    
    return fonts

def get_next_version(output_dir: str, base_name: str = "Clip_FFmpeg_V"):
    """Get next available version number"""
    version = 1
    while os.path.exists(os.path.join(output_dir, f"{base_name}{version}.mp4")):
        version += 1
    return version

def run_ffmpeg_builder(video_path: str, subtitle_path: str, output_path: str, 
                       filter_script_path: str, log_path: str):
    """Run FFmpeg with progressive builder captions"""
    
    # Setup logging
    setup_logging(log_path)
    logger = logging.getLogger(__name__)
    
    logger.info("=== FFmpeg Progressive Builder Captions Test ===")
    logger.info(f"Video: {video_path}")
    logger.info(f"Subtitles: {subtitle_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Filter Script: {filter_script_path}")
    
    # Detect fonts
    fonts = detect_fonts()
    logger.info(f"Fonts detected: {fonts}")
    
    # Check inputs
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
    
    if not os.path.exists(subtitle_path):
        logger.error(f"Subtitle file not found: {subtitle_path}")
        return False
    
    try:
        # Parse subtitles
        logger.info("Parsing subtitles...")
        segments = SubtitleParser.parse_subtitles(subtitle_path)
        logger.info(f"Found {len(segments)} subtitle segments")
        
        # Generate caption states
        logger.info("Generating progressive caption states...")
        generator = CaptionGenerator(
            lead_in_ms=180,
            min_visibility_ms=120,
            overlap_ms=50,
            max_words=5
        )
        
        # Get video duration (default to 33.23s if we can't detect)
        video_duration = 33.23
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ], capture_output=True, text=True, check=True)
            video_duration = float(result.stdout.strip())
            logger.info(f"Detected video duration: {video_duration:.3f}s")
        except (subprocess.CalledProcessError, ValueError):
            logger.warning(f"Could not detect video duration, using default: {video_duration}s")
        
        states = generator.generate_states(segments, clip_start=0.0, clip_end=video_duration)
        states = generator.assign_caption_levels(states)
        
        active_states = [s for s in states if not s.skip]
        logger.info(f"Generated {len(active_states)} caption states")
        
        # Generate FFmpeg filter script
        logger.info("Generating FFmpeg filter script...")
        # Choose a usable font path for FFmpeg drawtext
        font_path_candidates = [
            'Poppins-Black.ttf',
            os.path.join('outputs', 'Poppins-Black.ttf')
        ]
        chosen_font_path = None
        for cand in font_path_candidates:
            if os.path.exists(cand):
                chosen_font_path = cand
                break
        if chosen_font_path:
            logger.info(f"Using font for FFmpeg: {chosen_font_path}")
            ffmpeg_gen = FFmpegGenerator(chosen_font_path)
        else:
            logger.info("No local Poppins font found; letting FFmpeg use default font")
            ffmpeg_gen = FFmpegGenerator()
        ffmpeg_gen.generate_filter_script(states, filter_script_path)
        logger.info(f"Filter script saved to: {filter_script_path}")
        
        # Run FFmpeg
        logger.info("Running FFmpeg...")
        
        # Read the filter script content and use -filter_complex directly
        with open(filter_script_path, 'r', encoding='utf-8') as f:
            filter_complex = f.read().strip()
        
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', video_path,
            '-filter_complex', filter_complex,
            '-map', '[v]'
        ]

        # Map audio if present; if mapping fails, we will retry without audio
        has_audio = True
        try:
            probe = subprocess.run([
                'ffprobe', '-v', 'quiet', '-select_streams', 'a:0', '-show_entries', 'stream=codec_type',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ], capture_output=True, text=True, check=True)
            has_audio = 'audio' in probe.stdout.lower()
        except Exception:
            has_audio = True

        if has_audio:
            cmd += ['-map', '0:a', '-c:a', 'copy']

        cmd.append(output_path)
        
        logger.info(f"FFmpeg command: ffmpeg -y -i {video_path} -filter_complex <script> -map [v] {'-map 0:a -c:a copy' if has_audio else ''} {output_path}")
        
        # Run FFmpeg and capture output; if it fails due to audio mapping, retry without audio
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.warning("FFmpeg failed on first attempt, retrying without audio mapping...")
            cmd_no_audio = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-filter_complex', filter_complex,
                '-map', '[v]',
                output_path
            ]
            result = subprocess.run(
                cmd_no_audio,
                capture_output=True,
                text=True,
                check=True
            )
        
        logger.info("FFmpeg completed successfully")
        logger.info(f"FFmpeg stdout: {result.stdout}")
        logger.info(f"FFmpeg stderr: {result.stderr}")
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            logger.info(f"Output file created: {output_path} ({file_size:.2f} MB)")
            
            if file_size > 1:
                logger.info("✓ Output file size check passed (> 1 MB)")
            else:
                logger.warning("⚠ Output file size is small (< 1 MB)")
        else:
            logger.error("❌ Output file was not created")
            return False
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed with exit code {e.returncode}")
        logger.error(f"FFmpeg stdout: {e.stdout}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        return False
        
    except Exception as e:
        logger.error(f"Error during FFmpeg processing: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run FFmpeg Progressive Builder Captions Test')
    parser.add_argument('--video', required=True, help='Input video file path')
    parser.add_argument('--subs', required=True, help='Input subtitle file path')
    parser.add_argument('--out', required=True, help='Output video file path')
    parser.add_argument('--filter-script', required=True, help='Filter script file path')
    parser.add_argument('--log', required=True, help='Log file path')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    os.makedirs(os.path.dirname(args.filter_script), exist_ok=True)
    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    
    # Run the test
    success = run_ffmpeg_builder(
        args.video, args.subs, args.out, args.filter_script, args.log
    )
    
    if success:
        print(f"✓ FFmpeg test completed successfully: {args.out}")
        sys.exit(0)
    else:
        print(f"❌ FFmpeg test failed: {args.out}")
        sys.exit(1)

if __name__ == "__main__":
    main()
