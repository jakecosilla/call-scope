import io
import zipfile

import pytest

from app.application.batch_runner import BatchProcessor
from app.storage.store import BatchStore


def test_process_zip_bytes_valid():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test_call.wav", b"RIFF....WAVEfmt ....data....")
        zf.writestr("labels.csv", 'name,result_json\ntest_call.wav,"{""emotional_tone"":""neutral"",""emotional_intensity"":""low"",""background_noise_present"":false,""background_noise_type"":"""",""background_noise_severity"":""none"",""audio_quality"":""clear"",""speaker_overlap_present"":false,""long_silence_present"":false,""confidence"":0.5}"\n')

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


def test_unsafe_zip_path_is_rejected():
    z=io.BytesIO()
    with zipfile.ZipFile(z,"w") as f: f.writestr("../escape.wav",b"RIFF")
    with pytest.raises(ValueError,match="unsafe path"): BatchProcessor.process_zip_bytes(z.getvalue())

def test_invalid_manifest_result_json_is_rejected():
    z=io.BytesIO()
    with zipfile.ZipFile(z,"w") as f:
        f.writestr("test_call.wav",b"RIFF")
        f.writestr("labels.csv",'name,result_json\ntest_call.wav,"{}"\n')
    with pytest.raises(ValueError,match="invalid result_json"): BatchProcessor.process_zip_bytes(z.getvalue())


def test_process_audio_without_manifest_returns_none_validation():
    batch_id, validation = BatchProcessor.process_zip_bytes(
        b"RIFF....WAVEfmt ....data....", filename="test_call.wav", approach="approach_a"
    )

    assert batch_id
    assert validation is None


def test_standalone_csv_returns_manifest_specific_error():
    with pytest.raises(ValueError, match="manifest, not an audio batch"):
        BatchProcessor.process_zip_bytes(
            b"name,result_json\ntest.wav,{}\n", filename="labels.csv", approach="approach_a"
        )


def test_batch_store_recreates_schema_if_database_file_is_replaced(tmp_path):
    from app.storage.store import BatchStore

    db_path = tmp_path / "recreated.db"
    store = BatchStore(str(db_path))
    db_path.unlink()

    batch = store.create_batch("schema-recovery", 1, "2026-08-27T00:00:00+00:00")

    assert batch.batch_id == "schema-recovery"
    assert store.get_batch("schema-recovery") is not None
