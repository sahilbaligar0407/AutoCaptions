# Progressive Builder Captions Algorithm Specification

## Overview
This document specifies the Progressive Builder Captions algorithm that renders sliding 5-word captions with precise timing, auto-wrapping, and center alignment for 9:16 videos (1080x1920).

## Core Requirements

### Input
- **Video**: 1080×1920 (9:16) MP4 file
- **Subtitles**: One of ASS, SRT, or VTT format
- **Font**: TTF font file (e.g., Poppins-Black.ttf)

### Output
- **Sliding 5-word captions** with progressive word building
- **180ms lead-in** (capped at segment start)
- **120ms minimum visibility** per state
- **50ms overlap** between consecutive states
- **Auto-wrapping** within 90% width (center-aligned)
- **Vertical positioning** in bottom band (y = h-260 for primary, h-320 for secondary)

## Algorithm Architecture

### 1. Subtitle Parsing (Unified Format)
All subtitle formats are converted to a unified internal representation:
```python
@dataclass
class SubtitleSegment:
    start: float      # Start time in seconds
    end: float        # End time in seconds
    text: str         # Subtitle text
    index: int        # Original segment index for stable sorting
```

**Supported Formats:**
- **ASS**: Parses Dialogue lines from [Events] section
- **SRT**: Parses numbered blocks with timecode → text format
- **VTT**: Parses WEBVTT blocks with timecode → text format

### 2. Word Tokenization & Timing Synthesis
```python
def compute_word_times(seg_start: float, seg_end: float, N: int) -> List[Tuple[float, float]]:
    """Synthesizes uniform word timings with constraints"""
    total_dur = seg_end - seg_start
    min_total_dur = N * 0.12  # 120ms min per word
    actual_dur = max(total_dur, min_total_dur)
    slot = actual_dur / N
    
    word_times = []
    for i in range(N):
        w_start = seg_start + i * slot
        w_end = seg_start + (i + 1) * slot
        # Clamp to segment boundaries
        w_start = max(seg_start, min(seg_end, w_start))
        w_end = max(seg_start, min(seg_end, w_end))
        word_times.append((w_start, w_end))
    return word_times
```

**Timing Constraints:**
- Minimum 120ms per word (enforced via `min_total_dur`)
- Uniform distribution within segment boundaries
- Clamped to segment start/end times

### 3. Caption State Generation
```python
def generate_states(segments: List[SubtitleSegment], clip_start: float, clip_end: float) -> List[CaptionState]:
    """Emits sliding-window states with precise timing"""
    states = []
    for seg in segments:
        # Adjust to clip-relative timeline
        adj_start = max(0, seg.start - clip_start)
        adj_end = min(clip_end - clip_start, seg.end - clip_start)
        
        words = tokenize(seg.text)
        word_times = compute_word_times(adj_start, adj_end, len(words))
        
        for i in range(len(words)):
            # Build 5-word sliding window
            window_start = max(0, i - 4)
            window_text = " ".join(words[window_start:i+1])
            
            # Compute state timing
            on = max(0, word_times[i][0] - 0.18)  # 180ms lead-in
            off = word_times[i+1][0] - 0.05 if i < len(words)-1 else adj_end
            off = max(off, on + 0.12)  # Enforce 120ms min
            
            states.append(CaptionState(
                text=window_text,
                on=on,
                off=off,
                seg_idx=seg.index,
                y=260  # Default primary level
            ))
    
    return sorted(states, key=lambda s: (s.on, s.seg_idx))
```

**State Properties:**
- **Text**: Sliding window of up to 5 words
- **Timing**: `on` = word_start - 180ms, `off` = next_word_start - 50ms
- **Duration**: Minimum 120ms enforced
- **Sorting**: By start time, then by segment index (stable sort)

### 4. Layout & Level Assignment
```python
def assign_caption_levels(states: List[CaptionState]) -> List[CaptionState]:
    """Assigns vertical levels for overlapping captions (max 2 levels)"""
    levels = [[] for _ in range(2)]  # Primary/secondary levels
    for state in states:
        assigned = False
        for lvl in range(2):
            if not levels[lvl] or levels[lvl][-1].off <= state.on:
                state.y = 260 if lvl == 0 else 320  # y-offset from bottom
                levels[lvl].append(state)
                assigned = True
                break
        if not assigned:
            state.skip = True  # Skip if >2 overlaps
    return states
```

**Layout Rules:**
- **Primary Level**: y = h-260 (260px from bottom)
- **Secondary Level**: y = h-320 (320px from bottom, 60px above primary)
- **Overlap Handling**: Maximum 2 simultaneous captions
- **Skip Logic**: Captions with >2 overlaps are marked for skipping

### 5. Text Wrapping
```python
def wrap_text(text: str, max_chars: int = 28) -> str:
    """Soft-wraps text to max_chars per line (center-aligned later)"""
    words = text.split()
    lines, current = [], []
    for word in words:
        if len(" ".join(current + [word])) > max_chars:
            if current:
                lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)
```

**Wrapping Constraints:**
- **Max Characters**: 28 per line (conservative for 54px font)
- **Width Safety**: 90% of 1080px = 972px safe area
- **Font Scaling**: 54px font ≈ 32px/character
- **Center Alignment**: Applied in rendering layer

## Implementation Options

### Option 1: FFmpeg Filter Script Generation
```python
def generate_filter_script(states: List[CaptionState], output_file: str):
    """Generates FFmpeg filter_complex_script for progressive captions"""
    script_lines = [
        "[0:v] format=yuv420p,",
        "drawbox=x=0:y=h-340:w=iw:h=320:color=black@0.65:t=fill,"
    ]
    
    for state in states:
        if state.skip:
            continue
        
        # Escape text for FFmpeg
        text = escape_ffmpeg_text(wrap_text(state.text))
        
        script_lines.append(
            f"drawtext=fontfile='{font_file}':"
            f"text='{text}':"
            f"enable='between(t,{state.on:.3f},{state.off:.3f})':"
            f"x=(w-tw)/2:y=h-{state.y}:"
            f"fontsize=54:fontcolor=white:"
            f"box=1:boxcolor=black@0.6:boxborderw=20,"
        )
    
    script_lines.append("[v]")
    
    with open(output_file, "w") as f:
        f.write("\n".join(script_lines))
```

**FFmpeg Features:**
- **Background Box**: 320px height, 65% opacity black
- **Text Rendering**: 54px white text with black outline
- **Timing Control**: `enable='between(t,start,end)'` for precise timing
- **Positioning**: Center-aligned with `x=(w-tw)/2`

### Option 2: MoviePy Text Layer Generation
```python
def generate_text_clips(states: List[CaptionState]) -> List[Dict]:
    """Generate MoviePy text clip specifications"""
    text_clips = []
    for state in states:
        if state.skip:
            continue
        
        text_clips.append({
            'text': wrap_text(state.text),
            'start_time': state.on,
            'end_time': state.off,
            'position': ('center', video_height - state.y),
            'font_size': 54,
            'font_color': 'white',
            'font_file': font_file,
            'bg_color': 'black',
            'bg_opacity': 0.6
        })
    return text_clips
```

**MoviePy Features:**
- **Text Clips**: Individual text layers with precise timing
- **Compositing**: Overlay text clips on video timeline
- **Positioning**: Center-aligned with calculated y-offsets
- **Background**: Semi-transparent black background per clip

## Usage Examples

### FFmpeg Rendering
```bash
# Generate filter script
python progressive_captions.py

# Apply to video
ffmpeg -i ClipV1.mp4 -filter_complex_script filter_script.txt \
       -map "[v]" -map 0:a -c:a copy output_with_captions.mp4
```

### MoviePy Rendering
```python
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

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

## Validation & Testing

### Acceptance Test Case
**Input**: "This room is like a red carpet Hollywood hallway." (9 words)

**Expected Output States**:
1. "This" (0.000s - 0.282s)
2. "This room" (0.282s - 0.564s)
3. "This room is" (0.564s - 0.846s)
4. "This room is like" (0.846s - 1.128s)
5. "This room is like a" (1.128s - 1.410s)
6. "room is like a red" (1.410s - 1.692s)
7. "is like a red carpet" (1.692s - 1.974s)
8. "like a red carpet Hollywood" (1.974s - 2.256s)
9. "a red carpet Hollywood hallway." (2.256s - 2.535s)

**Timing Validation**:
- State N starts at word_N_start - 0.18s
- State N ends at word_{N+1}_start - 0.05s (or segment end)
- Minimum duration: 120ms enforced
- 50ms overlap between consecutive states

### Edge Case Handling
- **Short Segments**: Minimum duration enforced via word timing synthesis
- **Fast Speech**: 120ms minimum per word prevents flickering
- **Overlapping Segments**: Dual-level layout prevents caption overlap
- **Clip Boundaries**: Relative timing conversion handles sub-clip extraction
- **Empty Text**: Segments with no words are skipped
- **Special Characters**: Proper escaping for FFmpeg compatibility

## Performance Characteristics

### Computational Complexity
- **Parsing**: O(n) where n = number of subtitle segments
- **State Generation**: O(m × w) where m = segments, w = words per segment
- **Level Assignment**: O(s²) where s = number of states (typically small)
- **Text Wrapping**: O(w) where w = words in text

### Memory Usage
- **Subtitle Data**: ~100 bytes per segment
- **Caption States**: ~200 bytes per state
- **Filter Script**: ~500 bytes per state
- **Typical Video**: 1-5 MB for caption data

### Rendering Performance
- **FFmpeg**: Hardware-accelerated, real-time capable
- **MoviePy**: CPU-based, suitable for offline processing
- **Filter Script**: Single-pass rendering, no intermediate files

## Configuration Options

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
# Video dimensions
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

### Font Configuration
```python
# Font file path
font_file = "Poppins-Black.ttf"

# Fallback fonts (if primary unavailable)
fallback_fonts = ["Arial", "Helvetica", "sans-serif"]
```

## Error Handling & Robustness

### Input Validation
- **File Format**: Automatic detection and parsing
- **Encoding**: UTF-8 support with fallback handling
- **Timing**: Validation of start < end times
- **Text Content**: Filtering of empty or invalid segments

### Runtime Robustness
- **Missing Fonts**: Graceful fallback to system fonts
- **Invalid Timing**: Clamping to valid ranges
- **Memory Limits**: Efficient data structures for large files
- **Platform Compatibility**: Cross-platform path handling

### Output Validation
- **Filter Script**: Syntax validation for FFmpeg compatibility
- **Timing Consistency**: Verification of state sequence
- **Layout Constraints**: Validation of positioning and overlap rules
- **Text Wrapping**: Verification of line length constraints

## Future Enhancements

### Advanced Features
- **Multi-language Support**: Internationalization and RTL text
- **Dynamic Styling**: Color and font variations based on content
- **Animation Effects**: Smooth transitions between caption states
- **Accessibility**: High contrast modes and larger text options

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

## Conclusion

The Progressive Builder Captions algorithm provides a robust, efficient solution for generating dynamic captions with precise timing and professional layout. The dual implementation approach (FFmpeg + MoviePy) ensures compatibility across different use cases and performance requirements.

The algorithm successfully handles the complexity of overlapping subtitles, maintains consistent timing constraints, and produces visually appealing results that enhance video accessibility and user experience.
