"""
Tab modules for the application
Each tab has its own dedicated buttons and functionality
"""
from .base_tab import BaseTableTab
from .sources_tab import SourcesTab
from .contents_tab import ContentsTab
from .analysis_tab import ContentAnalysisTab
from .all_data_tab import AllDataDisplayTab

__all__ = [
    'BaseTableTab',
    'SourcesTab', 
    'ContentsTab',
    'ContentAnalysisTab',
    'AllDataDisplayTab'
]
