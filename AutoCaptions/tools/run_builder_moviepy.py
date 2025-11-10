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
    
    # Check for fonts in multiple possible locations
    # Get the script directory and check relative to it
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_dirs = [
        '.',  # Current directory
        'AutoCaptions',  # AutoCaptions subdirectory
        os.path.join(script_dir, 'AutoCaptions'),  # Full path to AutoCaptions
        os.path.join('AutoCaptions'),  # Relative AutoCaptions
        'outputs',  # Outputs directory
        os.path.join('AutoCaptions', 'outputs')  # AutoCaptions/outputs
    ]
    
    for font_dir in font_dirs:
        black_path = os.path.join(font_dir, 'Poppins-Black.ttf')
        bold_path = os.path.join(font_dir, 'Poppins-Bold.ttf')
        extrabold_path = os.path.join(font_dir, 'Poppins-ExtraBold.ttf')
        
        if os.path.exists(black_path):
            fonts['Black'] = True
        if os.path.exists(bold_path):
            fonts['Bold'] = True
        if os.path.exists(extrabold_path):
            fonts['ExtraBold'] = True
    
    return fonts

def get_wow_words():
    """Get list of 'wow' words that should use Poppins-ExtraBold font"""
    return {
        'wow', 'shocking', 'unbelievable', 'insane', 'crazy', 'secret', 'revealed', 
        'exclusive', 'viral', 'legendary', 'epic', 'mind-blowing', 'unreal', 'amazing', 
        'incredible', 'unexpected', 'rare', 'hidden', 'must-see', 'top', 'ultimate', 
        'best', 'wild', 'funny', 'hilarious', 'breaking', 'alert', 'warning', 'stop', 
        'wait', 'omg', 'wtf', 'no-way', 'game-changer', 'hack', 'trick', 'tip', 
        'proven', 'official', 'first', 'last', 'limited', 'challenge', 'dare', 
        'trending', 'for-you', 'now', 'right-now', 'today', 'instantly', 'fast', 
        'quick', 'easy', 'free', 'win', 'lose', 'fail', 'success', 'power', 'boost', 
        'unlock', 'behind-the-scenes', 'true-story', 'real-life', 'fact', 'secret-sauce'
    }

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
        logger.info("Generating 1-3 word caption states...")
        generator = CaptionGenerator(
            min_visibility_ms=200,
            min_words_per_caption=1,
            max_words_per_caption=3
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
        
        # Assign caption levels (simplified for 1-3 word style)
        logger.info("Assigning caption levels...")
        states = generator.assign_caption_levels(states)
        
        active_states = [s for s in states if not s.skip]
        logger.info(f"Generated {len(active_states)} caption states")
        
        # Generate MoviePy text clip specifications
        logger.info("Generating MoviePy text clip specifications...")
        # Choose a usable font path for MoviePy
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path_candidates = [
            'Poppins-Black.ttf',
            'AutoCaptions/Poppins-Black.ttf',
            os.path.join('AutoCaptions', 'Poppins-Black.ttf'),
            os.path.join(script_dir, 'AutoCaptions', 'Poppins-Black.ttf'),
            os.path.join('outputs', 'Poppins-Black.ttf'),
            os.path.join('AutoCaptions', 'outputs', 'Poppins-Black.ttf')
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
        
        # Create text clips with layered multi-font support
        logger.info("Creating layered multi-font text clips with non-overlapping timing...")
        text_clips = []
        
        # Get wow words and fonts
        wow_words = get_wow_words()
        
        # Find actual font file paths - use absolute paths to avoid issues
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dirs = ['.', 'AutoCaptions', os.path.join(script_dir, 'AutoCaptions'), 
                     os.path.join('AutoCaptions'), 'outputs', os.path.join('AutoCaptions', 'outputs')]
        
        black_font = None
        extrabold_font = None
        
        for font_dir in font_dirs:
            black_path = os.path.join(font_dir, 'Poppins-Black.ttf')
            extrabold_path = os.path.join(font_dir, 'Poppins-ExtraBold.ttf')
            
            if black_font is None and os.path.exists(black_path):
                # Convert to absolute path to avoid any path issues
                black_font = os.path.abspath(black_path) if not os.path.isabs(black_path) else black_path
            if extrabold_font is None and os.path.exists(extrabold_path):
                extrabold_font = os.path.abspath(extrabold_path) if not os.path.isabs(extrabold_path) else extrabold_path
        
        # Sort specs by start time to ensure proper sequencing
        sorted_specs = sorted(text_clips_specs, key=lambda x: x['start_time'])
        
        def detect_wow_words_in_text(text, wow_words):
            """Detect wow words and their positions in text"""
            words = text.split()
            wow_positions = []
            for i, word in enumerate(words):
                clean_word = word.lower().strip('.,!?;:')
                if clean_word in wow_words:
                    wow_positions.append((i, word, clean_word))
            return wow_positions
        
        def estimate_word_x_position(text, word_index, font_size=54):
            """Estimate X position of a word in center-aligned text"""
            words = text.split()
            
            # Estimate character width at font size 54 (Poppins has ~0.52 width ratio)
            char_width = font_size * 0.52
            space_width = char_width * 0.3
            
            # Calculate text before target word
            words_before = words[:word_index]
            chars_before = sum(len(word) for word in words_before)
            spaces_before = len(words_before)
            
            # Calculate total text width
            total_chars = sum(len(word) for word in words)
            total_spaces = len(words) - 1
            total_width = total_chars * char_width + total_spaces * space_width
            
            # Calculate position
            width_before = chars_before * char_width + spaces_before * space_width
            text_start_x = (1080 - total_width) / 2  # Center alignment
            word_x = text_start_x + width_before
            
            return word_x, words[word_index]
        
        for i, spec in enumerate(sorted_specs):
            try:
                caption_text = spec['text']
                
                # Calculate timing (shared for base and overlay clips)
                start_time = spec['start_time']
                if i > 0:
                    prev_end = sorted_specs[i - 1]['start_time'] + (sorted_specs[i - 1]['end_time'] - sorted_specs[i - 1]['start_time'])
                    if start_time < prev_end:
                        start_time = prev_end
                
                if i < len(sorted_specs) - 1:
                    next_start = sorted_specs[i + 1]['start_time']
                    end_time = next_start
                else:
                    end_time = spec['end_time']
                
                min_duration = 0.120
                actual_duration = end_time - start_time
                if actual_duration < min_duration:
                    end_time = start_time + min_duration
                
                # Extract Y position safely
                if isinstance(spec['position'], tuple) and len(spec['position']) == 2:
                    base_y = spec['position'][1]
                else:
                    base_y = 1660  # Fallback
                
                # Create base clip (all text in Poppins-Black)
                # Constrain text width to 90% of video width (972px) to prevent clipping
                # Use method='caption' which handles text rendering properly with margins
                font_size = spec['font_size']
                video_width = video.size[0] if hasattr(video, 'size') else 1080
                video_height = video.size[1] if hasattr(video, 'size') else 1920
                
                # Calculate safe text area: 90% of video width (as per spec)
                safe_width = int(video_width * 0.9)  # 972px for 1080px video
                
                # Ensure text fits within safe width and has proper vertical padding to prevent clipping
                # Strategy: Create clip with margin for padding, then check width and recreate with size constraint if needed
                try:
                    # Calculate proper padding to prevent character clipping
                    # Vertical padding: space for ascenders (h, b, d, l, t) and descenders (p, g, y, j)
                    # For 54px font, we need generous padding to ensure full character display
                    # Poppins font has larger ascenders/descenders, so we need more padding
                    vertical_padding = int(font_size * 0.6)  # 60% padding for ascenders/descenders (very generous)
                    horizontal_padding = 25  # Horizontal padding to prevent edge clipping
                    
                    # Create TextClip with method='caption' for better text rendering
                    # The caption method handles text wrapping and respects margins better
                    # Constrain width to safe area from the start to prevent horizontal clipping
                    try:
                        if black_font and os.path.exists(black_font):
                            base_clip = TextClip(
                                text=caption_text,
                                font=black_font,
                                font_size=font_size,
                                color=spec['font_color'],
                                stroke_color='black',
                                stroke_width=2,
                                method='caption',  # Use caption method for better text handling
                                size=(safe_width, None),  # Constrain width to safe area, auto height
                                margin=(horizontal_padding, vertical_padding)  # Generous padding to prevent clipping
                            )
                        else:
                            base_clip = TextClip(
                                text=caption_text,
                                font_size=font_size,
                                color=spec['font_color'],
                                stroke_color='black',
                                stroke_width=2,
                                method='caption',  # Use caption method for better text handling
                                size=(safe_width, None),  # Constrain width to safe area, auto height
                                margin=(horizontal_padding, vertical_padding)  # Generous padding to prevent clipping
                            )
                    except Exception as e_caption:
                        # Fallback: If caption method fails, use label method with margin
                        logger.debug(f"Caption method failed for '{caption_text}', trying label: {e_caption}")
                        if black_font and os.path.exists(black_font):
                            base_clip = TextClip(
                                text=caption_text,
                                font=black_font,
                                font_size=font_size,
                                color=spec['font_color'],
                                stroke_color='black',
                                stroke_width=2,
                                method='label',  # Fallback to label method
                                margin=(horizontal_padding, vertical_padding)  # Still add margin
                            )
                        else:
                            base_clip = TextClip(
                                text=caption_text,
                                font_size=font_size,
                                color=spec['font_color'],
                                stroke_color='black',
                                stroke_width=2,
                                method='label',  # Fallback to label method
                                margin=(horizontal_padding, vertical_padding)  # Still add margin
                            )
                        
                        # For label method, check width and handle if too wide
                        if hasattr(base_clip, 'size') and base_clip.size:
                            clip_width = base_clip.size[0]
                            if clip_width > safe_width:
                                # Label method doesn't wrap, so we need to scale or skip wide text
                                # For now, log a warning - in production you might want to wrap text manually
                                logger.warning(f"Label method clip '{caption_text}' width {clip_width} exceeds safe width {safe_width}")
                    
                    # Position and time the clip
                    # Ensure the clip stays within video bounds
                    if hasattr(base_clip, 'size') and base_clip.size:
                        clip_height = base_clip.size[1]
                        
                        # Adjust Y position to ensure clip doesn't extend outside video frame
                        # base_y is the desired Y position, but we need to account for clip height
                        # Position from center of clip, not top, to prevent clipping
                        # For bottom-aligned captions, ensure clip bottom edge doesn't go below video
                        clip_bottom = base_y + (clip_height // 2)  # Approximate bottom edge if centered
                        max_y = video_height - (clip_height // 2) - 10  # Leave 10px margin from bottom
                        
                        # If clip would extend below video, adjust Y position upward
                        if clip_bottom > max_y:
                            adjusted_y = max_y - (clip_height // 2)
                            base_y = max(adjusted_y, clip_height // 2 + 10)  # Ensure clip stays in frame
                    
                    # Position clip: center horizontally, position vertically
                    # Use 'center' for both to center the clip at base_y
                    base_clip = base_clip.with_position(('center', base_y))
                    base_clip = base_clip.with_start(start_time).with_end(end_time)
                    text_clips.append(base_clip)
                    logger.info(f"Created base caption: '{caption_text}' at {start_time:.3f}s to {end_time:.3f}s")
                    
                except Exception as e:
                    logger.error(f"Could not create text clip for '{caption_text}': {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
                
                # Detect wow words in this caption
                wow_positions = detect_wow_words_in_text(caption_text, wow_words)
                
                if wow_positions and extrabold_font and os.path.exists(extrabold_font):
                    # Create overlay clips for wow words
                    overlay_info = []
                    
                    for word_index, original_word, clean_word in wow_positions:
                        try:
                            # Estimate word position
                            word_x, word_text = estimate_word_x_position(caption_text, word_index, spec['font_size'])
                            
                            # Create wow word overlay clip - use margins like base
                            overlay_font_size = int(spec['font_size'] * 1.1)
                            overlay_vertical_margin = int(overlay_font_size * 0.5)
                            overlay_horizontal_margin = 10
                            
                            overlay_kwargs = {
                                'text': original_word,
                                'font_size': overlay_font_size,
                                'color': spec['font_color'],
                                'font': extrabold_font,
                                'method': 'caption',  # Use caption method for proper rendering
                                'text_align': 'center',  # Use text_align instead of align
                                'margin': (overlay_horizontal_margin, overlay_vertical_margin),  # Add margins
                                'stroke_color': 'black',
                                'stroke_width': 2,
                            }
                            
                            try:
                                overlay_clip = TextClip(**overlay_kwargs)
                                overlay_clip = overlay_clip.with_position((word_x, base_y))
                                overlay_clip = overlay_clip.with_duration(end_time - start_time)
                                overlay_clip = overlay_clip.with_start(start_time)
                                text_clips.append(overlay_clip)
                            except Exception as e:
                                # Fallback: try with label method and margins
                                logger.warning(f"Overlay caption failed, trying label with margins: {e}")
                                overlay_kwargs['method'] = 'label'
                                try:
                                    overlay_clip = TextClip(**overlay_kwargs)
                                    overlay_clip = overlay_clip.with_position((word_x, base_y))
                                    overlay_clip = overlay_clip.with_duration(end_time - start_time)
                                    overlay_clip = overlay_clip.with_start(start_time)
                                    text_clips.append(overlay_clip)
                                except Exception as e2:
                                    # Final fallback: label without margins
                                    logger.warning(f"Overlay label with margins failed, trying without: {e2}")
                                    overlay_kwargs.pop('margin', None)
                                    overlay_clip = TextClip(**overlay_kwargs)
                                    overlay_clip = overlay_clip.with_position((word_x, base_y))
                                    overlay_clip = overlay_clip.with_duration(end_time - start_time)
                                    overlay_clip = overlay_clip.with_start(start_time)
                                    text_clips.append(overlay_clip)
                            
                            overlay_info.append(f"{original_word}(ExtraBold@{word_x:.0f}px)")
                            
                        except Exception as e:
                            logger.warning(f"Failed to create overlay for '{original_word}': {e}")
                    
                    if overlay_info:
                        logger.info(f"Created layered caption: '{caption_text}' with overlays: {', '.join(overlay_info)} at {start_time:.3f}s to {end_time:.3f}s")
                    else:
                        logger.info(f"Created base caption: '{caption_text}' at {start_time:.3f}s to {end_time:.3f}s")
                else:
                    logger.info(f"Created base caption: '{caption_text}' at {start_time:.3f}s to {end_time:.3f}s")
                
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
            logger.info("[OK] No overlapping captions detected")
        else:
            logger.warning("[WARNING] Some caption overlaps detected - this may cause double text")
        
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
                logger.info("[OK] Output file size check passed (> 1 MB)")
            else:
                logger.warning("[WARNING] Output file size is small (< 1 MB)")
        else:
            logger.error("[ERROR] Output file was not created")
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
        print(f"[SUCCESS] MoviePy test completed successfully: {args.out}")
        sys.exit(0)
    else:
        print(f"[FAILED] MoviePy test failed: {args.out}")
        sys.exit(1)

if __name__ == "__main__":
    main()
