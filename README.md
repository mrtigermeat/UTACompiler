# UTACompiler
_Compile & Encode your UTAU Voicebank_

UTACompiler is a tool that extracts the necessary audio from your UTAU library based on the oto.ini file and scrambles it, with the option to include randomized noise to deter misuse of your recordings!

<div align="center">
  <p>
    <sub>No Generative AI was used in the creation of UTACompiler or any component written for it.</sub>
  </p>
  <a href="https://notbyai.fyi/" target="_blank" rel="noopener noreferrer">
    <img src="src/img/notbyai.png" alt="Not by AI badge.">
  </a>
</div>

## Known Issues / To do list
- It is extremely untested, and will not be fully released until I'm confident it works how I want.
- It's highly possible that including generated audio will cause frq problems when using the UTAU. It's not feasable to create a way to splice up frq files, so I might implement something that ensures each file has some voiced singing samples.
- It's possible that a VCV with CVVC aliases will end up a bigger file size than it started with, so I might make a function that pulls just the VCV segments and alises them with the CVVC. No idea how I'd go about that currently.

## ~~How to use - Portable version (RECOMMENDED)~~ Not ready yet
Step 1: Download the portable version from [here]().

Step 2: Unzip to a folder.

Step 3: Run "run_webapp.bat" and click allow if prompted by Python.

Step 4: Follow directions on webapp.

## How to use - Manual Setup
Step 1: Clone the repository, setup a new environment (I use conda) and install requirements. (It doesn't necessarily need to be Python 3.12, but that's the version I developed it with.)
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
Step 3.5: Alternatively, use the command-line version of UTACompiler. You will need to place a copy of "utacompiler_config.yaml" into your voice library's folder, and adjust the settings accordingly. Reference the webapp to know what each option does. There is no need to include `-c <path_to_config>` if you place it in the voice library's root.
```
python UTACompiler.py -c <path_to_config>
```

Output will be saved to `<db_path>/UTACompilerOutput`. Be sure to rigorously test your VB, and ensure it functions well and sounds right. Please report any issues to this repository!

## Attribution

French webapp translation by [Mim](https://bsky.app/profile/mimsynth.bsky.social)

German webapp translation by [Gyromancy](https://bsky.app/profile/gyromancyx.bsky.social)