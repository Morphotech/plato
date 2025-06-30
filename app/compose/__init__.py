from .renderer import Renderer
from .jinja_filters import num_to_ordinal, format_dates, nth
ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())
AVAILABLE_IMG_MIME_TYPES = [key for key in Renderer.renderers.keys() if key.startswith("image")]

FILTERS = [num_to_ordinal, format_dates, nth]
