"""Auto Color Corrector - UI and host hook. The work is in lib_acc/."""

import os
import sys
import traceback

import gradio as gr
from modules import devices, script_callbacks, scripts
from modules.ui_components import InputAccordion

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if EXTENSION_ROOT not in sys.path:
    sys.path.insert(0, EXTENSION_ROOT)

from lib_acc.auto import correct  # noqa: E402
from lib_acc.controls import (  # noqa: E402
    BY_NAME, INFOTEXT_KEY, NAMES, REPORT_KEY, coerce, from_infotext, settings, to_infotext,
)
from lib_acc.reference import reference_html  # noqa: E402
from lib_acc import xyz  # noqa: E402

GUIDE = ("*Fixes what is off and nothing else: colour casts, milky blacks, too dark or too bright, flat or "
         "harsh, dull colour. Each fix measures the image first and is skipped when there is nothing to "
         "fix. Runs before Optical Realism and Digital Mastering, so they start from a clean picture. "
         "The console and PNG info say what was found.*")

SECTIONS = [
    ("Colour cast", ["en_wb", "wb", "keep_mood"]),
    ("Tone", ["en_levels", "levels", "en_exposure", "exposure", "en_contrast", "contrast"]),
    ("Colour strength", ["en_saturation", "saturation"]),
    ("Intent", ["protect_intent"]),
]


XYZ_ATTR = "_acc_xyz"


def _register_xyz():
    xyz.register("ACC", XYZ_ATTR, [
        ("Overall strength", float, "strength", None),
        ("Keep mood", float, "keep_mood", None),
        ("Fix colour cast", str, "en_wb", xyz.bools),
        ("Fix black & white points", str, "en_levels", xyz.bools),
        ("Fix exposure", str, "en_exposure", xyz.bools),
        ("Fix contrast", str, "en_contrast", xyz.bools),
        ("Fix colour strength", str, "en_saturation", xyz.bools),
        ("Respect low-key / high-key", str, "protect_intent", xyz.bools),
    ])


# Once the scripts are loaded, before the UI is built: the X/Y/Z plot reads its
# axis list when it builds its own panel.
script_callbacks.on_before_ui(_register_xyz)


class Script(scripts.Script):
    # First of the three: correction, then the camera (Optical Realism, 150),
    # then the grade (Digital Mastering, 160).
    sorting_priority = 140

    def title(self):
        return "Auto Color Corrector"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        tab = "img2img" if is_img2img else "txt2img"
        comps = {}

        def add(name):
            c = BY_NAME[name]
            eid = f"acc_{name}_{tab}"
            info = c.info or None
            if c.kind == "checkbox":
                comps[name] = gr.Checkbox(label=c.label, value=c.default, elem_id=eid, info=info)
            else:
                comps[name] = gr.Slider(label=c.label, minimum=c.minimum, maximum=c.maximum, step=c.step,
                                        value=c.default, elem_id=eid, info=info)

        # Explicit elem_ids everywhere, one set per tab, so saved ui-config
        # defaults stay bound to the right control.
        with InputAccordion(False, label="Auto Color Corrector", elem_id=f"acc_enabled_{tab}") as enabled:
            gr.Markdown(GUIDE)
            gr.HTML(reference_html(EXTENSION_ROOT, "acc-ref", "Auto Color Corrector before and after"),
                    elem_id=f"acc_ref_{tab}")
            add("strength")
            for title, names in SECTIONS:
                gr.Markdown(f"**{title}**")
                for n in names:
                    add(n)
            with gr.Accordion("Reference image (optional)", open=False):
                reference = gr.Image(label="Match colour to this picture", type="pil", height=160,
                                     elem_id=f"acc_reference_{tab}")
                add("ref_strength")

        def field(name):
            def get(params):
                s = from_infotext(params.get(INFOTEXT_KEY, ""))
                return None if s is None else s[name]
            return get

        self.infotext_fields = [(enabled, lambda d: INFOTEXT_KEY in d)]
        self.infotext_fields += [(comps[n], field(n)) for n in NAMES]
        self.paste_field_names = [INFOTEXT_KEY]

        return [enabled, reference, *[comps[n] for n in NAMES]]

    # After the composite, so an "only masked" inpaint is corrected as a whole
    # image instead of leaving a seam at the crop edge.
    def postprocess_image_after_composite(self, p, pp, enabled, reference, *values):
        axis = xyz.overrides(p, XYZ_ATTR)
        if not (enabled or axis) or pp.image is None:
            return
        s = settings(dict(zip(NAMES, values)))
        if axis:
            s = xyz.merged(s, axis, coerce, BY_NAME)
        try:
            result, plan = correct(pp.image, s, reference=reference, device=devices.device)
        except Exception as exc:
            traceback.print_exc()
            print(f"[Auto Color Corrector] Error, image left untouched: {exc}")
            return
        print(f"[Auto Color Corrector] {plan.report()}")
        pp.image = result
        p.extra_generation_params[INFOTEXT_KEY] = to_infotext(s)
        p.extra_generation_params[REPORT_KEY] = plan.report()
