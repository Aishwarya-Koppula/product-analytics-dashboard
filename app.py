import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64
import io

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Product Analytics Dashboard"

# Load default sample data
def load_default_data():
    df = pd.read_csv('sample_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

df_default = load_default_data()

# Helper function to calculate metrics
def calculate_metrics(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    metrics = {
        'mau': latest['monthly_active_users'],
        'mau_change': ((latest['monthly_active_users'] - previous['monthly_active_users']) / previous['monthly_active_users'] * 100),
        'revenue': latest['monthly_revenue'],
        'revenue_change': ((latest['monthly_revenue'] - previous['monthly_revenue']) / previous['monthly_revenue'] * 100),
        'churn_rate': (latest['churned_users'] / previous['monthly_active_users'] * 100),
        'conversion': latest['conversion_rate']
    }
    return metrics

# Simple forecasting function
def forecast_metrics(df, months_ahead=3, scenario_multiplier=1.0):
    # Calculate growth rates
    df_sorted = df.sort_values('date')
    
    # Simple linear regression for trend
    recent_data = df_sorted.tail(6)
    growth_rate = recent_data['monthly_active_users'].pct_change().mean()
    revenue_growth = recent_data['monthly_revenue'].pct_change().mean()
    
    # Apply scenario multiplier
    adjusted_growth = growth_rate * scenario_multiplier
    adjusted_revenue_growth = revenue_growth * scenario_multiplier
    
    # Generate forecast
    last_date = df_sorted['date'].max()
    last_mau = df_sorted['monthly_active_users'].iloc[-1]
    last_revenue = df_sorted['monthly_revenue'].iloc[-1]
    
    forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, months_ahead+1)]
    forecast_mau = [last_mau * (1 + adjusted_growth)**i for i in range(1, months_ahead+1)]
    forecast_revenue = [last_revenue * (1 + adjusted_revenue_growth)**i for i in range(1, months_ahead+1)]
    
    return pd.DataFrame({
        'date': forecast_dates,
        'monthly_active_users': forecast_mau,
        'monthly_revenue': forecast_revenue,
        'type': 'Forecast'
    })

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Product Analytics Dashboard", className="text-center mb-4 mt-4"),
            html.P("Upload your product metrics or use the sample data to explore analytics and scenario modeling.",
                   className="text-center text-muted mb-4")
        ])
    ]),
    
    # File Upload Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Upload Your Data", className="card-title"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select CSV File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-2")
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # KPI Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Monthly Active Users", className="text-muted"),
                    html.H3(id='kpi-mau', className="mb-0"),
                    html.Small(id='kpi-mau-change', className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Monthly Revenue", className="text-muted"),
                    html.H3(id='kpi-revenue', className="mb-0"),
                    html.Small(id='kpi-revenue-change', className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Churn Rate", className="text-muted"),
                    html.H3(id='kpi-churn', className="mb-0"),
                    html.Small("Current Month", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Conversion Rate", className="text-muted"),
                    html.H3(id='kpi-conversion', className="mb-0"),
                    html.Small("Current Month", className="text-muted")
                ])
            ])
        ], width=3),
    ], className="mb-4"),
    
    # Main Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("User Growth Trend", className="card-title"),
                    dcc.Graph(id='growth-chart')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Revenue Trend", className="card-title"),
                    dcc.Graph(id='revenue-chart')
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Scenario Modeling Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Scenario Modeling", className="card-title mb-4"),
                    html.P("Model different scenarios by adjusting key parameters:"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Growth Rate Multiplier"),
                            dcc.Slider(
                                id='growth-slider',
                                min=0.5,
                                max=2.0,
                                step=0.1,
                                value=1.0,
                                marks={0.5: '0.5x', 1.0: '1x', 1.5: '1.5x', 2.0: '2x'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Forecast Months"),
                            dcc.Slider(
                                id='months-slider',
                                min=1,
                                max=12,
                                step=1,
                                value=6,
                                marks={1: '1', 3: '3', 6: '6', 9: '9', 12: '12'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=6),
                    ], className="mb-4"),
                    
                    dcc.Graph(id='forecast-chart')
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Cohort/Engagement Analysis
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Engagement Metrics", className="card-title"),
                    dcc.Graph(id='engagement-chart')
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Data store
    dcc.Store(id='stored-data', data=df_default.to_json(date_format='iso', orient='split'))
    
], fluid=True)

# Callbacks
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_data(contents, filename):
    if contents is None:
        return df_default.to_json(date_format='iso', orient='split'), ""
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        df['date'] = pd.to_datetime(df['date'])
        
        return df.to_json(date_format='iso', orient='split'), dbc.Alert(f"✓ Loaded {filename}", color="success", dismissable=True)
    except Exception as e:
        return df_default.to_json(date_format='iso', orient='split'), dbc.Alert(f"Error loading file: {str(e)}", color="danger", dismissable=True)

@app.callback(
    [Output('kpi-mau', 'children'),
     Output('kpi-mau-change', 'children'),
     Output('kpi-revenue', 'children'),
     Output('kpi-revenue-change', 'children'),
     Output('kpi-churn', 'children'),
     Output('kpi-conversion', 'children')],
    Input('stored-data', 'data')
)
def update_kpis(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    metrics = calculate_metrics(df)
    
    return (
        f"{metrics['mau']:,.0f}",
        f"↑ {metrics['mau_change']:.1f}% from last month",
        f"${metrics['revenue']:,.0f}",
        f"↑ {metrics['revenue_change']:.1f}% from last month",
        f"{metrics['churn_rate']:.1f}%",
        f"{metrics['conversion']:.1f}%"
    )

@app.callback(
    Output('growth-chart', 'figure'),
    Input('stored-data', 'data')
)
def update_growth_chart(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    
    fig = px.line(df, x='date', y='monthly_active_users',
                  labels={'monthly_active_users': 'Users', 'date': 'Date'},
                  title='')
    fig.update_traces(line_color='#0066CC', line_width=3)
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        hovermode='x unified',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    
    return fig

@app.callback(
    Output('revenue-chart', 'figure'),
    Input('stored-data', 'data')
)
def update_revenue_chart(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    
    fig = px.area(df, x='date', y='monthly_revenue',
                  labels={'monthly_revenue': 'Revenue ($)', 'date': 'Date'},
                  title='')
    fig.update_traces(line_color='#00AA66', fillcolor='rgba(0,170,102,0.2)')
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        hovermode='x unified',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    
    return fig

@app.callback(
    Output('forecast-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('growth-slider', 'value'),
     Input('months-slider', 'value')]
)
def update_forecast(jsonified_data, growth_multiplier, months):
    df = pd.read_json(jsonified_data, orient='split')
    
    # Get forecast
    df_forecast = forecast_metrics(df, months, growth_multiplier)
    
    # Combine historical and forecast
    df_historical = df[['date', 'monthly_active_users', 'monthly_revenue']].copy()
    df_historical['type'] = 'Historical'
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=df_historical['date'],
        y=df_historical['monthly_active_users'],
        name='Historical MAU',
        line=dict(color='#0066CC', width=3),
        mode='lines'
    ))
    
    # Forecast data
    fig.add_trace(go.Scatter(
        x=df_forecast['date'],
        y=df_forecast['monthly_active_users'],
        name='Forecast MAU',
        line=dict(color='#FF6B35', width=3, dash='dash'),
        mode='lines'
    ))
    
    fig.update_layout(
        title=f'Forecast with {growth_multiplier}x Growth Rate',
        xaxis_title='Date',
        yaxis_title='Monthly Active Users',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    
    return fig

@app.callback(
    Output('engagement-chart', 'figure'),
    Input('stored-data', 'data')
)
def update_engagement_chart(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['new_signups'],
        name='New Signups',
        marker_color='#00AA66'
    ))
    
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['churned_users'],
        name='Churned Users',
        marker_color='#FF6B35'
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title='Date',
        yaxis_title='Users',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
