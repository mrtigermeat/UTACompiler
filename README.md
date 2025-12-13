# UTACompiler
_Compile & Encode your UTAU Voicebank_

UTACompiler is a tool that extracts the necessary audio from your UTAU library based on the oto.ini file and scrambles it, with the option to include randomized noise to deter misuse of your recordings!

## How to use (Manual setup)
Step 1: Clone the repository, setup a new environment (I use conda) and install requirements.
```
git clone https://github.com/mrtigermeat/UTACompiler.git
cd UTACompiler
conda create -n "utacompiler" python=3.12 -y
conda activate utacompiler
pip install -r requirements.txt
```
Step 2: BACK UP A COPY OF YOUR UTAU VB!!! I cannot be held liable if UTACompiler messes up your VB in an irreversible way.

Step 3: Open the gradio webapp.
```
python webapp.py
```
Step 3.5: Alternatively, use the command-line version of UTACompiler. You will need to place a copy of "utacompiler_config.yaml" into your voice library's folder, and adjust the settings accordingly. Reference the webapp to know what each option does. There is no need to include `-c <path_to_config>` if you place it in the voice libary's root.
```
python UTACompiler.py -c <path_to_config>
```

Output will be saved to `<db_path>/UTACompilerOutput`. Be sure to rigorously test your VB, and ensure it functions well and sounds right. Please report any issues to this repository!
