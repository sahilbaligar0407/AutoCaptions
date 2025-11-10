# Progressive Builder Captions - Implementation Summary

## 🎯 Project Overview

This project implements a sophisticated algorithm that renders progressive 1-3 word captions for 9:16 videos (1080x1920). The algorithm creates captions that cycle through 1-3 words as words are spoken, with precise timing, auto-wrapping, professional layout, and dynamic styling.

## 🏗️ Architecture

### Core Components

1. **`SubtitleParser`** - Unified parser for ASS, SRT, and VTT formats
2. **`CaptionGenerator`** - 1-3 word caption state generation with timing constraints
3. **`MoviePyGenerator`** - MoviePy text clip specifications for Python-based rendering
4. **`FFmpegGenerator`** - FFmpeg filter script generation (optional)

### Data Flow

```
Subtitle Files (ASS/SRT/VTT) 
    ↓
Unified SubtitleSegments
    ↓
Word-level Timing Synthesis
    ↓
1-3 Word Caption States
    ↓
Layout & Level Assignment
    ↓
Overlap Resolution
    ↓
Dynamic Styling
    ↓
MoviePy Text Clips
    ↓
Rendered Video
```

## 📊 Implementation Results

### Current Implementation

**Caption Generation:**
- **Word Count**: Cycles through 1-3 words (1, 2, 3, 1, 2, 3...)
- **Timing**: Minimum 200ms visibility per caption
- **Styling**: Dynamic font and color based on content
- **Overlap Prevention**: Intelligent temporal overlap detection and resolution

**Styling Features:**
- **Wow Words**: ExtraBold font with yellow color (e.g., gosh, last, secret, revealed, exclusive, viral, epic, amazing, incredible)
- **Italic Words**: BlackItalic font with white color (e.g., like, feel, think, seem, maybe, perhaps, probably, might, could, should)
- **Default**: Black font with white color

## ✅ Specification Compliance

### Timing Constraints
- ✅ **200ms Minimum Visibility**: Enforced via word timing synthesis
- ✅ **Word Count Cycling**: Cycles through 1-3 words based on timing
- ✅ **Segment Boundaries**: All timings clamped to valid ranges
- ✅ **Overlap Prevention**: Temporal overlap detection and resolution

### Layout Requirements
- ✅ **1-3 Word Captions**: Progressive word cycling implemented
- ✅ **Auto-wrapping**: Text wrapped within 28 characters per line
- ✅ **Center Alignment**: Applied in rendering layer
- ✅ **Dual-Level Positioning**: Primary (y=h-260) and Secondary (y=h-320)
- ✅ **Overlap Handling**: Temporal overlaps resolved by adjusting timings and skipping subsets

### Visual Styling
- ✅ **Dynamic Styling**: Font and color based on content (wow words, italic words, default)
- ✅ **Text Rendering**: 54px text with black outline (2px stroke)
- ✅ **Font Support**: Poppins font family (Black, Bold, ExtraBold, BlackItalic, BoldItalic)
- ✅ **Width Safety**: 90% of video width (972px safe area)
- ✅ **Padding**: Generous vertical and horizontal padding to prevent text clipping

## 🚀 Production Output

### MoviePy Rendering
- **Tool**: `tools/run_builder_moviepy.py`
- **Input**: Video file and subtitle file (ASS, SRT, or VTT)
- **Output**: Captioned video with dynamic styling
- **Logs**: Processing logs saved to logs/ folder

### Usage
```bash
python AutoCaptions/tools/run_builder_moviepy.py \
    --video AutoCaptions/uploads/your_video.mp4 \
    --subs AutoCaptions/subs/your_subtitles.ass \
    --out AutoCaptions/outputs/output_video.mp4 \
    --log AutoCaptions/logs/output_video.log
```

## 🔧 Technical Implementation

### Algorithm Complexity
- **Parsing**: O(n) where n = subtitle segments
- **State Generation**: O(m × w) where m = segments, w = words per segment
- **Level Assignment**: O(s²) where s = number of states
- **Overlap Resolution**: O(s²) where s = number of states
- **Memory Usage**: ~1-5 MB for typical video caption data

### Key Features

#### 1. Word Count Determination
- Cycles through 1-3 words based on word index
- Adjusts word count based on speech rate
- Ensures minimum visibility duration

#### 2. Overlap Resolution
- Groups captions by Y position
- Adjusts timings to prevent overlaps
- Skips captions that cannot fit minimum duration
- Detects and skips subset overlaps

#### 3. Dynamic Styling
- Detects wow words and applies ExtraBold font with yellow color
- Detects italic words and applies BlackItalic font with white color
- Applies default styling to regular captions
- Styles entire 1-3 word caption groups

#### 4. Text Rendering
- Uses MoviePy TextClip with method='caption' for better text handling
- Constrains width to 90% of video width
- Applies generous padding to prevent text clipping
- Adjusts Y position to ensure clips stay within video bounds

## 📁 File Structure

```
AutoCaptions/
├── progressive_captions.py      # Core algorithm implementation
├── tools/
│   ├── run_builder_moviepy.py  # MoviePy rendering tool
│   └── run_builder_ffmpeg.py   # FFmpeg rendering tool (optional)
├── uploads/                     # Input video files
├── outputs/                     # Generated captioned videos
├── logs/                        # Processing logs
├── subs/                        # Subtitle files (.ass, .srt, .vtt)
├── Poppins-Black.ttf           # Default font
├── Poppins-Bold.ttf            # Bold font variant
├── Poppins-ExtraBold.ttf       # ExtraBold font for wow words
├── Poppins-BlackItalic.ttf     # Italic font for italic words
├── Poppins-BoldItalic.ttf      # BoldItalic font variant
├── README.md                   # Main documentation
├── PROGRESSIVE_CAPTIONS_SPEC.md # Detailed specification
├── IMPLEMENTATION_SUMMARY.md   # This file
└── LICENSE                     # License file
```

## 🎨 Styling Configuration

### Wow Words
Words that trigger ExtraBold font with yellow color:
- Emotional words: wow, gosh, holy, damn, heck, jeez, whoa
- Impact words: shocking, unbelievable, insane, crazy, amazing, incredible
- Exclusive words: secret, revealed, exclusive, viral, legendary, epic
- Action words: breaking, alert, warning, stop, wait
- Quality words: best, top, ultimate, must-see, game-changer

### Italic Words
Words that trigger BlackItalic font with white color:
- Perception verbs: like, feel, think, seem, appear, look, sound, taste, smell
- Uncertainty words: maybe, perhaps, possibly, probably
- Modal verbs: might, could, would, should
- Approximation words: almost, nearly, about, around, roughly, approximately

## 🔍 Troubleshooting

### Common Issues

1. **Font Not Found**
   - Ensure Poppins font files are in the AutoCaptions/ directory
   - The script will fall back to system fonts if Poppins fonts are not found

2. **Text Clipping**
   - Text clipping is prevented with generous padding
   - Vertical padding: 60% of font size
   - Horizontal padding: 25 pixels
   - Y position adjusted to keep clips within video bounds

3. **Caption Overlaps**
   - Overlaps are automatically detected and resolved
   - Captions that cannot fit minimum duration are skipped
   - Subset overlaps are detected and shorter captions are skipped
   - Check logs for overlap detection messages

4. **Timing Issues**
   - Check subtitle file format and encoding
   - Verify start/end times are valid
   - Check logs for timing warnings

## 🚀 Future Enhancements

### Advanced Features
- **Multi-language Support**: Internationalization and RTL text
- **Animation Effects**: Smooth transitions between caption states
- **Accessibility**: High contrast modes and larger text options
- **Custom Styling**: User-defined wow words and italic words

### Performance Optimizations
- **Parallel Processing**: Multi-threaded subtitle parsing
- **GPU Acceleration**: Hardware-accelerated text rendering
- **Caching**: Intermediate result caching for repeated processing
- **Streaming**: Real-time caption generation for live content

### Integration Capabilities
- **API Endpoints**: RESTful service for caption generation
- **Plugin Architecture**: Extensible parser and renderer system
- **Batch Processing**: Multi-file processing with progress tracking
- **Cloud Rendering**: Distributed caption generation services

## 📚 Documentation

- **README.md**: Main documentation with quick start guide
- **PROGRESSIVE_CAPTIONS_SPEC.md**: Detailed algorithm specification
- **IMPLEMENTATION_SUMMARY.md**: This file - implementation summary

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MoviePy**: For Python-based video editing
- **Poppins Font**: For beautiful typography
- **Subtitle Standards**: ASS, SRT, and VTT format specifications

---

**Happy Captioning! 🎬✨**
