"""Clean Data - Calculate Metrics"""

import csv
import pandas as pd

######## Get File Path##################
VLMS_DATA_PATH = "vlms-data\VLMS_Entires--Dana-Farber--All-Time--20250108.csv"  # type: ignore
CENSUS_DATA_PATH = "census-data\state_and_county_fips_master.csv"  # type: ignore
# PROCESSED_PATH='processed-data\' # type: ignore
############ Constant Lists############
columns_to_exclude = [
    "studentName",
    "userGraduationYear",
    "rotationPeriod",
    "preceptorName",
    "codeType",
    "ID",
    "institutionID",
    "type",
    "googleID",
    "addressSubpremise",
    "addressNeighborhood",
    "userCreated",
    "dateCreated",
    "dateModified",
]
county_list = [
    "Tazewell County",
    "Galax City County",
    "Hampton City County",
    "Lynchburg City County",
    "Manassas City County",
    "Newport News City County",
    "Norfolk City County",
    "Portsmouth City County",
    "Radford City County",
    "St. Louis City County",
    "Staunton City County",
    "Virginia Beach City County",
    "District of Columbia County",
]
rotation_drop = [
    "Standardized Patient",
    "Clinical Procedural Skills",
    "High Fidelity Simulation",
    "Anatomy Lab (OMS I)",
    "CREDO Development",
]

######### Read CSV DATA ########################

df = pd.read_csv(VLMS_DATA_PATH, usecols=lambda x: x not in columns_to_exclude)
fips = pd.read_csv(CENSUS_DATA_PATH, names=["fips", "addressCounty", "addressState"])
get_localities = (
    df[["addressLocality", "addressCounty", "addressState"]][
        ~df["addressCounty"].isna()
    ]
    .dropna()
    .drop_duplicates()
)

################## Clean VLMS ####################
get_nan_localities = (
    df[["addressLocality", "addressState"]][df["addressCounty"].isna()]
    .dropna()
    .drop_duplicates()
)

local_rep = get_localities[
    get_localities["addressLocality"].isin(list(get_nan_localities["addressLocality"]))
]

list_mia = sorted(
    list(
        set(get_nan_localities["addressLocality"])
        - set(list(local_rep["addressLocality"]))
    )
)

county_mia = get_nan_localities[
    get_nan_localities["addressLocality"].isin(list_mia)
].sort_values(
    by="addressLocality"
)  # type: ignore
county_mia["addressCounty"] = county_list

county_replacement = pd.concat([county_mia, local_rep])
df.fillna(county_replacement["addressCounty"])

result = pd.merge(
    df, county_replacement, how="left", on=["addressLocality", "addressState"]
)
result["addressCounty_x"] = result["addressCounty_x"].fillna(result["addressCounty_y"])
result.drop(["addressCounty_y"], inplace=True, axis=1)
result.rename(columns={"addressCounty_x": "addressCounty"}, inplace=True)
result = result.drop_duplicates(subset="recordID", keep="first")
result = result.dropna(subset=["geoLongitude"])
result_sorted = result.sort_values("entryLoggedAt")
result_sorted["entryDate"] = result_sorted["entryLoggedAt"].str.split().str[0]
new_df = result_sorted[~result_sorted["rotationType"].isin(rotation_drop)]

####################summary######################
summary = new_df.groupby(
    ["entryDate", "code", "codeDescription", "addressCounty"], as_index=False
)["code"].value_counts()
# summary.to_csv("County Counts Cancer Dated.csv", index=False)
summary_county = new_df.groupby(
    [
        "code",
        "codeDescription",
        "addressCounty",
        "addressState",
        "patientAge",
        "patientSex",
    ],
    as_index=False,
)["code"].value_counts()
# summary_county.to_csv("County Counts Cancer.csv", index=False)

###############Clean Fips###########
fips["addressCounty"] = fips["addressCounty"].str.replace("city", "City County")
fips["addressCounty"] = fips["addressCounty"].str.replace(
    "Anchorage Municipality", "Anchorage"
)
fips["addressCounty"] = fips["addressCounty"].str.replace(
    "District of Columbia", "District of Columbia County"
)

######### Final Data ###########
final = pd.merge(new_df, fips, how="left", on=["addressCounty", "addressState"])
final.loc[
    (final["addressLocality"] == "Danville") & (final["addressState"] == "VA"),
    "addressCounty",
] = final.loc[
    (final["addressLocality"] == "Danville") & (final["addressState"] == "VA"),
    "addressCounty",
].fillna(
    "Danville City County"
)
final.loc[
    (final["addressLocality"] == "Danville") & (final["addressState"] == "VA"), "fips"
] = final.loc[
    (final["addressLocality"] == "Danville") & (final["addressState"] == "VA"), "fips"
].fillna(
    "51590"
)
final.loc[
    (final["addressLocality"] == "Bristol") & (final["addressState"] == "VA"),
    "addressCounty",
] = final.loc[
    (final["addressLocality"] == "Bristol") & (final["addressState"] == "VA"),
    "addressCounty",
].fillna(
    "Bristol City County"
)
final.loc[
    (final["addressLocality"] == "Bristol") & (final["addressState"] == "VA"), "fips"
] = final.loc[
    (final["addressLocality"] == "Bristol") & (final["addressState"] == "VA"), "fips"
].fillna(
    "51520"
)
final[["addressLocality", "addressState"]][
    final["fips"].isna() & ~final["addressCountry"].isna()
].drop_duplicates()

final_us = final[~final["addressCountry"].isna()]
final_us_complete = final_us[~final_us["fips"].isna()]


# final_us[(final_us["fips"].isna()) & (final_us["addressCountry"] == "US")].to_csv(
#    "Undetermined Location US.csv"
# )

######## Summary for Clean ###############
summary_county = final_us_complete.groupby(
    ["fips", "addressCounty", "addressState"], as_index=False
)["fips"].value_counts()
# summary_county.to_csv("County Counts Cancer Final US.csv", index=False)
summary_county_by_cancer = final_us_complete.groupby(
    ["fips", "code", "codeDescription", "addressCounty", "addressState"], as_index=False
)["code"].value_counts()
# summary_county_by_cancer.to_csv("County Counts by Cancer Final US.csv", index=False)
summary_all = (
    summary_county_by_cancer.pivot_table(
        index=["fips", "addressCounty", "addressState"],
        columns="code",
        values="count",
        aggfunc="first",
    )  # type: ignore
    .reset_index()
    .fillna(0)
)
summary_all["Total"] = summary_all.iloc[:, 4:].sum(axis=1)

summary_all.sort_values(by="Total", ascending=False)

col_nam = list(summary_all.iloc[:, 4:-1].columns)
cancer_group = set([e.split(".")[0] for e in col_nam])

with open("processed-data\cancer_group.csv", "w", encoding="utf-8", newline="") as csvfile:  # type: ignore
    writer = csv.writer(csvfile)
    writer.writerow(cancer_group)

for i in cancer_group:
    filter_group = summary_all.iloc[:, 4:].filter(regex=i)
    summary_all[f"{i}" + " Total"] = filter_group.sum(axis=1)
# summary_all.to_csv("County Counts by Cancer Final US.csv", index=False)

summary_totals = pd.concat(
    [summary_all.iloc[:, :3], summary_all.iloc[:, (summary_all.shape[1] - 15) :]],
    axis=1,
)
summary_totals["fips"] = summary_totals["fips"].apply(
    lambda x: "0" + x if len(x) <= 4 else x
)
# summary_totals.to_csv('County Counts by Cancer Final US.csv', index =False)

final["parent code"] = final[["code", "codeDescription"]]["code"].str.split(".").str[0]

cancer_name_map = final[["parent code", "codeDescription"]][
    final["parent code"] == final["code"]
].drop_duplicates()

cancer_name_map.loc[-1] = [
    "C93",
    "Chronic myelomonocytic leukemia (CMML) that has not achieved remission",
]
cancer_name_map.loc[-2] = ["C54", "Malignant neoplasm of the corpus uteri"]
cancer_name_map.to_csv("processed-data\cancer_name_map.csv", index=False) # type: ignore

final_us_complete["parent code"] = (
    final_us_complete[["code", "codeDescription"]]["code"].str.split(".").str[0]
)
final_us_complete["year"] = final_us_complete["entryDate"].str.split("-").str[0]
sex_summary = (
    final_us_complete.groupby(["year", "parent code"], as_index=False)["patientSex"]
    .value_counts()
    .pivot_table(
        index=["year", "parent code"],
        columns="patientSex",
        values="count",
        aggfunc="first",
    )  # type: ignore
    .reset_index()
    .fillna(0)
)
age_summary = final_us_complete.groupby(["year", "parent code"], as_index=False)[
    "patientAge"
].value_counts()
# summary_date = final_us_complete.groupby(['year', 'parent code', 'codeDescription',
# 'fips','addressCounty','addressState'], as_index=False)['parent code'].value_counts()
# summary_date.to_csv('County Counts Cancer Dated.csv', index =False)

summary_date = final_us_complete.groupby(
    ["year", "parent code", "fips", "addressCounty", "addressState"], as_index=False
)["parent code"].value_counts()
summary_date.to_csv("processed-data\summary_date.csv", index=False)  # type: ignore

summary_date_all = (
    summary_date.pivot_table(
        index=["year", "fips", "addressCounty", "addressState"],
        columns=["parent code", "year"],
        values="count",
        aggfunc="first",
    )  # type: ignore
    .reset_index()
    .fillna(0)
)

sex_summary["percentage"] = sex_summary["Female"] / (
    sex_summary["Female"] + sex_summary["Male"]
)

age_summary = pd.merge(age_summary, sex_summary, how="left", on=["year", "parent code"])

age_summary = final_us_complete.groupby(
    ["year", "parent code", "patientSex"], as_index=False
)["patientAge"].value_counts()
age_summary.to_csv("processed-data\demographic_summary.csv", index=False) # type: ignore
