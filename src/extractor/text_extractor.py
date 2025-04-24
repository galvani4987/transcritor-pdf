# -*- coding: utf-8 -*-
"""Extracts text content from preprocessed page images using a multimodal LLM.

Includes specific error handling for OpenAI API exceptions.
"""

import base64
import io
import sys
import logging
from typing import Optional
from PIL import Image
# Import the function to get the initialized LLM client
from .llm_client import get_llm_client
# Import necessary Langchain components
from langchain_core.messages import HumanMessage
# Import specific OpenAI exceptions for handling
try:
    from openai import (
        APIError,             # Base class for API errors
        APIConnectionError,   # Network issues
        APITimeoutError,      # Request timed out
        AuthenticationError,  # Invalid API key / auth issues
        BadRequestError,      # Invalid request (e.g., bad params, model not found)
        PermissionDeniedError,# Key lacks permission for the resource
        RateLimitError        # Rate limit exceeded
    )
    OPENAI_ERRORS_AVAILABLE = True
except ImportError:
    # Define dummy exceptions if openai library isn't installed or has changed structure
    # This allows the code to load but fail gracefully if errors occur later.
    OPENAI_ERRORS_AVAILABLE = False
    class APIError(Exception): pass
    class APIConnectionError(APIError): pass
    class APITimeoutError(APIError): pass
    class AuthenticationError(APIError): pass
    class BadRequestError(APIError): pass
    class PermissionDeniedError(APIError): pass
    class RateLimitError(APIError): pass
    logging.warning("openai library not found or exceptions changed. Specific API error handling may be limited.")


# Get a logger instance for this module
logger = logging.getLogger(__name__)

def encode_image_to_base64(image: Image.Image, format: str = "WEBP") -> str:
    """Encodes a PIL Image object into a base64 data URI string."""
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

def extract_text_from_image(image: Image.Image) -> Optional[str]:
    """Extracts text content from an image using a multimodal LLM with specific error handling.

    Args:
        image: The preprocessed PIL Image object of a document page.

    Returns:
        The extracted text as a single string if successful, otherwise None.

    Raises:
        TypeError: If the input `image` is not a PIL Image object.
        RuntimeError: If the LLM client cannot be initialized.
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
                {"type": "text", "text": "Extract all text content..."}, # Keep prompt concise here
                {"type": "image_url", "image_url": {"url": base64_data_uri}},
            ]
        )

        logger.info("Sending image and prompt to LLM for text extraction...")
        # --- Enhanced Error Handling around invoke ---
        response = None
        try:
            response = llm.invoke([message])
        except AuthenticationError as e:
            logger.critical(f"OpenAI API Authentication Error: Invalid API Key? {e}", exc_info=True)
            # Fail fast for auth errors
            raise RuntimeError("API Authentication Failed") from e
        except PermissionDeniedError as e:
             logger.critical(f"OpenAI API Permission Error: Key lacks permission for model/resource? {e}", exc_info=True)
             raise RuntimeError("API Permission Denied") from e
        except RateLimitError as e:
            logger.error(f"OpenAI API Rate Limit Exceeded: {e}", exc_info=True)
            # TODO: Implement retry logic here? For now, return None.
            return None
        except APITimeoutError as e:
             logger.error(f"OpenAI API Timeout Error: {e}", exc_info=True)
             # TODO: Implement retry logic here? For now, return None.
             return None
        except APIConnectionError as e:
             logger.error(f"OpenAI API Connection Error: Network issue? {e}", exc_info=True)
             # Possibly retry? For now, return None.
             return None
        except BadRequestError as e:
             # E.g., Invalid request, prompt too long, model not found
             logger.error(f"OpenAI API Bad Request Error: {e}", exc_info=True)
             # Usually not recoverable, return None. Check e.code if needed.
             return None
        except APIError as e: # Catch other OpenAI API errors (like 5xx server errors)
             logger.error(f"OpenAI API Error (Server issue?): {e}", exc_info=True)
             # Possibly retry? For now, return None.
             return None
        # --- End Enhanced Error Handling ---

        # Process successful response
        if hasattr(response, 'content') and isinstance(response.content, str):
            extracted_text = response.content
            logger.info("LLM text extraction successful.")
            logger.debug(f"Extracted Text Snippet: {extracted_text[:100]}...")
            return extracted_text
        else:
            logger.error(f"Unexpected LLM response format or type after successful call. Response: {response}")
            return None

    except TypeError as e: # Catch TypeError from input validation
        logger.error(f"Type error during text extraction setup: {e}", exc_info=True)
        raise
    except RuntimeError as e: # Catch client initialization errors
         logger.error(f"LLM client runtime error during text extraction: {e}", exc_info=True)
         raise
    except Exception as e: # Catch other unexpected errors (e.g., encoding)
        logger.error(f"An unexpected error occurred during text extraction: {e}", exc_info=True)
        return None

# Example usage block (remains the same)
if __name__ == "__main__":
    # ...(Testing block remains unchanged)...
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running text_extractor.py directly for testing ---")
    test_image_dir = "temp_test_loader"; test_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")
    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        try:
            input_image = Image.open(test_image_path); input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")
            logger.info("Attempting text extraction (requires configured .env)...")
            extracted_text = extract_text_from_image(input_image)
            if extracted_text is not None: logger.info("--- Extracted Text ---"); print(extracted_text); logger.info("----------------------")
            else: logger.warning("Text extraction failed or returned None.")
        except FileNotFoundError: logger.error(f"Test image not found at {test_image_path}")
        except (TypeError, RuntimeError) as e: logger.error(f"Test failed due to configuration or input error: {e}")
        except Exception as e: logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
    logger.info("--- Text Extractor Test Complete ---")