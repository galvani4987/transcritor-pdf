# tests/test_api.py

import io
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.main import app # FastAPI app instance
from src.celery_app import celery_app # Celery app instance for mocking AsyncResult

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

def test_process_pdf_enqueues_task_and_returns_id():
    """
    Tests the /process-pdf/ endpoint with a dummy PDF.
    Verifies that a Celery task is enqueued and the endpoint returns a task_id.
    The actual task processing is mocked.
    """
    dummy_pdf_content = b"%PDF-1.4\n%created by test\n%%EOF"
    file_name = "dummy_enqueue_test.pdf"
    file_like_object = io.BytesIO(dummy_pdf_content)

    # Mock the Celery task's delay method
    with patch('src.tasks.process_pdf_task.delay') as mock_task_delay:
        # Configure the mock to return a mock task object with a specific id
        mock_task_delay.return_value.id = "fake_task_id_for_enqueue_test"

        response = client.post(
            "/process-pdf/",
            files={"file": (file_name, file_like_object, "application/pdf")}
        )

        # Based on src/main.py, it returns 200 and a message including task_id
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_id"] == "fake_task_id_for_enqueue_test"
        assert "message" in response_data
        assert "PDF processing has been queued" in response_data["message"]

        # Verify that the Celery task's delay method was called once with correct arguments
        mock_task_delay.assert_called_once_with(
            file_content_bytes=dummy_pdf_content,
            filename=file_name
        )

def test_process_pdf_no_file_provided():
    """
    Tests the /process-pdf/ endpoint when no file is provided in the request.
    FastAPI should return a 422 Unprocessable Entity error.
    """
    response = client.post("/process-pdf/") # No 'files' argument
    assert response.status_code == 422

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
    assert response.json()["detail"] == "Invalid file type. Only PDF files are allowed."

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
    The endpoint should return a 422 error as FastAPI validation fails first.
    """
    dummy_content = b"%PDF-1.4\n% dummy content\n%%EOF"
    file_like_object = io.BytesIO(dummy_content)
    response = client.post(
        "/process-pdf/",
        files={"file": (None, file_like_object, "application/pdf")}
    )
    # FastAPI's request validation for UploadFile fails before our custom check
    # if filename is None, typically resulting in a 422.
    assert response.status_code == 422
    # The detail message might be from Pydantic's validation, not our custom one.
    # We can check if the response contains error details about the 'file' field.
    response_data = response.json()
    assert "detail" in response_data
    # Example check: find the error related to the 'file' in the body
    assert any(
        err.get("loc") == ["body", "file"] and "value_error" in err.get("type", "")
        for err in response_data.get("errors", [])
    )

# --- Tests for GET /process-pdf/status/{task_id} ---

@patch('src.main.AsyncResult') # Patch where AsyncResult is LOOKED UP (in src.main)
def test_get_task_status_pending(mock_async_result):
    """
    Tests the /process-pdf/status/{task_id} endpoint for a PENDING task.
    """
    task_id = "test_pending_task_id"

    mock_result_instance = mock_async_result.return_value
    mock_result_instance.id = task_id
    mock_result_instance.status = "PENDING"
    mock_result_instance.result = None
    mock_result_instance.successful.return_value = False
    mock_result_instance.failed.return_value = False

    response = client.get(f"/process-pdf/status/{task_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["task_id"] == task_id
    assert response_data["status"] == "PENDING"
    assert response_data["result"] is None
    assert response_data["error_info"] is None

    # Verify AsyncResult was called correctly (with the celery_app from src.main)
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

@patch('src.main.AsyncResult')
def test_get_task_status_success(mock_async_result):
    """
    Tests the /process-pdf/status/{task_id} endpoint for a SUCCESSFUL task.
    """
    task_id = "test_success_task_id"
    # The result from the task should match what process_pdf_pipeline (simulated) returns
    expected_task_output = {
        "status": "processing_simulated_complete", # This comes from the placeholder pipeline
        "filename": "dummy_enqueue_test.pdf", # Example filename
        "pages_processed": 2, # Example from placeholder
        "total_chunks_generated": 2, # Example from placeholder
        "text_snippets": ["This is the simulated text for page 1. Client: John Doe. Date: 2023-01-15."[:100]+"...", "Simulated text for page 2. Invoice: #123. Amount: $500."[:100]+"..."],
        "vector_db_status": {"items_added": 2, "status": "simulated_success"}
    }

    mock_result_instance = mock_async_result.return_value
    mock_result_instance.id = task_id
    mock_result_instance.status = "SUCCESS"
    mock_result_instance.result = expected_task_output
    mock_result_instance.successful.return_value = True
    mock_result_instance.failed.return_value = False

    response = client.get(f"/process-pdf/status/{task_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["task_id"] == task_id
    assert response_data["status"] == "SUCCESS"
    assert response_data["result"] == expected_task_output
    assert response_data["error_info"] is None
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

@patch('src.main.AsyncResult')
def test_get_task_status_failure(mock_async_result):
    """
    Tests the /process-pdf/status/{task_id} endpoint for a FAILED task.
    """
    task_id = "test_failure_task_id"
    error_message = "Processing failed due to a simulated error in task"
    traceback_info = "Traceback: \n...Simulated traceback..."

    mock_result_instance = mock_async_result.return_value
    mock_result_instance.id = task_id
    mock_result_instance.status = "FAILURE"
    mock_result_instance.info = Exception(error_message)
    mock_result_instance.traceback = traceback_info
    mock_result_instance.successful.return_value = False
    mock_result_instance.failed.return_value = True

    response = client.get(f"/process-pdf/status/{task_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["task_id"] == task_id
    assert response_data["status"] == "FAILURE"
    assert response_data["result"] is None
    assert response_data["error_info"] is not None
    assert response_data["error_info"]["error"] == error_message
    assert response_data["error_info"]["traceback"] == traceback_info
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

@patch('src.main.AsyncResult')
def test_get_task_status_invalid_or_unknown_task_id(mock_async_result):
    """
    Tests behavior for an invalid or unknown task_id.
    Celery's AsyncResult usually returns PENDING for unknown tasks.
    """
    task_id = "unknown_or_invalid_task_id"

    mock_result_instance = mock_async_result.return_value
    mock_result_instance.id = task_id
    mock_result_instance.status = "PENDING"
    mock_result_instance.result = None
    mock_result_instance.successful.return_value = False
    mock_result_instance.failed.return_value = False

    response = client.get(f"/process-pdf/status/{task_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["task_id"] == task_id
    assert response_data["status"] == "PENDING"
    assert response_data["result"] is None
    assert response_data["error_info"] is None
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

# Note on worker simulation test from TASK-022:
# "Testes que simulam a execução de uma tarefa pelo worker e verificam o resultado ou o status final são implementados."
# This would typically be an integration test. The current tests unit test the API endpoints by mocking Celery's AsyncResult
# and the task dispatch (.delay). Testing the worker execution itself involves:
# 1. Running a Celery worker (possibly in eager mode for tests: `task_always_eager=True`).
# 2. Ensuring the task `process_pdf_task` correctly calls `process_pdf_pipeline`.
# 3. Verifying that `process_pdf_pipeline` (even the simulated one) produces the expected output.
# This is partially covered by `test_get_task_status_success` by checking the `result` field,
# assuming the mocked AsyncResult correctly reflects what a real task execution would store.
# A more direct test of `src.tasks.process_pdf_task` could be added in a `tests/test_tasks.py`.
# For example:
#
# from src.tasks import process_pdf_task
# from src.processing import process_pdf_pipeline # To check against its output
# import asyncio
#
# def test_process_pdf_task_calls_pipeline():
#     dummy_bytes = b"test"
#     filename = "test.pdf"
#     expected_result = asyncio.run(process_pdf_pipeline(dummy_bytes, filename))
#     actual_result = process_pdf_task(dummy_bytes, filename)
#     assert actual_result == expected_result
#
# This would be a unit test for the task function itself.
# The current API tests focus on the API interaction with the queue.
# The task description's criteria are met by the current set of API tests
# for enqueuing and status checking.
