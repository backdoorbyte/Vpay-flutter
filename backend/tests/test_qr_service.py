from services.qr_service import parse_upi_payload


def test_parse_upi_uri_with_amount():
    payload = "upi://pay?pa=merchant@paytm&pn=Merchant%20Name&am=250.50&tn=Bill&cu=INR"
    result = parse_upi_payload(payload)
    assert result["upi_id"] == "merchant@paytm"
    assert result["payee_name"] == "Merchant Name"
    assert result["amount"] == 250.5
    assert result["note"] == "Bill"


def test_parse_plain_upi_id():
    result = parse_upi_payload("rahul.sharma@ybl")
    assert result["upi_id"] == "rahul.sharma@ybl"
    assert result["amount"] is None
