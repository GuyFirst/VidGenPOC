

import os
import json
from ast_service import parse_code
from code_animator_poc.engine import render_code_animation, FONT_PATH

# Configuration and Paths
SOURCE_CODE_FILE = 'C:\\Users\\GuyFirst\\code-animator\\VidGenPOC\\ast_service\\code_snippets\\code_snippet2.py'  # The Python file you want to animate
INPUT_JSON_FILE = 'code_animator_poc/assets/jsonFiles/keyframes1401.json' # Manual bridge for now
OUTPUT_VIDEO_FILE = 'code_animator_poc.mp4'

def request_keyframes_from_openai(ast_json):
    """
    This function will eventually handle the communication with OpenAI.
    It takes the parsed AST and returns the 'Script JSON' (Keyframes).
    """
    # --- OPENAI API CALL (PLACEHOLDER) ---
    # client = OpenAI(api_key="YOUR_TOKEN_HERE")
    # response = client.chat.completions.create(
    #     model="gpt-4-turbo-preview",
    #     messages=[
    #         {"role": "system", "content": "You are a director converting Python AST into video keyframes."},
    #         {"role": "user", "content": f"Convert this AST to keyframes: {ast_json}"}
    #     ],
    #     response_format={ "type": "json_object" }
    # )
    # return response.choices[0].message.content
    
    print("Skipping AI call: Token not yet available. Using manual JSON file instead.")
    return None

def main():
    print(f"Starting Code Animator POC Engine...")

    # 1. READ SOURCE CODE
    try:
        with open(SOURCE_CODE_FILE, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"ERROR: Source code file '{SOURCE_CODE_FILE}' not found.")
        return

    # 2. PARSE AST
    print("Parsing source code into AST...")
    ast_output = parse_code(source_code, "python")
    print("the AST for the code is: ", ast_output)
    # In the final version, this ast_output goes to the function below:
    # keyframes_from_ai = request_keyframes_from_openai(ast_output)

    # 3. LOAD KEYFRAMES (Manual Bridge)
    # Since you are doing this manually for now, we read the external file
    try:
        with open(INPUT_JSON_FILE, 'r') as f:
            json_input = f.read()
    except FileNotFoundError:
        print(f"ERROR: Input file '{INPUT_JSON_FILE}' not found. Please create it manually from your AST analysis.")
        return

    # 4. RENDER VIDEO
    try:
        final_video, num_frames = render_code_animation(json_input)
    except Exception as e:
        print(f"An error occurred during video generation: {e}")
        return

    print(f"Rendering final video to '{OUTPUT_VIDEO_FILE}'...")
    final_video.write_videofile(OUTPUT_VIDEO_FILE, fps=24, codec='libx264', audio_codec='aac')
    print("Video rendering complete!")

    # 5. CLEANUP
    print("Cleaning up temporary audio files...")
    for i in range(num_frames):
        try:
            os.remove(f"temp_audio_{i}.mp3")
        except OSError:
            pass

    print("Cleanup complete. POC finished successfully.")

if __name__ == "__main__":
    main()