# qa_uniqueness.py
"""
QA Test Script for Bedtime Story Maker's Content Engine.

This script verifies that the ContentEngine's generation method produces unique stories
even when given the exact same input parameters, as required by the project specifications.
It does this by generating 100 stories with static parameters and asserting that
each generated story has a unique ID and that the number of unique story texts meets a
high threshold.
"""

import sys
import os
import importlib

# Ensure the current directory is on the path to find main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# We must import main and then reload it to ensure we get the latest
# version from the file, bypassing Python's import cache which can cause
# issues in interactive testing environments.
import main
importlib.reload(main)

try:
    # Now we can safely import the class from the reloaded module
    from main import ContentEngine
except ImportError as e:
    print("Error: Could not import ContentEngine from main.py.")
    print("Please ensure main.py is in the same directory as this script.")
    print(f"Details: {e}")
    sys.exit(1)

def test_story_uniqueness():
    """
    Tests the uniqueness of story generation.
    """
    print("--- Starting Story Uniqueness QA Test ---")

    engine = ContentEngine()

    # Static parameters for generation
    test_params = {
        "topic": "The Lost Star",
        "name": "Leo",
        "age": "6",
        "language": "en",
        "tone": "Adventurous",
        "theme": "Space Explorer's Quest",
        "include_moral": True,
        "include_breathing": False,
    }

    num_tests = 100
    generated_ids = set()
    generated_texts = set()

    print(f"Generating {num_tests} stories with identical parameters...")

    for i in range(num_tests):
        story = engine.generate_story(test_params)

        if 'error' in story:
            print(f"Error during generation on iteration {i+1}: {story['error']}")
            return False # Test fails

        generated_ids.add(story['id'])
        generated_texts.add(story['text'])

    print("--- Test Results ---")

    # 1. Test that all IDs are unique
    unique_id_count = len(generated_ids)
    print(f"Generated {num_tests} stories.")
    print(f"Found {unique_id_count} unique story IDs.")
    try:
        assert unique_id_count == num_tests
        print("✅ PASSED: All generated story IDs are unique.")
    except AssertionError:
        print("❌ FAILED: Duplicate story IDs were generated.")
        return False

    # 2. Test that story texts are highly unique
    # With a finite number of templates (4x4x4x4 = 256), collisions are
    # possible when generating 100 stories (see the "Birthday Problem").
    # We assert a high threshold of uniqueness, not 100%.
    unique_text_count = len(generated_texts)
    uniqueness_threshold = 90
    print(f"Found {unique_text_count} unique story texts.")
    try:
        assert unique_text_count >= uniqueness_threshold
        print(f"✅ PASSED: Unique text count ({unique_text_count}) is above threshold ({uniqueness_threshold}).")
    except AssertionError:
        print(f"❌ FAILED: Unique text count ({unique_text_count}) is below threshold ({uniqueness_threshold}).")
        print("This may indicate a problem with randomization or insufficient template variety.")
        return False

    print("\n--- QA Uniqueness Test Successfully Completed ---")
    return True

if __name__ == "__main__":
    if test_story_uniqueness():
        sys.exit(0)
    else:
        sys.exit(1)
