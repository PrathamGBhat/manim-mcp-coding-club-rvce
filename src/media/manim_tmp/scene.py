from manim import *
import numpy as np

config.pixel_width = 720
config.pixel_height = 1280
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#0E1116"

WHITE = "#EDF2F4"
CYAN = "#4DD0E1"
AMBER = "#FFC857"
RED = "#FF6B6B"
GREEN = "#7BE495"
SLATE = "#39424E"

CELL = 0.86
BASE_Y = 1.55


def make_cell(char, accent, w=CELL, h=CELL, fs=40):
    box = RoundedRectangle(
        width=w, height=h, corner_radius=0.12,
        stroke_color=accent, stroke_width=2.2,
        fill_color=accent, fill_opacity=0.12,
    )
    txt = Text(char, font_size=fs, color=WHITE)
    return VGroup(box, txt)


class RemoveKDigits(Scene):
    def construct(self):
        title = Text("Remove K Digits", font_size=44, weight=BOLD, color=WHITE)
        title.move_to([0, 5.95, 0])
        sub = Text("Monotonic Stack | O(n)", font_size=24, color=CYAN)
        sub.next_to(title, DOWN, buff=0.18)
        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(sub), run_time=0.8)

        num = "1043219"
        k = 3

        in_cells = VGroup(*[make_cell(ch, SLATE, 0.80, 0.80, 38) for ch in num])
        in_cells.arrange(RIGHT, buff=0.10)
        in_cells.move_to([0, 4.45, 0])
        self.play(
            LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in in_cells], lag_ratio=0.08),
            run_time=0.7,
        )

        k_box = RoundedRectangle(
            width=1.55, height=0.62, corner_radius=0.18,
            stroke_color=AMBER, stroke_width=2,
            fill_color=AMBER, fill_opacity=0.12,
        )
        k_txt = Text(f"k = {k}", font_size=28, color=AMBER)
        k_badge = VGroup(k_box, k_txt).move_to([0, 3.45, 0])
        self.play(FadeIn(k_badge), run_time=0.4)

        stack_label = Text("stack", font_size=22, color=CYAN)
        stack_label.move_to([-3.35, 2.45, 0])
        base = Line([-3.6, 1.02, 0], [3.6, 1.02, 0], stroke_color=SLATE, stroke_width=3)
        self.play(FadeIn(stack_label), Create(base), run_time=0.5)

        status = {"mob": None}

        def say(msg, color=WHITE):
            new = Text(msg, font_size=22, color=color).move_to([0, 0.42, 0])
            if status["mob"] is None:
                status["mob"] = new
                self.play(FadeIn(new, shift=UP * 0.08), run_time=0.22)
            else:
                old = status["mob"]
                self.play(Transform(old, new), run_time=0.26)

        def set_k(new_k):
            new = Text(f"k = {new_k}", font_size=28, color=AMBER).move_to(k_txt.get_center())
            self.play(Transform(k_txt, new), run_time=0.22)

        def slot(i):
            return np.array([-2.77 + i * 0.96, BASE_Y, 0])

        stack_cells = []

        def push(ch, i):
            c = make_cell(ch, CYAN)
            c.move_to(slot(i) + UP * 1.25)
            c.set_opacity(0)
            self.play(c.animate.move_to(slot(i)).set_opacity(1), run_time=0.42)
            stack_cells.append(c)

        for idx, ch in enumerate(num):
            cur = in_cells[idx]
            self.play(cur[0].animate.set_stroke(AMBER, width=3.2), run_time=0.18)

            while stack_cells and k > 0 and stack_cells[-1][1].text > ch:
                top = stack_cells[-1]
                topd = top[1].text
                self.play(
                    top[0].animate.set_stroke(RED),
                    top[1].animate.set_color(RED),
                    run_time=0.18,
                )
                say(f"pop {topd}   ({topd} > {ch})", RED)
                self.play(top.animate.shift(UP * 1.0).set_opacity(0), run_time=0.32)
                self.remove(top)
                stack_cells.pop()
                k -= 1
                set_k(k)

            say(f"push {ch}", CYAN)
            push(ch, len(stack_cells))
            self.play(cur[0].animate.set_stroke(SLATE, width=2.2), run_time=0.14)

        while k > 0:
            say(f"k = {k} left  ->  drop last", AMBER)
            top = stack_cells.pop()
            self.play(top.animate.shift(UP * 1.0).set_opacity(0), run_time=0.3)
            self.remove(top)
            k -= 1
            set_k(k)

        if stack_cells and stack_cells[0][1].text == "0":
            say("strip leading zeros", AMBER)
            while stack_cells and stack_cells[0][1].text == "0":
                lead = stack_cells.pop(0)
                self.play(
                    lead[0].animate.set_stroke(AMBER),
                    lead[1].animate.set_color(AMBER),
                    run_time=0.18,
                )
                self.play(lead.animate.shift(UP * 0.9).set_opacity(0), run_time=0.3)
                self.remove(lead)
                if stack_cells:
                    self.play(
                        *[c.animate.move_to(slot(i)) for i, c in enumerate(stack_cells)],
                        run_time=0.3,
                    )

        res = "".join(c[1].text for c in stack_cells) if stack_cells else "0"

        say("done", GREEN)
        res_lbl = Text("result", font_size=22, color=GREEN)
        res_val = Text(res, font_size=52, weight=BOLD, color=GREEN)
        res_grp = VGroup(res_lbl, res_val).arrange(RIGHT, buff=0.35)
        res_grp.move_to([0, -1.05, 0])
        self.play(FadeIn(res_grp, shift=UP * 0.2), run_time=0.7)
        self.wait(1.2)
