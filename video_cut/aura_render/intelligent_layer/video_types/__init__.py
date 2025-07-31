"""12种视频类型模板"""

from .base_template import BaseVideoTemplate
from .product_ad import ProductAdTemplate
from .brand_promo import BrandPromoTemplate
from .knowledge_explain import KnowledgeExplainTemplate
from .online_course import OnlineCourseTemplate
from .short_drama import ShortDramaTemplate
from .music_mv import MusicMVTemplate
from .vlog import VlogTemplate
from .life_share import LifeShareTemplate
from .micro_film import MicroFilmTemplate
from .concept_show import ConceptShowTemplate
from .game_video import GameVideoTemplate
from .training_video import TrainingVideoTemplate

# 视频类型注册表
VIDEO_TEMPLATES = {
    'product_ad': ProductAdTemplate,
    'brand_promo': BrandPromoTemplate,
    'knowledge_explain': KnowledgeExplainTemplate,
    'online_course': OnlineCourseTemplate,
    'short_drama': ShortDramaTemplate,
    'music_mv': MusicMVTemplate,
    'vlog': VlogTemplate,
    'life_share': LifeShareTemplate,
    'micro_film': MicroFilmTemplate,
    'concept_show': ConceptShowTemplate,
    'game_video': GameVideoTemplate,
    'training_video': TrainingVideoTemplate
}

__all__ = [
    'BaseVideoTemplate',
    'VIDEO_TEMPLATES',
    'ProductAdTemplate',
    'BrandPromoTemplate',
    'KnowledgeExplainTemplate',
    'OnlineCourseTemplate',
    'ShortDramaTemplate',
    'MusicMVTemplate',
    'VlogTemplate',
    'LifeShareTemplate',
    'MicroFilmTemplate',
    'ConceptShowTemplate',
    'GameVideoTemplate',
    'TrainingVideoTemplate'
]