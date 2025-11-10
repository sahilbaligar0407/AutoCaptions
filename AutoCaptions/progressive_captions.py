#!/usr/bin/env python3
"""
1-3 Word Captions Algorithm Implementation

This module implements a caption algorithm that displays 1-3 words on screen
at a time, appearing as words are spoken. Words are selected based on timing
constraints, and cycle through 1-3 words when no strict constraints exist.

Core Features:
- Parses ASS, SRT, and VTT subtitle formats
- Generates 1-3 word captions that appear as words are spoken
- Synthesizes word-level timing with constraints
- Cycles through 1-3 words based on timing (1, 2, 3, 1, 2, 3...)
- Generates FFmpeg filter scripts for rendering
- Supports MoviePy text layer generation

Author: AutoCaptions
License: MIT
"""

import os
import re
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubtitleSegment:
    """Represents a subtitle segment with timing and text"""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Subtitle text
    index: int    # Original segment index for stable sorting


@dataclass
class CaptionState:
    """Represents a caption state with timing and layout"""
    text: str           # Display text (wrapped)
    on: float          # Start time in seconds
    off: float         # End time in seconds
    seg_idx: int       # Source segment index
    y: int            # Vertical position (260 or 320 from bottom)
    skip: bool = False # Whether to skip this state


class SubtitleParser:
    """Unified parser for ASS, SRT, and VTT subtitle formats"""
    
    @staticmethod
    def parse_ass(file_path: str) -> List[SubtitleSegment]:
        """Parse ASS subtitle file"""
        segments = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find Events section
        events_match = re.search(r'\[Events\].*?(?=\[|$)', content, re.DOTALL)
        if not events_match:
            return segments
        
        events_content = events_match.group(0)
        lines = events_content.strip().split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('Dialogue:'):
                parts = line.split(',', 9)  # Split into max 10 parts
                if len(parts) >= 10:
                    start_time = SubtitleParser._parse_ass_time(parts[1])
                    end_time = SubtitleParser._parse_ass_time(parts[2])
                    text = parts[9].strip()
                    
                    if start_time is not None and end_time is not None:
                        segments.append(SubtitleSegment(
                            start=start_time,
                            end=end_time,
                            text=text,
                            index=i
                        ))
        
        return segments
    
    @staticmethod
    def parse_srt(file_path: str) -> List[SubtitleSegment]:
        """Parse SRT subtitle file"""
        segments = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for i, block in enumerate(blocks):
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Parse timecode line (e.g., "00:00:00,000 --> 00:00:07,350")
                time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', lines[1])
                if time_match:
                    start_time = SubtitleParser._parse_srt_time(time_match.group(1))
                    end_time = SubtitleParser._parse_srt_time(time_match.group(2))
                    text = ' '.join(lines[2:]).strip()
                    
                    if start_time is not None and end_time is not None:
                        segments.append(SubtitleSegment(
                            start=start_time,
                            end=end_time,
                            text=text,
                            index=i
                        ))
        
        return segments
    
    @staticmethod
    def parse_vtt(file_path: str) -> List[SubtitleSegment]:
        """Parse VTT subtitle file"""
        segments = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into subtitle blocks (skip WEBVTT header)
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for i, block in enumerate(blocks):
            if block.startswith('WEBVTT'):
                continue
                
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Parse timecode line (e.g., "0:00:00.000 --> 0:00:02.535692")
                time_match = re.match(r'(\d{1,2}:\d{2}:\d{2}\.\d{3,6})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3,6})', lines[1])
                if time_match:
                    start_time = SubtitleParser._parse_vtt_time(time_match.group(1))
                    end_time = SubtitleParser._parse_vtt_time(time_match.group(2))
                    text = ' '.join(lines[2:]).strip()
                    
                    if start_time is not None and end_time is not None:
                        segments.append(SubtitleSegment(
                            start=start_time,
                            end=end_time,
                            text=text,
                            index=i
                        ))
        
        return segments
    
    @staticmethod
    def parse_subtitles(file_path: str) -> List[SubtitleSegment]:
        """Parse any subtitle format and return unified format"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.ass':
            return SubtitleParser.parse_ass(file_path)
        elif ext == '.srt':
            return SubtitleParser.parse_srt(file_path)
        elif ext == '.vtt':
            return SubtitleParser.parse_vtt(file_path)
        else:
            raise ValueError(f"Unsupported subtitle format: {ext}")
    
    @staticmethod
    def _parse_ass_time(time_str: str) -> Optional[float]:
        """Parse ASS time format (H:MM:SS.cc)"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            pass
        return None
    
    @staticmethod
    def _parse_srt_time(time_str: str) -> Optional[float]:
        """Parse SRT time format (HH:MM:SS,mmm)"""
        try:
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            pass
        return None
    
    @staticmethod
    def _parse_vtt_time(time_str: str) -> Optional[float]:
        """Parse VTT time format (H:MM:SS.mmm)"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            pass
        return None


class CaptionGenerator:
    """Generates 1-3 word captions that appear as words are spoken"""
    
    def __init__(self, 
                 min_visibility_ms: int = 200,
                 min_words_per_caption: int = 1,
                 max_words_per_caption: int = 3):
        self.min_visibility_sec = min_visibility_ms / 1000.0
        self.min_words = min_words_per_caption
        self.max_words = max_words_per_caption
    
    def tokenize(self, text: str) -> List[str]:
        """Split text into words with trailing punctuation"""
        # Split on whitespace and filter empty strings
        words = [word.strip() for word in re.split(r'\s+', text) if word.strip()]
        return words
    
    def compute_word_times(self, seg_start: float, seg_end: float, word_count: int) -> List[Tuple[float, float]]:
        """Synthesize uniform word timings with constraints"""
        total_dur = seg_end - seg_start
        # Ensure minimum duration for visibility
        min_total_dur = word_count * (self.min_visibility_sec / self.max_words)
        actual_dur = max(total_dur, min_total_dur)
        slot = actual_dur / word_count
        
        word_times = []
        for i in range(word_count):
            w_start = seg_start + i * slot
            w_end = seg_start + (i + 1) * slot
            
            # Clamp to segment boundaries
            w_start = max(seg_start, min(seg_end, w_start))
            w_end = max(seg_start, min(seg_end, w_end))
            
            word_times.append((w_start, w_end))
        
        return word_times
    
    def determine_word_count(self, word_index: int, total_words: int, avg_time_per_word: float) -> int:
        """Determine how many words to show (cycles through 1-3 based on timing)"""
        remaining_words = total_words - word_index
        
        # If speech is very fast, show fewer words
        if avg_time_per_word < self.min_visibility_sec / 2:
            return min(1, remaining_words)
        elif avg_time_per_word < self.min_visibility_sec:
            return min(2, remaining_words)
        
        # Normal speech: cycle through 1, 2, 3, 1, 2, 3, ...
        # This creates a natural rhythm
        cycle_pos = word_index % 3
        word_count = self.min_words + cycle_pos
        word_count = min(word_count, self.max_words, remaining_words)
        
        # Ensure we show at least min_words if possible
        if word_count < self.min_words and remaining_words >= self.min_words:
            word_count = self.min_words
        
        return word_count
    
    def generate_states(self, segments: List[SubtitleSegment], 
                       clip_start: float = 0.0, 
                       clip_end: float = float('inf')) -> List[CaptionState]:
        """Generate 1-3 word caption states that appear as words are spoken"""
        states = []
        
        for seg in segments:
            # Adjust to clip-relative timeline
            adj_start = max(0, seg.start - clip_start)
            adj_end = min(clip_end - clip_start, seg.end - clip_start)
            
            if adj_end <= adj_start:
                continue
            
            words = self.tokenize(seg.text)
            if not words:
                continue
            
            # Compute word timings
            word_times = self.compute_word_times(adj_start, adj_end, len(words))
            total_duration = adj_end - adj_start
            
            # Calculate average time per word for timing-based decisions
            avg_time_per_word = total_duration / len(words) if len(words) > 0 else self.min_visibility_sec
            
            # Process words in groups of 1-3
            i = 0
            while i < len(words):
                # Determine how many words to show in this caption
                # Cycles through 1, 2, 3, 1, 2, 3... based on timing constraints
                word_count = self.determine_word_count(i, len(words), avg_time_per_word)
                
                # Ensure we don't exceed remaining words
                word_count = min(word_count, len(words) - i)
                
                # Get the words for this caption
                caption_words = words[i:i + word_count]
                caption_text = ' '.join(caption_words)
                
                # Compute timing: start when first word appears, end when last word finishes
                if i < len(word_times):
                    on = word_times[i][0]
                else:
                    on = adj_start + (i / len(words)) * total_duration
                
                # End time: when the last word in this caption group finishes
                last_word_idx = min(i + word_count - 1, len(word_times) - 1)
                if last_word_idx < len(word_times):
                    off = word_times[last_word_idx][1]
                else:
                    # If we've run out of word times, use segment end
                    off = adj_end
                
                # Ensure minimum duration
                if off - on < self.min_visibility_sec:
                    off = on + self.min_visibility_sec
                
                # Clamp to segment boundaries
                on = max(adj_start, min(adj_end, on))
                off = max(adj_start, min(adj_end, off))
                
                # Ensure valid timing
                if off > on:
                    states.append(CaptionState(
                        text=caption_text,
                        on=on,
                        off=off,
                        seg_idx=seg.index,
                        y=260  # Default primary level
                    ))
                
                # Move to next group of words
                i += word_count
        
        # Sort by start time (stable sort on segment index)
        return sorted(states, key=lambda s: (s.on, s.seg_idx))
    
    def assign_caption_levels(self, states: List[CaptionState]) -> List[CaptionState]:
        """Assign vertical levels for overlapping captions (simplified for 1-3 word style)"""
        # For 1-3 word captions, we use a simpler approach:
        # All captions use the same Y position (primary level)
        # If captions overlap, we skip the overlapping ones to avoid clutter
        levels = []  # Track active captions
        
        for state in states:
            # Check for overlaps with existing captions
            has_overlap = False
            for level_state in levels:
                if not (state.off <= level_state.on or state.on >= level_state.off):
                    # Overlap detected
                    has_overlap = True
                    break
            
            if not has_overlap:
                state.y = 260  # Primary level
                levels.append(state)
            else:
                # Skip overlapping captions for cleaner display
                state.skip = True
        
        return states
    
    def wrap_text(self, text: str, max_chars: int = 28) -> str:
        """Soft-wrap text to max_chars per line (center-aligned later)"""
        words = text.split()
        lines, current = [], []
        
        for word in words:
            if len(' '.join(current + [word])) > max_chars:
                if current:  # Only add line if we have content
                    lines.append(' '.join(current))
                current = [word]
            else:
                current.append(word)
        
        if current:
            lines.append(' '.join(current))
        
        return '\n'.join(lines)


class FFmpegGenerator:
    """Generates FFmpeg filter scripts for progressive captions"""
    
    def __init__(self, font_file: str = "Poppins-Black.ttf"):
        self.font_file = font_file
    
    def escape_ffmpeg_text(self, text: str) -> str:
        """Escape text for FFmpeg drawtext filter"""
        # Escape special characters that need escaping in FFmpeg
        text = text.replace('\\', '\\\\')
        text = text.replace(':', '\\:')
        text = text.replace(',', '\\,')
        text = text.replace('%', '\\%')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        text = text.replace('=', '\\=')
        text = text.replace('#', '\\#')
        text = text.replace(';', '\\;')
        # Escape single quotes used inside drawtext text='...'
        text = text.replace("'", "\\'")
        text = text.replace('\n', '\\n')
        return text
    
    def generate_filter_script(self, states: List[CaptionState], 
                              output_file: str,
                              video_width: int = 1080,
                              video_height: int = 1920) -> None:
        """Generate FFmpeg filter script for progressive captions"""
        
        # Build the entire filter as a single line
        # IMPORTANT: no space between label and first filter
        filter_parts = ["[0:v]format=yuv420p"]
        
        # Add background box
        filter_parts.append("drawbox=x=0:y=h-340:w=iw:h=320:color=black@0.65:t=fill")
        
        # Add all drawtext filters
        for state in states:
            if state.skip:
                continue
            
            # Wrap and escape text
            wrapped_text = CaptionGenerator().wrap_text(state.text)
            # Replace newlines with spaces for FFmpeg compatibility
            wrapped_text = wrapped_text.replace('\n', ' ')
            escaped_text = self.escape_ffmpeg_text(wrapped_text)
            
            # Build drawtext filter
            drawtext_filter = (
                f"drawtext=fontfile='{self.font_file}':"
                f"text='{escaped_text}':"
                f"enable='between(t,{state.on:.3f},{state.off:.3f})':"
                f"x=(w-tw)/2:y=h-{state.y}:"
                f"fontsize=54:fontcolor=white:"
                f"box=1:boxcolor=black@0.6:boxborderw=20"
            )
            
            filter_parts.append(drawtext_filter)
        
        # Join all parts with commas and add output label (with a space)
        filter_string = ",".join(filter_parts) + " [v]"
        
        # Write the script as a single line
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(filter_string)


class MoviePyGenerator:
    """Generates MoviePy text clips for progressive captions"""
    
    def __init__(self, font_file: str = "Poppins-Black.ttf"):
        self.font_file = font_file
    
    def generate_text_clips(self, states: List[CaptionState],
                           video_width: int = 1080,
                           video_height: int = 1920) -> List[Dict]:
        """Generate MoviePy text clip specifications"""
        text_clips = []
        
        for state in states:
            if state.skip:
                continue
            
            # Wrap text
            wrapped_text = CaptionGenerator().wrap_text(state.text)
            
            text_clips.append({
                'text': wrapped_text,
                'start_time': state.on,
                'end_time': state.off,
                'position': ('center', video_height - state.y),
                'font_size': 54,
                'font_color': 'white',
                'font_file': self.font_file,
                'bg_color': 'black',
                'bg_opacity': 0.6
            })
        
        return text_clips


def main():
    """Main function demonstrating the progressive captions algorithm"""
    
    # Example usage
    subtitle_file = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass"
    
    if not os.path.exists(subtitle_file):
        print(f"Subtitle file not found: {subtitle_file}")
        return
    
    # Parse subtitles
    print("Parsing subtitles...")
    segments = SubtitleParser.parse_subtitles(subtitle_file)
    print(f"Found {len(segments)} subtitle segments")
    
    # Generate caption states
    print("Generating caption states...")
    generator = CaptionGenerator()
    states = generator.generate_states(segments, clip_start=0.0, clip_end=33.23)
    states = generator.assign_caption_levels(states)
    
    print(f"Generated {len([s for s in states if not s.skip])} caption states")
    
    # Show first few states
    print("\nFirst 5 caption states:")
    for i, state in enumerate(states[:5]):
        if not state.skip:
            print(f"  {i+1}. '{state.text}' | {state.on:.3f}s - {state.off:.3f}s | y={state.y}")
    
    # Generate FFmpeg filter script
    print("\nGenerating FFmpeg filter script...")
    ffmpeg_gen = FFmpegGenerator()
    ffmpeg_gen.generate_filter_script(states, "filter_script.txt")
    print("FFmpeg filter script saved to 'filter_script.txt'")
    
    # Generate MoviePy specifications
    print("Generating MoviePy text clip specifications...")
    moviepy_gen = MoviePyGenerator()
    text_clips = moviepy_gen.generate_text_clips(states)
    print(f"Generated {len(text_clips)} MoviePy text clip specifications")
    
    # Save MoviePy specs to JSON
    with open("moviepy_specs.json", 'w', encoding='utf-8') as f:
        json.dump(text_clips, f, indent=2, ensure_ascii=False)
    print("MoviePy specifications saved to 'moviepy_specs.json'")
    
    # Generate usage instructions
    print("\n" + "="*60)
    print("USAGE INSTRUCTIONS")
    print("="*60)
    print("\n1. FFmpeg (Recommended for production):")
    print("   ffmpeg -i ClipV1.mp4 -filter_complex_script filter_script.txt \\")
    print("          -map \"[v]\" -map 0:a -c:a copy output_with_captions.mp4")
    print("\n2. MoviePy (Python implementation):")
    print("   Use the specifications in 'moviepy_specs.json' to create text clips")
    print("   and composite them with your video.")
    print("\n3. Custom timing adjustments:")
    print("   Modify lead_in_ms, min_visibility_ms, and overlap_ms in CaptionGenerator")
    print("   to fine-tune the caption behavior.")


if __name__ == "__main__":
    main()
