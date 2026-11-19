from datetime import UTC
from io import BytesIO

import pandas as pd
import plotly.express as px

from trackabee.models import Tracker


class ChartNoPointsError(Exception):
    pass


def generate_chart(tracker: Tracker) -> BytesIO:
    points = tracker.points
    if not points:
        raise ChartNoPointsError()

    first_timestamp = min(point.timestamp.astimezone(UTC) for point in points)

    data = {
        "Date": [point.timestamp for point in points],
        tracker.unit: [point.value for point in points],
    }
    df = pd.DataFrame(data)

    fig = px.line(
        df,
        x="Date",
        y=tracker.unit,
        title=tracker.name,
        template="plotly_dark",
        width=1200,
        height=600,
    )

    if tracker.goal and tracker.ends_at:
        goal_start = 0 if tracker.trend == "up" else tracker.goal
        goal_end = tracker.goal if tracker.trend == "up" else 0

        fig.add_scatter(
            x=[first_timestamp, tracker.ends_at],
            y=[goal_start, goal_end],
            mode="lines",
            line={"color": "orange", "dash": "dash"},
            showlegend=False,
        )

        # Keep the scatter behind the main line
        fig.data = (fig.data[-1], *fig.data[:-1])

    fig.update_xaxes(
        range=[first_timestamp, tracker.ends_at] if tracker.ends_at else None,
        tickformat="%b %d",
        tickmode="linear",
        tickangle=-45,
        rangemode="tozero",
    )

    if tracker.goal:
        fig.update_yaxes(range=[0, tracker.goal])

    image = BytesIO(fig.to_image(format="png"))
    image.seek(0)
    return image
