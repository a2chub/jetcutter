"""
JetCutter - DaVinci Resolve 自動編集エージェント

動画内の無音区間およびフィラー（「あー」「えっと」等）を自動検知・削除し、
ジェットカット済みのタイムラインを生成する自動編集ツール。
"""

__version__ = "0.1.0"
__author__ = "atusi"

from jetcutter.editor.segment import Segment, SegmentType

__all__ = [
    "__version__",
    "__author__",
    "Segment",
    "SegmentType",
]
