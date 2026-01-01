"""
types - DaVinci Resolve API型定義

DaVinci Resolve Scripting APIの型エイリアス定義。
公式の型スタブがないため、Anyのエイリアスとして定義し、
将来の型付けに備える。

Usage:
    from jetdr.davinci.types import DRTimeline, DRProject

Note:
    これらの型は現在すべてAnyのエイリアスです。
    DaVinci Resolveの公式型スタブが利用可能になった場合、
    ここを更新することで全体の型付けが改善されます。
"""

from __future__ import annotations

from typing import Any

# DaVinci Resolve API型エイリアス
# 将来の型付けのためのプレースホルダー

# Core API objects
DRResolve = Any
"""DaVinci Resolve application object"""

DRProjectManager = Any
"""Project manager object"""

DRProject = Any
"""Project object (note: different from jetdr.davinci.project.DRProject class)"""

DRMediaPool = Any
"""Media pool object (note: different from jetdr.davinci.media_pool.DRMediaPool class)"""

DRMediaPoolItem = Any
"""Media pool item (clip in media pool)"""

DRTimeline = Any
"""Timeline object"""

DRTimelineItem = Any
"""Item on timeline (clip, compound clip, etc.)"""

DRFolder = Any
"""Bin/folder in media pool"""

# Render settings
DRRenderJob = Any
"""Render job object"""

DRRenderPreset = Any
"""Render preset"""
