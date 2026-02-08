import io

import pandas as pd
from charset_normalizer import from_bytes
from pandas.errors import EmptyDataError, ParserError
from werkzeug.datastructures import FileStorage


class CSVUploadError(ValueError):
    """Raised when uploaded CSV content cannot be parsed safely."""


def parse_csv_upload(file_storage: FileStorage) -> pd.DataFrame:
    raw = file_storage.read()
    if not raw:
        raise CSVUploadError("The uploaded file is empty.")

    best_match = from_bytes(raw).best()
    encoding = best_match.encoding if best_match and best_match.encoding else "utf-8"

    try:
        dataframe = pd.read_csv(
            io.BytesIO(raw),
            sep=None,
            engine="python",
            on_bad_lines="skip",
            encoding=encoding
        )
    except ParserError as exc:
        raise CSVUploadError("Could not parse this CSV file. Please check delimiter and row format.") from exc
    except UnicodeDecodeError as exc:
        raise CSVUploadError("Could not decode this file. Please export it as UTF-8 CSV and try again.") from exc
    except EmptyDataError as exc:
        raise CSVUploadError("The uploaded CSV does not contain any rows.") from exc
    except MemoryError as exc:
        raise CSVUploadError("The file is too large to parse in memory.") from exc

    if dataframe.empty and len(dataframe.columns) == 0:
        raise CSVUploadError("The uploaded CSV does not contain tabular data.")

    return dataframe
