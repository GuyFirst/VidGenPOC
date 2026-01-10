import os
from code_animator_poc.engine import render_code_animation, FONT_PATH

INPUT_JSON_FILE = 'code_animator_poc/assets/jsonFiles/keyframes2.json'
OUTPUT_VIDEO_FILE = 'code_animator_poc.mp4'

def main():
    print(f"Starting Code Animator POC Engine...")

    try:
        with open(INPUT_JSON_FILE, 'r') as f:
            json_input = f.read()
    except FileNotFoundError:
        print(f"ERROR: Input file '{INPUT_JSON_FILE}' not found. Please create it.")
        return

    # if not os.path.exists(FONT_PATH):
    #     print(f"WARNING: '{FONT_PATH}' not found. Using default MoviePy/PIL font.")

    try:
        final_video, num_frames = render_code_animation(json_input)
    except Exception as e:
        print(f"An error occurred during video generation: {e}")
        return

    print(f"Rendering final video to '{OUTPUT_VIDEO_FILE}'...")
    final_video.write_videofile(OUTPUT_VIDEO_FILE, fps=24, codec='libx264', audio_codec='aac')
    print("Video rendering complete!")

    print("Cleaning up temporary audio files...")
    for i in range(num_frames):
        try:
            os.remove(f"temp_audio_{i}.mp3")
        except OSError:
            pass

    print("Cleanup complete. POC finished successfully.")


if __name__ == "__main__":
    main()