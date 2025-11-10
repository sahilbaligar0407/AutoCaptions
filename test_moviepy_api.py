#!/usr/bin/env python3
"""
Test MoviePy API to see what methods are available
"""

try:
    from moviepy import VideoClip, TextClip
    print("MoviePy imported successfully")
    
    # Check VideoClip methods
    print("\nVideoClip methods:")
    vc_methods = [m for m in dir(VideoClip) if not m.startswith('_')]
    print(vc_methods[:20])  # Show first 20
    
    # Check for timing methods
    timing_methods = [m for m in vc_methods if any(word in m.lower() for word in ['start', 'time', 'duration', 'position'])]
    print(f"\nTiming/Position methods: {timing_methods}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
