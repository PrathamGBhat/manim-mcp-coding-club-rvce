from manim import *

class ForLoopPrint(Scene):
    def construct(self):
        title = Text("for i in range(5): print(i)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))

        code_box = RoundedRectangle(
            width=7.5, height=1.4, corner_radius=0.15,
            color=BLUE, fill_opacity=0.12
        )
        code_box.next_to(title, DOWN, buff=0.5)

        code = VGroup(
            Text("for i in range(5):", font_size=30, color=YELLOW),
            Text("    print(i)", font_size=30, color=YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        code.move_to(code_box.get_center())

        self.play(Create(code_box), Write(code), run_time=1.5)
        self.wait(0.5)

        loop_arc = Arc(radius=0.8, start_angle=0, angle=-TAU, color=GREEN)
        loop_arc.next_to(code_box, RIGHT, buff=0.8)
        loop_label = Text("loop", font_size=28, color=GREEN).move_to(loop_arc)
        arrow_cap = Arrow(
            loop_arc.get_end(), loop_arc.get_start(),
            buff=0, color=GREEN, stroke_width=4,
        )

        output_title = Text("Output", font_size=28, color=GREY_B).move_to(LEFT * 4 + DOWN * 0.5)
        divider = Line(UP * 2.5, DOWN * 2.5, color=GREY_D)
        divider.shift(LEFT * 0.8)

        self.play(Create(divider), FadeIn(output_title))

        run_box = RoundedRectangle(
            width=4.5, height=3.6, corner_radius=0.15,
            color=GREEN, fill_opacity=0.08
        )
        run_box.move_to(RIGHT * 4 + DOWN * 0.5)
        self.play(Create(run_box))

        self.play(Create(loop_arc), FadeIn(loop_label), GrowArrow(arrow_cap))

        printed = VGroup()
        for i in range(5):
            i_label = Text(f"i = {i}", font_size=28, color=ORANGE)
            i_label.next_to(code_box, LEFT, buff=0.6)

            out_line = Text(str(i), font_size=34, color=WHITE)
            out_line.next_to(printed, DOWN, buff=0.22) if len(printed) else \
                out_line.next_to(run_box.get_top(), DOWN, buff=0.4)

            self.play(FadeIn(i_label, shift=RIGHT * 0.2), run_time=0.4)
            flash = code[1].copy().set_color(GREEN)
            self.play(Transform(code[1].copy(), flash), run_time=0.01)
            self.play(Write(out_line), run_time=0.4)
            printed.add(out_line)
            self.play(FadeOut(i_label), run_time=0.3)

        self.play(loop_label.animate.set_color(YELLOW), run_time=0.5)
        done = Text("Loop complete", font_size=26, color=GREEN)
        done.next_to(run_box, DOWN, buff=0.3)
        self.play(FadeIn(done))
        self.wait(2)
