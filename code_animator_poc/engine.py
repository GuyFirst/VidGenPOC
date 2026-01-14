from manim import *
import json
import os
import shutil
import glob
import numpy as np
from gtts import gTTS
from mutagen.mp3 import MP3

# ==========================================
# 0. HELPER: TTS SERVICE
# ==========================================
class TTSService:
    def generate_audio(self, text, step_index):
        if not text or not text.strip():
            return None, 0
        filename = f"voiceover_{step_index}.mp3"
        try:
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
            audio = MP3(filename)
            return filename, audio.info.length
        except Exception:
            return filename, 2.0 

# ==========================================
# 1. LEGO BLOCK: DynamicStack
# ==========================================
class DynamicStack:
    def __init__(self, frame_name="Global Frame", capacity=3):
        self.frame_name = frame_name
        self.capacity = max(capacity, 1)
        
        # Dimensions
        self.var_height = 1.0
        self.var_spacing = 0.2
        self.header_height = 0.8
        self.padding = 0.5
        
        # Calculate total height based on capacity
        self.content_height = (self.capacity * self.var_height) + ((self.capacity - 1) * self.var_spacing)
        self.total_height = self.content_height + self.header_height + (self.padding * 2)
        
        self.width = 4.5
        self.center_point = RIGHT * 3.5 

    def generate_mobjects(self):
        # 1. Frame
        self.rect = Rectangle(height=self.total_height, width=self.width, color=WHITE)
        self.rect.move_to(self.center_point)
        
        # 2. Header Background
        self.header_bg = Rectangle(height=self.header_height, width=self.width, color=WHITE)
        self.header_bg.set_fill(GRAY, opacity=0.5)
        
        # Align header to top of rect
        header_pos = self.rect.get_top() + (DOWN * (self.header_height / 2))
        self.header_bg.move_to(header_pos)

        # 3. Header Text
        self.label = Text(self.frame_name, font_size=24, color=WHITE)
        self.label.move_to(self.header_bg.get_center())

        return VGroup(self.rect, self.header_bg, self.label)

    def get_animations(self):
        return [Create(self.rect), FadeIn(self.header_bg), Write(self.label)]
    
    def get_slot_position(self, index):
        # Calculate Y position (Bottom Up)
        base_y = self.rect.get_bottom()[1] + self.padding + (self.var_height / 2)
        offset_y = index * (self.var_height + self.var_spacing)
        target_y = base_y + offset_y
        
        # X position is centered
        target_x = self.rect.get_center()[0]
        return np.array([target_x, target_y, 0])

# ==========================================
# 2. LEGO BLOCK: VarCreate
# ==========================================
class VarCreate:
    def __init__(self, name, value, target_position):
        self.name = name
        self.value = str(value)
        self.target_pos = target_position

    def generate_mobjects(self):
        # 1. Box
        self.box = Rectangle(height=1.0, width=3.8, color=BLUE)
        self.box.set_fill(BLUE, opacity=0.2)
        self.box.move_to(self.target_pos)

        # 2. Name Label (Auto-Scaling)
        self.label = Text(self.name, font_size=24, color=YELLOW)
        if self.label.width > 1.6:
            self.label.scale_to_fit_width(1.6)
        self.label.next_to(self.box.get_left(), RIGHT, buff=0.2)

        # 3. Value Label (Auto-Scaling)
        self.value_text = Text(self.value, font_size=24, color=WHITE)
        if self.value_text.width > 1.6:
            self.value_text.scale_to_fit_width(1.6)
        self.value_text.next_to(self.box.get_right(), LEFT, buff=0.2)

        return VGroup(self.box, self.label, self.value_text)

    def get_animations(self):
        return [FadeIn(self.box, shift=RIGHT), FadeIn(self.label, shift=RIGHT), Write(self.value_text)]

# ==========================================
# 3. THE SCENE: CodeAnimatorEngine
# ==========================================
class CodeAnimatorEngine(Scene):
    def __init__(self, script_data, **kwargs):
        self.script_data = script_data
        self.tts = TTSService()
        super().__init__(**kwargs)

    def construct(self):
        # Data Loading
        if isinstance(self.script_data, str):
            data = json.loads(self.script_data)
        else:
            data = self.script_data
        
        script_sequence = data.get("sequence", [])

        # --- SETUP UI ---
        code_header = Text("Current Instruction:", font_size=24, color=GRAY)
        code_header.to_edge(UP, buff=0.5).to_edge(LEFT, buff=1.0)
        
        current_code_line = Text("Initializing...", font="Monospace", font_size=28)
        current_code_line.next_to(code_header, DOWN).align_to(code_header, LEFT)
        
        subtitle = Text("", font_size=28, color=WHITE).to_edge(DOWN, buff=1.0)

        self.add(code_header, current_code_line, subtitle)
        
        # --- STATE TRACKING ---
        self.variables_on_screen = [] 
        self.active_stack = None       

        # Count total vars to size the stack correctly (Scalability prep)
        total_vars = sum(1 for step in script_sequence if step.get("type") == "VarCreate")

        # --- EXECUTION LOOP ---
        for i, step in enumerate(script_sequence):
            
            # Common Data
            code_text = step.get("code", "")
            narration_text = step.get("narration", "")
            action_type = step.get("type", "")
            params = step.get("params", {})
            
            # 1. Audio Generation
            audio_path, audio_duration = self.tts.generate_audio(narration_text, i)
            if audio_path: self.add_sound(audio_path)

            # 2. Text Updates
            new_code = Text(code_text, font="Monospace", font_size=28, color=GREEN)
            new_code.next_to(code_header, DOWN).align_to(code_header, LEFT)
            new_subtitle = Text(narration_text, font_size=24, color=WHITE).to_edge(DOWN, buff=1.0)
            
            # Base animations (Text changes)
            animations = [
                Transform(current_code_line, new_code),
                Transform(subtitle, new_subtitle)
            ]
            
            # ====================================================
            # SCALABLE LOGIC BLOCK
            # ====================================================

            if action_type == "VarCreate":
                # A. Detect Scope Change
                target_scope = params.get("scope", "Global Frame")
                
                # If stack doesn't exist OR name doesn't match current scope -> Create New Stack Frame
                if not self.active_stack or self.active_stack.frame_name != target_scope:
                    
                    # Create new stack visual
                    self.active_stack = DynamicStack(target_scope, capacity=total_vars)
                    self.active_stack.generate_mobjects()
                    
                    # Add stack animation to the list (it will play with the text update)
                    animations.extend(self.active_stack.get_animations())
                    
                    # Optional: If changing scope, maybe clear old variables? 
                    # For now, we keep them to show history, but usually you'd hide them.
                    # self.variables_on_screen = [] # Uncomment to clear vars on scope change

                # B. Create Variable
                idx = len(self.variables_on_screen)
                target_pos = self.active_stack.get_slot_position(idx)

                var_block = VarCreate(params["name"], params["value"], target_pos)
                mobjects = var_block.generate_mobjects()
                
                self.variables_on_screen.append(mobjects)
                animations.extend(var_block.get_animations())

            # elif action_type == "FuncCreate":
            #    pass  <-- Place holder for future logic
            
            # elif action_type == "Return":
            #    pass  <-- Place holder for future logic

            # ====================================================
            
            # 3. Play All Animations Together
            self.play(*animations, run_time=1.5)

            # 4. Wait
            remaining_audio = audio_duration - 1.5
            buffer_time = 0.1
            if remaining_audio > 0:
                self.wait(remaining_audio + buffer_time)
            else:
                self.wait(buffer_time)

# ==========================================
# 4. WRAPPER
# ==========================================
def render_code_animation(json_input):
    output_folder = "./output_video"
    config.media_dir = output_folder
    config.verbosity = "WARNING"
    config.quality = "low_quality"
    config.preview = False 
    
    scene = CodeAnimatorEngine(script_data=json_input)
    scene.render()
    
    final_filename = "CodeAnimatorEngine.mp4"
    found_video = None
    for root, dirs, files in os.walk(output_folder):
        if final_filename in files:
            found_video = os.path.join(root, final_filename)
            break
            
    target_video = "final_output.mp4"
    final_path = os.path.abspath(target_video)

    if found_video:
        if os.path.exists(target_video): os.remove(target_video)
        shutil.move(found_video, target_video)
    else:
        return None

    if os.path.exists(output_folder): shutil.rmtree(output_folder)
    for f in glob.glob("voiceover_*.mp3"): 
        try: os.remove(f)
        except: pass
        
    return final_path