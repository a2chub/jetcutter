# Third-Party Licenses

This document lists the third-party libraries used by JetCutter and their respective licenses.

## License Summary

| Package | License | Notes |
|---------|---------|-------|
| ffmpeg-python | MIT | Video/audio processing wrapper |
| pydub | MIT | Audio manipulation |
| faster-whisper | MIT | Speech recognition |
| PyYAML | MIT | YAML configuration parsing |
| pydantic | MIT | Data validation |
| pydantic-settings | MIT | Settings management |
| loguru | MIT | Logging |
| typer | MIT | CLI framework |
| rich | MIT | Terminal formatting |
| PySimpleGUI4 | LGPL-3.0 | Legacy GUI (see special notice below) |
| pyobjc-core | MIT | Python-Objective-C bridge |
| pyobjc-framework-Cocoa | MIT | macOS Cocoa framework bindings |

## Special Notice: PySimpleGUI4 (LGPL-3.0)

PySimpleGUI4 is distributed under the GNU Lesser General Public License v3.0 (LGPL-3.0).

As required by LGPL-3.0:
- The complete source code for PySimpleGUI4 can be obtained from: https://github.com/PySimpleGUI/PySimpleGUI
- The full text of the LGPL-3.0 license is available in `LICENSES/LGPL-3.0.txt`
- The full text of the GPL-3.0 license (referenced by LGPL-3.0) is available in `LICENSES/GPL-3.0.txt`

JetCutter uses PySimpleGUI4 as a dynamically linked library, which means:
- You have the right to modify or replace the PySimpleGUI4 library
- The library is located in `Contents/Resources/app_packages/` within the application bundle
- Your modifications to JetCutter itself are not required to be licensed under LGPL/GPL

## External Tools

### FFmpeg

JetCutter requires FFmpeg for video and audio processing. FFmpeg is NOT bundled with JetCutter.

Users must install FFmpeg separately via:
```bash
brew install ffmpeg
```

FFmpeg is a separate project with its own licensing. When built with default options, it is typically licensed under LGPL-2.1+. Some build configurations may include GPL-licensed components.

For FFmpeg licensing details, see: https://ffmpeg.org/legal.html

### Whisper Models

JetCutter uses the faster-whisper library, which loads OpenAI Whisper models.

OpenAI Whisper is licensed under MIT License.
- Repository: https://github.com/openai/whisper
- License: MIT

## Detailed License Information

### MIT Licensed Packages

The following packages are licensed under the MIT License:

**ffmpeg-python**
- Copyright (c) 2017 Karl Kroening
- https://github.com/kkroening/ffmpeg-python

**pydub**
- Copyright (c) 2011 James Robert
- https://github.com/jiaaro/pydub

**faster-whisper**
- Copyright (c) 2023 Guillaume Klein
- https://github.com/SYSTRAN/faster-whisper

**PyYAML**
- Copyright (c) 2017-2021 Ingy döt Net
- Copyright (c) 2006-2016 Kirill Simonov
- https://github.com/yaml/pyyaml

**pydantic**
- Copyright (c) 2017-present, Samuel Colvin and other contributors
- https://github.com/pydantic/pydantic

**pydantic-settings**
- Copyright (c) 2022-present, Hasan Ramezani
- https://github.com/pydantic/pydantic-settings

**loguru**
- Copyright (c) 2017 Delgan
- https://github.com/Delgan/loguru

**typer**
- Copyright (c) 2019 Sebastián Ramírez
- https://github.com/tiangolo/typer

**rich**
- Copyright (c) 2020 Will McGugan
- https://github.com/Textualize/rich

**pyobjc-core / pyobjc-framework-Cocoa**
- Copyright (c) 2002-2023 Ronald Oussoren
- https://github.com/ronaldoussoren/pyobjc

### LGPL-3.0 Licensed Packages

**PySimpleGUI4**
- Copyright (c) 2018-2023 PySimpleGUI
- https://github.com/PySimpleGUI/PySimpleGUI
- License: LGPL-3.0
- See `LICENSES/LGPL-3.0.txt` for the full license text

---

For the full text of each license, see the `LICENSES/` directory.
