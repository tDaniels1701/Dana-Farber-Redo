# pylint: disable=use-dict-literal
"""Generate Dash Board"""

import json
import pathlib

from urllib.request import urlopen
import os
import dash
import geopandas as gpd
import pandas as pd
import plotly.express as px

# import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.figure_factory as ff

# Replace 'your_shapefile.shp' with the actual path to your shapefile
cancer_centers = gpd.read_file(
    "NCI_CancerCenter_Address_fall2024/NCI_CancerCenter_Address_fall2024.shp"
)
# Initialize app
with urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
) as response:
    counties = json.load(response)
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.title = "VLMS Cancer Logging"
server = app.server

# Load data

APP_PATH = str(pathlib.Path(__file__).parent.resolve())

YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

DATA_LIST = ["cancer_name_map", "cancer_group", "summary_date", "demographic_summary"]

p = os.getcwd().split(os.path.sep)
CSV_PATH = f"processed-data/{DATA_LIST[0]}.csv"
cancer_name_map = pd.read_csv(CSV_PATH)
cancer_name_map = cancer_name_map.sort_values("parent code")
CSV_PATH = f"processed-data/{DATA_LIST[1]}.csv"
cancer_group = pd.read_csv(CSV_PATH)
CSV_PATH = f"processed-data/{DATA_LIST[2]}.csv"
summary_date = pd.read_csv(CSV_PATH)
# summary_date["fips"] = (
#     summary_date["fips"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
# )
CSV_PATH = f"processed-data/{DATA_LIST[3]}.csv"
demographic_summary = pd.read_csv(CSV_PATH)

POP_PATH = "census-data/PopulationEstimates.csv"
pop = pd.read_csv(POP_PATH, engine="python", encoding="latin1")
POV_PATH = "census-data/PovertyEstimates.csv"
poverty = pd.read_csv(POV_PATH)
EMP_PATH = "census-data/Unemployment.csv"
employ = pd.read_csv(EMP_PATH)
IND_PATH = "census-data/CBP2022.CB2200CBP-Data.csv"
industry_data = pd.read_csv(IND_PATH, header=0, low_memory=False).drop(0, axis=0)

industry_data["fips"] = industry_data["GEO_ID"].str.split("US").str[1]
industry_data.drop(["PAYANN_N", "PAYQTR1_N", "EMP_N"], axis=1, inplace=True)
industry_actual = industry_data[industry_data["PAYANN"] != "N"]
industry_county_max = industry_actual.groupby(["fips", "NAME", "NAICS2017_LABEL"])[
    ["ESTAB", "PAYANN", "EMP"]
].max()
FEM_PATH = "census-data/female demographic totals.csv"
female_pop = pd.read_csv(FEM_PATH)
female_pop["FIP"] = (
    female_pop["FIP"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)
MALE_PATH = "census-data/male demographic totals.csv"
male_pop = pd.read_csv(MALE_PATH)
male_pop["FIP"] = (
    male_pop["FIP"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)
pop["year"] = pop["Attribute"].str.split("_").str[-1]
poverty["year"] = poverty["Attribute"].str.split("_").str[-1]
employ["year"] = employ["Attribute"].str.split("_").str[-1]

summary_date["fips"] = (
    summary_date["fips"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)
pop["FIPStxt"] = (
    pop["FIPStxt"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)
poverty["FIPS_Code"] = (
    poverty["FIPS_Code"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)
employ["FIPS_Code"] = (
    employ["FIPS_Code"].astype(str).apply(lambda x: "0" + x if len(x) <= 4 else x)
)


CANCER_CENTER = "processed-data/cancer centers.xlsx"
cancer_cent = pd.read_excel(CANCER_CENTER)
cancer_cent["type"] = cancer_cent["type"].str.replace("RADIOIO", "Radiology Only")
cancer_cent["type"] = cancer_cent["type"].str.replace("RADIO", "Radiology Only")
cancer_cent["type"] = cancer_cent["type"].str.replace("CHEMO", "Chemotherapy Only")
cancer_cent["type"] = cancer_cent["type"].str.replace("BOTH", "Chemo and Radiology")
cancer_cent["type"] = cancer_cent["type"].str.replace(
    "TREAT", "Cancer Treatment Center"
)
cancer_centers["type"] = "NCI " + cancer_centers["type"]
TABLE_LIST = [
    "Employment",
    "Industry",
    "Population",
    "Poverty",
    "Female Race/Ethnicity By Age Ranges",
    "Male Race/Ethnicity By Age Ranges",
]
AGE_GROUP_LIST = [
    "Infant",
    "Neonate",
    "1-14",
    "14-18",
    "19-44",
    "45-64",
    "65-84",
    "85+",
]

### Location data + Zip code shapes
ZIP_DATA_PATH = "processed-data/locations.csv"
SHAPEFILE_PATH = "processed-data/cb_2018_us_zcta510_500k.shp"
zip_df = pd.read_csv(ZIP_DATA_PATH)
zip_df["addressPostalCode"] = zip_df["addressPostalCode"].astype(str).str.zfill(5)
zip_counts = zip_df["addressPostalCode"].value_counts().reset_index()
zip_counts.columns = ["zip", "count"]
zcta_full = gpd.read_file(SHAPEFILE_PATH)
zcta_full = zcta_full.rename(columns={"ZCTA5CE10": "zip"})
zcta_full["zip"] = zcta_full["zip"].astype(str).str.zfill(5)
zcta_filtered = zcta_full[zcta_full["zip"].isin(zip_counts["zip"])]
zcta_merged = zcta_filtered.merge(zip_counts, on="zip", how="left")
zcta_merged["count"] = zcta_merged["count"].fillna(0)
zcta_merged = zcta_merged.to_crs(epsg=4326)


def build_upper_left_panel():
    """Create the Upper Layout"""
    return html.Div(
        id="upper-left",
        className="six columns",
        children=[
            html.Div(
                className="control-row-1",
                children=[
                    html.Div(
                        id="diagnosis-select-outer",
                        children=[
                            html.Label("Select Cancer Diagnosis"),
                            dcc.Dropdown(
                                id="diagnosis-select",
                                options=[
                                    {"label": j + "-" + i, "value": j}
                                    for i, j in zip(
                                        cancer_name_map["codeDescription"],
                                        cancer_name_map["parent code"],
                                    )
                                ],
                                value=cancer_name_map["parent code"].iloc[0],
                            ),
                        ],
                    ),
                    html.Div(
                        id="select-metric-outer",
                        children=[
                            html.Label("Choose a Demographic/SocioEconomic Table"),
                            dcc.Dropdown(
                                id="metric-select",
                                options=[{"label": i, "value": i} for i in TABLE_LIST],
                                value=TABLE_LIST[0],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_lower_left_panel():
    """Create the Upper Layout"""
    return html.Div(
        id="lower-left",
        className="row",
        children=[
            html.Div(
                children=[
                    dcc.Graph(
                        id="county-choropleth",
                        style={
                            "width": "65%",
                            "height": "800px",
                            "vertical-align": "top",
                            "display": "inline-block",
                        },
                        figure={
                            "layout": dict(
                                margin=dict(l=0, r=0, b=0, t=0, pad=0),
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                            )
                        },
                    ),
                    html.Div(
                        style={
                            "width": "2%",  # Adjust the width as needed
                            "height": "100%",  # Full height
                            "background-color": "lightgray",  # Adjust the color as needed
                            "display": "inline-block",
                            "vertical-align": "middle",
                        }
                    ),
                    dcc.Graph(
                        id="table-data",
                        style={
                            "width": "33%",
                            "height": "75vh",
                            "vertical-align": "middle",
                            "display": "inline-block",
                        },
                    ),
                ],
            ),
        ],
    )


@app.callback(
    Output("county-choropleth", "figure"),
    Input("diagnosis-select", "value"),
)
def create_geoplot(code):
    """Create Choropleth Visualization"""
    cancer_centers["size"] = [5] * len(cancer_centers)
    cancer_cent["size"] = [5] * len(cancer_cent)
    value = "count"
    cancer_name = cancer_name_map["codeDescription"][
        cancer_name_map["parent code"] == code.split()[0]
    ].iloc[0]
    df = summary_date[summary_date["parent code"] == code]
    df["name"] = [cancer_name] * len(df)
    figc = px.choropleth_map(
        df,
        geojson=counties,
        locations="fips",  # Spatial coordinates
        color=value,  # Data to be color-coded
        hover_data={
            "name": True,
            "parent code": True,
            "addressState": True,
            value: True,
            "fips": False,
        },
        labels={
            "name": "Cancer",
            "parent code": "ICD 10",
            "addressState": "State",
            value: "Total Count",
            "year": "Year",
        },
        animation_frame="year",
        color_continuous_scale="Viridis",
        hover_name="addressCounty",
        map_style="open-street-map",
        zoom=6,
        center={"lat": 34.9496, "lon": -81.9321},
        opacity=0.5,
    ).update_traces(visible=True)

    figc.update_layout(
        sliders=[
            dict(
                yanchor="top",
                xanchor="left",
                y=1.15,
                x=0.15,
                steps=[
                    dict(
                        method="animate",
                        args=[
                            [f"{date}"],
                            dict(
                                mode="immediate", frame=dict(duration=1000, redraw=True)
                            ),
                        ],
                    )
                    for date in summary_date["year"].unique()
                ],
            )
        ],
        coloraxis_colorbar=dict(
            yanchor="top",
            y=1,
            # len=0.75,
            x=-0.05,
            bgcolor="#171b26",
            # ticklabelposition="outside left",
            ticks="outside",
            # ticksuffix=" counts",
        ),
    )
    figc.update_layout(
        title=f"{code} - {cancer_name}",
        title_y=0.99,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=1.20,
                x=0,
                xanchor="left",
                yanchor="top",
            )
        ],
    )
    figc["layout"]["sliders"][0]["pad"] = dict(  # type: ignore
        r=70,
        t=0.0,
    )  # type: ignore
    nci_centers = px.scatter_map(
        cancer_centers,
        lat="Latitude",
        lon="Longitude",
        color="type",
        color_discrete_sequence=["salmon", "orange", "dodgerblue"],
        hover_name="name",
        size="size",
        labels={"type": "Type"},
        hover_data={
            "type": True,
            "Street": True,
            "City": True,
            "County": True,
            "Longitude": False,
            "Latitude": False,
            "name": False,
            "size": False,
        },
    )
    figc.add_trace(nci_centers.data[0])
    figc.add_trace(nci_centers.data[1])
    figc.add_trace(nci_centers.data[2])
    researched_centers = px.scatter_map(
        cancer_cent,
        lat="Y",
        lon="X",
        color="type",
        color_discrete_sequence=["violet", "red", "brown", "grey"],
        hover_name="Hospital Name",
        size="size",
        labels={"type": "Type"},
        hover_data={
            "type": True,
            "ADDRESS": True,
            "CITY": True,
            "STATE": True,
            "ZIP": True,
            "X": False,
            "Y": False,
            "Hospital Name": False,
            "size": False,
        },
    )
    figc.add_trace(researched_centers.data[0])
    figc.add_trace(researched_centers.data[1])
    figc.add_trace(researched_centers.data[2])
    figc.add_trace(researched_centers.data[3])
    figc.update_layout(
        dict(
            margin=dict(l=0, r=0, b=0.5, t=0, pad=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            legend=dict(
                title="Cancer Center Classifications",
                yanchor="top",
                bgcolor="#171b26",
                y=0.99,
                # xanchor="right",
                x=0.1,
                itemsizing="constant",
            ),
        )
    )
    return figc


@app.callback(
    Output("cancer-sunburst", "figure"),
    [
        Input("county-choropleth", "hoverData"),
    ],
)
def create_comparison(hover_data):
    """Create Sunburst"""
    #     fig = go.Figure()
    fip = hover_data["points"][0]["customdata"][4]
    county = hover_data["points"][0]["hovertext"]
    df = summary_date[summary_date["fips"] == fip]
    df = df.merge(cancer_name_map, how="left")
    fig = px.bar(
        df,
        x="year",
        y="count",
        color="parent code",
        color_discrete_sequence=[
            "violet",
            "firebrick",
            "yellowGreen",
            "orange",
            "cyan",
            "hotpink",
            "lightgreen",
            "darkolivegreen",
            "mediumvioletred",
            "salmon",
            "dodgerblue",
            "seashell",
            "sienna",
            "slateblue",
        ],
        barmode="group",
        hover_data={
            "codeDescription": True,
            "parent code": True,
            "count": True,
            "year": True,
        },
        labels={
            "codeDescription": "Cancer Diagnosis",
            "parent code": "ICD 10",
            "count": "Total Count",
            "year": "Year",
        },
    ).update_traces(width=0.05)
    fig.update_layout(
        title=f"Cancer Diagnosis: {county}",
        xaxis=dict(title="Year: 2017-2025"),
    )
    fig.update_layout(
        dict(
            # margin=dict(l=0, r=0, b=0, t=0.5, pad=0),
            legend=dict(title="ICD 10 Codes"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
    )
    return fig


@app.callback(
    Output("bar-plot", "figure"),
    Input("diagnosis-select", "value"),
)
def create_bar(code):
    """Create Bar Plot"""
    df = demographic_summary[
        (demographic_summary["parent code"] == code)
        & (demographic_summary["patientSex"].isin(["Female", "Male"]))
    ]
    cancer_name = cancer_name_map["codeDescription"][
        cancer_name_map["parent code"] == code.split()[0]
    ].iloc[0]
    fig = px.bar(
        df,
        x="year",
        y="count",
        color="patientAge",
        barmode="group",
        facet_col="patientSex",
        category_orders={
            "patientAge": AGE_GROUP_LIST,
            "patientSex": ["Female", "Male"],
        },
        labels={
            "patientSex": "Sex",
            "patientAge": "Age Range",
            "count": "Total Count",
            "year": "Year",
        },
    ).update_traces(width=0.1)
    fig.update_xaxes(title_text=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    fig.update_layout(
        title=f"All Counties Aggregated: {code} - {cancer_name}",
        xaxis=dict(title="", categoryorder="category ascending"),
        yaxis=dict(title="Cancer Counts"),
    )
    fig.add_annotation(
        text="Year: 2017-2025",
        x=0.5,
        y=-0.25,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_layout(
        dict(
            # margin=dict(l=0, r=0, b=0, t=0.5, pad=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
    )
    return fig


@app.callback(
    Output("table-data", "figure"),
    [
        Input("county-choropleth", "hoverData"),
        Input("metric-select", "value"),
    ],
)
def display_selected_data(hover_data, value):
    """Display Demo/Socioeconmic Data"""
    # fig=None
    if hover_data:
        county = hover_data["points"][0]["hovertext"]
        fip = hover_data["points"][0]["customdata"][4]
        pop_sc = pop[pop["FIPStxt"] == fip]
        pov_sc = poverty[poverty["FIPS_Code"] == fip]
        employ_sc = employ[employ["FIPS_Code"] == fip]
        colorscale = [[0, "#4d004c"], [0.5, "#f2e5ff"], [1, "#ffffff"]]
        if value == "Employment":
            # fig = get_employment(employ_sc, colorscale)
            df = employ_sc[employ_sc["year"] == "2022"]
            df["Attribute"] = df["Attribute"].str.replace("_", " ")  #
            df["Attribute"] = df["Attribute"].str.rsplit(" ", n=1, expand=True)[0]
            df = df.set_index("Attribute").sort_index()
            fig = ff.create_table(df.iloc[:, 3:], index=True, colorscale=colorscale)
            fig.update_layout(
                title_text=f'Employment Metrics: {df["Area_Name"].iloc[0]} '
            )
            # fig.update_layout({"margin": {"t": 50}})
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 10
            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )
        if value == "Poverty":
            # fig = get_poverty(pov_sc, colorscale)
            df = pov_sc[
                (pov_sc["year"] == "2021") & (pov_sc["Attribute"].str.contains("ALL"))
            ]
            pov_pct = df.iloc[3:, 3:]
            pov_pct["Attribute"] = [
                "Poverty %",
                "90% Conf.<br>Interval Lower",
                "90% Conf.<br>Interval Upper",
            ]
            pov_pct = pov_pct.set_index("Attribute").sort_index()
            fig = ff.create_table(
                pov_pct, index=True, colorscale=colorscale, height_constant=60
            )
            fig.update_layout(title_text=f'Poverty Metrics: {df["Area_name"].iloc[0]} ')
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 12

            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )
        if value == "Industry":
            # fig = get_industry(fip, colorscale, county)
            ind_county = industry_county_max.loc[
                industry_county_max.index.get_level_values(0) == str(fip)
            ]
            ind_list = [e[2] for e in list(ind_county.index)]
            ind_county_new = ind_county.reset_index(drop=True)
            ind_county_new["Industry"] = ind_list
            ind_county_new["Industry"] = ind_county_new["Industry"].str.replace(
                "and", " "
            )
            ind_county_new["Industry"] = ind_county_new["Industry"].str.replace(
                ",", " "
            )
            ind_county_new["Industry"] = (
                ind_county_new["Industry"].str.split(" ").str[0]
            )
            ind_format = ind_county_new.set_index("Industry").sort_index()
            ind_format.columns = ["Establishments", "Annual Payroll", "Employees"]
            fig = ff.create_table(ind_format, index=True, colorscale=colorscale)
            fig.update_layout(title_text=f"Industry: {county}")
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 10
            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )

        if value == "Population":
            # fig = get_population(pop_sc,colorscale)
            df = pop_sc[pop_sc["year"] == "2022"]
            pop_pct = df.iloc[[0, 10, 11, 12, 13, 14, 15], 3:]
            pop_pct["Attribute"] = pop_pct["Attribute"].str.replace("_", " ")
            pop_pct["Attribute"] = pop_pct["Attribute"].str.rsplit(
                " ", n=1, expand=True
            )[0]
            pop_pct["Attribute"] = pop_pct["Attribute"].str.replace("R ", "")
            rename = [e + " RATE" for e in pop_pct["Attribute"] if e != "POP ESTIMATE"]
            pop_pct["Attribute"] = ["POP ESTIMATE"] + rename
            pop_pct["Attribute"] = pop_pct["Attribute"].str.replace(" ", "<br>")
            pop_pct = pop_pct.set_index("Attribute").sort_index()
            fig = ff.create_table(
                pop_pct,
                index=True,
                colorscale=colorscale,
                height_constant=60,
            )
            fig.update_layout(
                title_text=f'Population Metrics: {df["Area_Name"].iloc[0]} '
            )
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 12
            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )
        if value == "Female Race/Ethnicity By Age Ranges":
            # fig = get_demo(female_pop, fip,colorscale, county, value)
            female = female_pop.loc[female_pop["FIP"] == str(fip)]
            female = female.set_index("Age Range VLMS").sort_index()
            female.columns = female.columns.str.replace("_", " ")
            female.columns = female.columns.str.replace("/", " ")
            female.columns = female.columns.str.replace("-", " ")
            female.columns = female.columns.str.replace("TOT", "")
            female.columns = female.columns.str.replace(" ", "<br>")
            fig = ff.create_table(
                female.iloc[:, 3:],
                index=True,
                index_title="Age<br>Range",
                colorscale=colorscale,
                height_constant=60,
            )
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 10
            fig.update_layout(
                title_text=f"Female Race/Ethnicity By Age Ranges:<br> {county}"
            )
            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )
        if value == "Male Race/Ethnicity By Age Ranges":
            # fig = get_demo(male_pop, fip,colorscale, county, value)
            male = male_pop.loc[male_pop["FIP"] == str(fip)]
            male = male.set_index("Age Range VLMS").sort_index()
            male.columns = male.columns.str.replace("_", " ")
            male.columns = male.columns.str.replace("/", " ")
            male.columns = male.columns.str.replace("-", " ")
            male.columns = male.columns.str.replace("TOT", "")
            male.columns = male.columns.str.replace(" ", "<br>")
            fig = ff.create_table(
                male.iloc[:, 3:],
                index=True,
                index_title="Age<br>Range",
                colorscale=colorscale,
                height_constant=60,
            )
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].font.size = 10
            fig.update_layout(
                title_text=f"Male Race/Ethnicity By Age Ranges:<br> {county}"
            )
            fig.update_layout(
                dict(
                    margin=dict(l=0, r=0, b=0, t=50, pad=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    # plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                )
            )
    return fig  # type: ignore


def create_zip_heatmap():
    fig = px.choropleth_mapbox(
        zcta_merged,
        geojson=zcta_merged.geometry.__geo_interface__,
        locations=zcta_merged.index,
        color="count",
        color_continuous_scale=[[0, "white"], [1, "darkgreen"]],
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 34.9, "lon": -81.0},
        opacity=0.6,
        labels={"count": "Count"},
        hover_data={
            "zip": True,
            "count": True,
        },
    )
    fig.update_layout(
        title={
            "text": "Heatmap of Preceptor Locations",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20},
        },
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    return fig


app.layout = html.Div(
    className="container scalable",
    children=[
        html.Div(
            id="banner",
            className="banner",
            children=[
                html.H6("Cancer Counts in VLMS through the Years 2016-2025"),
                # html.Img(src=app.get_asset_url("plotly_logo_white.png")),
            ],
        ),
        html.Div(
            id="upper-container",
            className="row",
            children=[
                build_upper_left_panel(),
                # build_upper_right_panel(),
                # build_lower_left_panel(),
            ],
        ),
        html.Div(
            id="left-container",
            className="row",
            children=[
                build_lower_left_panel(),
            ],
        ),
        html.Div(
            id="banner h6",
            className="banner h6",
            children=[
                html.H6(""),
                # html.Img(src=app.get_asset_url("plotly_logo_white.png")),
            ],
        ),
        html.Div(
            id="right-container",
            children=[
                dcc.Graph(
                    id="cancer-sunburst",
                ),
                dcc.Graph(
                    id="bar-plot",
                ),
            ],
        ),
        html.Div(
            id="zip-heatmap-container",
            children=[
                dcc.Graph(
                    id="zip-heatmap",
                    figure=create_zip_heatmap(),
                ),
            ],
        ),
    ],
)


if __name__ == "__main__":  # type: ignore
    app.run_server(debug=True)
