# -*- coding: utf-8 -*-
"""
Module responsible for extracting text content from a preprocessed page image.

Uses a multimodal LLM via the configured Langchain client to perform OCR-like
text extraction from the image data. Includes logging.
"""

import base64
import io
import sys
import logging # Import logging
from PIL import Image
# Import the function to get the initialized LLM client
from .llm_client import get_llm_client
# Import necessary Langchain components for multimodal input
from langchain_core.messages import HumanMessage # Removed SystemMessage import for now

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def encode_image_to_base64(image: Image.Image) -> str:
    """Encodes a PIL Image object into a base64 string."""
    try:
        buffered = io.BytesIO()
        # Using WEBP lossless as it's our intermediate format
        image.save(buffered, format="WEBP", lossless=True)
        img_bytes = buffered.getvalue()
        base64_str = base64.b64encode(img_bytes).decode('utf-8')
        return base64_str
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}", exc_info=True)
        raise # Re-raise the error to be caught by the caller

def extract_text_from_image(image: Image.Image) -> str | None:
    """
    Extracts text content from a given PIL Image using the configured LLM.

    Args:
        image: The preprocessed PIL Image object of a document page.

    Returns:
        The extracted text as a string, or None if extraction fails.
    Raises:
        TypeError: If input is not a PIL Image object.
        Exception: If errors occur during LLM client interaction or image processing.
    """
    if not isinstance(image, Image.Image):
        # Log error and raise TypeError for incorrect input type
        logger.error("Invalid input type for text extraction: Expected PIL Image.")
        raise TypeError("Input must be a PIL Image object.")

    logger.info(f"Starting text extraction for image (mode: {image.mode}, size: {image.size})...")

    try:
        # Get the initialized LLM client
        llm = get_llm_client() # This function handles initialization and config loading

        # --- Prepare the image for the multimodal LLM ---
        logger.debug("Encoding image to base64 for LLM...")
        base64_image = encode_image_to_base64(image)
        logger.debug("Image successfully encoded.")

        # --- Construct the prompt for the LLM ---
        # Using the pattern from previous implementation
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Extract all the text content from this image of a document page. Focus on accuracy and preserving the original structure as much as possible. Output only the extracted text.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/webp;base64,{base64_image}" # Specify webp format
                    },
                },
            ]
        )

        # --- Invoke the LLM ---
        logger.info("Sending image to LLM for text extraction...")
        response = llm.invoke([message])

        # --- Process the response ---
        if hasattr(response, 'content'):
            extracted_text = response.content
            logger.info("LLM extraction successful.")
            # logger.debug(f"Extracted Text Snippet: {extracted_text[:100]}...") # Optional debug log
            return extracted_text
        else:
            logger.error(f"Unexpected LLM response format: {response}")
            return None

    except Exception as e:
        # Log errors from encoding, client getting, or LLM invocation
        logger.error(f"Error during text extraction: {e}", exc_info=True)
        # Returning None allows the main pipeline to potentially continue with other pages
        return None

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running text_extractor.py directly for testing ---")

    import os # Import os for file operations

    test_image_dir = "temp_test_loader"
    test_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png") # Use processed image

    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            extracted_text = extract_text_from_image(input_image)

            if extracted_text is not None:
                logger.info("--- Extracted Text ---")
                print(extracted_text) # Print the result directly in the test
                logger.info("----------------------")
            else:
                logger.warning("Text extraction failed or returned None.")

        except FileNotFoundError:
             logger.error(f"Test image not found at {test_image_path}")
        except Exception as e:
             logger.error(f"An error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()

    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
        logger.warning("Please ensure the test image exists (e.g., by running image_processor.py test)")
        logger.warning("Also ensure your .env file is configured correctly for the LLM client.")

    logger.info("--- Text Extractor Test Complete ---")