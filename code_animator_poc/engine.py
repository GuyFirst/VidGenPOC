from moviepy import *
import json
from gtts import gTTS
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# read json file
# generate audio
# frame by frame generation
# composition

ASSETS_DIR = 'code_animator_poc/assets'
MASCOT_STATES_DIR = os.path.join(ASSETS_DIR, 'mascotStates')
VIDEO_W, VIDEO_H = 1024, 768
LINE_HEIGHT = 60
CODE_START_Y = 100
CODE_POS_X = 50
FONT_SIZE = 32
FONT_PATH = "arial.ttf"

def generate_voiceover(script, output_filename):
    try:
        # 1. Generate MP3 file
        tts = gTTS(script, lang='en', slow=False)
        tts.save(output_filename)

        # 2. Return the file as a MoviePy AudioFileClip
        return AudioFileClip(output_filename)

    except Exception as e:
        print(f"Error generating audio for '{script}': {e}")
        # Fallback: Return a silent audio clip (duration will be set later)
        return AudioClip(lambda t: 0, duration=1.0)

def create_mascot_clip(mascot_state, duration):

    # Map JSON state to provided filenames
    image_map = {
        "pointing_at_code": "pointing.png",
        "nodding_yes": "idle.png",
        "hands_on_head": "thinking.png",
        "waving_bye": "idle.png"
    }

    base_img_filename = image_map.get(mascot_state, "idle.png")
    img_path = os.path.join(MASCOT_STATES_DIR, base_img_filename)

    try:
        # 1. Load the PNG
        mascot_img = ImageClip(img_path).with_duration(duration)

        # 2. Normalize height
        mascot_img = mascot_img.resized(height=250)

        # 3. Add a Nodding Effect if the state is 'nodding_yes'
        # This rotates the image 5 degrees and back every 0.5 seconds
        if mascot_state == "nodding_yes":
            # In MoviePy 2.x, rotation effects can be applied via image_transform
            # but for a POC, rotating the Clip object itself is more efficient
            mascot_img = mascot_img.rotated(angle=lambda t: 5 * np.sin(2 * np.pi * t * 2))

        # 4. Position in the bottom right corner with padding
        final_clip = mascot_img.with_position(("right", "bottom"))

        return final_clip

    except Exception as e:
        print(f"Error loading mascot image {img_path}: {e}")
        # Fallback circle if images are missing
        return ColorClip((100, 100), color=(255, 165, 0), duration=duration).with_position(("right", "bottom"))

def create_memory_box_clip(var_name, value, pos, duration, effect=None):
    BOX_WIDTH = 220

    def make_frame(t):
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        # Get exact font metrics: ascent (above baseline), descent (below baseline)
        ascent, descent = font.getmetrics()

        # Calculate minimum height needed for text + some padding
        text_content = f"{var_name}: {value}"
        total_text_height = ascent + descent

        # Canvas height: text height + significant vertical padding
        # We add 40px padding to be very safe
        IMAGE_HEIGHT = total_text_height + 40

        img = Image.new('RGBA', (BOX_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        box_color = (255, 255, 255)
        if effect == 'flash' and t < 0.2:
            box_color = (255, 0, 0)

        # Draw the box rectangle
        # We position the box relative to the vertical center of the canvas
        RECT_Y_START = 5
        draw.rectangle([(5, RECT_Y_START), (BOX_WIDTH - 5, IMAGE_HEIGHT - 5)],
                       fill=box_color, outline=(0, 0, 0), width=3)

        # Draw the text precisely
        # (15, 15) provides a safe internal margin from the box edges
        draw.text((15, 15), text_content, fill=(0, 0, 0), font=font)

        return np.array(img.convert('RGB'))

    clip = VideoClip(make_frame, duration=duration).with_fps(24)
    clip.position = pos
    return clip

def render_code_animation(json_data):
    data = json.loads(json_data)
    all_audio_clips = []
    all_video_clips = []
    current_memory_boxes = {}

    current_code_snippet = data['code_snippet']
    total_duration = data['total_duration']

    # 1. Background and Static Code Setup
    bg_clip = ColorClip((VIDEO_W, VIDEO_H), color=(50, 50, 50), duration=total_duration).with_position('center')
    all_video_clips.append(bg_clip)

    # Render static code (lasts for the entire duration)
    for i, line in enumerate(current_code_snippet):
        y_pos = CODE_START_Y + i * LINE_HEIGHT
        text_clip = TextClip(text=line, font_size=FONT_SIZE, color='white', font=FONT_PATH)
        text_clip = text_clip.with_position((CODE_POS_X, y_pos)).with_duration(total_duration)
        all_video_clips.append(text_clip)

    print("Generating voiceover and visual clips frame-by-frame...")

    current_time_cursor = 0.0
    # 2. Iterate through Frames for Dynamic Content
    for i, frame in enumerate(data['frames']):
        start = current_time_cursor

        # Define a temporary file name
        audio_filename = f"temp_audio_{i}.mp3"

        # Generate the audio clip
        audio_clip = generate_voiceover(frame['script'], audio_filename)

        # AUTO-SYNC: Get actual duration of the generated speech
        audio_clip.start = start
        actual_duration = audio_clip.duration
        all_audio_clips.append(audio_clip)

        # B. Mascot Clip (e.g., pointing, nodding)
        # Assuming create_mascot_clip returns a clip that has position set internally
        mascot_clip = create_mascot_clip(frame['mascot_state'], actual_duration)
        mascot_clip = mascot_clip.with_start(start)
        all_video_clips.append(mascot_clip)

        # C. Code Highlighting
        if 'code_line' in frame:
            line_index = frame['code_line'] - 1
            highlight_y = CODE_START_Y + line_index * LINE_HEIGHT

            # ColorClip for highlighting
            highlight_clip = ColorClip((int(VIDEO_W * 0.5), LINE_HEIGHT), color=(255, 255, 0), duration=actual_duration)
            highlight_clip = highlight_clip.with_opacity(0.6)
            highlight_clip = highlight_clip.with_position((CODE_POS_X - 10, highlight_y))
            highlight_clip = highlight_clip.with_start(start)
            all_video_clips.append(highlight_clip)

            # D. Handle Animations (Memory Boxes and Output Text)
            for anim in frame.get('animations', []):
                if anim['type'] == "MemoryBox":
                    # Variable Declaration (Clip appears)
                    clip = create_memory_box_clip(anim['var_name'], anim['new_value'], anim['target_pos'], actual_duration)
                    clip = clip.with_position(clip.position).with_start(start)

                    all_video_clips.append(clip)
                    current_memory_boxes[anim['var_name']] = clip  # Track the last version of the box

                elif anim['type'] == "MemoryBoxUpdate":
                    # Variable Reassignment (Clip updates, often with an effect)
                    new_clip = create_memory_box_clip(anim['var_name'], anim['new_value'], anim['target_pos'], actual_duration, anim['effect'])
                    new_clip = new_clip.with_position(new_clip.position).with_start(start)
                    all_video_clips.append(new_clip)
                    current_memory_boxes[anim['var_name']] = new_clip

                elif anim['type'] == "OutputText":
                    # Output to a console area
                    output_text = TextClip(text=f"> {anim['text']}", font_size=FONT_SIZE * 1.5, color='#33FF57',font=FONT_PATH)
                    output_text = output_text.with_duration(actual_duration)
                    output_text = output_text.with_position(anim['position']).with_start(start)
                    all_video_clips.append(output_text)
        current_time_cursor += actual_duration

    print(f"Successfully generated {len(all_audio_clips)} audio clips and {len(all_video_clips)} video clips.")

    # 3. Final Composition

    # Combine all individual video clips into one master video
    final_video = CompositeVideoClip(all_video_clips, size=(VIDEO_W, VIDEO_H))

    # Combine all generated audio clips into one track
    final_audio = concatenate_audioclips(all_audio_clips)

    # Attach the audio to the final video
    final_video = final_video.with_audio(final_audio)
    final_video.duration = total_duration

    return final_video, len(data['frames'])
