#!/usr/bin/env python3
"""
Simple FFmpeg Test for Progressive Captions
This script tests FFmpeg rendering with just a few caption states
"""

import os
import sys
import subprocess
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from progressive_captions import SubtitleParser, CaptionGenerator, FFmpegGenerator

def test_simple_ffmpeg():
    """Test FFmpeg with simplified captions"""
    
    print("=== Simple FFmpeg Test ===")
    
    # Parse subtitles
    subtitle_file = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass"
    segments = SubtitleParser.parse_subtitles(subtitle_file)
    print(f"Found {len(segments)} subtitle segments")
    
    # Take only first 2 segments for testing
    test_segments = segments[:2]
    print(f"Testing with {len(test_segments)} segments")
    
    # Generate caption states
    video_duration = 33.233
    generator = CaptionGenerator()
    states = generator.generate_states(test_segments, clip_start=0.0, clip_end=video_duration)
    
    # Filter to only first 3 states for testing
    test_states = [s for s in states if not s.skip][:3]
    print(f"Generated {len(test_states)} test caption states")
    
    # Generate FFmpeg filter
    ffmpeg_gen = FFmpegGenerator("Poppins-Black.ttf")
    filter_script = "temp/simple_test_filter.txt"
    ffmpeg_gen.generate_filter_script(test_states, filter_script)
    
    print(f"Filter script saved to: {filter_script}")
    
    # Read and display filter content
    with open(filter_script, 'r') as f:
        filter_content = f.read()
    
    print(f"Filter content (first 200 chars): {filter_content[:200]}...")
    
    # Test FFmpeg command
    video_input = "ClipV1.mp4"
    output_file = "outputs/simple_test_output.mp4"
    
    # Ensure output directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Build FFmpeg command using filter script file
    cmd = [
        'ffmpeg', '-y',
        '-i', video_input,
        '-filter_complex', filter_content,
        '-map', '[v]',
        '-map', '0:a',
        '-c:a', 'copy',
        output_file
    ]
    
    print(f"FFmpeg command: ffmpeg -y -i {video_input} -filter_complex <script> -map [v] -map 0:a -c:a copy {output_file}")
    
    try:
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ FFmpeg test successful!")
        print(f"Output file: {output_file}")
        
        # Check file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"Output file size: {size} bytes ({size/1024/1024:.2f} MB)")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed with exit code {e.returncode}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_ffmpeg()
