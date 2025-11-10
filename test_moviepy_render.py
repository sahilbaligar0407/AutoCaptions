#!/usr/bin/env python3
"""
MoviePy Rendering Test for Progressive Builder Captions
This script tests the actual rendering of progressive captions using MoviePy.
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from progressive_captions import SubtitleParser, CaptionGenerator, MoviePyGenerator

def test_moviepy_render():
    """Test MoviePy rendering with progressive captions"""
    
    print("=== MoviePy Rendering Test ===")
    
    try:
        from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
        print("✅ MoviePy imports successful")
    except ImportError as e:
        print(f"❌ MoviePy import failed: {e}")
        return
    
    # Parse subtitles
    subtitle_file = "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass"
    segments = SubtitleParser.parse_subtitles(subtitle_file)
    print(f"Found {len(segments)} subtitle segments")
    
    # Take only first 3 segments for testing (to keep render time reasonable)
    test_segments = segments[:3]
    print(f"Testing with {len(test_segments)} segments")
    
    # Generate caption states
    video_duration = 33.233
    generator = CaptionGenerator()
    states = generator.generate_states(test_segments, clip_start=0.0, clip_end=video_duration)
    
    # Filter out skipped states and limit to first 20 for testing
    valid_states = [s for s in states if not s.skip][:20]
    print(f"Generated {len(valid_states)} valid caption states for rendering")
    
    # Load video
    print("Loading video...")
    video = VideoFileClip("ClipV1.mp4")
    print(f"✅ Video loaded: {video.duration:.3f}s, {video.size[0]}x{video.size[1]}")
    
    # Create background box for captions
    print("Creating background box...")
    bg_clip = ColorClip(size=(1080, 320), color=(0, 0, 0, 0.65))
    bg_clip = bg_clip.with_position(('center', 'bottom')).with_duration(video.duration)
    
    # Create text clips
    print("Creating text clips...")
    text_clips = []
    
    for i, state in enumerate(valid_states):
        if i % 10 == 0:
            print(f"  Processing caption {i+1}/{len(valid_states)}")
        
        # Create text clip
        text_clip = TextClip(
            state.text,
            fontsize=54,
            color='white',
            font='Arial',  # Use Arial as fallback
            stroke_color='black',
            stroke_width=2
        )
        
        # Position and time the clip
        text_clip = text_clip.with_position(('center', video.size[1] - state.y))
        text_clip = text_clip.with_start(state.on).with_end(state.off)
        
        text_clips.append(text_clip)
    
    print(f"✅ Created {len(text_clips)} text clips")
    
    # Composite all clips
    print("Compositing video...")
    final_video = CompositeVideoClip([video, bg_clip] + text_clips)
    
    # Ensure output directory exists
    os.makedirs("outputs", exist_ok=True)
    output_file = "outputs/Clip_MoviePy_V1.mp4"
    
    # Write output
    print(f"Rendering to {output_file}...")
    final_video.write_videofile(
        output_file,
        fps=video.fps,
        codec='libx264',
        audio_codec='aac',
        verbose=False,
        logger=None
    )
    
    print(f"✅ Rendering complete: {output_file}")
    
    # Check file size
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"Output file size: {size} bytes ({size/1024/1024:.2f} MB)")
        
        if size > 1024*1024:  # > 1 MB
            print("✅ File size check passed (> 1 MB)")
        else:
            print("❌ File size check failed (≤ 1 MB)")
    
    # Clean up
    video.close()
    bg_clip.close()
    for clip in text_clips:
        clip.close()
    final_video.close()
    
    print("\n🎉 MoviePy rendering test successful!")

if __name__ == "__main__":
    test_moviepy_render()
