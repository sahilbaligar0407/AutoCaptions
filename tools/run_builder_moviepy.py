#!/usr/bin/env python3
"""
MoviePy Test Entrypoint for Progressive Builder Captions

This script runs the progressive builder captions algorithm using MoviePy rendering.
It produces versioned outputs with Clip_MoviePy_V1.mp4, Clip_MoviePy_V2.mp4, etc.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from progressive_captions import SubtitleParser, CaptionGenerator, MoviePyGenerator

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

def get_next_version(output_dir: str, base_name: str = "Clip_MoviePy_V"):
    """Get next available version number"""
    version = 1
    while os.path.exists(os.path.join(output_dir, f"{base_name}{version}.mp4")):
        version += 1
    return version

def run_moviepy_builder(video_path: str, subtitle_path: str, output_path: str, log_path: str):
    """Run MoviePy with progressive builder captions"""
    
    # Setup logging
    setup_logging(log_path)
    logger = logging.getLogger(__name__)
    
    logger.info("=== MoviePy Progressive Builder Captions Test ===")
    logger.info(f"Video: {video_path}")
    logger.info(f"Subtitles: {subtitle_path}")
    logger.info(f"Output: {output_path}")
    
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
        # Import MoviePy here to avoid import errors if not installed
        try:
            from moviepy import VideoFileClip, TextClip, CompositeVideoClip
            logger.info("MoviePy imported successfully")
        except ImportError as e:
            logger.error(f"MoviePy not available: {e}")
            logger.error("Please install MoviePy: pip install moviepy")
            return False
        
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
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            video_clip.close()
            logger.info(f"Detected video duration: {video_duration:.3f}s")
        except Exception as e:
            logger.warning(f"Could not detect video duration, using default: {video_duration}s")
        
        states = generator.generate_states(segments, clip_start=0.0, clip_end=video_duration)
        
        # Skip caption level assignment since we'll use non-overlapping timing
        # All captions will use the same Y position (primary level)
        logger.info("Skipping caption level assignment - all captions will use same Y position")
        for state in states:
            state.y = 260  # Force all captions to primary level (260px from bottom)
        
        active_states = [s for s in states if not s.skip]
        logger.info(f"Generated {len(active_states)} caption states")
        
        # Generate MoviePy text clip specifications
        logger.info("Generating MoviePy text clip specifications...")
        # Choose a usable font path for MoviePy
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
            logger.info(f"Using font for MoviePy: {chosen_font_path}")
            moviepy_gen = MoviePyGenerator(chosen_font_path)
        else:
            logger.info("No local Poppins font found; letting MoviePy use default font")
            moviepy_gen = MoviePyGenerator()
        

        
        text_clips_specs = moviepy_gen.generate_text_clips(states)
        logger.info(f"Generated {len(text_clips_specs)} text clip specifications")
        
        # Load video
        logger.info("Loading video...")
        video = VideoFileClip(video_path)
        
        # Create text clips with non-overlapping timing
        logger.info("Creating text clips with non-overlapping timing...")
        text_clips = []
        
        # Sort specs by start time to ensure proper sequencing
        sorted_specs = sorted(text_clips_specs, key=lambda x: x['start_time'])
        
        for i, spec in enumerate(sorted_specs):
            try:
                # Create text clip with fallback font handling
                font_file = spec['font_file']
                if not os.path.exists(font_file):
                    # Try to find alternative fonts
                    if fonts['Black']:
                        font_file = 'Poppins-Black.ttf'
                    elif fonts['Bold']:
                        font_file = 'Poppins-Bold.ttf'
                    elif fonts['ExtraBold']:
                        font_file = 'Poppins-ExtraBold.ttf'
                    else:
                        font_file = None  # Use system default
                
                # Create text clip with proper font handling
                text_clip_kwargs = {
                    'text': spec['text'],
                    'font_size': spec['font_size'],
                    'color': spec['font_color']
                }
                
                # Only add font if it exists and is valid
                if font_file and os.path.exists(font_file):
                    text_clip_kwargs['font'] = font_file
                
                # Calculate precise timing to prevent overlap
                start_time = spec['start_time']
                
                # Ensure this caption doesn't start before the previous one ends
                if i > 0:
                    prev_end = sorted_specs[i - 1]['start_time'] + (sorted_specs[i - 1]['end_time'] - sorted_specs[i - 1]['start_time'])
                    if start_time < prev_end:
                        start_time = prev_end  # Start after previous ends
                
                # End time: either the next caption starts, or this caption's natural end
                if i < len(sorted_specs) - 1:
                    next_start = sorted_specs[i + 1]['start_time']
                    # End this caption exactly when the next one starts (no overlap)
                    end_time = next_start
                else:
                    # Last caption uses its natural end time
                    end_time = spec['end_time']
                
                # Ensure minimum visibility (120ms)
                min_duration = 0.120  # 120ms
                actual_duration = end_time - start_time
                if actual_duration < min_duration:
                    end_time = start_time + min_duration
                
                # Create text clip with precise timing
                clip = TextClip(**text_clip_kwargs)
                clip = clip.with_position(spec['position'])
                clip = clip.with_duration(end_time - start_time)
                clip = clip.with_start(start_time)
                
                text_clips.append(clip)
                logger.info(f"Created text clip: '{spec['text']}' at {start_time:.3f}s to {end_time:.3f}s (duration: {end_time-start_time:.3f}s)")
                
            except Exception as e:
                logger.warning(f"Failed to create text clip for '{spec['text']}': {e}")
                continue
        
        logger.info(f"Successfully created {len(text_clips)} text clips")
        
        # Validate no overlapping captions
        logger.info("Validating caption timing...")
        overlapping_found = False
        for i in range(len(text_clips) - 1):
            current_end = text_clips[i].start + text_clips[i].duration
            next_start = text_clips[i + 1].start
            if current_end > next_start:
                logger.warning(f"Overlap detected: clip {i} ends at {current_end:.3f}s, clip {i+1} starts at {next_start:.3f}s")
                overlapping_found = True
        
        if not overlapping_found:
            logger.info("✓ No overlapping captions detected")
        else:
            logger.warning("⚠ Some caption overlaps detected - this may cause double text")
        
        # Composite video
        logger.info("Compositing video with text clips...")
        final_video = CompositeVideoClip([video] + text_clips)
        
        # Write output
        logger.info(f"Writing output to: {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=f'temp-audio-{os.getpid()}.m4a',
            remove_temp=True,
            logger=None  # Suppress MoviePy's own logging
        )
        
        # Clean up
        video.close()
        final_video.close()
        for clip in text_clips:
            clip.close()
        
        logger.info("MoviePy processing completed successfully")
        
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
        
    except Exception as e:
        logger.error(f"Error during MoviePy processing: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run MoviePy Progressive Builder Captions Test')
    parser.add_argument('--video', required=True, help='Input video file path')
    parser.add_argument('--subs', required=True, help='Input subtitle file path')
    parser.add_argument('--out', required=True, help='Output video file path')
    parser.add_argument('--log', required=True, help='Log file path')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    
    # Run the test
    success = run_moviepy_builder(
        args.video, args.subs, args.out, args.log
    )
    
    if success:
        print(f"✓ MoviePy test completed successfully: {args.out}")
        sys.exit(0)
    else:
        print(f"❌ MoviePy test failed: {args.out}")
        sys.exit(1)

if __name__ == "__main__":
    main()
