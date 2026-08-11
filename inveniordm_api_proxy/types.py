from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProxyState:
    sessions: dict[str, str] = field(default_factory=dict)
    oauth_states: dict[str, str] = field(default_factory=dict)
