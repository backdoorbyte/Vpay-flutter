"""Tests for spoken UPI extraction."""

from services.upi_normalizer import (
    extract_upi_from_speech,
    isolate_latest_command,
    preprocess_speech,
    strip_upi_from_text,
)


def test_literal_phone_upi():
    assert extract_upi_from_speech("pay 500 to 9876543210@ybl") == "9876543210@ybl"


def test_spoken_digits_at_ybl():
    text = "send 500 to nine eight seven six five four three two one zero at ybl"
    assert extract_upi_from_speech(text) == "9876543210@ybl"


def test_numeric_at_phonepe():
    assert extract_upi_from_speech("transfer 200 to 9988776655 at phone pe") == "9988776655@ybl"


def test_handle_at_paytm():
    assert extract_upi_from_speech("pay 100 to merchant at paytm") == "merchant@paytm"


def test_at_the_rate_ybl():
    assert (
        extract_upi_from_speech("pay 200 to 9142478891 at the rate ybl")
        == "9142478891@ybl"
    )


def test_hyphenated_phone_at_the_rate():
    assert (
        extract_upi_from_speech("Pay 200 to 914-247-8891 at the rate YBL")
        == "9142478891@ybl"
    )


def test_to_not_treated_as_digit_two():
    assert extract_upi_from_speech("pay 200 to 9876543210 at ybl") == "9876543210@ybl"


def test_isolate_latest_command():
    text = "Send 500 to Rahul. Pay 200 to 9876543210 at the rate ybl."
    assert isolate_latest_command(text) == "Pay 200 to 9876543210 at the rate ybl"


def test_mixed_commands_uses_latest():
    text = "Send 500 to Rahul. Pay 200 to 9876543210 at the rate ybl."
    assert extract_upi_from_speech(text) == "9876543210@ybl"


def test_preprocess_at_the_rate():
    assert preprocess_speech("9142478891 at the rate ybl") == "9142478891@ybl"


def test_strip_upi_leaves_amount():
    upi = "9876543210@ybl"
    text = "send 500 to 9876543210 at ybl"
    cleaned = strip_upi_from_text(text, upi)
    assert "9876543210" not in cleaned
    assert "500" in cleaned
