import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Coze API token from environment variable with fallback to provided key
coze_api_token = os.getenv('COZE_API_KEY', 'pat_cwIbrVcSP2ac6oTaCCdyVZ1qvc5tIse5fyGaCtZsftPIyNyippcQy4rzlEuFc85G')
