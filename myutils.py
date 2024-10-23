from datetime import datetime
from arcgis.geocoding import reverse_geocode


def get_unique_fs_name_per_env(fs_name, hosting_env):
    # For non-production environment, append env suffix to feature service name
    if hosting_env != "PROD":
        return f"{fs_name}_{hosting_env}"
    
    # For production environment, leave as is
    return fs_name


def sanitize_fs_name(mission_name):
    BLOB_NAME_SPLITTER = '-'
    FS_NAME_SPLITTER = '_'

    fs_name = mission_name.replace(BLOB_NAME_SPLITTER, FS_NAME_SPLITTER)

    return fs_name

def convert_iso8601_to_epoch_ms(iso8601_time_str):
    if iso8601_time_str is None or iso8601_time_str.strip == "":
        return None

    dt = datetime.fromisoformat(iso8601_time_str.replace('Z', '+00:00'))
    epoch_ms = int(dt.timestamp() * 1000)
    return epoch_ms

