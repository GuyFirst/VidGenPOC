from manim import *
import json
import os
import shutil # For moving files and deleting folders
import glob   # For finding the mp3 files
from gtts import gTTS
from mutagen.mp3 import MP3

# ==========================================
# 0. HELPER: SMART TTS SERVICE
# ==========================================
class TTSService:
    def generate_audio(self, text, step_index):
        if not text or not text.strip():
            return None, 0
            
        filename = f"voiceover_{step_index}.mp3"
        
        # 1. Generate Audio
        try:
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
        except Exception as e:
            print(f"TTS Error: {e}")
            return None, 0

        # 2. Get Duration
        try:
            audio = MP3(filename)
            duration_sec = audio.info.length
            return filename, duration_sec
        except Exception as e:
            print(f"Error reading MP3 length: {e}")
            return filename, 2.0 

# ==========================================
# 1. THE LEGO BLOCK: VarCreate
# ==========================================
class VarCreate:
    def __init__(self, name, value, position_index):
        self.name = name
        self.value = str(value)
        self.base_position = UP * 1.0
        self.vertical_spacing = position_index * 1.5 

    def generate_mobjects(self):
        self.box = Rectangle(height=1, width=3.5, color=BLUE)
        self.box.set_fill(BLUE, opacity=0.2)
        target_pos = self.base_position + (DOWN * self.vertical_spacing)
        self.box.move_to(target_pos)

        self.label = Text(self.name, font_size=24, color=YELLOW)
        self.label.next_to(self.box, UP, buff=0.1)

        self.value_text = Text(self.value, font_size=32, color=WHITE)
        self.value_text.move_to(self.box.get_center())

        return VGroup(self.box, self.label, self.value_text)

    def get_animations(self):
        return [
            GrowFromCenter(self.box),
            FadeIn(self.label, shift=DOWN),
            Write(self.value_text)
        ]

# ==========================================
# 2. THE SCENE: CodeAnimatorEngine
# ==========================================
class CodeAnimatorEngine(Scene):
    def __init__(self, script_data, **kwargs):
        self.script_data = script_data
        self.tts = TTSService()
        super().__init__(**kwargs)

    def construct(self):
        if isinstance(self.script_data, str):
            data = json.loads(self.script_data)
        else:
            data = self.script_data
            
        script_sequence = data.get("sequence", [])

        # --- SETUP LAYOUT ---
        code_header = Text("Current Instruction:", font_size=24, color=GRAY)
        code_header.to_edge(UP, buff=0.5)
        
        current_code_line = Text("Initializing...", font="Monospace", font_size=32)
        current_code_line.next_to(code_header, DOWN)
        
        subtitle = Text("", font_size=28, color=WHITE).to_edge(DOWN, buff=1.0)

        self.add(code_header, current_code_line, subtitle)
        self.variables_on_screen = [] 

        # --- EXECUTION LOOP ---
        for i, step in enumerate(script_sequence):
            
            code_text = step.get("code", "")
            narration_text = step.get("narration", "")

            # 1. Audio
            audio_path, audio_duration = self.tts.generate_audio(narration_text, i)
            if audio_path:
                self.add_sound(audio_path)

            # 2. Text Updates
            new_code = Text(code_text, font="Monospace", font_size=32, color=GREEN)
            new_code.next_to(code_header, DOWN)
            new_subtitle = Text(narration_text, font_size=24, color=WHITE).to_edge(DOWN, buff=1.0)
            
            # 3. Animations
            animations = [
                Transform(current_code_line, new_code),
                Transform(subtitle, new_subtitle)
            ]
            
            if step["type"] == "VarCreate":
                block = VarCreate(
                    name=step["params"]["name"], 
                    value=step["params"]["value"], 
                    position_index=len(self.variables_on_screen)
                )
                mobjects = block.generate_mobjects()
                self.variables_on_screen.append(mobjects)
                animations.extend(block.get_animations())

            # 4. Play
            self.play(*animations, run_time=1.5)

            # 5. Smart Wait
            remaining_audio = audio_duration - 1.5
            buffer_time = 0.5 
            
            if remaining_audio > 0:
                self.wait(remaining_audio + buffer_time)
            else:
                self.wait(buffer_time)

# ==========================================
# 3. WRAPPER FUNCTION (WITH CLEANUP)
# ==========================================
def render_code_animation(json_input):
    output_folder = "./output_video"
    
    # 1. Configure Manim
    config.media_dir = output_folder
    config.verbosity = "WARNING"
    config.quality = "low_quality"
    config.preview = False # Engine does NOT open it anymore
    
    # 2. Render
    scene = CodeAnimatorEngine(script_data=json_input)
    scene.render()
    
    # 3. CLEANUP & MOVE
    print("\n--- [Engine] Processing Output ---")
    
    final_filename = "CodeAnimatorEngine.mp4"
    found_video = None
    
    for root, dirs, files in os.walk(output_folder):
        if final_filename in files:
            found_video = os.path.join(root, final_filename)
            break
            
    target_video = "final_output.mp4"
    final_path = os.path.abspath(target_video)

    if found_video:
        if os.path.exists(target_video):
            os.remove(target_video)
        shutil.move(found_video, target_video)
        print(f"SUCCESS: Video moved to -> {final_path}")
    else:
        print("ERROR: Could not find the generated video file.")
        return None

    # 4. DELETE TEMP FOLDERS
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
        
    # 5. DELETE AUDIO FILES
    for f in glob.glob("voiceover_*.mp3"):
        try: os.remove(f)
        except: pass
        
    # RETURN THE PATH TO MAIN
    return final_path