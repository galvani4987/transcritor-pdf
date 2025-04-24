# -*- coding: utf-8 -*-
"""Extracts text content from preprocessed page images using a multimodal LLM.

This module utilizes the configured Langchain LLM client (obtained via
`llm_client.get_llm_client`) to perform Optical Character Recognition (OCR)
or text extraction directly from image data. It handles encoding the image
and constructing the appropriate prompt for the multimodal model.
Includes logging for operations and errors.
"""

import base64
import io
import sys
import logging
from typing import Optional # <<< CORRECTION: Added Optional import
from PIL import Image
# Import the function to get the initialized LLM client
from .llm_client import get_llm_client
# Import necessary Langchain components for multimodal input
from langchain_core.messages import HumanMessage

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def encode_image_to_base64(image: Image.Image, format: str = "WEBP") -> str:
    """Encodes a PIL Image object into a base64 data URI string.

    Args:
        image: The PIL Image object to encode.
        format: The image format to use for encoding (e.g., "WEBP", "PNG", "JPEG").
                Defaults to "WEBP". Lossless WEBP is preferred for quality.

    Returns:
        A base64 encoded string representation of the image, prefixed with the
        appropriate data URI scheme (e.g., "data:image/webp;base64,...").

    Raises:
        Exception: If errors occur during image saving to buffer or base64 encoding.
                   Logs the error before raising.
    """
    logger.debug(f"Encoding image to base64 using format: {format}")
    try:
        buffered = io.BytesIO()
        save_kwargs = {"format": format}
        if format.upper() == "WEBP":
            save_kwargs["lossless"] = True
        image.save(buffered, **save_kwargs)
        img_bytes = buffered.getvalue()
        base64_str = base64.b64encode(img_bytes).decode('utf-8')
        mime_type = f"image/{format.lower()}"
        return f"data:{mime_type};base64,{base64_str}"
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}", exc_info=True)
        raise

def extract_text_from_image(image: Image.Image) -> Optional[str]: # Optional is used here
    """Extracts text content from an image using a multimodal LLM.

    Takes a preprocessed PIL Image object, encodes it to base64, sends it
    to the configured multimodal LLM (via Langchain client) with a prompt
    instructing it to perform text extraction, and returns the extracted text.

    Args:
        image: The preprocessed PIL Image object of a document page.

    Returns:
        The extracted text as a single string if successful, otherwise None
        if an error occurs during the process or the LLM response is invalid.

    Raises:
        TypeError: If the input `image` is not a PIL Image object.
        RuntimeError: If the LLM client cannot be initialized (propagated from
                      `get_llm_client`).
        Exception: For errors during image encoding or LLM API interaction.
                   These are logged, and the function typically returns None
                   instead of re-raising to allow pipeline continuation.
    """
    if not isinstance(image, Image.Image):
        msg = "Invalid input type for text extraction: Expected PIL Image."
        logger.error(msg)
        raise TypeError(msg)

    logger.info(f"Starting text extraction for image (mode: {image.mode}, size: {image.size})...")

    try:
        llm = get_llm_client()
        logger.debug("Encoding image to base64 data URI for LLM...")
        base64_data_uri = encode_image_to_base64(image, format="WEBP")
        logger.debug(f"Image successfully encoded (URI length: {len(base64_data_uri)}).")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Extract all text content from the provided image of a document page. "
                            "Preserve the original structure (paragraphs, line breaks) as accurately as possible. "
                            "Output only the extracted text, without any additional commentary or formatting.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": base64_data_uri},
                },
            ]
        )

        logger.info("Sending image and prompt to LLM for text extraction...")
        response = llm.invoke([message]) # Pass the list containing the message

        if hasattr(response, 'content') and isinstance(response.content, str):
            extracted_text = response.content
            logger.info("LLM text extraction successful.")
            logger.debug(f"Extracted Text Snippet: {extracted_text[:100]}...")
            return extracted_text
        else:
            logger.error(f"Unexpected LLM response format or type. Response: {response}")
            return None

    except TypeError as e:
        logger.error(f"Type error during text extraction: {e}", exc_info=True)
        raise
    except RuntimeError as e:
         logger.error(f"LLM client runtime error during text extraction: {e}", exc_info=True)
         raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during text extraction: {e}", exc_info=True)
        return None

# Example usage block (remains the same)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running text_extractor.py directly for testing ---")
    test_image_dir = "temp_test_loader"
    test_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")
    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")
            logger.info("Attempting text extraction (requires configured .env)...")
            extracted_text = extract_text_from_image(input_image)
            if extracted_text is not None:
                logger.info("--- Extracted Text ---")
                print(extracted_text)
                logger.info("----------------------")
            else:
                logger.warning("Text extraction failed or returned None.")
        except FileNotFoundError: logger.error(f"Test image not found at {test_image_path}")
        except (TypeError, RuntimeError) as e: logger.error(f"Test failed due to configuration or input error: {e}")
        except Exception as e: logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
        logger.warning("Please ensure the test image exists (e.g., by running image_processor.py test)")
        logger.warning("Also ensure your .env file is configured correctly for the LLM client.")
    logger.info("--- Text Extractor Test Complete ---")