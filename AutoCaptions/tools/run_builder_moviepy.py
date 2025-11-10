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
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Use text mode explicitly and ensure proper encoding
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
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
    """Get list of 'wow' words that should use Poppins-ExtraBold font with special colors"""
    return {
        'wow', 'shocking', 'unbelievable', 'insane', 'crazy', 'secret', 'revealed', 
        'exclusive', 'viral', 'legendary', 'epic', 'mind-blowing', 'unreal', 'amazing', 
        'incredible', 'unexpected', 'rare', 'hidden', 'must-see', 'top', 'ultimate', 
        'best', 'wild', 'funny', 'hilarious', 'breaking', 'alert', 'warning', 'stop', 
        'wait', 'omg', 'wtf', 'no-way', 'game-changer', 'hack', 'trick', 'tip', 
        'proven', 'official', 'first', 'last', 'limited', 'challenge', 'dare', 
        'trending', 'for-you', 'now', 'right-now', 'today', 'instantly', 'fast', 
        'quick', 'easy', 'free', 'win', 'lose', 'fail', 'success', 'power', 'boost', 
        'unlock', 'behind-the-scenes', 'true-story', 'real-life', 'fact', 'secret-sauce',
        'gosh', 'holy', 'damn', 'heck', 'jeez', 'whoa'
    }

def get_italic_words():
    """Get list of words that should be italicized"""
    return {
        'like', 'feel', 'think', 'seem', 'appear', 'look', 'sound', 'taste', 'smell',
        'maybe', 'perhaps', 'possibly', 'probably', 'might', 'could', 'would', 'should',
        'almost', 'nearly', 'about', 'around', 'roughly', 'approximately'
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
        
        # Create text clips with styled fonts and colors
        logger.info("Creating styled text clips with dynamic font/color based on content...")
        text_clips = []
        
        # Find actual font file paths - use absolute paths to avoid issues
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dirs = ['.', 'AutoCaptions', os.path.join(script_dir, 'AutoCaptions'), 
                     os.path.join('AutoCaptions'), 'outputs', os.path.join('AutoCaptions', 'outputs')]
        
        # Detect all available fonts for styling
        black_font = None
        bold_font = None
        extrabold_font = None
        blackitalic_font = None
        bolditalic_font = None
        
        for font_dir in font_dirs:
            black_path = os.path.join(font_dir, 'Poppins-Black.ttf')
            bold_path = os.path.join(font_dir, 'Poppins-Bold.ttf')
            extrabold_path = os.path.join(font_dir, 'Poppins-ExtraBold.ttf')
            blackitalic_path = os.path.join(font_dir, 'Poppins-BlackItalic.ttf')
            bolditalic_path = os.path.join(font_dir, 'Poppins-BoldItalic.ttf')
            
            if black_font is None and os.path.exists(black_path):
                black_font = os.path.abspath(black_path) if not os.path.isabs(black_path) else black_path
            if bold_font is None and os.path.exists(bold_path):
                bold_font = os.path.abspath(bold_path) if not os.path.isabs(bold_path) else bold_path
            if extrabold_font is None and os.path.exists(extrabold_path):
                extrabold_font = os.path.abspath(extrabold_path) if not os.path.isabs(extrabold_path) else extrabold_path
            if blackitalic_font is None and os.path.exists(blackitalic_path):
                blackitalic_font = os.path.abspath(blackitalic_path) if not os.path.isabs(blackitalic_path) else blackitalic_path
            if bolditalic_font is None and os.path.exists(bolditalic_path):
                bolditalic_font = os.path.abspath(bolditalic_path) if not os.path.isabs(bolditalic_path) else bolditalic_path
        
        # Sort specs by start time to ensure proper sequencing
        sorted_specs = sorted(text_clips_specs, key=lambda x: x['start_time'])
        
        # Get word lists for styling
        wow_words = get_wow_words()
        italic_words = get_italic_words()
        
        def detect_wow_words_in_text(text, wow_words):
            """Detect wow words and their positions in text"""
            words = text.split()
            wow_positions = []
            for i, word in enumerate(words):
                clean_word = word.lower().strip('.,!?;:')
                if clean_word in wow_words:
                    wow_positions.append((i, word, clean_word))
            return wow_positions
        
        def detect_italic_words_in_text(text, italic_words):
            """Detect italic words in text"""
            words = text.split()
            for word in words:
                clean_word = word.lower().strip('.,!?;:')
                if clean_word in italic_words:
                    return True
            return False
        
        def determine_caption_style(text, wow_words, italic_words):
            """Determine font and color style for a caption based on its content"""
            words = text.split()
            
            # Check for wow words first (higher priority)
            has_wow_word = False
            for word in words:
                clean_word = word.lower().strip('.,!?;:')
                if clean_word in wow_words:
                    has_wow_word = True
                    break
            
            # Check for italic words
            has_italic_word = detect_italic_words_in_text(text, italic_words)
            
            # Determine style
            if has_wow_word:
                # Wow words: ExtraBold font, yellow/gold color
                return {
                    'font': extrabold_font if extrabold_font and os.path.exists(extrabold_font) else bold_font if bold_font and os.path.exists(bold_font) else black_font,
                    'color': 'yellow',  # Bright yellow for wow words
                    'style': 'wow'
                }
            elif has_italic_word:
                # Italic words: BlackItalic or BoldItalic font
                return {
                    'font': blackitalic_font if blackitalic_font and os.path.exists(blackitalic_font) else bolditalic_font if bolditalic_font and os.path.exists(bolditalic_font) else black_font,
                    'color': 'white',  # White for italic words
                    'style': 'italic'
                }
            else:
                # Default: Black font, white color
                return {
                    'font': black_font,
                    'color': 'white',
                    'style': 'default'
                }
        
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
        
        # First pass: Detect and skip shorter captions that are subsets of longer overlapping captions
        # This prevents issues like "Last" overlapping with "Last Guest" causing visual overlap
        # We only check captions that actually overlap temporally (not just adjacent)
        logger.info("Checking for subset caption overlaps...")
        skip_indices = set()
        
        def normalize_text(text):
            """Normalize text for comparison (lowercase, strip punctuation)"""
            import re
            return re.sub(r'[^\w\s]', '', text.lower().strip())
        
        def is_subset(shorter_text, longer_text):
            """Check if shorter_text is a prefix/subset of longer_text"""
            shorter_norm = normalize_text(shorter_text)
            longer_norm = normalize_text(longer_text)
            # Check if shorter is a prefix of longer (allowing for word boundaries)
            shorter_words = shorter_norm.split()
            longer_words = longer_norm.split()
            if len(shorter_words) >= len(longer_words):
                return False
            # Check if shorter words match the beginning of longer words
            return shorter_words == longer_words[:len(shorter_words)]
        
        def captions_overlap_temporally(spec1, spec2):
            """Check if two caption specs overlap temporally"""
            return not (spec1['end_time'] <= spec2['start_time'] or spec1['start_time'] >= spec2['end_time'])
        
        # Check all pairs of captions for subset overlaps
        for i, spec1 in enumerate(sorted_specs):
            if i in skip_indices:
                continue
            text1 = spec1['text']
            words1 = len(text1.split())
            
            for j, spec2 in enumerate(sorted_specs):
                if i == j or j in skip_indices:
                    continue
                text2 = spec2['text']
                words2 = len(text2.split())
                
                # Only check if captions actually overlap temporally (not just adjacent)
                if not captions_overlap_temporally(spec1, spec2):
                    continue
                
                # If one caption is shorter and is a subset of the longer one, skip the shorter
                if words1 < words2 and is_subset(text1, text2):
                    skip_indices.add(i)
                    logger.info(f"Skipping shorter caption '{text1}' (index {i}) - it's a subset of overlapping caption '{text2}' (index {j})")
                    break
                elif words2 < words1 and is_subset(text2, text1):
                    skip_indices.add(j)
                    logger.info(f"Skipping shorter caption '{text2}' (index {j}) - it's a subset of overlapping caption '{text1}' (index {i})")
        
        logger.info(f"Marked {len(skip_indices)} captions to skip due to subset overlaps")
        
        # Second pass: Group clips by Y position (level), then calculate timings per level
        # Clips at different Y positions can overlap temporally (different levels)
        # Clips at the same Y position must NOT overlap (same level)
        min_duration = 0.120
        
        # Group specs by Y position (skip indices that are marked for skipping)
        specs_by_y = {}
        for i, spec in enumerate(sorted_specs):
            if i in skip_indices:
                continue  # Skip captions marked as subsets
            if isinstance(spec['position'], tuple) and len(spec['position']) == 2:
                y_pos = spec['position'][1]
            else:
                y_pos = 1660  # Fallback
            if y_pos not in specs_by_y:
                specs_by_y[y_pos] = []
            specs_by_y[y_pos].append((i, spec))  # Store index and spec
        
        # Create a mapping from original index to calculated timing as we process
        timing_map = {}
        
        # Process each Y position group and store timings in map
        # This ensures clips at the same Y position don't overlap
        # Sort each group by start_time to process in chronological order
        for y_pos, y_specs in specs_by_y.items():
            # Sort by start_time to ensure chronological processing
            y_specs.sort(key=lambda x: x[1]['start_time'])
            
            # Single pass: Calculate non-overlapping timings in one forward sweep
            # This ensures each clip starts AFTER the previous one ends
            # and ends BEFORE (or at) the next one starts - STRICT NO-OVERLAP GUARANTEE
            last_clip_end_time = 0.0
            
            for i, (idx, spec) in enumerate(y_specs):
                original_start = spec['start_time']
                original_end = spec['end_time']
                
                # CRITICAL: Start time MUST be >= previous clip's end time (strict - no exceptions)
                # This ensures no temporal overlap
                start_time = max(original_start, last_clip_end_time)
                
                # Find the next clip's original start time to cap our end time
                # We look ahead to find the earliest next clip start time
                next_start_candidates = []
                for j in range(i + 1, len(y_specs)):
                    next_idx, next_spec = y_specs[j]
                    next_start_candidates.append(next_spec['start_time'])
                
                # Calculate end time with strict non-overlap guarantee
                if next_start_candidates:
                    # Use the earliest next clip start time as maximum end time
                    # This ensures we don't overlap with ANY future clip
                    max_end_time = min(next_start_candidates)
                    min_end_time = start_time + min_duration
                    
                    # Check if we can fit minimum duration before next clip starts
                    if min_end_time > max_end_time:
                        # Can't fit minimum duration without overlapping - skip this clip
                        gap = max_end_time - start_time
                        logger.info(f"Skipping clip {idx} '{spec['text'][:40]}' at Y={y_pos} - cannot fit {min_duration:.3f}s (gap available: {gap:.3f}s) before next clip at {max_end_time:.3f}s")
                        timing_map[idx] = {
                            'start_time': start_time,
                            'end_time': max_end_time,
                            'skip': True,
                            'original_start': original_start,
                            'original_end': original_end
                        }
                        # Don't update last_clip_end_time for skipped clips
                        continue
                    
                    # End time: use original_end if it fits, otherwise cap at next clip's start
                    # But ALWAYS ensure we don't exceed max_end_time
                    end_time = min(original_end, max_end_time)
                    # Ensure minimum duration
                    end_time = max(end_time, min_end_time)
                    
                    # FINAL CHECK: Ensure end_time <= max_end_time (next clip's start)
                    # This is the critical non-overlap guarantee
                    if end_time > max_end_time:
                        end_time = max_end_time
                else:
                    # Last clip in this Y position - use original end time or minimum duration
                    end_time = max(original_end, start_time + min_duration)
                
                # Final validation: ensure we have valid timing
                duration = end_time - start_time
                if duration < min_duration:
                    # This shouldn't happen given our checks above, but handle it gracefully
                    logger.warning(f"Skipping clip {idx} '{spec['text'][:40]}' at Y={y_pos} - final duration {duration:.3f}s is less than minimum {min_duration:.3f}s")
                    timing_map[idx] = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'skip': True,
                        'original_start': original_start,
                        'original_end': original_end
                    }
                    continue
                
                # Store final timing (guaranteed non-overlapping)
                timing_map[idx] = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'skip': False,
                    'original_start': original_start,
                    'original_end': original_end
                }
                
                # Update last clip end time for next iteration
                # This ensures the next clip starts after this one ends
                last_clip_end_time = end_time
                
                # Log if timing was significantly adjusted from original
                start_adjusted = abs(start_time - original_start) > 0.01
                end_adjusted = abs(end_time - original_end) > 0.01
                if start_adjusted or end_adjusted:
                    logger.debug(f"Timing adjusted for clip {idx} '{spec['text'][:40]}' at Y={y_pos}: {start_time:.3f}s-{end_time:.3f}s (original: {original_start:.3f}s-{original_end:.3f}s)")
        
        # Rebuild calculated_timings in original order
        # Mark skipped indices from subset detection as skipped
        calculated_timings = []
        for i in range(len(sorted_specs)):
            if i in skip_indices:
                # Mark as skipped due to subset overlap
                calculated_timings.append({
                    'start_time': sorted_specs[i]['start_time'],
                    'end_time': sorted_specs[i]['end_time'],
                    'skip': True
                })
            else:
                # Use timing from map, or default if not in map
                calculated_timings.append(timing_map.get(i, {
                    'start_time': sorted_specs[i]['start_time'],
                    'end_time': sorted_specs[i]['end_time'],
                    'skip': False
                }))
        
        # Second pass: Create clips with resolved timings
        for i, spec in enumerate(sorted_specs):
            try:
                # Skip if marked for skipping
                if calculated_timings[i]['skip']:
                    logger.debug(f"Skipping clip {i} '{spec['text']}' due to timing constraints")
                    continue
                
                caption_text = spec['text']
                
                # Use calculated timings (guaranteed no overlaps)
                start_time = calculated_timings[i]['start_time']
                end_time = calculated_timings[i]['end_time']
                
                # Extract Y position safely
                if isinstance(spec['position'], tuple) and len(spec['position']) == 2:
                    base_y = spec['position'][1]
                else:
                    base_y = 1660  # Fallback
                
                # Determine caption style based on content (wow words, italic words, etc.)
                style_info = determine_caption_style(caption_text, wow_words, italic_words)
                caption_font = style_info['font']
                caption_color = style_info['color']
                style_type = style_info['style']
                
                # Create styled caption clip with appropriate font and color
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
                        if caption_font and os.path.exists(caption_font):
                            base_clip = TextClip(
                                text=caption_text,
                                font=caption_font,
                                font_size=font_size,
                                color=caption_color,
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
                                color=caption_color,
                                stroke_color='black',
                                stroke_width=2,
                                method='caption',  # Use caption method for better text handling
                                size=(safe_width, None),  # Constrain width to safe area, auto height
                                margin=(horizontal_padding, vertical_padding)  # Generous padding to prevent clipping
                            )
                    except Exception as e_caption:
                        # Fallback: If caption method fails, use label method with margin
                        logger.debug(f"Caption method failed for '{caption_text}', trying label: {e_caption}")
                        if caption_font and os.path.exists(caption_font):
                            base_clip = TextClip(
                                text=caption_text,
                                font=caption_font,
                                font_size=font_size,
                                color=caption_color,
                                stroke_color='black',
                                stroke_width=2,
                                method='label',  # Fallback to label method
                                margin=(horizontal_padding, vertical_padding)  # Still add margin
                            )
                        else:
                            base_clip = TextClip(
                                text=caption_text,
                                font_size=font_size,
                                color=caption_color,
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
                    
                    # Log caption creation with style information
                    style_desc = f"[{style_type}]" if style_type != 'default' else ""
                    logger.info(f"Created caption {style_desc}: '{caption_text}' at {start_time:.3f}s to {end_time:.3f}s (font: {os.path.basename(caption_font) if caption_font else 'default'}, color: {caption_color})")
                    
                except Exception as e:
                    logger.error(f"Could not create text clip for '{caption_text}': {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
                
            except Exception as e:
                logger.warning(f"Failed to create text clip for '{spec['text']}': {e}")
                continue
        
        logger.info(f"Successfully created {len(text_clips)} text clips")
        
        # Validate no overlapping BASE captions at the same Y position
        # Overlay clips are INTENDED to overlap with base clips (they're layered on top)
        # Only BASE clips at the SAME Y position should not overlap with each other
        logger.info("Validating caption timing...")
        overlapping_found = False
        overlap_details = []
        
        # Extract Y positions and identify base vs overlay clips
        # Base clips are centered horizontally ('center' in X position)
        # Overlay clips have specific X coordinates (not 'center')
        clip_info = []
        for i, clip in enumerate(text_clips):
            try:
                if callable(clip.pos):
                    pos = clip.pos(0)  # Evaluate at t=0
                else:
                    pos = clip.pos
                
                if isinstance(pos, (tuple, list)) and len(pos) > 1:
                    x_pos = pos[0]
                    y_pos = pos[1]
                elif isinstance(pos, (int, float)):
                    x_pos = None
                    y_pos = pos
                else:
                    x_pos = None
                    y_pos = None
                
                # Identify if this is a base clip (centered) or overlay (specific X position)
                # Base clips use 'center' for X, overlays use numeric X coordinates
                is_base_clip = (x_pos == 'center' or (isinstance(x_pos, str) and 'center' in str(x_pos).lower()))
                
                clip_info.append({
                    'index': i,
                    'clip': clip,
                    'x_pos': x_pos,
                    'y_pos': y_pos,
                    'is_base': is_base_clip,
                    'start': clip.start,
                    'end': clip.start + clip.duration,
                    'duration': clip.duration
                })
            except Exception as e:
                logger.debug(f"Could not extract position for clip {i}: {e}")
                clip_info.append({
                    'index': i,
                    'clip': clip,
                    'x_pos': None,
                    'y_pos': None,
                    'is_base': True,  # Assume base if we can't determine
                    'start': clip.start,
                    'end': clip.start + clip.duration,
                    'duration': clip.duration
                })
        
        # Group base clips by Y position and check for overlaps
        # Ignore overlay clips in overlap detection (they're supposed to overlap with base)
        base_clips_by_y = {}
        for info in clip_info:
            if info['is_base'] and info['y_pos'] is not None:
                y_pos = info['y_pos']
                if y_pos not in base_clips_by_y:
                    base_clips_by_y[y_pos] = []
                base_clips_by_y[y_pos].append(info)
        
        # Check for overlaps between base clips at the same Y position
        for y_pos, base_clips in base_clips_by_y.items():
            # Sort by start time
            base_clips_sorted = sorted(base_clips, key=lambda x: x['start'])
            
            # Check consecutive base clips for overlaps
            for j in range(len(base_clips_sorted) - 1):
                clip1 = base_clips_sorted[j]
                clip2 = base_clips_sorted[j + 1]
                
                # Check if clip1 ends after clip2 starts (overlap)
                if clip1['end'] > clip2['start']:
                    # Real overlap between base clips - this is a problem!
                    overlap_details.append({
                        'y_pos': y_pos,
                        'clip1_idx': clip1['index'],
                        'clip1_start': clip1['start'],
                        'clip1_end': clip1['end'],
                        'clip1_duration': clip1['duration'],
                        'clip2_idx': clip2['index'],
                        'clip2_start': clip2['start'],
                        'clip2_end': clip2['end'],
                        'clip2_duration': clip2['duration']
                    })
                    overlapping_found = True
                    logger.warning(f"Overlap detected at Y={y_pos}: base clip {clip1['index']} ({clip1['start']:.3f}s-{clip1['end']:.3f}s, dur={clip1['duration']:.3f}s) overlaps with base clip {clip2['index']} ({clip2['start']:.3f}s-{clip2['end']:.3f}s, dur={clip2['duration']:.3f}s)")
        
        if not overlapping_found:
            logger.info("[OK] No overlapping base captions detected at same level")
        else:
            logger.error(f"[ERROR] {len(overlap_details)} base caption overlap(s) detected at same level - this will cause double text!")
            # Log overlap details for debugging
            for overlap in overlap_details:
                logger.error(f"  Overlap at Y={overlap['y_pos']}: clip {overlap['clip1_idx']} ({overlap['clip1_start']:.3f}s-{overlap['clip1_end']:.3f}s) overlaps with clip {overlap['clip2_idx']} ({overlap['clip2_start']:.3f}s-{overlap['clip2_end']:.3f}s)")
        
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
