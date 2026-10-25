from manim import *
import numpy as np


class ForLoopPrint(Scene):
    def construct(self):
        self.camera.background_color = "#0F1117"

        PANEL = "#171B24"
        STROKE = "#2D3545"
        BLUE = "#58A6FF"
        GREEN = "#3FB950"
        YELLOW = "#D29922"
        RED = "#F85149"
        TEXT = "#E6EDF3"
        GRAY = "#8B949E"
        MONO = "Consolas"

        code_panel = RoundedRectangle(
            width=6.9,
            height=5.2,
            corner_radius=0.18,
            fill_color=PANEL,
            fill_opacity=0.96,
            stroke_color=STROKE,
            stroke_width=1.5,
        ).move_to(LEFT * 3.6)

        out_panel = RoundedRectangle(
            width=4.3,
            height=5.2,
            corner_radius=0.18,
            fill_color=PANEL,
            fill_opacity=0.96,
            stroke_color=STROKE,
            stroke_width=1.5,
        ).move_to(RIGHT * 3.95)

        self.play(
            FadeIn(code_panel, shift=RIGHT * 0.15),
            FadeIn(out_panel, shift=LEFT * 0.15),
            run_time=0.7,
        )

        code_x = code_panel.get_left()[0] + 0.38
        line1 = Text(
            "for (int i=0; i<5; i++) {",
            font=MONO,
            font_size=28,
            color=TEXT,
        ).move_to(np.array([code_x, 1.45, 0]), aligned_edge=LEFT)
        line2 = Text(
            "    print(i);",
            font=MONO,
            font_size=28,
            color=TEXT,
        ).move_to(np.array([code_x, 0.80, 0]), aligned_edge=LEFT)
        line3 = Text(
            "}",
            font=MONO,
            font_size=28,
            color=TEXT,
        ).move_to(np.array([code_x, 0.15, 0]), aligned_edge=LEFT)

        badge = RoundedRectangle(
            width=2.1,
            height=0.68,
            corner_radius=0.12,
            fill_color=BLUE,
            fill_opacity=0.12,
            stroke_color=BLUE,
            stroke_width=1.8,
        ).move_to(np.array([code_panel.get_left()[0] + 1.45, -1.35, 0]))

        i_text = Text("i = 0", font=MONO, font_size=30, color=TEXT).move_to(badge)

        self.play(
            Write(line1),
            Write(line2),
            Write(line3),
            FadeIn(badge),
            FadeIn(i_text),
            run_time=1.0,
        )
        self.wait(0.25)

        out_title = Text("OUTPUT", font=MONO, font_size=21, color=GRAY)
        out_title.move_to(np.array([out_panel.get_center()[0], 2.15, 0]))
        divider = Line(
            np.array([out_panel.get_left()[0] + 0.35, 1.85, 0]),
            np.array([out_panel.get_right()[0] - 0.35, 1.85, 0]),
            stroke_color=STROKE,
            stroke_width=1.2,
        )
        self.play(FadeIn(out_title), Create(divider), run_time=0.45)

        print_hl = SurroundingRectangle(
            line2, color=YELLOW, buff=0.09, corner_radius=0.07
        )
        print_hl.set_fill(YELLOW, 0.08)

        slot_y = [1.40, 0.75, 0.10, -0.55, -1.20]

        for n in range(5):
            self.play(
                Indicate(line1, color=GREEN, scale_factor=1.025),
                run_time=0.45,
            )
            self.play(Create(print_hl), run_time=0.20)

            number = Text(str(n), font=MONO, font_size=48, color=GREEN)
            number.move_to(np.array([out_panel.get_center()[0], slot_y[n], 0]))
            self.play(
                FadeIn(number, shift=UP * 0.12, scale=0.75),
                run_time=0.35,
            )
            self.play(FadeOut(print_hl), run_time=0.15)

            if n < 4:
                next_i = Text(f"i = {n + 1}", font=MONO, font_size=30, color=TEXT)
                next_i.move_to(badge)
                self.play(Transform(i_text, next_i), run_time=0.28)

        final_i = Text("i = 5", font=MONO, font_size=30, color=TEXT)
        final_i.move_to(badge)
        self.play(Transform(i_text, final_i), run_time=0.30)
        self.play(
            Indicate(line1, color=RED, scale_factor=1.025),
            run_time=0.55,
        )
        self.wait(1.0)
