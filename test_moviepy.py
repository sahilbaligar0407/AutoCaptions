#!/usr/bin/env python3
"""
MoviePy Test for Progressive Builder Captions
This script tests the progressive captions algorithm using MoviePy rendering.
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from progressive_captions import SubtitleParser, CaptionGenerator, MoviePyGenerator

def test_moviepy():
    """Test MoviePy rendering with progressive captions"""
    
    print("=== MoviePy Progressive Captions Test ===")
    
    # Parse subtitles
    subtitle_file = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass"
    segments = SubtitleParser.parse_subtitles(subtitle_file)
    print(f"Found {len(segments)} subtitle segments")
    
    # Generate caption states
    video_duration = 33.233
    generator = CaptionGenerator()
    states = generator.generate_states(segments, clip_start=0.0, clip_end=video_duration)
    
    # Filter out skipped states
    valid_states = [s for s in states if not s.skip]
    print(f"Generated {len(valid_states)} valid caption states")
    
    # Generate MoviePy text clips
    moviepy_gen = MoviePyGenerator("Poppins-Black.ttf")
    text_clips = moviepy_gen.generate_text_clips(valid_states)
    
    print(f"Generated {len(text_clips)} MoviePy text clips")
    
    # Display first few text clips
    print("\nFirst 3 text clips:")
    for i, clip in enumerate(text_clips[:3]):
        print(f"  {i+1}. '{clip['text']}' at {clip['start_time']:.3f}s - {clip['end_time']:.3f}s")
    
    # Save MoviePy specifications
    output_file = "temp/moviepy_specs.json"
    os.makedirs("temp", exist_ok=True)
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(text_clips, f, indent=2, ensure_ascii=False)
    
    print(f"\nMoviePy specifications saved to: {output_file}")
    
    # Check if MoviePy is available
    try:
        import moviepy
        print(f"✅ MoviePy {moviepy.__version__} is available")
        
        # Try to create a simple test
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
        
        print("Testing MoviePy video loading...")
        video = VideoFileClip("ClipV1.mp4")
        print(f"✅ Video loaded: {video.duration:.3f}s, {video.size[0]}x{video.size[1]}")
        
        # Create a simple text clip
        print("Testing MoviePy text clip creation...")
        text_clip = TextClip("Test Caption", fontsize=54, color='white', font='Arial')
        print(f"✅ Text clip created: {text_clip.size}")
        
        # Clean up
        video.close()
        text_clip.close()
        
        print("\n🎉 MoviePy test successful! MoviePy is ready for rendering.")
        
    except ImportError:
        print("❌ MoviePy is not installed. Install with: pip install moviepy")
    except Exception as e:
        print(f"❌ MoviePy test failed: {e}")

if __name__ == "__main__":
    test_moviepy()
