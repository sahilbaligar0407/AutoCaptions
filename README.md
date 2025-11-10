# AutoCaptions - 1-3 Word Progressive Captions

A sophisticated algorithm that renders progressive 1-3 word captions for 9:16 videos with precise timing, auto-wrapping, professional layout, and dynamic styling.

## 🎯 Features

- **1-3 Word Captions**: Rate-aware adaptive chunking (1-2 words for fast speech, 2-3 words for slow speech)
- **Precise Timing**: 200ms minimum visibility per caption, smart timing based on speaking rate (words per second)
- **Smart Layout**: Auto-wrapping within 90% width, center-aligned, professional positioning
- **Multi-Format Support**: Parses ASS, SRT, and VTT subtitle files
- **Dynamic Styling**: Automatic font and color styling based on content
  - **Wow Words** (gosh, last, secret, etc.): ExtraBold font with yellow color
  - **Italic Words** (like, feel, should, etc.): BlackItalic font with white color
  - **Default**: Black font with white color
- **Overlap Prevention**: Intelligent overlap detection and resolution
- **MoviePy Rendering**: Python-based video rendering with styled captions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Required Python packages
pip install moviepy
```

### 2. Prepare Your Files

Place your video files in the `uploads/` folder and subtitle files (`.ass`, `.srt`, or `.vtt`) in the `subs/` folder (or specify paths directly).

### 3. Run the Caption Generator

```bash
# Generate captioned video with MoviePy
python AutoCaptions/tools/run_builder_moviepy.py \
    --video AutoCaptions/uploads/your_video.mp4 \
    --subs AutoCaptions/subs/your_subtitles.ass \
    --out AutoCaptions/outputs/output_video.mp4 \
    --log AutoCaptions/logs/output_video.log
```

The output video will be saved to `outputs/` and logs will be saved to `logs/`.

## 📁 File Structure

```
AutoCaptions/
├── progressive_captions.py      # Core algorithm implementation
├── tools/
│   └── run_builder_moviepy.py  # MoviePy rendering tool
├── uploads/                     # Input video files
├── outputs/                     # Generated captioned videos
├── logs/                        # Processing logs
├── subs/                        # Subtitle files (.ass, .srt, .vtt)
├── Poppins-Black.ttf           # Default font
├── Poppins-Bold.ttf            # Bold font variant
├── Poppins-ExtraBold.ttf       # ExtraBold font for wow words
├── Poppins-BlackItalic.ttf     # Italic font for italic words
├── Poppins-BoldItalic.ttf      # BoldItalic font variant
├── README.md                   # This file
├── PROGRESSIVE_CAPTIONS_SPEC.md # Detailed specification
├── IMPLEMENTATION_SUMMARY.md   # Implementation details
└── LICENSE                     # License file
```

## ⚙️ Configuration

### Timing Parameters

The caption generator uses the following default parameters:

```python
generator = CaptionGenerator(
    min_visibility_ms=200,      # Minimum 200ms visibility per caption
    min_words_per_caption=1,    # Minimum 1 word per caption
    max_words_per_caption=3     # Maximum 3 words per caption
)
```

### Styling Configuration

**Wow Words** (yellow, ExtraBold):
- Words like: gosh, last, secret, revealed, exclusive, viral, epic, amazing, incredible, etc.
- Font: Poppins-ExtraBold.ttf
- Color: Yellow

**Italic Words** (white, Italic):
- Words like: like, feel, think, seem, maybe, perhaps, probably, might, could, should, etc.
- Font: Poppins-BlackItalic.ttf or Poppins-BoldItalic.ttf
- Color: White

**Default Captions** (white, Black):
- Font: Poppins-Black.ttf
- Color: White

## 🔧 How It Works

### 1. Subtitle Parsing
- **ASS**: Parses Dialogue lines from [Events] section
- **SRT**: Parses numbered blocks with timecode → text format  
- **VTT**: Parses WEBVTT blocks with timecode → text format

### 2. Word Timing Synthesis
- Splits text into individual words
- Synthesizes uniform word timings with constraints
- Enforces minimum 200ms per word group
- Clamps to segment boundaries

### 3. Caption State Generation (Rate-Aware)
- **Speaking Rate Detection**: Calculates words per second (wps) for each segment
- **Adaptive Chunk Sizing**:
  - **Fast speech** (>3.2 wps): 1-2 words per chunk (prefer 2)
  - **Normal speech** (2.2-3.2 wps): 2 words per chunk (occasionally 3)
  - **Slow speech** (<2.2 wps): 2-3 words per chunk (prefer 3)
- **Smart Grouping**: Prefers 2-word chunks as default for optimal rhythm and readability
- **Line Length Safety**: 3-word chunks only when total ≤20 characters to prevent wrapping
- **Timing Constraints**: Maintains minimum 200ms visibility per caption
- **Phrase Integrity**: Keeps related words together (e.g., "red carpet", "look at")

### 4. Layout & Level Assignment
- **Primary Level**: y = h-260 (260px from bottom)
- **Secondary Level**: y = h-320 (320px from bottom)
- Handles overlapping captions with level assignment
- Skips captions that would cause visual overlaps

### 5. Dynamic Styling
- Detects wow words and applies ExtraBold font with yellow color
- Detects italic words and applies Italic font with white color
- Applies default styling to regular captions
- Styles entire 1-3 word caption groups for clean appearance

### 6. Text Wrapping
- Soft-wraps text to maximum 28 characters per line
- Maintains 90% width safety margin
- Center-aligned in rendering layer

## 📊 Example Output

**Input**: "This room is like a red carpet Hollywood hallway." (9 words)

**Generated Captions** (example for normal speech rate):
1. "This room" (2 words, default style)
2. "is like" (2 words, italic style - contains "like")
3. "a red" (2 words, default style)
4. "carpet Hollywood" (2 words, default style)
5. "hallway." (1 word, default style)

**For slow speech**, you might see:
1. "This room is" (3 words, default style)
2. "like a red" (3 words, italic style)
3. "carpet Hollywood" (2 words, default style)
4. "hallway." (1 word, default style)

Note: The actual output adapts to speaking rate (words per second), with 2-word chunks as the default for optimal readability.

## 🎨 Visual Features

- **Background**: Semi-transparent black box (if using background)
- **Text**: 54px text with black outline (2px stroke)
- **Positioning**: Center-aligned horizontally, dual-level vertically
- **Fonts**: Poppins font family (Black, Bold, ExtraBold, BlackItalic, BoldItalic)
- **Colors**: White (default, italic), Yellow (wow words)
- **Wrapping**: Automatic line breaks at 28 characters
- **Padding**: Generous padding to prevent text clipping

## 🔍 Troubleshooting

### Common Issues

1. **Font Not Found**
   - Ensure Poppins font files are in the AutoCaptions/ directory
   - The script will fall back to system fonts if Poppins fonts are not found

2. **Video Not Found**
   - Check that the video file path is correct
   - Ensure the video file exists in the uploads/ folder or provide full path

3. **Subtitle File Not Found**
   - Check that the subtitle file path is correct
   - Ensure the subtitle file exists and is in a supported format (.ass, .srt, .vtt)

4. **Timing Issues**
   - Check subtitle file format and encoding
   - Verify start/end times are valid
   - Check logs for timing warnings

5. **Text Overflow**
   - Text is automatically wrapped at 28 characters
   - Check logs for width warnings
   - Adjust font size if needed (default: 54px)

6. **Caption Overlaps**
   - The system automatically detects and resolves overlaps
   - Check logs for overlap detection messages
   - Some captions may be skipped to prevent visual overlaps

### Debug Mode

Enable verbose logging by checking the log file:

```bash
# View log file
cat AutoCaptions/logs/output_video.log
```

## 🚀 Advanced Usage

### Custom Timing Parameters

You can modify the timing parameters in `progressive_captions.py`:

```python
generator = CaptionGenerator(
    min_visibility_ms=250,      # Increase minimum visibility
    min_words_per_caption=1,    # Keep minimum 1 word
    max_words_per_caption=3     # Keep maximum 3 words
)
```

### Custom Styling

Modify the wow words and italic words lists in `tools/run_builder_moviepy.py`:

```python
def get_wow_words():
    """Get list of 'wow' words that should use Poppins-ExtraBold font with special colors"""
    return {
        'wow', 'shocking', 'unbelievable', 'insane', 'crazy', ...
        # Add your own wow words here
    }

def get_italic_words():
    """Get list of words that should be italicized"""
    return {
        'like', 'feel', 'think', 'seem', ...
        # Add your own italic words here
    }
```

### Batch Processing

Process multiple videos with a script:

```bash
#!/bin/bash
for video in AutoCaptions/uploads/*.mp4; do
    basename=$(basename "$video" .mp4)
    python AutoCaptions/tools/run_builder_moviepy.py \
        --video "$video" \
        --subs "AutoCaptions/subs/${basename}.ass" \
        --out "AutoCaptions/outputs/${basename}_captioned.mp4" \
        --log "AutoCaptions/logs/${basename}.log"
done
```

## 📚 API Reference

### Core Classes

- **`SubtitleParser`**: Unified parser for ASS, SRT, and VTT formats
- **`CaptionGenerator`**: Generates 1-3 word caption states with timing
- **`MoviePyGenerator`**: Creates MoviePy text clip specifications

### Key Methods

- **`parse_subtitles(file_path)`**: Parse any subtitle format
- **`generate_states(segments, clip_start, clip_end)`**: Generate caption states
- **`assign_caption_levels(states)`**: Assign vertical positioning
- **`generate_text_clips(states)`**: Create MoviePy specifications

## 📈 Performance

- **Parsing**: O(n) where n = number of subtitle segments
- **State Generation**: O(m × w) where m = segments, w = words per segment
- **Level Assignment**: O(s²) where s = number of states
- **Memory Usage**: ~1-5 MB for typical video caption data
- **Rendering**: CPU-based with MoviePy (can be slow for long videos)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Test with sample videos
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MoviePy**: For Python-based video editing
- **Poppins Font**: For beautiful typography
- **Subtitle Standards**: ASS, SRT, and VTT format specifications

## 📞 Support

For questions, issues, or contributions:

1. Check the troubleshooting section
2. Review the specification document (PROGRESSIVE_CAPTIONS_SPEC.md)
3. Check the logs for error messages
4. Open an issue on GitHub

---

**Happy Captioning! 🎬✨**
