# tests/test_api.py

import io # Added for simulating file uploads
from fastapi.testclient import TestClient
# Assuming your FastAPI app instance is named 'app' in src.main
# Adjust the import if your app instance or module path is different.
# For this project structure, accessing 'app' from 'src.main' is typical.
from src.main import app

# Create a TestClient instance for the FastAPI app
client = TestClient(app)

def test_health_check():
    """
    Tests the /health/ endpoint.
    Verifies that the endpoint returns a 200 OK status and the expected JSON response.
    """
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_process_pdf_success():
    """
    Tests the /process-pdf/ endpoint with a successful dummy PDF upload.
    Verifies that the endpoint returns a 200 OK status and the expected JSON response
    based on the current placeholder implementation of process_pdf_pipeline.
    """
    dummy_pdf_content = b"%PDF-1.4\n%created by test\n%%EOF"
    file_name = "dummy_test.pdf"
    file_like_object = io.BytesIO(dummy_pdf_content)

    response = client.post(
        "/process-pdf/",
        files={"file": (file_name, file_like_object, "application/pdf")}
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "processing_simulated_complete"
    assert response_data["filename"] == file_name
    assert response_data["pages_processed"] == 2
    assert "total_chunks_generated" in response_data
    assert "text_snippets" in response_data
    assert "vector_db_status" in response_data
    assert len(response_data["text_snippets"]) == 2

def test_process_pdf_no_file_provided():
    """
    Tests the /process-pdf/ endpoint when no file is provided in the request.
    FastAPI should return a 422 Unprocessable Entity error.
    """
    response = client.post("/process-pdf/") # No 'files' argument
    assert response.status_code == 422
    # Check for a more specific error message if desired, e.g.,
    # response_data = response.json()
    # assert any("missing" in err["type"] and "file" in err["loc"] for err in response_data.get("detail", []))

def test_process_pdf_wrong_file_type():
    """
    Tests the /process-pdf/ endpoint when a non-PDF file type is uploaded.
    The endpoint should return a 415 Unsupported Media Type error.
    """
    dummy_content = b"This is not a PDF, just plain text."
    file_like_object = io.BytesIO(dummy_content)
    response = client.post(
        "/process-pdf/",
        files={"file": ("test.txt", file_like_object, "text/plain")}
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Invalid file type. Only PDF files are allowed." # Corrected based on current endpoint logic

def test_process_pdf_empty_file_content():
    """
    Tests the /process-pdf/ endpoint when an empty PDF file is uploaded.
    The endpoint should return a 400 Bad Request error.
    """
    dummy_empty_content = b""
    file_like_object = io.BytesIO(dummy_empty_content)
    response = client.post(
        "/process-pdf/",
        files={"file": ("empty.pdf", file_like_object, "application/pdf")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."

def test_process_pdf_no_filename():
    """
    Tests the /process-pdf/ endpoint when a file is uploaded without a filename.
    The endpoint should return a 400 Bad Request error.
    """
    dummy_content = b"%PDF-1.4\n% dummy content\n%%EOF"
    file_like_object = io.BytesIO(dummy_content)
    # TestClient might require a filename, but we test how the endpoint handles it if it were None.
    # The current endpoint logic checks `if not file.filename`.
    # Sending `(None, ...)` or `("", ...)` in `files` for the filename part.
    response = client.post(
        "/process-pdf/",
        files={"file": (None, file_like_object, "application/pdf")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "No filename provided." # Corrected based on current endpoint logic
```
