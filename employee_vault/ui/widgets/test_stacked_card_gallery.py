import pytest
from PySide6.QtWidgets import QApplication
from employee_vault.ui.widgets.stacked_card_gallery import StackedCardGallery, GalleryPreviewDialog

app = QApplication([])

def test_gallery_widget_styles():
    gallery = StackedCardGallery()
    # Check header style uses TOKENS
    header_style = gallery.header.styleSheet()
    assert 'color:' in header_style and 'padding:' in header_style
    # Check card area style uses TOKENS
    card_area_style = gallery._card_container.styleSheet()
    assert 'background:' in card_area_style and 'border-radius:' in card_area_style

def test_error_dialog_styles():
    gallery = StackedCardGallery()
    gallery.show_error('Test error')
    dialog = gallery.error_dialog
    style = dialog.styleSheet()
    assert 'background:' in style and 'color:' in style and 'border-radius:' in style

def test_gallery_preview_dialog_styles():
    dialog = GalleryPreviewDialog([], title='Test Gallery')
    style = dialog.styleSheet()
    assert 'background:' in style and 'border-radius:' in style
    # Check title label style
    title_label = dialog.findChild(type(dialog._gallery.header), None)
    assert title_label is not None

if __name__ == '__main__':
    pytest.main([__file__])
