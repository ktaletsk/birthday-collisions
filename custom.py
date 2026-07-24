# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.2.2",
#     "marimo>=0.23.14",
#     "numpy==2.5.1",
#     "pandas==3.0.3",
#     "segno>=1.6.6",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="medium",
    layout_file="layouts/custom.slides.json",
    css_file="custom.css",
    auto_download=["html"],
)

with app.setup:
    import calendar
    import html
    from datetime import date
    from itertools import combinations

    import marimo as mo
    import numpy as np
    import pandas as pd
    import altair as alt

    from birthday_room import notebook_live

    def birthday_label(birthday):
        return f"{calendar.month_name[birthday['month']]} {birthday['day']}"

    def birthday_people(birthday):
        labels = list(birthday["names"])
        anonymous = max(int(birthday["count"]) - len(labels), 0)
        if anonymous == 1:
            labels.append("a mystery guest")
        elif anonymous > 1:
            labels.append(f"{anonymous} mystery guests")
        if len(labels) < 2:
            return labels[0] if labels else "mystery guests"
        if len(labels) == 2:
            return f"{labels[0]} and {labels[1]}"
        return f"{', '.join(labels[:-1])}, and {labels[-1]}"

    def birthday_distance(pair):
        first, second = pair
        first_day = date(2000, first["month"], first["day"]).timetuple().tm_yday
        second_day = date(
            2000, second["month"], second["day"]
        ).timetuple().tm_yday
        direct = abs(first_day - second_day)
        return min(direct, 366 - direct)


@app.cell
def _():
    join_url = notebook_live.join_url(mo.app_meta().request)
    qr_data_uri = notebook_live.qr_data_uri(join_url)
    refresh_results = mo.ui.refresh(
        default_interval=notebook_live.REFRESH_INTERVAL,
        label="Live results",
    )
    return join_url, qr_data_uri, refresh_results


@app.cell(hide_code=True)
def title(join_url, qr_data_uri, refresh_results):
    refresh_results
    birthday_snapshot = notebook_live.snapshot()
    participant_count = int(birthday_snapshot["participant_count"])
    mo.vstack(
        [
            mo.md(
                f"""
                # 🎂 The Birthday Paradox

                ### How many people do you need in a room before **two of them share a birthday**?

                **Join the room:** [{join_url}]({join_url})
                """
            ),
            mo.Html(notebook_live.corner_styles(qr_data_uri, participant_count)),
            refresh_results,
        ],
        gap=0,
    )
    return birthday_snapshot, participant_count


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Take a guess 🤔

    - A year has **365 possible birthdays**.
    - So surely you'd need *a lot* of people for a collision...
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    - **50?**
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    - **100?**
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    - **183?** (half of 365)
    """)
    return


@app.cell
def _():
    mo.md(r"""
    ## **23 people!**

    With **23 people**, there is already a **> 50%** chance two share a birthday.

    With **57 people**, it's **> 99%**.
    """)
    return


@app.cell
def _():
    mo.md(r"""
    ## Count the *pairs*, not the people

    You aren't comparing one person to everyone else, **every pair** is a chance for a match.

    $$\text{pairs} = \binom{n}{2} = \frac{n(n-1)}{2}$$

    - 23 people → **253 pairs**
    - That's a *lot* of chances for a collision.
    """)
    return


@app.cell
def math1():
    mo.md(r"""
    ### Step 1: probability of **no** shared birthday

    Add people one at a time; each new person must dodge every previous birthday:

    $$P(\text{no match}) = \frac{365}{365}\cdot\frac{364}{365}\cdots\frac{365-n+1}{365}$$
    """)
    return


@app.cell
def math2():
    mo.md(r"""
    ### Step 2: flip it around

    $$P(\text{match}) = 1 - P(\text{no match}) = 1 - \frac{365!}{(365-n)!\,\cdot\,365^{\,n}}$$

    Run the computation
    """)
    return


@app.function
def birthday_prob(n: int) -> float:
    """Exact probability that at least two of n people share a birthday."""
    if n < 2:
        return 0.0
    p_no_match = 1.0
    for _k in range(n):
        p_no_match *= (365 - _k) / 365
    return 1.0 - p_no_match


@app.function
def near_miss_prob(n: int) -> float:
    """Poisson approximation for birthdays exactly one day apart."""
    return 1.0 - float(np.exp(-n * (n - 1) / 365))


@app.cell
def _():
    n_people = mo.ui.slider(
        2, 80, value=23, label="People in the room", show_value=True
    )
    return (n_people,)


@app.cell
def live(n_people):
    mo.md(f"""
    {n_people}
    ### With **{n_people.value} people** in the room...

    chance of a shared birthday: **{birthday_prob(n_people.value):.1%}**
    """)
    return


@app.cell
def curve(n_people):
    _ns = np.arange(1, 81)
    _curve = pd.DataFrame(
        {"people": _ns, "probability": [birthday_prob(int(_n)) for _n in _ns]}
    )
    _line = (
        alt.Chart(_curve)
        .mark_line(color="#7c3aed", strokeWidth=3)
        .encode(
            x=alt.X("people:Q", title="Number of people"),
            y=alt.Y(
                "probability:Q",
                title="P(shared birthday)",
                axis=alt.Axis(format="%"),
            ),
        )
    )
    _rule = (
        alt.Chart(pd.DataFrame({"people": [n_people.value]}))
        .mark_rule(color="#ef4444", strokeDash=[6, 4])
        .encode(x="people:Q")
    )
    _dot = (
        alt.Chart(
            pd.DataFrame(
                {
                    "people": [n_people.value],
                    "probability": [birthday_prob(n_people.value)],
                }
            )
        )
        .mark_point(size=140, color="#ef4444", filled=True)
        .encode(x="people:Q", y="probability:Q")
    )
    birthday_chart = (_line + _rule + _dot).properties(
        width=640, height=360, title="Probability vs. room size"
    )
    birthday_chart
    return


@app.cell
def near_miss_math():
    mo.md(r"""
    ## What about a near miss? 📅

    Call two birthdays a near miss when they are **one calendar day apart**.
    For any one pair:

    $$P(\text{near miss}) = \frac{2}{365}$$

    With $\binom{n}{2}$ pairs, the expected number of near misses is

    $$\lambda = \binom{n}{2}\frac{2}{365} = \frac{n(n-1)}{365}$$

    Treating these rare pair-events as approximately Poisson:

    $$P(\text{at least one near miss}) \approx 1-e^{-\lambda}
      = 1-e^{-n(n-1)/365}$$
    """)
    return


@app.cell
def near_miss_chart(birthday_snapshot):
    _ns = np.arange(2, 61)
    _comparison = pd.DataFrame(
        {
            "people": np.tile(_ns, 2),
            "probability": [
                *[birthday_prob(int(_n)) for _n in _ns],
                *[near_miss_prob(int(_n)) for _n in _ns],
            ],
            "event": [
                *(["Same birthday"] * len(_ns)),
                *(["One day apart"] * len(_ns)),
            ],
        }
    )
    _chart = (
        alt.Chart(_comparison)
        .mark_line(strokeWidth=3)
        .encode(
            x=alt.X("people:Q", title="Number of people"),
            y=alt.Y(
                "probability:Q",
                title="Probability",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color(
                "event:N",
                title="",
                scale=alt.Scale(
                    domain=["Same birthday", "One day apart"],
                    range=["#7c3aed", "#059669"],
                ),
            ),
        )
        .properties(width=640, height=280)
    )
    mo.vstack(
        [
            mo.md(
                f"""
                ## Near misses arrive sooner

                **17 people → {near_miss_prob(17):.1%}** chance of a near miss.
                By 23 people, it is already **{near_miss_prob(23):.1%}**.

                **This room, live:** {notebook_live.near_miss_summary(birthday_snapshot)}
                """
            ),
            _chart,
        ],
        gap=0,
    )
    return


@app.function
def simulate_birthday(n: int, trials: int = 5000, seed: int = 0) -> float:
    """Fraction of random rooms of n people that contain a shared birthday."""
    _rng = np.random.default_rng(seed)
    _bdays = _rng.integers(0, 365, size=(trials, n))
    _bdays.sort(axis=1)
    _has_match = (np.diff(_bdays, axis=1) == 0).any(axis=1)
    return float(_has_match.mean())


@app.cell
def _():
    slider = mo.ui.slider(1, 10000, value=5000)
    return


@app.cell
def sim_chart_cell():
    _ns2 = np.arange(2, 81, 2)
    trials = 2000
    _sim = pd.DataFrame(
        {
            "people": _ns2,
            "theory": [birthday_prob(int(_n)) for _n in _ns2],
            "simulation": [
                simulate_birthday(int(_n), trials=trials) for _n in _ns2
            ],
        }
    )
    _melt = _sim.melt("people", var_name="source", value_name="probability")
    sim_chart = (
        alt.Chart(_melt)
        .mark_line(point=True)
        .encode(
            x=alt.X("people:Q", title="Number of people"),
            y=alt.Y(
                "probability:Q",
                title="P(shared birthday)",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color("source:N", title=""),
        )
        .properties(
            width=640, height=360, title=f"Theory vs. {trials}-room simulation"
        )
    )

    sim_chart
    return


@app.cell(hide_code=True)
def room_results(birthday_snapshot, participant_count):
    _birthdays = list(birthday_snapshot["birthdays"])
    result_counts = {
        (int(_item["month"]), int(_item["day"])): int(_item["count"])
        for _item in _birthdays
    }
    result_matches = sorted(
        (_item for _item in _birthdays if int(_item["count"]) > 1),
        key=lambda _item: (
            -int(_item["count"]),
            int(_item["month"]),
            int(_item["day"]),
        ),
    )
    result_near_miss = min(
        combinations(_birthdays, 2),
        key=birthday_distance,
        default=None,
    )

    _distinct = len(result_counts)
    _possible_pairs = participant_count * (participant_count - 1) // 2
    _matching_pairs = sum(
        _count * (_count - 1) // 2 for _count in result_counts.values()
    )
    _birthday_word = "birthday" if participant_count == 1 else "birthdays"
    _day_word = "day" if _distinct == 1 else "days"
    mo.md(
        f"""
        ## The room, so far

        # {participant_count} {_birthday_word} checked in

        - **{_distinct}** distinct calendar {_day_word}
        - **{_possible_pairs}** possible pairs
        - **{_matching_pairs}** actual matching pairs
        """
    )
    return result_counts, result_matches, result_near_miss


@app.cell(hide_code=True)
def exact_results(result_matches):
    if result_matches:
        _match_lines = "\n".join(
            (
                f"- **{html.escape(birthday_label(_match))}:** "
                f"{html.escape(birthday_people(_match))} "
                f'({_match["count"]} people)'
            )
            for _match in result_matches[:6]
        )
        _content = f"""
        ## Exact matches

        # The room has a birthday collision.

        {_match_lines}
        """
    else:
        _content = """
        ## Exact matches

        # No exact matches. Yet.

        New votes will appear here automatically.
        """
    mo.md(_content)
    return


@app.cell(hide_code=True)
def closest_results(result_near_miss):
    if result_near_miss is not None:
        _first, _second = result_near_miss
        _distance = birthday_distance(result_near_miss)
        _unit = "day" if _distance == 1 else "days"
        _content = f"""
        ## The closest near miss

        # {html.escape(birthday_label(_first))}
        ### {html.escape(birthday_people(_first))}

        **{_distance} {_unit} apart**

        # {html.escape(birthday_label(_second))}
        ### {html.escape(birthday_people(_second))}
        """
    else:
        _content = """
        ## Near misses

        # We need at least two distinct dates.

        One birthday is a fact. Two birthdays are a dataset.
        """
    mo.md(_content)
    return


@app.cell(hide_code=True)
def calendar_results(result_counts):
    _months = []
    for _month in range(1, 13):
        _days = []
        for _day in range(1, calendar.monthrange(2000, _month)[1] + 1):
            _count = int(result_counts.get((_month, _day), 0))
            _class_name = "match" if _count > 1 else "one" if _count == 1 else ""
            _title = (
                f"{calendar.month_name[_month]} {_day}: {_count}"
                if _count
                else f"{calendar.month_name[_month]} {_day}"
            )
            _days.append(
                f'<span class="calendar-day {_class_name}" '
                f'title="{html.escape(_title)}"></span>'
            )
        _months.append(
            '<div class="calendar-month">'
            f"<strong>{calendar.month_name[_month]}</strong>"
            f'<div class="calendar-days">{"".join(_days)}</div>'
            "</div>"
        )
    mo.vstack(
        [
            mo.md("## The room on a calendar"),
            mo.Html(f'<div class="calendar-grid">{"".join(_months)}</div>'),
        ],
        gap=0,
    )
    return


@app.cell
def takeaways(birthday_snapshot, participant_count):
    mo.md(f"""
    ## Takeaways 🎉

    - **23 people → > 50%**, **57 → > 99%** — collisions are cheap once you count *pairs*.
    - The "paradox" is really just **n(n − 1)/2 pairs** growing fast.
    - The same math powers **hash collisions**, **cryptography**, and **load balancing**.

    ### This room, live

    **{notebook_live.attendance(participant_count)}.**
    {notebook_live.collision_summary(birthday_snapshot)}
    """)
    return


if __name__ == "__main__":
    app.run()
