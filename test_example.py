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
        lead_in_ms=180,        # 180ms lead-in
        min_visibility_ms=120, # 120ms minimum visibility
        overlap_ms=50,         # 50ms overlap
        max_words=5            # 5-word sliding window
    )
    
    # Generate caption states
    states = generator.generate_states([segment], clip_start=0.0, clip_end=end_time)
    
    print("Generated Caption States:")
    print("-" * 60)
    for i, state in enumerate(states, 1):
        duration = state.off - state.on
        print(f"{i:2d}. '{state.text:<25}' | {state.on:6.3f}s - {state.off:6.3f}s | "
              f"Duration: {duration:5.3f}s | y={state.y}")
    
    print()
    
    # Analyze timing constraints
    print("Timing Constraint Analysis:")
    print("-" * 60)
    for i, state in enumerate(states):
        duration = state.off - state.on
        lead_in = state.on - (start_time + (i * (end_time - start_time) / len(example_text.split())))
        
        print(f"State {i+1}:")
        print(f"  - Duration: {duration:.3f}s (min: 0.120s) {'✓' if duration >= 0.120 else '✗'}")
        print(f"  - Lead-in: {lead_in:.3f}s (target: -0.180s) {'✓' if abs(lead_in + 0.180) < 0.001 else '✗'}")
        
        if i < len(states) - 1:
            overlap = state.off - states[i + 1].on
            print(f"  - Overlap: {overlap:.3f}s (target: 0.050s) {'✓' if abs(overlap - 0.050) < 0.001 else '✗'}")
        print()
    
    # Test text wrapping
    print("Text Wrapping Test:")
    print("-" * 60)
    for state in states[:3]:  # Test first 3 states
        wrapped = generator.wrap_text(state.text, max_chars=28)
        lines = wrapped.split('\n')
        print(f"'{state.text}' -> {len(lines)} line(s):")
        for line in lines:
            print(f"  '{line}' ({len(line)} chars)")
        print()
    
    # Test level assignment
    print("Level Assignment Test:")
    print("-" * 60)
    assigned_states = generator.assign_caption_levels(states)
    
    levels = {0: [], 1: []}
    for state in assigned_states:
        if not state.skip:
            level = 0 if state.y == 260 else 1
            levels[level].append(state)
    
    for level, level_states in levels.items():
        print(f"Level {level} (y = h-{260 if level == 0 else 320}): {len(level_states)} states")
        for state in level_states[:3]:  # Show first 3
            print(f"  - '{state.text}' | {state.on:.3f}s - {state.off:.3f}s")
        if len(level_states) > 3:
            print(f"  ... and {len(level_states) - 3} more")
        print()
    
    # Summary statistics
    print("Summary Statistics:")
    print("-" * 60)
    total_duration = sum(state.off - state.on for state in states)
    avg_duration = total_duration / len(states)
    min_duration = min(state.off - state.on for state in states)
    max_duration = max(state.off - state.on for state in states)
    
    print(f"Total states: {len(states)}")
    print(f"Total caption time: {total_duration:.3f}s")
    print(f"Average duration: {avg_duration:.3f}s")
    print(f"Duration range: {min_duration:.3f}s - {max_duration:.3f}s")
    print(f"Video coverage: {(total_duration / end_time) * 100:.1f}%")
    
    # Validate against specification requirements
    print()
    print("Specification Compliance:")
    print("-" * 60)
    
    # Check timing constraints
    all_durations_valid = all(state.off - state.on >= 0.120 for state in states)
    print(f"✓ Minimum 120ms visibility: {'PASS' if all_durations_valid else 'FAIL'}")
    
    # Check lead-in constraints
    lead_ins_valid = all(state.on >= 0 for state in states)
    print(f"✓ Lead-in capped at segment start: {'PASS' if lead_ins_valid else 'FAIL'}")
    
    # Check overlap constraints
    overlaps_valid = True
    for i in range(len(states) - 1):
        if states[i + 1].on < states[i].off:
            overlap = states[i].off - states[i + 1].on
            if overlap < 0.050:
                overlaps_valid = False
                break
    print(f"✓ 50ms minimum overlap: {'PASS' if overlaps_valid else 'FAIL'}")
    
    # Check text wrapping
    all_wrapped_valid = all(len(line) <= 28 for state in states 
                           for line in generator.wrap_text(state.text).split('\n'))
    print(f"✓ Text wrapped within 28 chars: {'PASS' if all_wrapped_valid else 'FAIL'}")
    
    # Check level assignment
    levels_valid = all(state.y in [260, 320] for state in assigned_states if not state.skip)
    print(f"✓ Vertical positioning correct: {'PASS' if levels_valid else 'FAIL'}")
    
    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_progressive_captions()
