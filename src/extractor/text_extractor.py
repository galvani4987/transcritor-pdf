# -*- coding: utf-8 -*-
"""
Module responsible for extracting text content from a preprocessed page image.

Uses a multimodal LLM via the configured Langchain client to perform OCR-like
text extraction from the image data.
"""

import base64
import io
import sys
from PIL import Image
# Import the function to get the initialized LLM client
from .llm_client import get_llm_client
# Import necessary Langchain components for multimodal input
from langchain_core.messages import HumanMessage, SystemMessage

def encode_image_to_base64(image: Image.Image) -> str:
    """Encodes a PIL Image object into a base64 string."""
    # Use BytesIO to handle the image in memory without saving to disk
    buffered = io.BytesIO()
    # Save the image to the buffer in a suitable format (e.g., WEBP or PNG)
    # Using WEBP lossless as it's our intermediate format, but PNG is also fine here.
    image.save(buffered, format="WEBP", lossless=True)
    # Get the byte string from the buffer
    img_bytes = buffered.getvalue()
    # Encode the byte string to base64
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    return base64_str

def extract_text_from_image(image: Image.Image) -> str | None:
    """
    Extracts text content from a given PIL Image using the configured LLM.

    Args:
        image: The preprocessed PIL Image object of a document page.

    Returns:
        The extracted text as a string, or None if extraction fails.

    Raises:
        Exception: If errors occur during LLM client interaction or image processing.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    print(f"Starting text extraction for image (mode: {image.mode}, size: {image.size})...")

    try:
        # Get the initialized LLM client
        llm = get_llm_client() # This function handles initialization and config loading

        # --- Prepare the image for the multimodal LLM ---
        # Most multimodal models expect the image encoded as a base64 string.
        base64_image = encode_image_to_base64(image)

        # --- Construct the prompt for the LLM ---
        # This prompt needs to instruct the model to perform OCR on the image.
        # The structure for multimodal input varies slightly between models/Langchain versions.
        # This is a common pattern using HumanMessage with a content list.
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Extract all the text content from this image of a document page. Focus on accuracy and preserving the original structure as much as possible. Output only the extracted text.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        # Use the data URI scheme for base64 encoded images
                        "url": f"data:image/webp;base64,{base64_image}"
                    },
                },
            ]
        )

        # --- Invoke the LLM ---
        print("  Sending image to LLM for text extraction...")
        # Add SystemMessage for better context if needed (optional)
        # system_prompt = SystemMessage(content="You are an expert OCR engine specialized in medical documents.")
        # response = llm.invoke([system_prompt, message])
        response = llm.invoke([message])

        # --- Process the response ---
        # The actual text is usually in the 'content' attribute of the response object
        if hasattr(response, 'content'):
            extracted_text = response.content
            print("  LLM extraction successful.")
            # print(f"  Extracted Text Snippet: {extracted_text[:100]}...") # Optional: Log snippet
            return extracted_text
        else:
            print(f"  Error: Unexpected LLM response format: {response}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Error during text extraction: {e}", file=sys.stderr)
        # Decide whether to return None or re-raise the exception
        # Returning None might allow the pipeline to continue with other pages
        # Re-raising stops the whole process
        # raise # Option to re-raise
        return None # Option to return None and let main loop handle it

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    print("\n--- Running text_extractor.py directly for testing ---")
    # This requires a sample image file and a configured .env file for the LLM client

    import os
    test_image_dir = "temp_test_loader" # Use the same dir as other tests
    test_image_path = os.path.join(test_image_dir, "processed_test_image.png") # Use the processed image if available

    if os.path.exists(test_image_path):
        print(f"\nLoading test image: {test_image_path}")
        input_image = None
        try:
            input_image = Image.open(test_image_path)
            input_image.load()
            print(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")

            # Attempt text extraction
            extracted_text = extract_text_from_image(input_image)

            if extracted_text is not None:
                print("\n--- Extracted Text ---")
                print(extracted_text)
                print("----------------------")
            else:
                print("\nText extraction failed or returned None.")

        except FileNotFoundError:
             print(f"Error: Test image not found at {test_image_path}")
        except Exception as e:
             print(f"An error occurred during testing: {e}")
        finally:
            # Close image if opened
            if input_image:
                input_image.close()
            # Note: We leave the dummy input and processed output files for inspection.

    else:
        print(f"\nTest image not found at '{test_image_path}'.")
        print(f"Please ensure the test image exists (e.g., by running the image_processor.py test first)")
        print(f"or update the 'test_image_path' variable in this script.")
        print("Also ensure your .env file is configured correctly for the LLM client.")

    print("\n--- Text Extractor Test Complete ---")