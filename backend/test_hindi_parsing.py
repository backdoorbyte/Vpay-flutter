"""Test script for Hindi/Hinglish payment command parsing."""

import sys
sys.path.insert(0, '.')

from services.command_parser import parse_payment_command
from services.recipient_resolver import parse_and_resolve_text

# Test cases for Hindi/Hinglish parsing
test_cases = [
    # Hinglish (Roman Hindi)
    ("Rahul ko 500 rupaye bhejo", "Hinglish: Rahul ko 500 bhejo"),
    ("Rahul ko paanch sau rupaye bhejo", "Hinglish: paanch sau"),
    ("Rahul ko char sau bhejo", "Hinglish: char sau"),
    ("Priya ko do hazaar rupaye do", "Hinglish: do hazaar"),
    ("500 rupaye Rahul ko bhejo", "Hinglish: reversed"),
    ("Bhejo 500 rupaye Rahul ko", "Hinglish: verb first"),

    # Devanagari Hindi
    ("राहुल को 500 रुपये भेजो", "Devanagari: 500 rupaye"),
    ("राहुल को पाँच सौ रुपये भेजो", "Devanagari: paanch sau"),
    ("राहुल को चार सौ रुपये भेजो", "Devanagari: chaar sau"),
    ("प्रिया को दो हज़ार रुपये दो", "Devanagari: do hazaar"),
    ("५०० रुपये राहुल को भेजो", "Devanagari: digits in Devanagari"),

    # Mixed Hinglish
    ("Rahul ko 5 sau bhejo", "Mixed: digit + sau"),
    ("Send 500 rupees to Rahul", "English"),
]

print("=" * 80)
print("HINDI/HINGLISH PARSING TEST")
print("=" * 80)

for text, description in test_cases:
    print(f"\n{description}")
    print(f"Input: '{text}'")
    print("-" * 60)

    try:
        result = parse_and_resolve_text(text)
        print(f"  Recipient: {result.recipient}")
        print(f"  UPI ID: {result.upi_id}")
        print(f"  Amount: {result.amount}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Resolution: {result.resolution}")

        # Check if parsing succeeded
        if result.amount is None:
            print("  ⚠️  WARNING: Amount not parsed!")
        if result.recipient is None and result.upi_id is None:
            print("  ⚠️  WARNING: Recipient not parsed!")

    except Exception as e:
        print(f"  ❌ ERROR: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)