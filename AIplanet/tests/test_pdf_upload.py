import pytest
from fastapi import status

def test_pdf_upload_success(test_client, test_pdf):
    with open(test_pdf, "rb") as f:
        response = test_client.post(
            "/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == status.HTTP_200_OK
    assert "document_id" in response.json()

def test_pdf_upload_invalid_file(test_client):
    response = test_client.post(
        "/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST 