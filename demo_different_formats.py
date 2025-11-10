#!/usr/bin/env python3
"""
Demonstration: Progressive Captions with Different Subtitle Formats

This script demonstrates how the progressive captions algorithm works
with ASS, SRT, and VTT subtitle files.
"""

import os
from progressive_captions import SubtitleParser, CaptionGenerator, FFmpegGenerator

def demo_subtitle_formats():
    """Demonstrate the algorithm with different subtitle formats"""
    
    print("=" * 70)
    print("PROGRESSIVE CAPTIONS - MULTI-FORMAT DEMONSTRATION")
    print("=" * 70)
    
    # Available subtitle files
    subtitle_files = [
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass",
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.srt", 
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.vtt"
    ]
    
    for subtitle_file in subtitle_files:
        if not os.path.exists(subtitle_file):
            print(f"⚠️  File not found: {subtitle_file}")
            continue
            
        print(f"\n📁 Processing: {subtitle_file}")
        print("-" * 50)
        
        try:
            # Parse subtitles
            segments = SubtitleParser.parse_subtitles(subtitle_file)
            print(f"✅ Parsed {len(segments)} subtitle segments")
            
            # Show first few segments
            print("\n📝 First 3 segments:")
            for i, seg in enumerate(segments[:3]):
                print(f"  {i+1}. [{seg.start:.3f}s - {seg.end:.3f}s] '{seg.text}'")
            
            # Generate caption states
            generator = CaptionGenerator()
            states = generator.generate_states(segments, clip_start=0.0, clip_end=33.23)
            states = generator.assign_caption_levels(states)
            
            active_states = [s for s in states if not s.skip]
            print(f"\n🎬 Generated {len(active_states)} caption states")
            
            # Show timing statistics
            if active_states:
                total_duration = sum(s.off - s.on for s in active_states)
                avg_duration = total_duration / len(active_states)
                min_duration = min(s.off - s.on for s in active_states)
                max_duration = max(s.off - s.on for s in active_states)
                
                print(f"📊 Timing Statistics:")
                print(f"  - Total caption time: {total_duration:.3f}s")
                print(f"  - Average duration: {avg_duration:.3f}s")
                print(f"  - Duration range: {min_duration:.3f}s - {max_duration:.3f}s")
                print(f"  - Video coverage: {(total_duration / 33.23) * 100:.1f}%")
            
            # Show first few caption states
            print(f"\n🎯 First 5 caption states:")
            for i, state in enumerate(active_states[:5]):
                duration = state.off - state.on
                level = "Primary" if state.y == 260 else "Secondary"
                print(f"  {i+1}. '{state.text}' | {state.on:.3f}s - {state.off:.3f}s | {level}")
            
            # Generate FFmpeg filter script
            output_script = f"filter_{os.path.splitext(subtitle_file)[0]}.txt"
            ffmpeg_gen = FFmpegGenerator()
            ffmpeg_gen.generate_filter_script(states, output_script)
            print(f"\n💾 FFmpeg filter script saved to: {output_script}")
            
            # Show usage command
            print(f"\n🚀 Usage command:")
            print(f"ffmpeg -i ClipV1.mp4 -filter_complex_script {output_script} \\")
            print(f"       -map \"[v]\" -map 0:a -c:a copy output_{os.path.splitext(subtitle_file)[0]}.mp4")
            
        except Exception as e:
            print(f"❌ Error processing {subtitle_file}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETED!")
    print("=" * 70)
    print("\n📋 Summary of generated files:")
    
    # List all generated filter scripts
    filter_scripts = [f for f in os.listdir(".") if f.startswith("filter_") and f.endswith(".txt")]
    for script in filter_scripts:
        print(f"  - {script}")
    
    print(f"\n🎥 To render with captions, use any of the filter scripts above.")
    print(f"📚 See README.md for detailed usage instructions.")
    print(f"🧪 Run test_example.py for algorithm validation.")

def compare_formats():
    """Compare the output of different subtitle formats"""
    
    print("\n" + "=" * 70)
    print("FORMAT COMPARISON ANALYSIS")
    print("=" * 70)
    
    subtitle_files = [
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.ass",
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.srt", 
        "clip_1_6613faa6-b6ce-410d-885b-0f0ba58390c3.vtt"
    ]
    
    format_data = {}
    
    for subtitle_file in subtitle_files:
        if not os.path.exists(subtitle_file):
            continue
            
        try:
            segments = SubtitleParser.parse_subtitles(subtitle_file)
            generator = CaptionGenerator()
            states = generator.generate_states(segments, clip_start=0.0, clip_end=33.23)
            states = generator.assign_caption_levels(states)
            
            active_states = [s for s in states if not s.skip]
            
            format_data[subtitle_file] = {
                'segments': len(segments),
                'states': len(active_states),
                'total_duration': sum(s.off - s.on for s in active_states),
                'avg_duration': sum(s.off - s.on for s in active_states) / len(active_states) if active_states else 0
            }
            
        except Exception as e:
            print(f"❌ Error processing {subtitle_file}: {str(e)}")
    
    if format_data:
        print("\n📊 Format Comparison Table:")
        print("-" * 80)
        print(f"{'Format':<15} {'Segments':<10} {'States':<8} {'Total Time':<12} {'Avg Duration':<12}")
        print("-" * 80)
        
        for format_name, data in format_data.items():
            format_short = os.path.splitext(format_name)[1].upper()
            print(f"{format_short:<15} {data['segments']:<10} {data['states']:<8} "
                  f"{data['total_duration']:<12.3f} {data['avg_duration']:<12.3f}")
        
        print("-" * 80)
        
        # Find the format with most content
        best_format = max(format_data.items(), key=lambda x: x[1]['states'])
        print(f"\n🏆 Best format: {os.path.splitext(best_format[0])[1].upper()}")
        print(f"   - Most caption states: {best_format[1]['states']}")
        print(f"   - Highest coverage: {(best_format[1]['total_duration'] / 33.23) * 100:.1f}%")

if __name__ == "__main__":
    demo_subtitle_formats()
    compare_formats()
