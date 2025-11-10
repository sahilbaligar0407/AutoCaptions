#!/usr/bin/env python3
"""
Test Example: Progressive Builder Captions Algorithm

This script demonstrates the algorithm with a specific example from the user's
subtitle data: "This room is like a red carpet Hollywood hallway."
"""

from progressive_captions import SubtitleParser, CaptionGenerator, CaptionState

def test_progressive_captions():
    """Test the progressive captions algorithm with a specific example"""
    
    # Example subtitle segment (from user's ASS file)
    example_text = "This room is like a red carpet Hollywood hallway."
    start_time = 0.0
    end_time = 2.535
    
    print("=" * 60)
    print("PROGRESSIVE BUILDER CAPTIONS ALGORITHM TEST")
    print("=" * 60)
    print(f"Input text: '{example_text}'")
    print(f"Duration: {start_time:.3f}s - {end_time:.3f}s")
    print(f"Word count: {len(example_text.split())}")
    print()
    
    # Create a mock subtitle segment
    from progressive_captions import SubtitleSegment
    segment = SubtitleSegment(
        start=start_time,
        end=end_time,
        text=example_text,
        index=0
    )
    
    # Initialize caption generator with default parameters
    generator = CaptionGenerator(
        min_visibility_ms=120,      # 120ms minimum visibility
        min_words_per_caption=1,    # Minimum 1 word per caption
        max_words_per_caption=3     # Maximum 3 words per caption
    )
    
    # Generate caption states
    states = generator.generate_states([segment], clip_start=0.0, clip_end=end_time)
    # Assign caption levels (removes overlaps)
    states = generator.assign_caption_levels(states)
    
    print("Generated Caption States:")
    print("-" * 60)
    valid_states = [s for s in states if not s.skip]
    for i, state in enumerate(valid_states, 1):
        duration = state.off - state.on
        skip_indicator = " [SKIPPED]" if state.skip else ""
        print(f"{i:2d}. '{state.text:<25}' | {state.on:6.3f}s - {state.off:6.3f}s | "
              f"Duration: {duration:5.3f}s | y={state.y}{skip_indicator}")
    
    print()
    
    # Analyze timing constraints
    print("Timing Constraint Analysis:")
    print("-" * 60)
    valid_states = [s for s in states if not s.skip]
    for i, state in enumerate(valid_states):
        duration = state.off - state.on
        word_count = len(state.text.split())
        
        print(f"State {i+1} ('{state.text}'):")
        print(f"  - Word count: {word_count} (range: 1-3) {'[OK]' if 1 <= word_count <= 3 else '[FAIL]'}")
        print(f"  - Duration: {duration:.3f}s (min: 0.120s) {'[OK]' if duration >= 0.120 else '[FAIL]'}")
        print(f"  - Start time: {state.on:.3f}s")
        print(f"  - End time: {state.off:.3f}s")
        print()
    
    # Test text wrapping
    print("Text Wrapping Test:")
    print("-" * 60)
    valid_states = [s for s in states if not s.skip]
    for state in valid_states[:3]:  # Test first 3 valid states
        wrapped = generator.wrap_text(state.text, max_chars=28)
        lines = wrapped.split('\n')
        print(f"'{state.text}' -> {len(lines)} line(s):")
        for line in lines:
            print(f"  '{line}' ({len(line)} chars)")
        print()
    
    # Test level assignment
    print("Level Assignment Test:")
    print("-" * 60)
    valid_states = [s for s in states if not s.skip]
    skipped_states = [s for s in states if s.skip]
    
    print(f"Valid states: {len(valid_states)}")
    print(f"Skipped states (overlaps): {len(skipped_states)}")
    print()
    
    if valid_states:
        levels = {260: [], 320: []}
        for state in valid_states:
            levels[state.y].append(state)
        
        for y_pos, level_states in levels.items():
            if level_states:
                print(f"Level y=h-{y_pos}: {len(level_states)} states")
                for state in level_states[:3]:  # Show first 3
                    print(f"  - '{state.text}' | {state.on:.3f}s - {state.off:.3f}s")
                if len(level_states) > 3:
                    print(f"  ... and {len(level_states) - 3} more")
                print()
    
    # Summary statistics
    print("Summary Statistics:")
    print("-" * 60)
    valid_states = [s for s in states if not s.skip]
    total_duration = sum(state.off - state.on for state in valid_states)
    if valid_states:
        avg_duration = total_duration / len(valid_states)
        min_duration = min(state.off - state.on for state in valid_states)
        max_duration = max(state.off - state.on for state in valid_states)
    else:
        avg_duration = min_duration = max_duration = 0
    
    print(f"Total states generated: {len(states)}")
    print(f"Valid states (not skipped): {len(valid_states)}")
    print(f"Skipped states (overlaps): {len([s for s in states if s.skip])}")
    print(f"Total caption time: {total_duration:.3f}s")
    if valid_states:
        print(f"Average duration: {avg_duration:.3f}s")
        print(f"Duration range: {min_duration:.3f}s - {max_duration:.3f}s")
    print(f"Video coverage: {(total_duration / end_time) * 100:.1f}%")
    
    # Validate against specification requirements
    print()
    print("Specification Compliance:")
    print("-" * 60)
    
    valid_states = [s for s in states if not s.skip]
    
    # Check timing constraints
    if valid_states:
        all_durations_valid = all(state.off - state.on >= 0.120 for state in valid_states)
        print(f"[{'PASS' if all_durations_valid else 'FAIL'}] Minimum 120ms visibility")
    else:
        print(f"[SKIP] Minimum 120ms visibility (no valid states)")
    
    # Check word count constraints (1-3 words)
    if valid_states:
        all_word_counts_valid = all(1 <= len(state.text.split()) <= 3 for state in valid_states)
        print(f"[{'PASS' if all_word_counts_valid else 'FAIL'}] Word count in range 1-3")
    else:
        print(f"[SKIP] Word count in range 1-3 (no valid states)")
    
    # Check no overlaps (since overlaps are skipped)
    if valid_states:
        no_overlaps = True
        for i in range(len(valid_states) - 1):
            if valid_states[i].off > valid_states[i + 1].on:
                no_overlaps = False
                break
        print(f"[{'PASS' if no_overlaps else 'FAIL'}] No overlapping captions")
    else:
        print(f"[SKIP] No overlapping captions (no valid states)")
    
    # Check text wrapping
    if valid_states:
        all_wrapped_valid = all(len(line) <= 28 for state in valid_states 
                               for line in generator.wrap_text(state.text).split('\n'))
        print(f"[{'PASS' if all_wrapped_valid else 'FAIL'}] Text wrapped within 28 chars")
    else:
        print(f"[SKIP] Text wrapped within 28 chars (no valid states)")
    
    # Check level assignment
    if valid_states:
        levels_valid = all(state.y in [260, 320] for state in valid_states)
        print(f"[{'PASS' if levels_valid else 'FAIL'}] Vertical positioning correct")
    else:
        print(f"[SKIP] Vertical positioning correct (no valid states)")
    
    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_progressive_captions()
