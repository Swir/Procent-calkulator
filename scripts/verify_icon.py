"""Compare PE icon resources with the selected source ICO before publication."""
import hashlib
from pathlib import Path
import struct

def verify_executable_icon(executable, icon_path):
    import pefile
    ico = Path(icon_path).read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", ico)
    if reserved != 0 or kind != 1 or count == 0:
        raise ValueError("Invalid source ICO")
    expected = []
    for index in range(count):
        size, offset = struct.unpack_from("<II", ico, 6 + 16 * index + 8)
        expected.append(hashlib.sha256(ico[offset:offset + size]).digest())
    found = []
    groups = []
    with pefile.PE(str(executable)) as pe:
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id not in (3, 14):
                continue
            for item in entry.directory.entries:
                for language in item.directory.entries:
                    resource = language.data.struct
                    data = pe.get_data(resource.OffsetToData, resource.Size)
                    if entry.id == 3:
                        found.append(hashlib.sha256(data).digest())
                    else:
                        groups.append(struct.unpack_from("<HHH", data)[2])
    if sorted(found) != sorted(expected) or groups != [count]:
        raise RuntimeError("EXE icon does not match the selected application/SwirUI icon")
