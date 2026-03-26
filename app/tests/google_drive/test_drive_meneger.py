from unittest.mock import Mock
import pytest

from app.google_drive.drive_manager import GoogleDriveFileManager

def test_folder_exists_none_file():
    mock_client = Mock()

    mock_client.list.return_value = {
        "files": None
    }

    manager = GoogleDriveFileManager(client=mock_client)

    result = manager.folder_exist_by_name(
        parent_folder_id="parent_id",
        page_size=10,
        folder_name="2024",
    )

    assert result == None
    mock_client.list.assert_called_once()

def test_folder_exists_duplicate_files():
    mock_client = Mock()

    mock_client.list.return_value = {
        "files": [
            {
            "id": "1a2b3c",
            "name": "2024",
            "mimeType": "application/vnd.google-apps.folder"
            },
            {
            "id": "1a2b3c",
            "name": "2024",
            "mimeType": "application/vnd.google-apps.folder"
            },
        ]
}

    manager = GoogleDriveFileManager(client=mock_client)

    with pytest.raises(ValueError) as exc:
        manager.folder_exist_by_name(
            parent_folder_id="parent_id",
            page_size=10,
            folder_name="2024",
        )


    assert str(exc.value) == "2024 has duplicate"    
    mock_client.list.assert_called_once()