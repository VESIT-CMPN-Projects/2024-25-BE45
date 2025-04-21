import os
import pandas as pd
from tensorflow import keras
from dotenv import load_dotenv

# Get API keys
load_dotenv()

# Database Setup
DB = "gamespec"
USER_COLLECTION = "user"
CHAT_COLLECTION = "chats"
SESSION_COLLECTION = "sessions"
MONGODB_URI = os.getenv("MONGODB_URI")

# Data CSVs
game_data = pd.read_csv(r"data\cleaned-games.csv", low_memory=False)
cpu_data = pd.read_csv(r"data\cpus.csv")
ram_data = pd.read_csv(r"data\rams.csv")
gpu_data = pd.read_csv(r"data\gpus.csv")

std_cpu_data = pd.read_csv(r"data\std-cpus.csv")
std_ram_data = pd.read_csv(r"data\std-rams.csv")
std_gpu_data = pd.read_csv(r"data\std-gpus.csv")

# cpu_gpu_sentiment = pd.read_csv(r"data\cpu-gpu-sentiment.csv")
# cpu_ram_sentiment = pd.read_csv(r"data\cpu-ram-sentiment.csv")

arm_cpu_gpu = pd.read_csv(r"data\cpu_gpu_association_rules.csv")
arm_cpu_ram = pd.read_csv(r"data\cpu_memory_association_rules.csv")

# AutoEncoders
CPU_RAM_ENC = r"data-analysis\autoencoders\cpu_ram_encoder.keras"
cpu_ram_encoder = keras.models.load_model(CPU_RAM_ENC)

CPU_GPU_ENC = r"data-analysis\autoencoders\cpu_gpu_encoder.keras"
cpu_gpu_encoder = keras.models.load_model(CPU_GPU_ENC)

MAIN_ENC = r"data-analysis/autoencoders/autoencoder_model.keras"
main_encoder = keras.models.load_model(MAIN_ENC)

# Thresholds
COMPATIBILITY_THRESHOLD = [
    0.75, # CPU_RAM
    0.75 # CPU_GPU
]
