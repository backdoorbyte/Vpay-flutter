"""Tests for contact name → UPI resolution."""

import pytest

from services.command_parser import parse_payment_command
from services.recipient_resolver import parse_and_resolve_text


@pytest.mark.parametrize(
    "text,recipient,amount",
    [
        ("Send 500 rupees to Rahul", "Rahul", 500.0),
        ("Rahul ko 500 rupaye bhejo", "Rahul", 500.0),
        ("Priya ko do hazaar rupaye do", "Priya", 2000.0),
    ],
)
def test_parse_commands(text, recipient, amount):
    result = parse_payment_command(text)
    assert result.recipient == recipient
    assert result.amount == amount
    assert result.confidence >= 0.5


def test_hindi_devanagari():
    result = parse_payment_command("राहुल को 500 रुपये भेजो")
    assert result.amount == 500.0
    assert result.confidence >= 0.4


def test_phone_upi_in_command():
    parsed = parse_and_resolve_text("send 500 to 9876543210 at ybl")
    assert parsed.upi_id == "9876543210@ybl"
    assert parsed.amount == 500.0
