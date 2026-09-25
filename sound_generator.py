import os
import math
import struct
import wave

def generate_wav(filepath, duration, freq_fn, volume=0.4, sample_rate=44100):
    """Generates a WAV audio file based on a frequency generation function over time."""
    num_samples = int(sample_rate * duration)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            progress = t / duration
            freq = freq_fn(t, progress)
            
            # Envelope (attack / decay)
            env = 1.0
            if progress < 0.05:
                env = progress / 0.05
            elif progress > 0.7:
                env = (1.0 - progress) / 0.3
                
            sample_val = math.sin(2.0 * math.pi * freq * t) * env * volume
            # Clamp sample value
            sample_val = max(-1.0, min(1.0, sample_val))
            int_val = int(sample_val * 32767)
            frames.extend(struct.pack('<h', int_val))
            
        wav_file.writeframes(frames)

def generate_all_sounds():
    base_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Melee punch sound (quick downward frequency sweep + noise-like synth)
    def sfx_punch(t, p):
        return 300 * (1 - p ** 0.5) + 60
    generate_wav(os.path.join(base_dir, "punch.wav"), 0.12, sfx_punch, volume=0.5)
    
    # 2. Ranged laser shoot sound (high to low sweep)
    def sfx_shoot(t, p):
        return 880 * math.exp(-6 * p) + 120
    generate_wav(os.path.join(base_dir, "shoot.wav"), 0.2, sfx_shoot, volume=0.4)
    
    # 3. Hit / Impact sound
    def sfx_hit(t, p):
        return 180 * math.sin(p * 20) + 90
    generate_wav(os.path.join(base_dir, "hit.wav"), 0.15, sfx_hit, volume=0.6)

    # 4. Jump sound (low to high sweep)
    def sfx_jump(t, p):
        return 150 + 400 * (p ** 0.7)
    generate_wav(os.path.join(base_dir, "jump.wav"), 0.15, sfx_jump, volume=0.35)
    
    # 5. Select / Click sound
    def sfx_select(t, p):
        return 520 + 260 * math.sin(p * 15)
    generate_wav(os.path.join(base_dir, "select.wav"), 0.08, sfx_select, volume=0.3)
    
    # 6. Victory sound (arpeggio sequence)
    def sfx_win(t, p):
        step = int(p * 4)
        notes = [440, 554.37, 659.25, 880]
        return notes[min(step, 3)]
    generate_wav(os.path.join(base_dir, "victory.wav"), 0.6, sfx_win, volume=0.45)
    
    # 7. Defeat sound (descending tones)
    def sfx_lose(t, p):
        step = int(p * 4)
        notes = [440, 392, 349.23, 220]
        return notes[min(step, 3)]
    generate_wav(os.path.join(base_dir, "defeat.wav"), 0.7, sfx_lose, volume=0.45)

if __name__ == "__main__":
    generate_all_sounds()
    print("All sound assets generated successfully.")
