from unittest.mock import patch

import pytest


@pytest.fixture
def mock_streamlit():
    """Mock streamlit for testing without UI"""
    with (
        patch("streamlit.set_page_config"),
        patch("streamlit.markdown"),
        patch("streamlit.sidebar"),
        patch("streamlit.columns"),
        patch("streamlit.text_input"),
        patch("streamlit.text_area"),
        patch("streamlit.button"),
        patch("streamlit.success"),
        patch("streamlit.error"),
        patch("streamlit.info"),
        patch("streamlit.warning"),
        patch("streamlit.spinner"),
        patch("streamlit.tabs"),
        patch("streamlit.expander"),
        patch("streamlit.rerun"),
    ):
        yield
