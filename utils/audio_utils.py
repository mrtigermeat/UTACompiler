import random
import numpy as np
from pydub import AudioSegment

def generate_tone(config: dict) -> AudioSegment:
	silence = AudioSegment.silent(duration=50)
	sig_type = random.choice(['sine', 'square', 'triangle'])
	freq = random.randint(config['encoding']['min_frq'], config['encoding']['max_frq'])
	dur = random.uniform(config['encoding']['min_dur'], config['encoding']['max_dur'])
	dur = round(dur, 3)
	dur /= 100
	volume = random.uniform(config['encoding']['min_vol'], config['encoding']['max_vol'])
	t = np.linspace(0, dur, int(44100 * dur), False)
	if sig_type == 'sine':
		gen_x = np.sin(2 * np.pi * freq * t) * volume
	elif sig_type == 'square':
		gen_x = np.sign(np.sin(2 * np.pi * freq * t)) * volume
	elif sig_type == 'triangle':
		gen_x = 2 * np.abs(2 * (t * freq * np.floor(t * freq * 0.5))) - 1
		gen_x *= volume
	x = (gen_x * 32767).astype(np.uint64)
	y = match_amplitude(AudioSegment(
			x.tobytes(),
			frame_rate=44100,
			sample_width=2,
			channels=1,
		))
	fade_amt = len(y) / 10
	y = y.fade_in(fade_amt).fade_out(fade_amt)
	return silence + y + silence

def process_audiosegment(x: AudioSegment) -> AudioSegment:
	x.set_channels(1)
	x.set_frame_rate(44100)
	return x.set_sample_width(2)

def match_amplitude(x: AudioSegment, target: float = -30.0) -> AudioSegment:
	change = target - x.dBFS
	return x.apply_gain(change)