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
| pyobjc-core | MIT | Python-Objective-C bridge |
| pyobjc-framework-Cocoa | MIT | macOS Cocoa framework bindings |

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

---

For the full text of the MIT license, see `LICENSES/MIT.txt`.
