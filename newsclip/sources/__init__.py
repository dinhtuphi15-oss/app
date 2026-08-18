from .base import Candidate, SourceAdapter
from .archive_org import ArchiveOrgAdapter
from .wikimedia import WikimediaAdapter
from .pexels import PexelsAdapter
from .pixabay import PixabayAdapter
from .youtube import YouTubeAdapter

ALL_ADAPTERS = [
    WikimediaAdapter,
    ArchiveOrgAdapter,
    PexelsAdapter,
    PixabayAdapter,
    YouTubeAdapter,
]

__all__ = [
    "Candidate",
    "SourceAdapter",
    "ALL_ADAPTERS",
    "WikimediaAdapter",
    "ArchiveOrgAdapter",
    "PexelsAdapter",
    "PixabayAdapter",
    "YouTubeAdapter",
]
