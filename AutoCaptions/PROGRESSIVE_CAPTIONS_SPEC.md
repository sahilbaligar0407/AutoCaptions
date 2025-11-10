# Progressive Builder Captions Algorithm Specification

## Overview
This document specifies the Progressive Builder Captions algorithm that renders 1-3 word captions with precise timing, auto-wrapping, center alignment, and dynamic styling for 9:16 videos (1080x1920).

## Core Requirements

### Input
- **Video**: 1080×1920 (9:16) MP4 file
- **Subtitles**: One of ASS, SRT, or VTT format
- **Fonts**: TTF font files (Poppins-Black.ttf, Poppins-Bold.ttf, Poppins-ExtraBold.ttf, Poppins-BlackItalic.ttf, Poppins-BoldItalic.ttf)

### Output
- **1-3 word captions** that cycle through word counts based on timing
- **200ms minimum visibility** per caption
- **Dynamic styling** based on content (wow words, italic words, default)
- **Auto-wrapping** within 90% width (center-aligned)
- **Vertical positioning** in bottom band (y = h-260 for primary, h-320 for secondary)
- **Overlap prevention** with intelligent caption skipping

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
def compute_word_times(seg_start: float, seg_end: float, word_count: int) -> List[Tuple[float, float]]:
    """Synthesizes uniform word timings with constraints"""
    total_dur = seg_end - seg_start
    # Ensure minimum duration for visibility
    min_total_dur = word_count * (min_visibility_sec / max_words)
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
```

**Timing Constraints:**
- Minimum 200ms per word group (enforced via `min_total_dur`)
- Uniform distribution within segment boundaries
- Clamped to segment start/end times

### 3. Caption State Generation
```python
def generate_states(segments: List[SubtitleSegment], clip_start: float, clip_end: float) -> List[CaptionState]:
    """Generates 1-3 word caption states that appear as words are spoken"""
    states = []
    for seg in segments:
        # Adjust to clip-relative timeline
        adj_start = max(0, seg.start - clip_start)
        adj_end = min(clip_end - clip_start, seg.end - clip_start)
        
        words = tokenize(seg.text)
        word_times = compute_word_times(adj_start, adj_end, len(words))
        avg_time_per_word = total_duration / len(words)
        
        # Process words in groups of 1-3
        i = 0
        while i < len(words):
            # Determine how many words to show (cycles through 1, 2, 3)
            word_count = determine_word_count(i, len(words), avg_time_per_word)
            
            # Get words for this caption
            caption_words = words[i:i + word_count]
            caption_text = ' '.join(caption_words)
            
            # Compute timing: start when first word appears, end when last word finishes
            on = word_times[i][0]
            last_word_idx = min(i + word_count - 1, len(word_times) - 1)
            off = word_times[last_word_idx][1]
            
            # Ensure minimum duration
            if off - on < min_visibility_sec:
                off = on + min_visibility_sec
            
            states.append(CaptionState(
                text=caption_text,
                on=on,
                off=off,
                seg_idx=seg.index,
                y=260  # Default primary level
            ))
            
            # Move to next group of words
            i += word_count
    
    return sorted(states, key=lambda s: (s.on, s.seg_idx))
```

**Word Count Determination:**
```python
def determine_word_count(word_index: int, total_words: int, avg_time_per_word: float) -> int:
    """Determine how many words to show (cycles through 1-3 based on timing)"""
    remaining_words = total_words - word_index
    
    # If speech is very fast, show fewer words
    if avg_time_per_word < min_visibility_sec / 2:
        return min(1, remaining_words)
    elif avg_time_per_word < min_visibility_sec:
        return min(2, remaining_words)
    
    # Normal speech: cycle through 1, 2, 3, 1, 2, 3, ...
    cycle_pos = word_index % 3
    word_count = min_words + cycle_pos
    word_count = min(word_count, max_words, remaining_words)
    
    return word_count
```

**State Properties:**
- **Text**: 1-3 words per caption (cycles through word counts)
- **Timing**: `on` = first_word_start, `off` = last_word_end
- **Duration**: Minimum 200ms enforced
- **Sorting**: By start time, then by segment index (stable sort)

### 4. Layout & Level Assignment
```python
def assign_caption_levels(states: List[CaptionState]) -> List[CaptionState]:
    """Assigns vertical levels for overlapping captions (simplified for 1-3 word style)"""
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
```

**Layout Rules:**
- **Primary Level**: y = h-260 (260px from bottom)
- **Secondary Level**: y = h-320 (320px from bottom, 60px above primary)
- **Overlap Handling**: Captions that overlap temporally are skipped
- **Skip Logic**: Overlapping captions are marked for skipping to prevent visual overlap

### 5. Dynamic Styling
```python
def determine_caption_style(text: str, wow_words: set, italic_words: set) -> dict:
    """Determine font and color style for a caption based on its content"""
    words = text.split()
    
    # Check for wow words first (higher priority)
    has_wow_word = False
    for word in words:
        clean_word = word.lower().strip('.,!?;:')
        if clean_word in wow_words:
            has_wow_word = True
            break
    
    # Check for italic words
    has_italic_word = any(word.lower().strip('.,!?;:') in italic_words for word in words)
    
    # Determine style
    if has_wow_word:
        return {
            'font': 'Poppins-ExtraBold.ttf',
            'color': 'yellow',
            'style': 'wow'
        }
    elif has_italic_word:
        return {
            'font': 'Poppins-BlackItalic.ttf',
            'color': 'white',
            'style': 'italic'
        }
    else:
        return {
            'font': 'Poppins-Black.ttf',
            'color': 'white',
            'style': 'default'
        }
```

**Styling Rules:**
- **Wow Words**: ExtraBold font with yellow color (e.g., gosh, last, secret, revealed, exclusive, viral, epic, amazing, incredible)
- **Italic Words**: BlackItalic font with white color (e.g., like, feel, think, seem, maybe, perhaps, probably, might, could, should)
- **Default**: Black font with white color
- **Priority**: Wow words take precedence over italic words

### 6. Text Wrapping
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
- **Padding**: Generous vertical and horizontal padding to prevent text clipping

## Implementation: MoviePy Rendering

### MoviePy Text Clip Generation
```python
def generate_text_clips(states: List[CaptionState]) -> List[Dict]:
    """Generate MoviePy text clip specifications with dynamic styling"""
    text_clips = []
    for state in states:
        if state.skip:
            continue
        
        # Determine style based on content
        style_info = determine_caption_style(state.text, wow_words, italic_words)
        
        text_clips.append({
            'text': wrap_text(state.text),
            'start_time': state.on,
            'end_time': state.off,
            'position': ('center', video_height - state.y),
            'font_size': 54,
            'font_color': style_info['color'],
            'font_file': style_info['font'],
            'stroke_color': 'black',
            'stroke_width': 2
        })
    return text_clips
```

**MoviePy Features:**
- **Text Clips**: Individual text layers with precise timing
- **Compositing**: Overlay text clips on video timeline
- **Positioning**: Center-aligned with calculated y-offsets
- **Dynamic Styling**: Font and color based on content
- **Padding**: Generous padding to prevent text clipping
- **Overlap Prevention**: Temporal overlap detection and resolution

### Overlap Resolution
```python
def resolve_overlaps(specs: List[Dict]) -> List[Dict]:
    """Resolve temporal overlaps by adjusting timings and skipping subsets"""
    # Group by Y position
    specs_by_y = {}
    for i, spec in enumerate(specs):
        y_pos = spec['position'][1]
        if y_pos not in specs_by_y:
            specs_by_y[y_pos] = []
        specs_by_y[y_pos].append((i, spec))
    
    # Process each Y position group
    for y_pos, y_specs in specs_by_y.items():
        # Sort by start time
        y_specs.sort(key=lambda x: x[1]['start_time'])
        
        # Adjust timings to prevent overlaps
        last_clip_end_time = 0.0
        for i, (idx, spec) in enumerate(y_specs):
            original_start = spec['start_time']
            original_end = spec['end_time']
            
            # Start time MUST be >= previous clip's end time
            start_time = max(original_start, last_clip_end_time)
            
            # Find next clip's start time to cap end time
            next_start_candidates = [y_specs[j][1]['start_time'] for j in range(i + 1, len(y_specs))]
            if next_start_candidates:
                max_end_time = min(next_start_candidates)
                min_end_time = start_time + min_duration
                
                # Check if we can fit minimum duration
                if min_end_time > max_end_time:
                    # Can't fit - skip this clip
                    spec['skip'] = True
                    continue
                
                end_time = min(original_end, max_end_time)
                end_time = max(end_time, min_end_time)
            else:
                end_time = max(original_end, start_time + min_duration)
            
            # Update timing
            spec['start_time'] = start_time
            spec['end_time'] = end_time
            last_clip_end_time = end_time
    
    return [spec for spec in specs if not spec.get('skip', False)]
```

## Usage Examples

### MoviePy Rendering
```bash
# Generate captioned video with MoviePy
python AutoCaptions/tools/run_builder_moviepy.py \
    --video AutoCaptions/uploads/your_video.mp4 \
    --subs AutoCaptions/subs/your_subtitles.ass \
    --out AutoCaptions/outputs/output_video.mp4 \
    --log AutoCaptions/logs/output_video.log
```

## Validation & Testing

### Acceptance Test Case
**Input**: "This room is like a red carpet Hollywood hallway." (9 words)

**Expected Output States** (example, depends on timing):
1. "This" (1 word, default style)
2. "room is" (2 words, default style)
3. "like a" (2 words, italic style - contains "like")
4. "red carpet" (2 words, default style)
5. "Hollywood hallway." (2 words, default style)

**Timing Validation:**
- Each caption has minimum 200ms duration
- Captions cycle through 1-3 words based on timing
- No temporal overlaps at same Y position
- Dynamic styling applied based on content

### Edge Case Handling
- **Short Segments**: Minimum duration enforced via word timing synthesis
- **Fast Speech**: Word count adjusted based on speech rate
- **Overlapping Segments**: Temporal overlap detection and resolution
- **Clip Boundaries**: Relative timing conversion handles sub-clip extraction
- **Empty Text**: Segments with no words are skipped
- **Subset Overlaps**: Shorter captions that are subsets of longer overlapping captions are skipped

## Performance Characteristics

### Computational Complexity
- **Parsing**: O(n) where n = number of subtitle segments
- **State Generation**: O(m × w) where m = segments, w = words per segment
- **Level Assignment**: O(s²) where s = number of states (typically small)
- **Text Wrapping**: O(w) where w = words in text
- **Overlap Resolution**: O(s²) where s = number of states

### Memory Usage
- **Subtitle Data**: ~100 bytes per segment
- **Caption States**: ~200 bytes per state
- **Typical Video**: 1-5 MB for caption data

### Rendering Performance
- **MoviePy**: CPU-based, suitable for offline processing
- **Processing Time**: Depends on video length and number of captions
- **Memory Usage**: Moderate, loads video into memory for processing

## Configuration Options

### Timing Parameters
```python
generator = CaptionGenerator(
    min_visibility_ms=200,      # Minimum 200ms visibility per caption
    min_words_per_caption=1,    # Minimum 1 word per caption
    max_words_per_caption=3     # Maximum 3 words per caption
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

# Text formatting
font_size = 54
max_chars_per_line = 28
safe_width_ratio = 0.9  # 90% of video width
vertical_padding = font_size * 0.6  # 60% padding for ascenders/descenders
horizontal_padding = 25  # Horizontal padding to prevent edge clipping
```

### Styling Configuration
```python
# Wow words (ExtraBold, yellow)
wow_words = {
    'wow', 'shocking', 'unbelievable', 'insane', 'crazy', 'secret', 'revealed',
    'exclusive', 'viral', 'legendary', 'epic', 'mind-blowing', 'unreal', 'amazing',
    'incredible', 'unexpected', 'rare', 'hidden', 'must-see', 'top', 'ultimate',
    'best', 'wild', 'funny', 'hilarious', 'breaking', 'alert', 'warning', 'stop',
    'wait', 'omg', 'wtf', 'no-way', 'game-changer', 'hack', 'trick', 'tip',
    'proven', 'official', 'first', 'last', 'limited', 'challenge', 'dare',
    'trending', 'for-you', 'now', 'right-now', 'today', 'instantly', 'fast',
    'quick', 'easy', 'free', 'win', 'lose', 'fail', 'success', 'power', 'boost',
    'unlock', 'behind-the-scenes', 'true-story', 'real-life', 'fact', 'secret-sauce',
    'gosh', 'holy', 'damn', 'heck', 'jeez', 'whoa'
}

# Italic words (BlackItalic, white)
italic_words = {
    'like', 'feel', 'think', 'seem', 'appear', 'look', 'sound', 'taste', 'smell',
    'maybe', 'perhaps', 'possibly', 'probably', 'might', 'could', 'would', 'should',
    'almost', 'nearly', 'about', 'around', 'roughly', 'approximately'
}
```

### Font Configuration
```python
# Font file paths
black_font = "Poppins-Black.ttf"
bold_font = "Poppins-Bold.ttf"
extrabold_font = "Poppins-ExtraBold.ttf"
blackitalic_font = "Poppins-BlackItalic.ttf"
bolditalic_font = "Poppins-BoldItalic.ttf"

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
- **Text Clipping**: Generous padding to prevent character clipping

### Output Validation
- **Timing Consistency**: Verification of state sequence
- **Layout Constraints**: Validation of positioning and overlap rules
- **Text Wrapping**: Verification of line length constraints
- **Overlap Detection**: Validation of non-overlapping captions at same Y position

## Future Enhancements

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

## Conclusion

The Progressive Builder Captions algorithm provides a robust, efficient solution for generating dynamic 1-3 word captions with precise timing, professional layout, and dynamic styling. The MoviePy implementation ensures compatibility across different use cases and performance requirements.

The algorithm successfully handles the complexity of overlapping subtitles, maintains consistent timing constraints, applies dynamic styling based on content, and produces visually appealing results that enhance video accessibility and user experience.
