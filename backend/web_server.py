from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import uvicorn, asyncio, logging, sys, os, json, subprocess

from script_initiate import initiate_bot_script
from script_repair import repair_bot_script
from script_generation import generate_script

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_read_text(filepath, default = "Not found"):
        try:
            return filepath.read_text(encoding='utf-8')
        except (FileNotFoundError, UnicodeDecodeError):
            return default

def load_bots():
    bots = {}
    data_directory = Path("data")

    if not data_directory.exists():
        data_directory.mkdir()
        return bots

    for index, bot_directory in enumerate(data_directory.iterdir()):
        if not bot_directory.is_dir():
            continue
        iterations = [iteration_directory for iteration_directory in bot_directory.iterdir() if iteration_directory.is_dir()]
        if not iterations:
            continue
        latest_iteration = max(iterations, key=lambda x: int(x.name.split("iteration")[1]))
        bot_id = str(index)
        bots[bot_id] = {
            "id": bot_id,
            "name": bot_directory.name,
            "instruction": safe_read_text(latest_iteration / "instruction.txt"),
            "success_criteria": safe_read_text(latest_iteration / "successCriteria.txt"),
            "scriptUnmodified": safe_read_text(latest_iteration / "scriptUnmodified.py"),
            "script": safe_read_text(latest_iteration / "script.py"),
            "status": "ready"
        }
    return bots

bots_db = load_bots()

async def generate_initial_script_task(bot_id, bot_data):
    try:
        bots_db[bot_id]["status"] = "processing"

        iteration_filepath = initiate_bot_script(bot_data["name"], bot_data["instruction"], bot_data["success_criteria"])

        bots_db[bot_id].update({
            "status": "ready",
            "scriptUnmodified": safe_read_text(iteration_filepath / "scriptUnmodified.py"),
            "script": safe_read_text(iteration_filepath / "script.py")
        })
    except Exception as error:
        logger.error(f"Error generating script for bot {bot_id}: {error}")
        bots_db[bot_id].update({
            "status": "error",
            "error": str(error)
        })

async def generate_repair_script_task(bot_id, bot_data):
    try:
        bots_db[bot_id]["status"] = "processing"
        new_iteration_filepath = repair_bot_script(bot_data["name"])
        
        bots_db[bot_id].update({
            "status": "ready",
            "scriptUnmodified": safe_read_text(new_iteration_filepath / "scriptUnmodified.py"),
            "script": safe_read_text(new_iteration_filepath / "script.py")
        })
    except Exception as error:
        logger.error(f"Error generating repair script for bot {bot_id}: {error}")
        bots_db[bot_id].update({
            "status": "error",
            "error": str(error)
        })

def get_latest_iteration_path(bot_path):
    iterations = [d for d in bot_path.iterdir() if d.is_dir() and d.name.startswith("iteration")]
    if not iterations:
        raise FileNotFoundError("No iteration directories found")
    return max(iterations, key=lambda x: int(x.name.replace("iteration", "")))

class BotRequest(BaseModel):
    name: str
    instruction: str
    success_criteria: str

class BotResponse(BotRequest):
    id: str
    status: str = "pending"
    script_path: str = None
    error: str = None
    scriptUnmodified: str = None
    script: str = None

@app.post("/api/bots", response_model=BotResponse, status_code=201)
async def create_bot(bot: BotRequest, background_tasks: BackgroundTasks):
    bot_id = str(len(bots_db)+1)
    bot_data = bot.dict()
    bot_data["id"] = bot_id
    bot_data["status"] = "pending"
    bots_db[bot_id] = bot_data
    background_tasks.add_task(generate_initial_script_task, bot_id, bot_data)
    return {**bot_data}

@app.get("/api/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id):
    if bot_id not in bots_db:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bots_db[bot_id]

@app.post("/api/bots/{bot_id}/run", response_model=dict)
async def run_bot_script(bot_id):
    if bot_id not in bots_db:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot = bots_db[bot_id]
    
    bot_path = Path("data") / bot["name"]
    
    if not bot_path.exists():
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        latest_iteration = get_latest_iteration_path(bot_path)
        script_path = latest_iteration / "script.py"

        if not script_path.exists():
            raise FileNotFoundError(f"Script not found at {script_path}")

        process = subprocess.Popen(
            ["python", str(script_path)],
            text=True
        )
        
        return {
            "status": "completed",
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "running",
            "message": "Script execution is still running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running script: {str(e)}")

@app.post("/api/bots/{bot_id}/repair", response_model=BotResponse)
async def repair_bot(bot_id, background_tasks):
    if bot_id not in bots_db:
        raise HTTPException(status_code=404, detail="Bot not found")
    bots_db[bot_id]["status"] = "pending"
    background_tasks.add_task(generate_repair_script_task, bot_id, bots_db[bot_id])
    return bots_db[bot_id]

@app.get("/api/bots/{bot_id}/outputs")
async def get_bot_outputs(bot_id: str):
    if bot_id not in bots_db:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot = bots_db[bot_id]
    bot_path = Path("data") / bot["name"]
    
    try:
        latest_iteration = get_latest_iteration_path(bot_path)
        output_path = latest_iteration / "output.txt"
        error_path = latest_iteration / "errorMessage.txt"
        
        return {
            "output": safe_read_text(output_path, "No output found"),
            "error": safe_read_text(error_path, "No error message found")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots", response_model=list[BotResponse])
async def get_bots():
    return list(bots_db.values())

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000, reload=True)