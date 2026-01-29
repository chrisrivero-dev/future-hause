import yaml
from pathlib import Path


PANEL_CONFIG = Path("docs/dashboard_panels.yaml")
ANIMATION_CONFIG = Path("docs/animation_states.yaml")


def load_yaml(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing config: {path}")
    return yaml.safe_load(path.read_text())


def resolve_animation(panel_name: str, engine_state: str) -> str | None:
    """
    Returns the animation key for a given panel + engine state.
    No UI logic. No side effects.
    """

    panels = load_yaml(PANEL_CONFIG)["panels"]
    animations = load_yaml(ANIMATION_CONFIG)["animations"]

    panel = panels.get(panel_name)
    if not panel:
        return None

    animation_key = panel.get("animation_map", {}).get(engine_state)
    if not animation_key:
        return None

    if animation_key not in animations:
        raise ValueError(f"Animation '{animation_key}' not defined in animation_states.yaml")

    return animation_key
