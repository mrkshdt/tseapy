import io

from werkzeug.datastructures import FileStorage

from tseapy.data.upload import CSVUploadError, parse_csv_upload


def test_parse_csv_upload_autodetects_delimiter():
    storage = FileStorage(stream=io.BytesIO(b"a;b\n1;2\n"), filename="a.csv")
    dataframe = parse_csv_upload(storage)
    assert dataframe.columns.tolist() == ["a", "b"]
    assert dataframe.iloc[0]["b"] == 2


def test_parse_csv_upload_empty_file():
    storage = FileStorage(stream=io.BytesIO(b""), filename="empty.csv")
    try:
        parse_csv_upload(storage)
    except CSVUploadError:
        return
    assert False, "Expected CSVUploadError for empty file"
