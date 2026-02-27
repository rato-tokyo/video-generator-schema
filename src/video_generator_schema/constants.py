VIDEO_FPS: int = 30
WAV_SAMPLE_RATE: int = 24000
WAV_CHANNELS: int = 1  # mono
MAX_REVIEWS: int = 20
MIN_REVIEWS: int = 1
SHAPE_TIME_TOLERANCE: float = 1e-4

# Paragraph text length limits (newlines excluded)
PARAGRAPH_TEXT_MIN_LENGTH: int = 40
PARAGRAPH_TEXT_MAX_LENGTH: int = 200

# Paragraphs per review
MIN_PARAGRAPHS: int = 2
MAX_PARAGRAPHS: int = 3

# topBarText length limit ({accent} tags excluded)
TOP_BAR_TEXT_MAX_LENGTH: int = 20
