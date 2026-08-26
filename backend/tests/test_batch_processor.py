import io
import zipfile

import pytest

from app.application.batch_runner import BatchProcessor
from app.storage.store import BatchStore


def test_process_zip_bytes_valid():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test_call.wav", b"RIFF....WAVEfmt ....data....")
        zf.writestr("labels.csv", 'name,result_json\ntest_call.wav,"{}"\n')

    zip_bytes = zip_buffer.getvalue()
    batch_id, validation = BatchProcessor.process_zip_bytes(zip_bytes, approach="approach_a")

    assert batch_id is not None
    assert validation["matched_files"] == 1
    assert validation["total_manifest_rows"] == 1

    store = BatchStore.get_instance()
    batch = store.get_batch(batch_id)
    assert batch is not None
    assert batch.total_files == 1


def test_process_zip_bytes_oversized_rejection():
    fake_bytes = b"0" * (51 * 1024 * 1024)
    with pytest.raises(ValueError, match="Upload size exceeds"):
        BatchProcessor.process_zip_bytes(fake_bytes)
