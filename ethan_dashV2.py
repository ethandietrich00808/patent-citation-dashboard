import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# ── Tennessee color palette (matches Oct9P2 / LornasDashFinalfixed) ──────────
orange     = "#FF8200"
gray       = "#4B4B4B"
light_gray = "#d3d3d3"
dark_gray  = "#2f2f2f"

# ─────────────────────────────────────────────────────────────────────────────
# Info box helper (matches Oct9P2 / LornasDashFinalfixed style)
# ─────────────────────────────────────────────────────────────────────────────

def info_box(button_id, collapse_id, text):
    return html.Div([
        dbc.Button("ℹ️ Info", id=button_id, color="secondary", size="sm",
                   style={"marginTop": "10px"}),
        dbc.Collapse(
            dbc.Card(dbc.CardBody(
                text,
                style={"color": "black", "fontSize": "14px", "whiteSpace": "pre-line"}
            )),
            id=collapse_id,
            is_open=True
        )
    ])

# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_data():
    """Load the consolidated companies data"""
    return pd.read_csv('top_100_cited_companies_consolidated.csv')

def get_company_list(df):
    """Get list of companies for the dropdown"""
    companies = df.groupby(['assignee_id', 'raw_assignee_organization']).size().reset_index()
    companies['display_name'] = (
        companies['raw_assignee_organization'] + ' (' + companies['assignee_id'].str[:8] + '...)'
    )
    return companies[['assignee_id', 'display_name']].sort_values('display_name')

def get_patents_in_year(df_companies, selected_year):
    """Get number of patents assigned in the selected year for each company"""
    patents_info = []
    for assignee_id in df_companies['assignee_id'].unique():
        company_data = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = company_data['raw_assignee_organization'].iloc[0]
        year_data = company_data[company_data['cited_year'] == selected_year]
        patents_info.append({
            'company': company_name,
            'patents': year_data['patents_assigned'].sum() if not year_data.empty else 0
        })
    return patents_info

# ─────────────────────────────────────────────────────────────────────────────
# Chart builders
# ─────────────────────────────────────────────────────────────────────────────

CHART_LAYOUT = dict(
    plot_bgcolor=light_gray,
    paper_bgcolor=gray,
    font=dict(color='white', family='Gotham, sans-serif'),
    legend=dict(bgcolor=dark_gray, font=dict(color='white')),
    hovermode='x unified',
)

LINE_COLORS = [orange, '#00BFFF', '#7CFC00', '#FF69B4', '#FFD700',
               '#DA70D6', '#40E0D0', '#FF6347', '#ADFF2F', '#87CEEB']


def styled_lines(fig, df_companies, x_col, y_col, name_col='raw_assignee_organization',
                 hover_label='Value'):
    for i, assignee_id in enumerate(df_companies['assignee_id'].unique()):
        cd = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = cd[name_col].iloc[0]
        agg = cd.groupby(x_col)[y_col].sum().reset_index().sort_values(x_col)
        color = LINE_COLORS[i % len(LINE_COLORS)]
        fig.add_trace(go.Scatter(
            x=agg[x_col],
            y=agg[y_col],
            mode='lines+markers',
            name=company_name,
            line=dict(width=3, color=color),
            marker=dict(color=color),
            hovertemplate=(
                f"<b>{company_name}</b><br>"
                f"<b>Year:</b> %{{x}}<br>"
                f"<b>{hover_label}:</b> %{{y}}<br>"
                "<extra></extra>"
            )
        ))
    return fig


def create_citations_to_year_chart(df_companies, selected_year):
    fig = go.Figure()
    for i, assignee_id in enumerate(df_companies['assignee_id'].unique()):
        cd = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = cd['raw_assignee_organization'].iloc[0]
        year_data = cd[cd['cited_year'] == selected_year]
        if year_data.empty:
            continue
        year_cols = [str(y) for y in range(selected_year + 1, 2026)]
        rows = []
        for yc in year_cols:
            if yc in year_data.columns:
                rows.append({'year': int(yc), 'citations': year_data[yc].sum()})
        if not rows:
            continue
        cdf = pd.DataFrame(rows)
        color = LINE_COLORS[i % len(LINE_COLORS)]
        fig.add_trace(go.Scatter(
            x=cdf['year'], y=cdf['citations'],
            mode='lines+markers', name=company_name,
            line=dict(width=3, color=color),
            marker=dict(color=color),
            hovertemplate=(
                f"<b>{company_name}</b><br>"
                "<b>Year:</b> %{x}<br>"
                "<b>Citations:</b> %{y}<br>"
                "<extra></extra>"
            )
        ))
    fig.update_layout(
        title=f"Citations to Patents from {selected_year} by Subsequent Year",
        xaxis_title="Year Citations Were Received",
        yaxis_title="Number of Citations",
        **CHART_LAYOUT
    )
    return fig


def create_patents_timeline(df_companies):
    fig = go.Figure()
    fig = styled_lines(fig, df_companies, 'cited_year', 'patents_assigned',
                       hover_label='Patents')
    fig.update_layout(
        title="Patents Assigned by Year — Company Comparison",
        xaxis_title="Year",
        yaxis_title="Number of Patents",
        **CHART_LAYOUT
    )
    return fig


def create_citations_timeline(df_companies):
    fig = go.Figure()
    fig = styled_lines(fig, df_companies, 'cited_year', 'total_citations',
                       hover_label='Citations')
    fig.update_layout(
        title="Total Citations Received by Year — Company Comparison",
        xaxis_title="Year",
        yaxis_title="Total Citations",
        **CHART_LAYOUT
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────

try:
    df = load_data()
    companies = get_company_list(df)
    available_years = sorted(df['cited_year'].unique())
except FileNotFoundError:
    print("Could not find 'top_100_cited_companies_consolidated.csv' file")
    df = pd.DataFrame()
    companies = pd.DataFrame(columns=['assignee_id', 'display_name'])
    available_years = []

# ─────────────────────────────────────────────────────────────────────────────
# App layout
# ─────────────────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Montserrat&display=swap"
    ]
)

LABEL_STYLE  = {'fontWeight': 'bold', 'color': 'white', 'marginBottom': '6px',
                'fontFamily': 'Gotham, sans-serif'}
SECTION_STYLE = {'margin': '20px'}

DROPDOWN_STYLE = {
    'backgroundColor': dark_gray,
    'color': 'black',  # dropdown menu items appear on white background
}

app.layout = html.Div([

    # ── Header ───────────────────────────────────────────────────────────────
    html.H1(
        "Patent Citation Dashboard",
        style={
            'textAlign': 'center',
            'color': orange,
            'fontFamily': 'Gotham, sans-serif',
            'padding': '20px 0 10px',
            'letterSpacing': '1px',
        }
    ),

    # ── Controls ─────────────────────────────────────────────────────────────
    html.Div([
        html.Label("Select Companies:", style=LABEL_STYLE),
        dcc.Dropdown(
            id="company-dropdown",
            options=[{"label": r['display_name'], "value": r['assignee_id']}
                     for _, r in companies.iterrows()],
            value=[companies['assignee_id'].iloc[0]] if len(companies) > 0 else [],
            multi=True,
            style=DROPDOWN_STYLE
        ),
    ], style=SECTION_STYLE),

    html.Div([
        html.Label("Select Patent Year:", style=LABEL_STYLE),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": str(y), "value": y} for y in available_years],
            value=available_years[0] if available_years else None,
            style=DROPDOWN_STYLE
        ),
    ], style=SECTION_STYLE),

    # ── Summary ──────────────────────────────────────────────────────────────
    html.Div(id="summary-text", style={**SECTION_STYLE, 'color': 'white'}),

    # ── Tabs ─────────────────────────────────────────────────────────────────
    dcc.Tabs(
        id="tabs",
        value="citations-to-year",
        children=[
            dcc.Tab(label="Citations to Selected Year", value="citations-to-year",
                    style={'color': orange, 'backgroundColor': dark_gray, 'fontFamily': 'Gotham, sans-serif'},
                    selected_style={'color': 'black', 'backgroundColor': orange, 'fontFamily': 'Gotham, sans-serif', 'fontWeight': 'bold'}),
            dcc.Tab(label="Patents Timeline", value="patents-timeline",
                    style={'color': orange, 'backgroundColor': dark_gray, 'fontFamily': 'Gotham, sans-serif'},
                    selected_style={'color': 'black', 'backgroundColor': orange, 'fontFamily': 'Gotham, sans-serif', 'fontWeight': 'bold'}),
            dcc.Tab(label="Citations Timeline", value="citations-timeline",
                    style={'color': orange, 'backgroundColor': dark_gray, 'fontFamily': 'Gotham, sans-serif'},
                    selected_style={'color': 'black', 'backgroundColor': orange, 'fontFamily': 'Gotham, sans-serif', 'fontWeight': 'bold'}),
        ],
        style={'fontFamily': 'Gotham, sans-serif'},
        colors={
            "border":     gray,
            "primary":    orange,
            "background": dark_gray,
        }
    ),

    # ── Chart area ───────────────────────────────────────────────────────────
    html.Div(id="tab-content", style=SECTION_STYLE),

], style={
    'backgroundColor': gray,
    'minHeight': '100vh',
    'padding': '10px 30px',
    'fontFamily': 'Gotham, sans-serif',
})

# ─────────────────────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    [Output("summary-text", "children"),
     Output("tab-content",  "children")],
    [Input("company-dropdown", "value"),
     Input("year-dropdown",    "value"),
     Input("tabs",             "value")]
)
def update_dashboard(selected_companies, selected_year, active_tab):
    if not selected_companies or not selected_year:
        return (
            html.P("Please select companies and a year to analyze.",
                   style={'color': light_gray}),
            ""
        )

    companies_data = df[df['assignee_id'].isin(selected_companies)].copy()
    patents_in_year = get_patents_in_year(companies_data, selected_year)

    summary_items = [
        html.Li(
            f"{p['company']}: {p['patents']:,.0f} patents assigned in {selected_year}",
            style={'color': 'white', 'fontSize': '16px', 'margin': '5px 0'}
        )
        for p in patents_in_year
    ]

    summary_text = html.Div([
        html.H3(
            f"Patents Assigned in {selected_year}",
            style={'color': orange, 'marginBottom': '10px',
                   'fontFamily': 'Gotham, sans-serif'}
        ),
        html.Ul(summary_items),
        html.P(
            f"Below shows how many times these {selected_year} patents were cited "
            "in each subsequent year.",
            style={'color': light_gray, 'fontStyle': 'italic', 'marginTop': '10px'}
        )
    ])

    if active_tab == "citations-to-year":
        fig = create_citations_to_year_chart(companies_data, selected_year)
        info = info_box(
            "citations_year_info_btn", "citations_year_info_collapse",
            f"""Citations to Selected Year
This chart tracks how many times patents granted in {selected_year} were subsequently cited in each later year.

- Each line represents one selected company.
- A rising line indicates growing influence of that cohort of patents over time.
- A peak followed by decline is typical as a patent generation ages out of active citation.
- Use the company selector above to add or remove companies for comparison.

Note: Only years after {selected_year} are shown, as patents can only be cited after they are granted."""
        )
        content = html.Div([dcc.Graph(figure=fig), info])

    elif active_tab == "patents-timeline":
        fig = create_patents_timeline(companies_data)
        info = info_box(
            "patents_timeline_info_btn", "patents_timeline_info_collapse",
            """Patents Assigned by Year
This chart shows the total number of patents assigned to each selected company per year.

- Each line represents one company's yearly patent output.
- Spikes may reflect strategic filing surges, acquisitions, or R&D investment cycles.
- Declining counts in recent years may reflect data lag — recently filed patents take time to be processed and appear in the dataset.
- Use this view to compare the patent volume trajectory of companies over time."""
        )
        content = html.Div([dcc.Graph(figure=fig), info])

    elif active_tab == "citations-timeline":
        fig = create_citations_timeline(companies_data)
        info = info_box(
            "citations_timeline_info_btn", "citations_timeline_info_collapse",
            """Total Citations Received by Year
This chart shows the total number of citations received by each company's patents, aggregated by the year the original patent was granted.

- Each line represents one company's cumulative citation impact across its patent cohorts.
- Higher citation counts generally indicate greater influence on subsequent innovations.
- Companies with older, highly-cited portfolios may show peaks in earlier years.
- This view is useful for comparing the overall research impact and knowledge spillover of each company."""
        )
        content = html.Div([dcc.Graph(figure=fig), info])

    else:
        return summary_text, ""
    return summary_text, content


# ─────────────────────────────────────────────────────────────────────────────
# Info button toggle callbacks
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("citations_year_info_collapse", "is_open"),
    Input("citations_year_info_btn", "n_clicks"),
    State("citations_year_info_collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_citations_year_info(n, is_open):
    return not is_open

@app.callback(
    Output("patents_timeline_info_collapse", "is_open"),
    Input("patents_timeline_info_btn", "n_clicks"),
    State("patents_timeline_info_collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_patents_timeline_info(n, is_open):
    return not is_open

@app.callback(
    Output("citations_timeline_info_collapse", "is_open"),
    Input("citations_timeline_info_btn", "n_clicks"),
    State("citations_timeline_info_collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_citations_timeline_info(n, is_open):
    return not is_open


if __name__ == "__main__":
    app.run(debug=True)