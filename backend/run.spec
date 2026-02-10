# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Vibebells Backend
Bundles Flask backend into standalone executable
"""

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),  # Include entire app directory with all services
    ],
    hiddenimports=[
        # Core dependencies
        'flask',
        'flask_cors',
        'mido',
        'music21',
        'numpy',
        'werkzeug',
        'werkzeug.security',
        'werkzeug.utils',
        'dotenv',
        
        # Flask dependencies
        'flask.json',
        'flask.json.provider',
        
        # Backend services (explicit imports)
        'app',
        'app.routes',
        'app.services',
        'app.services.file_handler',
        'app.services.music_parser',
        'app.services.midi_parser',
        'app.services.musicxml_parser',
        'app.services.melody_harmony_extractor',
        'app.services.bell_assignment',
        'app.services.conflict_resolver',
        'app.services.arrangement_validator',
        'app.services.arrangement_generator',
        'app.services.swap_counter',
        'app.services.export_formatter',
        
        # Music21 dependencies
        'music21.midi',
        'music21.stream',
        'music21.note',
        'music21.chord',
        'music21.tempo',
        
        # Other potential dependencies
        'csv',
        'io',
        'datetime',
        'logging',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        
        # Music21 optional features
        # NOTE: music21 has complex internal dependencies
        # Cannot safely exclude corpus or test modules
        'music21.documentation',
        'music21.demos',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vibebells-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression to reduce size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for logging (can set to False later)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
