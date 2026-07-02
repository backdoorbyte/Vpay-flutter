"""Tests for display formatting and confirmation phrases."""

from services.confirm_parser import is_payment_confirmation
from services.display_formatter import (
    format_payment_display,
    infer_amount_from_pay_command,
)
from services.upi_normalizer import extract_upi_from_speech


def test_format_merged_pay_command():
    cmd = "Pay 200-914-2478894 at the rate YBL."
    upi = extract_upi_from_speech(cmd)
    assert upi == "9142478894@ybl"
    assert infer_amount_from_pay_command(cmd, upi) == 200.0
    assert format_payment_display(200, upi) == "Pay 200 to 9142478894@ybl"


def test_confirm_english():
    ok, conf = is_payment_confirmation("yes confirm the payment")
    assert ok and conf >= 0.8


def test_confirm_hindi_roman():
    ok, _ = is_payment_confirmation("haan payment confirm kar do")
    assert ok


def test_confirm_hinglish():
    ok, _ = is_payment_confirmation("yes confirm payment")
    assert ok


def test_reject_cancel():
    ok, _ = is_payment_confirmation("no cancel payment")
    assert not ok
