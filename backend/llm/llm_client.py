from mistralai.client import Mistral
from backend.core.config import settings


mistral_client = Mistral(api_key=settings.mistral_api_key)

