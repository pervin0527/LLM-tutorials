import plotly.graph_objects as go

def vision_radar(data):
    vision_data = data['visionResult']
    company_keywords = vision_data['company']['keyWord']
    compute_keywords = vision_data['compute']['keyWord']

    # Combine all unique keywords
    all_keywords = sorted(set(company_keywords.keys()).union(set(compute_keywords.keys())))

    # Ensure all keywords are present with default value 0 if missing
    company_scores = [company_keywords.get(key, 0) for key in all_keywords]
    compute_scores = [compute_keywords.get(key, 0) for key in all_keywords]

    # Close the radar chart by repeating the first score
    company_scores += company_scores[:1]
    compute_scores += compute_scores[:1]
    all_keywords += all_keywords[:1]

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=company_scores,
        theta=all_keywords,
        fill='toself',
        name='Company',
        line_color='red'
    ))

    fig.add_trace(go.Scatterpolar(
        r=compute_scores,
        theta=all_keywords,
        fill='toself',
        name='Compute',
        line_color='blue'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
    )

    return fig

def workstyle_radar(data):
    workstyle_data = data['workstyleResult']
    company_keywords = workstyle_data['company']['keyWord']
    compute_keywords = workstyle_data['compute']['keyWord']

    # Combine all unique keywords
    all_keywords = sorted(set(company_keywords.keys()).union(set(compute_keywords.keys())))

    # Ensure all keywords are present with default value 0 if missing
    company_scores = [company_keywords.get(key, 0) for key in all_keywords]
    compute_scores = [compute_keywords.get(key, 0) for key in all_keywords]

    # Close the radar chart by repeating the first score
    company_scores += company_scores[:1]
    compute_scores += compute_scores[:1]
    all_keywords += all_keywords[:1]

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=company_scores,
        theta=all_keywords,
        fill='toself',
        name='Company',
        line_color='red'
    ))

    fig.add_trace(go.Scatterpolar(
        r=compute_scores,
        theta=all_keywords,
        fill='toself',
        name='Compute',
        line_color='blue'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
    )

    return fig