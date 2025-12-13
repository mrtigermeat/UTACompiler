import sys
import os
import gradio as gr
from pathlib import Path
from ezlocalizr import ezlocalizr

root_dir = Path(__file__).parent.parent.resolve()
os.environ['PYTHONPATH'] = str(root_dir)
sys.path.insert(0, str(root_dir))

from UTACompiler import utacompiler
from utils.logger_utils import get_logger

logger = get_logger(level="INFO")

webapp_src = Path('src')
assert webapp_src.exists()

if sys.platform in ['linux', 'linux2', 'darwin']:
	sys_lang = os.environ['LANG']
elif sys.platform == 'win32':
	import ctypes
	import locale
	windll = ctypes.windll.kernel32
	sys_lang = locale.windows_locale[windll.GetUserDefaultUILanguage()]
L = ezlocalizr(
	language=sys_lang,
	string_path=webapp_src/'strings',
	default_lang='en_US'
)

def dummy() -> None:
	logger.info('bark bark :3')

def run_tool(
	db_path: str,
	db_name: str,
	seed: int,
	recording_style: str,
	keep_files: str,
	keep_folders: str,
	pitches: str,
	encoding: str,
	scramble: bool,
	glob_amt: int,
	encoder_active: bool,
	min_frq: int,
	max_frq: int,
	min_dur: float,
	max_dur: float,
	min_vol: float,
	max_vol: float,
	pad_val: float
) -> None:
	config = {}
	config['name'] = db_name
	config['seed'] = seed
	config['files'] = {}
	try:
		config['files']['keep_files'] = [x.strip() for x in keep_files.split(',')]
		config['files']['keep_folders'] = [x.strip() for x in keep_folders.split(',')]
		config['files']['pitches'] = [x.strip() for x in pitches.split(',')]
	except Exception as e:
		logger.error(f'Unable to process configuration: {e}')
		sys.exit(1)
	config['files']['file_encoding'] = encoding
	config['files']['scramble'] = scramble
	config['files']['glob'] = glob_amt
	config['encoding'] = {}
	config['encoding']['enabled'] = encoder_active
	config['encoding']['min_frq'] = min_frq
	config['encoding']['max_frq'] = max_frq
	config['encoding']['min_dur'] = min_dur
	config['encoding']['max_dur'] = max_dur
	config['encoding']['min_vol'] = min_vol
	config['encoding']['max_vol'] = max_vol
	config['encoding']['pad_val'] = pad_val
	
	try:
		utacompiler(db_path, config)
	except Exception as e:
		logger.error(f'Unable to compile UTAU Voice Library: {e}')
		sys.exit(1)

def gui() -> None:
	with gr.Blocks(title=L('title')) as app:

		gr.Markdown(f"# {L('title')}")
		gr.Markdown(L('how_to'))

		# ROW 1
		with gr.Row():
			# COLUMN 1
			with gr.Column():
				db_path = gr.Textbox(label=L('db_path'))

				with gr.Accordion(L('config'), open=True):
					gr.Markdown(L('config_exp'))
					db_name = gr.Textbox(
						label=L('db_name'),
						placeholder='Utane Uta'
					)
					with gr.Row():
						seed = gr.Number(
							label=L('seed'),
							value=69420,
						)
						recording_style = gr.Radio(
							choices=['CV', 'VCV', 'CVVC', 'VCCV'],
							value='CVVC',
							label=L('recording_style'),
							interactive=True
						)
					keep_files = gr.Textbox(
						label=L('keep_files'),
						placeholder='$read, character.txt, character.yaml, ...'
					)
					keep_folders = gr.Textbox(
						label=L('keep_folders'),
						placeholder='omake, extra, ...'
					)
					pitches = gr.Textbox(
						label=L('pitches'),
						placeholder='C4, Whisper, CVVC, ...'
					)
					encoding = gr.Radio(
						choices=['utf-8', 'shift-jis'],
						value='shift-jis',
						label=L('file_encoding'),
						interactive=True
					)

			# COLUMN 2
			with gr.Column():
				with gr.Accordion(L('config_adv'), open=False):
					gr.Markdown(L('config_adv_exp'))
					with gr.Row():
						scramble = gr.Checkbox(
							label=L('scramble'),
							value=True,
							interactive=True,
						)
						glob_amt = gr.Number(
							label=L('glob_amt'),
							value=8,
							interactive=True,
						)
					with gr.Row():
						pad_val = gr.Slider(
							label=L('pad_val'),
							value=0.75,
							minimum=0.25,
							maximum=2.0,
							step=0.05,
							interactive=True,
					)
					gr.Markdown(f"### {L('encoding_options')}")

					encoder_active = gr.Checkbox(
						label=L('encoder_active'),
						interactive=True,
						value=True,
					)

					gr.Markdown(L('gen_options'))

					with gr.Row():
						min_frq = gr.Slider(
							label=L('min_frq'),
							value=200,
							minimum=50,
							maximum=500,
							step=10,
							interactive=True,
						)
						max_frq = gr.Slider(
							label=L('max_frq'),
							value=1000,
							minimum=500,
							maximum=1500,
							step=10,
							interactive=True,
						)
					with gr.Row():
						min_dur = gr.Slider(
							label=L('min_dur'),
							value=1.0,
							minimum=0.5,
							maximum=3.0,
							step=0.1,
							interactive=True,
						)
						max_dur = gr.Slider(
							label=L('max_dur'),
							value=4.0,
							minimum=1.0,
							maximum=10.0,
							step=0.1,
							interactive=True,
						)
					with gr.Row():
						min_vol = gr.Slider(
							label=L('min_vol'),
							value=0.2,
							minimum=0.1,
							maximum=0.4,
							step=0.1,
							interactive=True,
						)
						max_vol = gr.Slider(
							label=L('max_vol'),
							value=0.6,
							minimum=0.4,
							maximum=1.0,
							step=0.1,
							interactive=True,
						)

				run_button = gr.Button(
					value=L('run_button'),
				)
				run_button.click(run_tool, inputs=[
					db_path,
					db_name,
					seed,
					recording_style,
					keep_files,
					keep_folders,
					pitches,
					encoding,
					scramble,
					glob_amt,
					encoder_active,
					min_frq,
					max_frq,
					min_dur,
					max_dur,
					min_vol,
					max_vol,
					pad_val,
				], outputs=None)

		gr.HTML("""
			<style>
				.bottom-right {
					position: fixed;
					bottom: 0;
					right: 0;
					padding: 15px;
					margin: 10px;
					z-index: 1000;
				}
			</style>

			<div class="bottom-right">
				<a href="https://notbyai.fyi/" target="_blank" rel="noopener noreferrer">
					<img src="https://github.com/mrtigermeat/UTACompiler/blob/main/src/img/notbyai.png?raw=true" width="131">
				</a>
			</div>
		""")

	app.queue().launch(
		server_name="0.0.0.0",
		inbrowser=True,
		quiet=True,
		favicon_path=webapp_src/'tgm.ico',
	)

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', '-d', is_flag=True, help='Display developer messages.')
	def main(debug: bool) -> None:
		if debug:
			logger.remove()
			logger.add(sys.stdout, format=logger_format, level="DEBUG")
		gui()
	main()