import requests
import subprocess
import os
import time

# --- CONFIGURATION ---
MODEL_NAME = "qwen2.5:14b-instruct-q4_K_M"
OLLAMA_URL = "http://localhost:11434/api/generate"
ITERATIONS = 35  # Number of refinement runs to execute overnight

MASTER_PROMPT = """
You are an expert Python and Streamlit developer specializing in running apps and athletic tools.
Your task is to take the provided Streamlit pace calculator code and enhance it.

IDEAS FOR IMPROVEMENTS YOU CAN ADD (Pick 1 or 2 per iteration):
- Add heart rate zone estimations (Zone 1-5 based on calculated pace).
- Add race predictor comparisons (5K, 10K, Half Marathon, Marathon finish projections).
- Add weather/heat pace adjustment calculators (adjusting target pace for temperature or humidity).
- Add elevation/grade-adjusted pace (GAP) estimation options.
- Improve Plotly chart styling, tooltips, or color schemes.
- Add an export button to download split sheets as CSV.

STRICT CRITICAL RULES:
1. Return ONLY the fully functional Python code enclosed inside a single ```python ``` block.
2. DO NOT alter or break the fundamental pace normalization math (the total split time must ALWAYS equal the goal time).
3. Do NOT remove existing features (Unit selector, Split bias slider, Custom overrides, Line graph, Warning badges).
4. Ensure all imported libraries are standard (streamlit, plotly.express, pandas).
"""

def query_ollama(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "temperature": 0.4
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        return response.json().get("response", "")
    except Exception as e:
        print(f"⚠️ Error contacting Ollama API: {e}")
        return ""

def extract_code(text):
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()

def run_tests():
    result = subprocess.run(["pytest", "test_app.py"], capture_output=True, text=True)
    return result.returncode == 0

def main():
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found in the current directory!")
        return

    print(f"🚀 Starting Overnight AI Loop using {MODEL_NAME}...")
    os.makedirs("version_history", exist_ok=True)

    for i in range(1, ITERATIONS + 1):
        print(f"\n================ Iteration {i}/{ITERATIONS} ================")
        
        with open("app.py", "r") as f:
            current_code = f.read()

        prompt = f"{MASTER_PROMPT}\n\nCURRENT APP CODE:\n```python\n{current_code}\n```"
        
        print(f"🤖 {MODEL_NAME} is generating improvements...")
        start_time = time.time()
        ai_response = query_ollama(prompt)
        elapsed = time.time() - start_time
        
        if not ai_response:
            print("⚠️ Skipping iteration due to empty response.")
            continue

        new_code = extract_code(ai_response)
        print(f"⏱️ Code generated in {elapsed:.1f} seconds.")

        # Test 1: Python Syntax Compile Check
        try:
            compile(new_code, "app_temp.py", "exec")
            print("✔️ Syntax check passed.")
        except Exception as e:
            print(f"❌ Syntax Error: {e}. Discarding this iteration.")
            continue

        # Backup temporary file to test against pytest
        with open("app_temp.py", "w") as f:
            f.write(new_code)

        # Test 2: Unit Math Test
        if run_tests():
            print("✅ All unit tests passed! Saving improvement to app.py...")
            with open("app.py", "w") as f:
                f.write(new_code)
            
            # Save version snapshot
            snapshot_path = f"version_history/app_v{i}.py"
            with open(snapshot_path, "w") as f:
                f.write(new_code)
            print(f"💾 Snapshot saved to {snapshot_path}")
        else:
            print("❌ Math validation failed. Discarding changes for this iteration.")

        # Cleanup temporary file
        if os.path.exists("app_temp.py"):
            os.remove("app_temp.py")

        time.sleep(1)

if __name__ == "__main__":
    main()
