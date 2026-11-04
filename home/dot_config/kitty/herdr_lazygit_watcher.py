# kitty watcher attached by `herdr-lazygit open`: records the lazygit OS window's screen position
# and size when it closes, so the next open restores them. kitty's remote control cannot
# report an OS window's position, so this runs inside kitty to read it.
import json
import os
from pathlib import Path
from typing import Any

from kitty.boss import Boss
from kitty.fast_data_types import get_os_window_pos, get_os_window_size
from kitty.window import Window


def on_close(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    x, y = get_os_window_pos(window.os_window_id)
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "herdr-lazygit"
    state.mkdir(parents=True, exist_ok=True)
    size = get_os_window_size(window.os_window_id)
    if size is None:
        return
    geometry = {"x": x, "y": y, "width": size["width"], "height": size["height"]}
    (state / "geometry.json").write_text(json.dumps(geometry))
