# Progressive Builder Captions Algorithm

A sophisticated algorithm that renders progressive "builder" captions for 9:16 videos with precise timing, auto-wrapping, and professional layout.

## 🎯 Features

- **Progressive Word Building**: Captions build up to 5 words, then slide forward one word at a time
- **Precise Timing**: 180ms lead-in, 120ms minimum visibility, 50ms overlap between states
- **Smart Layout**: Auto-wrapping within 90% width, center-aligned, dual-level positioning
- **Multi-Format Support**: Parses ASS, SRT, and VTT subtitle files
- **Dual Output**: Generates both FFmpeg filter scripts and MoviePy specifications
- **Professional Styling**: 54px white text with black outline, semi-transparent background

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Required Python packages
pip install moviepy

# FFmpeg (for video rendering)
# Download from: https://ffmpeg.org/download.html
```

### 2. Run the Algorithm

```bash
# Generate captions from your subtitle file
python progressive_captions.py

# This will create:
# - filter_script.txt (FFmpeg filter script)
# - moviepy_specs.json (MoviePy text clip specifications)
```

### 3. Render with FFmpeg (Recommended)

```bash
# Apply captions to your video
ffmpeg -i ClipV1.mp4 -filter_complex_script filter_script.txt \
       -map "[v]" -map 0:a -c:a copy output_with_captions.mp4
```

### 4. Render with MoviePy (Python)

```python
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json

# Load video
video = VideoFileClip("ClipV1.mp4")

# Load caption specifications
with open("moviepy_specs.json", "r") as f:
    caption_specs = json.load(f)

# Create text clips
text_clips = []
for spec in caption_specs:
    clip = TextClip(
        spec['text'],
        fontsize=spec['font_size'],
        color=spec['font_color'],
        font=spec['font_file']
    ).set_position(spec['position']).set_duration(
        spec['end_time'] - spec['start_time']
    ).set_start(spec['start_time'])
    
    text_clips.append(clip)

# Composite and render
final_video = CompositeVideoClip([video] + text_clips)
final_video.write_videofile("output_with_captions.mp4")
```

## 📁 File Structure

```
AutoCaptions/
├── progressive_captions.py      # Main algorithm implementation
├── test_example.py             # Test script with example
├── PROGRESSIVE_CAPTIONS_SPEC.md # Detailed specification
├── README.md                   # This file
├── filter_script.txt           # Generated FFmpeg filter script
├── moviepy_specs.json         # Generated MoviePy specifications
├── ClipV1.mp4                 # Your video file
├── *.ass, *.srt, *.vtt        # Subtitle files
└── *.ttf                      # Font files
```

## ⚙️ Configuration

### Timing Parameters

```python
generator = CaptionGenerator(
    lead_in_ms=180,        # Lead-in time in milliseconds
    min_visibility_ms=120, # Minimum visibility per state
    overlap_ms=50,         # Overlap between states
    max_words=5            # Maximum words in sliding window
)
```

### Layout Parameters

```python
# Video dimensions (9:16 aspect ratio)
video_width = 1080
video_height = 1920

# Caption positioning
primary_y = 260    # Primary caption y-offset from bottom
secondary_y = 320  # Secondary caption y-offset from bottom
caption_height = 320  # Background box height

# Text formatting
font_size = 54
max_chars_per_line = 28
safe_width_ratio = 0.9  # 90% of video width
```

## 🔧 How It Works

### 1. Subtitle Parsing
- **ASS**: Parses Dialogue lines from [Events] section
- **SRT**: Parses numbered blocks with timecode → text format  
- **VTT**: Parses WEBVTT blocks with timecode → text format

### 2. Word Timing Synthesis
- Splits text into individual words
- Synthesizes uniform word timings with constraints
- Enforces minimum 120ms per word
- Clamps to segment boundaries

### 3. Caption State Generation
- Creates sliding 5-word window captions
- Applies 180ms lead-in (capped at segment start)
- Ensures 50ms overlap between consecutive states
- Maintains minimum 120ms visibility per state

### 4. Layout & Level Assignment
- **Primary Level**: y = h-260 (260px from bottom)
- **Secondary Level**: y = h-320 (320px from bottom)
- Handles overlapping captions with dual-level layout
- Skips captions with >2 overlaps

### 5. Text Wrapping
- Soft-wraps text to maximum 28 characters per line
- Maintains 90% width safety margin
- Center-aligned in rendering layer

## 📊 Example Output

**Input**: "This room is like a red carpet Hollywood hallway." (9 words)

**Generated States**:
1. "This" (0.000s - 0.232s)
2. "This room" (0.102s - 0.513s) 
3. "This room is" (0.383s - 0.795s)
4. "This room is like" (0.665s - 1.077s)
5. "This room is like a" (0.947s - 1.358s)
6. "room is like a red" (1.228s - 1.640s)
7. "is like a red carpet" (1.510s - 1.922s)
8. "like a red carpet Hollywood" (1.792s - 2.203s)
9. "a red carpet Hollywood hallway." (2.073s - 2.535s)

## 🎨 Visual Features

- **Background**: 320px height semi-transparent black box (65% opacity)
- **Text**: 54px white text with black outline (20px border width)
- **Positioning**: Center-aligned horizontally, dual-level vertically
- **Font**: Poppins-Black.ttf (with system font fallback)
- **Wrapping**: Automatic line breaks at 28 characters

## 🧪 Testing

Run the test script to validate the algorithm:

```bash
python test_example.py
```

This will:
- Test the progressive caption generation
- Validate timing constraints
- Check text wrapping
- Verify level assignment
- Provide compliance reports

## 📈 Performance

- **Parsing**: O(n) where n = number of subtitle segments
- **State Generation**: O(m × w) where m = segments, w = words per segment
- **Level Assignment**: O(s²) where s = number of states
- **Memory Usage**: ~1-5 MB for typical video caption data
- **Rendering**: Hardware-accelerated with FFmpeg, CPU-based with MoviePy

## 🔍 Troubleshooting

### Common Issues

1. **Font Not Found**
   - Ensure Poppins-Black.ttf is in the same directory
   - Or modify the font path in the code

2. **FFmpeg Command Too Long**
   - The filter script is automatically written to a file
   - Use `-filter_complex_script` instead of `-filter_complex`

3. **Timing Issues**
   - Check subtitle file format and encoding
   - Verify start/end times are valid
   - Adjust timing parameters if needed

4. **Text Overflow**
   - Reduce `max_chars_per_line` parameter
   - Check font size and video dimensions

### Debug Mode

Enable verbose output by modifying the main script:

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Advanced Usage

### Custom Subtitle Processing

```python
from progressive_captions import SubtitleParser, CaptionGenerator

# Parse custom subtitle file
segments = SubtitleParser.parse_subtitles("my_subtitles.srt")

# Custom timing parameters
generator = CaptionGenerator(
    lead_in_ms=200,        # 200ms lead-in
    min_visibility_ms=150, # 150ms minimum visibility
    overlap_ms=75,         # 75ms overlap
    max_words=6            # 6-word sliding window
)

# Generate states for specific time range
states = generator.generate_states(segments, clip_start=10.0, clip_end=30.0)
```

### Batch Processing

```python
import glob

# Process multiple subtitle files
subtitle_files = glob.glob("*.ass") + glob.glob("*.srt") + glob.glob("*.vtt")

for subtitle_file in subtitle_files:
    print(f"Processing {subtitle_file}...")
    
    # Parse and generate captions
    segments = SubtitleParser.parse_subtitles(subtitle_file)
    generator = CaptionGenerator()
    states = generator.generate_states(segments)
    
    # Generate output files
    output_name = f"captions_{os.path.splitext(subtitle_file)[0]}"
    ffmpeg_gen = FFmpegGenerator()
    ffmpeg_gen.generate_filter_script(states, f"{output_name}_filter.txt")
```

## 📚 API Reference

### Core Classes

- **`SubtitleParser`**: Unified parser for ASS, SRT, and VTT formats
- **`CaptionGenerator`**: Generates progressive caption states with timing
- **`FFmpegGenerator`**: Creates FFmpeg filter scripts
- **`MoviePyGenerator`**: Generates MoviePy text clip specifications

### Key Methods

- **`parse_subtitles(file_path)`**: Parse any subtitle format
- **`generate_states(segments, clip_start, clip_end)`**: Generate caption states
- **`assign_caption_levels(states)`**: Assign vertical positioning
- **`generate_filter_script(states, output_file)`**: Create FFmpeg script
- **`generate_text_clips(states)`**: Create MoviePy specifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FFmpeg**: For powerful video processing capabilities
- **MoviePy**: For Python-based video editing
- **Poppins Font**: For beautiful typography
- **Subtitle Standards**: ASS, SRT, and VTT format specifications

## 📞 Support

For questions, issues, or contributions:

1. Check the troubleshooting section
2. Review the specification document
3. Run the test script
4. Open an issue on GitHub

---

**Happy Captioning! 🎬✨**
