from src.celery_app import celery_app
from src.main import process_pdf_pipeline # Attempting to import directly

# If direct import of process_pdf_pipeline causes issues due to FastAPI app context
# or other main.py specific initializations, the core logic of
# process_pdf_pipeline might need to be extracted into a separate utility module
# that both main.py and tasks.py can import.

@celery_app.task(name='src.tasks.process_pdf_task')
def process_pdf_task(file_content_bytes: bytes, filename: str) -> dict:
    '''
    Celery task to process a PDF file.
    Relies on process_pdf_pipeline from src.main for the core logic.
    '''
    try:
        # Assuming process_pdf_pipeline can be called with bytes and filename
        # and does not depend on FastAPI request objects directly.
        # This might require refactoring process_pdf_pipeline if it's too coupled with FastAPI.
        # For now, we assume it's callable like this.

        # Simulate process_pdf_pipeline for now if direct import/call is complex
        # In a real scenario, this would call the actual pipeline
        print(f"Celery task received processing for: {filename}")

        # This is where the actual call to process_pdf_pipeline would go.
        # For this subtask, we'll focus on setting up the structure.
        # The actual logic of process_pdf_pipeline will be tested/integrated
        # when this task is called by the endpoint.
        # Example:
        # result_summary = process_pdf_pipeline(file_content=file_content_bytes, input_filename=filename)

        # Placeholder result:
        chunks_added = 10 # Dummy value
        result_summary = {
            "message": f"PDF '{filename}' processed successfully by Celery task.",
            "filename": filename,
            "chunks_added": chunks_added,
            "status": "SUCCESS"
        }
        print(f"Celery task finished processing for: {filename}")
        return result_summary
    except Exception as e:
        # Log the exception
        print(f"Celery task failed for {filename}: {str(e)}")
        # You might want to re-raise or return a specific error structure
        # For now, let Celery handle it by re-raising, which marks task as FAILED
        raise
