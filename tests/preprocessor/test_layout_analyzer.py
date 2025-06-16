# -*- coding: utf-8 -*-
"""
Unit tests for the src.preprocessor.layout_analyzer module.
"""
import pytest
import logging
from unittest.mock import MagicMock, patch

# Module to test
from src.preprocessor import layout_analyzer
from src.preprocessor.layout_analyzer import (
    BoundingBox,
    LayoutBlockData,
    analyze_pdf_layout,
    _convert_docling_block_to_layout_block_data,
    # Assuming DOCLING_TYPE_MAP and DoclingLayoutBlockType might be needed for mock setup
)

# --- Fixtures ---

@pytest.fixture
def mock_docling_bbox(x=10.0, y=20.0, width=100.0, height=50.0):
    """Creates a mock Docling bounding box object."."""
    bbox = MagicMock()
    bbox.x = x
    bbox.y = y
    bbox.width = width
    bbox.height = height
    return bbox

@pytest.fixture
def mock_docling_text_block(mock_docling_bbox):
    """Creates a mock Docling layout block for TEXT."."""
    block = MagicMock()
    block.type = layout_analyzer.DoclingLayoutBlockType.TEXT # Assuming this is how types are represented
    block.bbox = mock_docling_bbox
    block.text_content = "This is some sample text."
    block.reading_order_id = 1
    block.confidence = 0.95
    return block

@pytest.fixture
def mock_docling_image_block(mock_docling_bbox):
    """Creates a mock Docling layout block for IMAGE."."""
    block = MagicMock()
    block.type = layout_analyzer.DoclingLayoutBlockType.IMAGE
    block.bbox = mock_docling_bbox
    block.text_content = None # Images usually don't have text_content directly
    block.reading_order_id = 2 # Example
    block.confidence = 0.88
    return block

@pytest.fixture
def mock_docling_unmapped_type_block(mock_docling_bbox):
    """Creates a mock Docling layout block with an unmapped type."."""
    # Create a mock enum value if DoclingLayoutBlockType is an enum
    mock_enum_val = MagicMock()
    mock_enum_val.name = "FIGURE" # Simulate an enum member .name attribute

    block = MagicMock()
    block.type = mock_enum_val # Use the mock enum value
    block.bbox = mock_docling_bbox
    block.text_content = "A figure caption."
    block.reading_order_id = 3
    return block


@pytest.fixture
def mock_docling_page(mock_docling_text_block, mock_docling_image_block):
    """Creates a mock Docling Page object with some layout blocks."."""
    page = MagicMock()
    page.id = "page_001"
    page.width = 595.0
    page.height = 842.0
    page.unit = "pt" # Assuming points
    page.layout_blocks = [mock_docling_text_block, mock_docling_image_block]
    page.text_content = "This is some sample text. " # Page level text
    return page

@pytest.fixture
def mock_empty_docling_page():
    """Creates a mock Docling Page object with no layout blocks."."""
    page = MagicMock()
    page.id = "page_002"
    page.width = 595.0
    page.height = 842.0
    page.unit = "pt"
    page.layout_blocks = []
    page.text_content = ""
    return page

@pytest.fixture
def mock_docling_document(mock_docling_page, mock_empty_docling_page):
    """Creates a mock DoclingDocument object."."""
    doc = MagicMock()
    doc.id = "doc_123"
    doc.source_path = "/path/to/dummy.pdf"
    doc.pages = [mock_docling_page, mock_empty_docling_page]
    return doc

# --- Tests for _convert_docling_block_to_layout_block_data ---

def test_convert_docling_text_block(mock_docling_text_block):
    page_w, page_h = 600.0, 800.0
    converted = _convert_docling_block_to_layout_block_data(mock_docling_text_block, page_w, page_h)
    assert isinstance(converted, LayoutBlockData)
    assert converted.type == "TEXT"
    assert converted.bbox_abs.x == mock_docling_text_block.bbox.x
    assert converted.bbox_abs.page_width == page_w
    assert converted.text_content == "This is some sample text."
    assert converted.reading_order_id == 1
    assert converted.confidence == 0.95
    assert converted.raw_block_type == str(layout_analyzer.DoclingLayoutBlockType.TEXT)

def test_convert_docling_image_block(mock_docling_image_block):
    page_w, page_h = 600.0, 800.0
    converted = _convert_docling_block_to_layout_block_data(mock_docling_image_block, page_w, page_h)
    assert isinstance(converted, LayoutBlockData)
    assert converted.type == "IMAGE"
    assert converted.text_content is None
    assert converted.raw_block_type == str(layout_analyzer.DoclingLayoutBlockType.IMAGE)

def test_convert_docling_unmapped_type_block(mock_docling_unmapped_type_block):
    page_w, page_h = 600.0, 800.0
    # To correctly test unmapped, we need to ensure DOCLING_TYPE_MAP doesn't have 'FIGURE'
    # For this test, we assume 'FIGURE' is not in DOCLING_TYPE_MAP by default.
    # If DoclingLayoutBlockType.FIGURE was a real enum member, it would be fine.
    # Here, mock_docling_unmapped_type_block.type is a MagicMock itself.

    # We need to ensure that DOCLING_TYPE_MAP.get(mock_enum_val, ...) works as expected.
    # The current _convert_docling_block_to_layout_block_data uses the enum value directly as key.
    # Let's simulate that the type is an enum that's not in the map.
    # The current mock_docling_unmapped_type_block.type is a MagicMock that has a .name attribute.
    # The code uses `getattr(docling_block, 'type', None)` which returns this MagicMock.
    # Then it does `DOCLING_TYPE_MAP.get(docling_block_type_enum_val, ...)`
    # For this to work as "unmapped", docling_block_type_enum_val must not be a key in DOCLING_TYPE_MAP.

    # Let's assume layout_analyzer.DoclingLayoutBlockType.FIGURE is not a defined key in DOCLING_TYPE_MAP
    # The mock_docling_unmapped_type_block.type is a MagicMock that will act as a unique key.

    converted = _convert_docling_block_to_layout_block_data(mock_docling_unmapped_type_block, page_w, page_h)
    assert isinstance(converted, LayoutBlockData)
    assert converted.type.startswith("UNMAPPED_") # e.g., UNMAPPED_<MagicMock name='FIGURE'>
    assert converted.text_content == "A figure caption."
    assert converted.raw_block_type == str(mock_docling_unmapped_type_block.type)


# --- Tests for analyze_pdf_layout ---

@patch('src.preprocessor.layout_analyzer.DocumentConverter')
def test_analyze_pdf_layout_success(MockDocumentConverter, mock_docling_document, caplog):
    caplog.set_level(logging.DEBUG)
    # Configure the mock DocumentConverter instance and its convert method
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value = mock_docling_document

    with patch('src.preprocessor.layout_analyzer.DOClING_AVAILABLE', True):
        result = analyze_pdf_layout("/fake/path.pdf")

    assert len(result) == 2 # Two pages from mock_docling_document
    # Page 1
    assert len(result[0]) == 2 # Two blocks from mock_docling_page
    assert result[0][0].type == "TEXT"
    assert result[0][0].text_content == "This is some sample text."
    assert result[0][1].type == "IMAGE"
    # Page 2
    assert len(result[1]) == 0 # Zero blocks from mock_empty_docling_page

    mock_converter_instance.convert.assert_called_once()
    # Check arguments of convert call if necessary:
    # args, kwargs = mock_converter_instance.convert.call_args
    # assert args[0] == "/fake/path.pdf"
    # assert ContentView.LAYOUT_BLOCKS in kwargs['params'].content_views
    assert "Successfully completed layout analysis" in caplog.text


@patch('src.preprocessor.layout_analyzer.DocumentConverter')
def test_analyze_pdf_layout_docling_unavailable(MockDocumentConverter, caplog):
    caplog.set_level(logging.WARNING)
    with patch('src.preprocessor.layout_analyzer.DOClING_AVAILABLE', False):
        result = analyze_pdf_layout("/fake/path.pdf")

    assert result == []
    assert "Docling library is not available. Cannot analyze PDF layout." in caplog.text
    MockDocumentConverter.assert_not_called()


@patch('src.preprocessor.layout_analyzer.DocumentConverter')
def test_analyze_pdf_layout_conversion_returns_none(MockDocumentConverter, caplog):
    caplog.set_level(logging.WARNING)
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value = None # Simulate Docling returning None

    with patch('src.preprocessor.layout_analyzer.DOClING_AVAILABLE', True):
        result = analyze_pdf_layout("/fake/path.pdf")

    assert result == []
    assert "Docling conversion of '/fake/path.pdf' resulted in no document or no pages." in caplog.text

@patch('src.preprocessor.layout_analyzer.DocumentConverter')
def test_analyze_pdf_layout_conversion_error(MockDocumentConverter, caplog):
    caplog.set_level(logging.ERROR)
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.side_effect = Exception("Simulated Docling conversion error")

    with patch('src.preprocessor.layout_analyzer.DOClING_AVAILABLE', True):
        result = analyze_pdf_layout("/fake/path.pdf")

    assert result == []
    assert "Error during Docling PDF layout analysis for '/fake/path.pdf': Simulated Docling conversion error" in caplog.text

@patch('src.preprocessor.layout_analyzer.DocumentConverter')
@patch('src.preprocessor.layout_analyzer._convert_docling_block_to_layout_block_data')
def test_analyze_pdf_layout_block_conversion_error(mock_convert_fn, MockDocumentConverter, mock_docling_document_one_page_one_block, caplog):
    # Setup: one page with one block, convert_fn will fail for that block
    mock_page_with_one_block = MagicMock()
    mock_page_with_one_block.layout_blocks = [MagicMock()] # One block
    mock_page_with_one_block.width = 100
    mock_page_with_one_block.height = 100

    mock_doc = MagicMock()
    mock_doc.pages = [mock_page_with_one_block]

    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value = mock_doc

    mock_convert_fn.side_effect = Exception("Simulated block conversion error")
    caplog.set_level(logging.ERROR)

    with patch('src.preprocessor.layout_analyzer.DOClING_AVAILABLE', True):
        result = analyze_pdf_layout("/fake/path.pdf")

    assert len(result) == 1      # One page processed
    assert len(result[0]) == 0   # No blocks successfully converted on that page
    assert "Error converting a Docling block: Simulated block conversion error" in caplog.text

# Minimal test for dataclasses just to ensure they can be instantiated
def test_dataclass_instantiation():
    bbox = BoundingBox(x=0, y=0, width=10, height=10, page_width=100, page_height=100)
    assert bbox.x == 0
    block = LayoutBlockData(type="TEXT", bbox_abs=bbox, text_content="hello")
    assert block.type == "TEXT"

# Fixture for the test_analyze_pdf_layout_block_conversion_error, was missing in prompt
@pytest.fixture
def mock_docling_document_one_page_one_block(mock_docling_text_block):
    page = MagicMock()
    page.id = "page_single_block"
    page.width = 595.0
    page.height = 842.0
    page.unit = "pt"
    page.layout_blocks = [mock_docling_text_block] # One block that could cause error during conversion
    page.text_content = "Single block page."

    doc = MagicMock()
    doc.id = "doc_single_page_single_block"
    doc.source_path = "/path/to/single_block.pdf"
    doc.pages = [page]
    return doc
