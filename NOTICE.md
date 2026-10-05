# Notice

This extension began as a conversion of
[ComfyUI-EasyColorCorrector](https://github.com/regiellis/ComfyUI-EasyColorCorrector)
by Regi E. (regiellis), released under the MIT License. Its Preset and Manual
modes, CLIP content analysis and SegFormer subject mask have been removed, and
the Auto correction has been rewritten; the original's copyright notice is kept
in `LICENSE`.

| File | Source |
|---|---|
| `lib_acc/auto.py`, `lib_acc/ops.py` | New: measuring, guards and corrections. |
| `scripts/auto_color_corrector.py`, `lib_acc/controls.py`, `lib_acc/reference.py`, `style.css` | New: WebUI panel, control table, PNG info, reference box. |
| `reference.jpg` | New. Rendered with this extension on scikit-image sample photos: Eileen Collins by NASA (public domain), coffee cup by Rachel Michetti (CC0), Falcon 9 launch by SpaceX (public domain). |
