import sys
import os
from pathlib import Path
import shutil
import logging

# Setup basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("docling_experiment")

# Try to import pypdfium2, fail gracefully if not found (though it should be in requirements)
try:
    import pypdfium2 as pdfium
    PYPDFIUM_AVAILABLE = True
    logger.info("pypdfium2 imported successfully.")
except ImportError:
    PYPDFIUM_AVAILABLE = False
    logger.error("pypdfium2 not found. Cannot create dummy PDF for Docling experiment.")
    sys.exit(1)

# Try to import docling, fail gracefully if not found
try:
    from docling import DocumentConverter, ConversionParameters
    from docling.datamodel.structure import ContentView
    DOClING_AVAILABLE = True
    logger.info("Docling imported successfully.")
except ImportError:
    DOClING_AVAILABLE = False
    logger.error("Docling library not found. Please ensure it's installed.")
    logger.error("This might be due to the `pip install` issue in the previous step.")
    logger.error("If Docling is not installed, this experiment cannot proceed.")
    sys.exit(1) # Exit if docling is not available

def create_dummy_pdf(pdf_path: Path, num_pages: int = 2) -> bool:
    if not PYPDFIUM_AVAILABLE:
        logger.error("Cannot create dummy PDF, pypdfium2 is not available.")
        return False
    try:
        logger.info(f"Creating dummy PDF at: {pdf_path} with {num_pages} pages.")
        pdf = pdfium.PdfDocument.new()
        for i in range(num_pages):
            page = pdf.new_page(width=595, height=842) # A4 size in points
            # Add some simple text to make it processable by Docling
            font = pdfium.PdfFont.new(pdf, "Helvetica", "WinAnsiEncoding") # Standard font
            text_object = page.new_text_object(font, 12) # Font size 12
            text_object.set_text(f"This is page {i+1} of the dummy PDF for Docling testing.")
            text_object.set_matrix((1, 0, 0, 1, 50, 750 - (i * 50))) # Position text
            page.add_object(text_object)
            page.generate_content() # Finalize page content
        pdf.save(str(pdf_path))
        pdf.close()
        logger.info(f"Dummy PDF created successfully: {pdf_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create dummy PDF: {e}", exc_info=True)
        return False

def run_docling_experiment():
    if not DOClING_AVAILABLE:
        logger.error("Docling is not available. Aborting experiment.")
        return

    temp_dir = Path("temp_docling_experiment_dir")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created temporary directory: {temp_dir}")

    dummy_pdf_path = temp_dir / "experiment_dummy.pdf"

    if not create_dummy_pdf(dummy_pdf_path, num_pages=2):
        logger.error("Exiting experiment due to dummy PDF creation failure.")
        shutil.rmtree(temp_dir)
        return

    logger.info(f"--- Starting Docling Processing for {dummy_pdf_path} ---")
    try:
        # Initialize DocumentConverter
        # For local testing, we might not need complex configurations.
        # The default converter should be able to handle basic PDF parsing.
        converter = DocumentConverter()
        logger.info("DocumentConverter initialized.")

        # Define conversion parameters - enable layout analysis if specific flags are needed
        # Based on Docling docs, layout analysis is a core part of PDF processing.
        # We might want to specify output views, e.g., TEXT, LAYOUT_BLOCKS
        params = ConversionParameters(
            content_views=[ContentView.TEXT, ContentView.LAYOUT_BLOCKS, ContentView.STRUCTURE]
        )
        logger.info(f"ConversionParameters set for views: {[v.name for v in params.content_views]}")

        # Convert the document
        logger.info(f"Calling converter.convert() on {dummy_pdf_path}")
        docling_doc = converter.convert(source=str(dummy_pdf_path), params=params)
        logger.info("Docling conversion complete.")

        if not docling_doc:
            logger.error("Docling conversion returned None or an empty document.")
            return

        logger.info(f"--- DoclingDocument Structure ---")
        logger.info(f"Document ID: {docling_doc.id}")
        logger.info(f"Source Path: {docling_doc.source_path}")
        logger.info(f"Number of pages: {len(docling_doc.pages)}")

        for i, page in enumerate(docling_doc.pages):
            logger.info(f"  --- Page {i+1} (ID: {page.id}) ---")
            logger.info(f"  Page Size (width x height): {page.width} x {page.height} {page.unit}")

            if page.text_content:
                logger.info(f"  Page Full Text (first 100 chars): '{page.text_content[:100].strip()}...'")

            if page.layout_blocks:
                logger.info(f"  Found {len(page.layout_blocks)} layout blocks:")
                for j, block in enumerate(page.layout_blocks):
                    logger.info(f"    Block {j+1}: Type='{block.type.name if block.type else 'N/A'}'")
                    logger.info(f"      Bounding Box (xywh): {block.bbox.x}, {block.bbox.y}, {block.bbox.width}, {block.bbox.height}")
                    logger.info(f"      Text (first 50 chars): '{block.text_content[:50].strip()}...'")
                    if block.reading_order_id is not None:
                         logger.info(f"      Reading Order ID: {block.reading_order_id}")
            else:
                logger.info("  No layout blocks found on this page through page.layout_blocks.")

            # Alternative way to explore structure, if available from Docling documentation
            # This part is speculative and depends on exact DoclingDocument structure
            if hasattr(page, 'elements') and page.elements:
                logger.info(f"  Found {len(page.elements)} generic elements:")
                for k, elem in enumerate(page.elements):
                    elem_type = getattr(elem, 'type', 'UnknownType')
                    elem_bbox = getattr(elem, 'bbox', None)
                    elem_text = getattr(elem, 'text_content', '')
                    logger.info(f"    Element {k+1}: Type='{elem_type}' Text='{elem_text[:30].strip()}...' BBox='{elem_bbox}'")

            logger.info(f"  --- End of Page {i+1} ---")

    except Exception as e:
        logger.error(f"An error occurred during Docling experiment: {e}", exc_info=True)
    finally:
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        logger.info("--- Docling Experiment Finished ---")

if __name__ == "__main__":
    run_docling_experiment()
