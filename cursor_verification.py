"""Regression probe for our own native window; no mouse input is injected."""
import ctypes


def check_window_cursor(hwnd):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.LoadCursorW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.LoadCursorW.restype = ctypes.c_void_p
    user32.GetCursor.argtypes = []
    user32.GetCursor.restype = ctypes.c_void_p
    user32.SetCursor.argtypes = [ctypes.c_void_p]
    user32.SetCursor.restype = ctypes.c_void_p
    user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    def load(resource):
        result = user32.LoadCursorW(None, ctypes.c_void_p(resource))
        assert result, f"Unable to load cursor {resource}"
        return result
    arrow = load(32512)
    previous = user32.GetCursor()
    scenarios = []
    try:
        # Native hit-test results: left, right, top, bottom and four corners.
        cases = [(10, 32644), (11, 32644), (12, 32645), (15, 32645),
                 (13, 32642), (17, 32642), (14, 32643), (16, 32643)]
        for hit, resource in cases:
            expected_border = load(resource)
            user32.SendMessageW(hwnd, 0x0020, hwnd, hit | (0x0200 << 16))
            assert user32.GetCursor() == expected_border, f"Border cursor changed at hit {hit}"
            user32.SendMessageW(hwnd, 0x0020, hwnd, 1 | (0x0200 << 16))
            actual = user32.GetCursor()
            assert actual == arrow, f"Client cursor remains a resize pointer after hit {hit}: {actual} != {arrow}"
            scenarios.append(f"border {hit} -> normal client pointer")
        for resource in (32513, 32514):  # I-beam and wait cursors inherited from elsewhere.
            user32.SetCursor(load(resource))
            user32.SendMessageW(hwnd, 0x0020, hwnd, 1 | (0x0200 << 16))
            assert user32.GetCursor() == arrow, "Client failed to restore its own cursor"
            scenarios.append(f"inherited cursor {resource} -> normal client pointer")
    finally:
        user32.SetCursor(previous)
    return scenarios
