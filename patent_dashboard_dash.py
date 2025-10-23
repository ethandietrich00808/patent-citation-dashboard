import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

def load_data():
    """Load the consolidated companies data"""
    return pd.read_csv('top_100_cited_companies_consolidated.csv')

def get_company_list(df):
    """Get list of companies for the dropdown"""
    companies = df.groupby(['assignee_id', 'raw_assignee_organization']).size().reset_index()
    companies['display_name'] = companies['raw_assignee_organization'] + ' (' + companies['assignee_id'].str[:8] + '...)'
    return companies[['assignee_id', 'display_name']].sort_values('display_name')

def get_company_data(df, assignee_id):
    """Get data for a specific company"""
    return df[df['assignee_id'] == assignee_id].copy()

def create_citations_to_year_chart(df_companies, selected_year):
    """Create chart showing citations made to patents from selected year for each subsequent year"""
    fig = go.Figure()
    
    for assignee_id in df_companies['assignee_id'].unique():
        company_data = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = company_data['raw_assignee_organization'].iloc[0]
        
        # Get data for the selected year
        year_data = company_data[company_data['cited_year'] == selected_year]
        
        if not year_data.empty:
            # Get year columns (years after the selected year)
            year_cols = [str(year) for year in range(selected_year + 1, 2026)]
            
            # Calculate citations received in each subsequent year
            citations_by_year = []
            for year_col in year_cols:
                if year_col in year_data.columns:
                    citations_in_year = year_data[year_col].sum()
                    # Include all years, even those with 0 citations, for better visualization
                    citations_by_year.append({
                        'year': int(year_col),
                        'citations': citations_in_year
                    })
            
            if citations_by_year:
                citations_df = pd.DataFrame(citations_by_year)
                
                fig.add_trace(go.Scatter(
                    x=citations_df['year'],
                    y=citations_df['citations'],
                    mode='lines+markers',
                    name=company_name,
                    line=dict(width=3),
                    hovertemplate=f"<b>{company_name}</b><br>" +
                                 f"<b>Year:</b> %{{x}}<br>" +
                                 f"<b>Citations:</b> %{{y}}<br>" +
                                 "<extra></extra>"
                ))
    
    fig.update_layout(
        title=f"Citations to Patents from {selected_year} by Subsequent Year",
        xaxis_title="Year Citations Were Received",
        yaxis_title="Number of Citations",
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )
    
    return fig

def get_patents_in_year(df_companies, selected_year):
    """Get number of patents assigned in the selected year for each company"""
    patents_info = []
    
    for assignee_id in df_companies['assignee_id'].unique():
        company_data = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = company_data['raw_assignee_organization'].iloc[0]
        
        # Get data for the selected year
        year_data = company_data[company_data['cited_year'] == selected_year]
        
        if not year_data.empty:
            patents_assigned = year_data['patents_assigned'].sum()
            patents_info.append({
                'company': company_name,
                'patents': patents_assigned
            })
        else:
            patents_info.append({
                'company': company_name,
                'patents': 0
            })
    
    return patents_info

def create_patents_timeline(df_companies):
    """Create timeline showing patents assigned per year for multiple companies"""
    fig = go.Figure()
    
    for assignee_id in df_companies['assignee_id'].unique():
        company_data = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = company_data['raw_assignee_organization'].iloc[0]
        
        patents_by_year = company_data.groupby('cited_year')['patents_assigned'].sum().reset_index()
        patents_by_year = patents_by_year.sort_values('cited_year')
        
        fig.add_trace(go.Scatter(
            x=patents_by_year['cited_year'],
            y=patents_by_year['patents_assigned'],
            mode='lines+markers',
            name=company_name,
            line=dict(width=3),
            hovertemplate=f"<b>{company_name}</b><br>" +
                         f"<b>Year:</b> %{{x}}<br>" +
                         f"<b>Patents:</b> %{{y}}<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Patents Assigned by Year - Company Comparison",
        xaxis_title="Year",
        yaxis_title="Number of Patents",
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )
    
    return fig

def create_citations_timeline(df_companies):
    """Create timeline showing total citations received per year for multiple companies"""
    fig = go.Figure()
    
    for assignee_id in df_companies['assignee_id'].unique():
        company_data = df_companies[df_companies['assignee_id'] == assignee_id]
        company_name = company_data['raw_assignee_organization'].iloc[0]
        
        citations_by_year = company_data.groupby('cited_year')['total_citations'].sum().reset_index()
        citations_by_year = citations_by_year.sort_values('cited_year')
        
        fig.add_trace(go.Scatter(
            x=citations_by_year['cited_year'],
            y=citations_by_year['total_citations'],
            mode='lines+markers',
            name=company_name,
            line=dict(width=3),
            hovertemplate=f"<b>{company_name}</b><br>" +
                         f"<b>Year:</b> %{{x}}<br>" +
                         f"<b>Citations:</b> %{{y}}<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Total Citations Received by Year - Company Comparison",
        xaxis_title="Year",
        yaxis_title="Total Citations",
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black')
    )
    
    return fig

# Load data
try:
    df = load_data()
    companies = get_company_list(df)
    available_years = sorted(df['cited_year'].unique())
except FileNotFoundError:
    print("Could not find 'top_100_cited_companies_consolidated.csv' file")
    df = pd.DataFrame()
    companies = pd.DataFrame()
    available_years = []

# Create Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Patent Citation Dashboard", style={'textAlign': 'center', 'color': 'black'}),
    
    html.Div([
        html.Label("Select Companies:", style={'fontWeight': 'bold', 'color': 'black'}),
        dcc.Dropdown(
            id="company-dropdown",
            options=[{"label": row['display_name'], "value": row['assignee_id']} for _, row in companies.iterrows()],
            value=[companies['assignee_id'].iloc[0]] if len(companies) > 0 else [],
            multi=True,
            style={'backgroundColor': 'white', 'color': 'black'}
        ),
    ], style={'margin': '20px'}),
    
    html.Div([
        html.Label("Select Patent Year:", style={'fontWeight': 'bold', 'color': 'black'}),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": str(year), "value": year} for year in available_years],
            value=available_years[0] if len(available_years) > 0 else None,
            style={'backgroundColor': 'white', 'color': 'black'}
        ),
    ], style={'margin': '20px'}),
    
    html.Div(id="summary-text", style={'margin': '20px', 'color': 'black'}),
    
    dcc.Tabs(id="tabs", value="citations-to-year", children=[
        dcc.Tab(label="Citations to Selected Year", value="citations-to-year", style={'color': 'black'}),
        dcc.Tab(label="Patents Timeline", value="patents-timeline", style={'color': 'black'}),
        dcc.Tab(label="Citations Timeline", value="citations-timeline", style={'color': 'black'}),
    ], style={'backgroundColor': 'white'}),
    
    html.Div(id="tab-content", style={'margin': '20px'})
], style={'backgroundColor': 'white', 'minHeight': '100vh'})

@app.callback(
    [Output("summary-text", "children"),
     Output("tab-content", "children")],
    [Input("company-dropdown", "value"),
     Input("year-dropdown", "value"),
     Input("tabs", "value")]
)
def update_dashboard(selected_companies, selected_year, active_tab):
    if not selected_companies or not selected_year:
        return "Please select companies and a year to analyze.", ""
    
    # Get company data for all selected companies
    companies_data = df[df['assignee_id'].isin(selected_companies)].copy()
    
    # Get patents assigned in the selected year
    patents_in_year = get_patents_in_year(companies_data, selected_year)
    
    # Create summary text showing patents assigned in selected year
    summary_items = []
    for patent_info in patents_in_year:
        summary_items.append(
            html.Li(
                f"{patent_info['company']}: {patent_info['patents']:,.0f} patents assigned in {selected_year}",
                style={'color': 'black', 'fontSize': '16px', 'margin': '5px 0'}
            )
        )
    
    summary_text = html.Div([
        html.H3(f"Patents Assigned in {selected_year}", style={'color': 'black', 'marginBottom': '10px'}),
        html.Ul(summary_items),
        html.P(f"Below shows how many times these {selected_year} patents were cited in each subsequent year.", 
               style={'color': 'black', 'fontStyle': 'italic', 'marginTop': '10px'})
    ])
    
    # Create content based on active tab
    if active_tab == "citations-to-year":
        fig = create_citations_to_year_chart(companies_data, selected_year)
        content = dcc.Graph(figure=fig)
    elif active_tab == "patents-timeline":
        fig = create_patents_timeline(companies_data)
        content = dcc.Graph(figure=fig)
    elif active_tab == "citations-timeline":
        fig = create_citations_timeline(companies_data)
        content = dcc.Graph(figure=fig)
    else:
        content = ""
    
    return summary_text, content

if __name__ == "__main__":
    app.run_server(debug=True)
