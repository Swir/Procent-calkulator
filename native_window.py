"""Window-local compatibility fix for SwirUI 0.1.0b1's missing class cursor.

A shared IDC_ARROW class cursor lets DefWindowProc restore the pointer on entry
to the client area and retain Windows' normal resize cursors on window borders.
No polling, cursor movement, process-global cursor replacement or WndProc hook.
"""
import ctypes
from swirui.platforms.windows import Win32PlatformBackend
from app_identity import resolve_icon

GCLP_HCURSOR = -12
IDC_ARROW = 32512


class CursorWin32Backend(Win32PlatformBackend):
    def __init__(self, icon_path=None):
        super().__init__()
        self.icon_path = icon_path or resolve_icon()
        self._window_icons = {}
        self._user32.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint,
                                          ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        self._user32.LoadImageW.restype = ctypes.c_void_p
        self._user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
        self._user32.SendMessageW.restype = ctypes.c_ssize_t
        self._user32.DestroyIcon.argtypes = [ctypes.c_void_p]
        self._user32.DestroyIcon.restype = ctypes.c_bool

    def create_window(self, spec):
        handle = super().create_window(spec)
        try:
            self._ensure_default_cursor(handle.value)
            self._set_window_icons(handle)
        except Exception:
            super().destroy_window(handle)
            raise
        return handle

    def _set_window_icons(self, handle):
        icons = []
        try:
            scale = self.window_scale(handle)
            for size in (16, 32):
                pixels = max(1, round(size * scale))
                icon = self._user32.LoadImageW(None, str(self.icon_path), 1, pixels, pixels, 0x10)
                if not icon:
                    raise ctypes.WinError(ctypes.get_last_error())
                icons.append(icon)
            for kind, icon in enumerate(icons):
                self._user32.SendMessageW(handle.value, 0x0080, kind, icon)
            self._window_icons[handle] = tuple(icons)
        except Exception:
            for icon in icons:
                self._user32.DestroyIcon(icon)
            raise

    def verify_window_icons(self, handle):
        expected = self._window_icons[handle]
        for kind, icon in enumerate(expected):
            actual = self._user32.SendMessageW(handle.value, 0x007F, kind, 0)
            if not actual or actual != icon:
                raise RuntimeError("Native window did not retain its application icon")
        return {"file": self.icon_path.name, "small_icon": True, "large_icon": True}

    def destroy_window(self, handle):
        super().destroy_window(handle)
        for icon in self._window_icons.pop(handle, ()):
            self._user32.DestroyIcon(icon)

    def shutdown(self):
        # The legacy shutdown destroys HWNDs directly; release owned icons first
        # through our normal per-window lifecycle, after each HWND is gone.
        for handle in tuple(self._windows):
            self.destroy_window(handle)
        super().shutdown()

    def _ensure_default_cursor(self, hwnd):
        # Win32 maps the Ptr APIs to their Long equivalents on 32-bit Windows.
        suffix = "LongPtrW" if ctypes.sizeof(ctypes.c_void_p) == 8 else "LongW"
        get_class = getattr(self._user32, "GetClass" + suffix)
        set_class = getattr(self._user32, "SetClass" + suffix)
        get_class.argtypes = [ctypes.c_void_p, ctypes.c_int]
        get_class.restype = ctypes.c_size_t
        set_class.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t]
        set_class.restype = ctypes.c_size_t
        self._user32.LoadCursorW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._user32.LoadCursorW.restype = ctypes.c_void_p

        # Preserve a cursor supplied by a future SwirUI version.
        if get_class(hwnd, GCLP_HCURSOR):
            return
        arrow = self._user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
        if not arrow:
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.set_last_error(0)
        previous = set_class(hwnd, GCLP_HCURSOR, arrow)
        error = ctypes.get_last_error()
        if not previous and error:
            raise ctypes.WinError(error)
        # LoadCursor gives a shared system resource; Windows owns its lifetime.
