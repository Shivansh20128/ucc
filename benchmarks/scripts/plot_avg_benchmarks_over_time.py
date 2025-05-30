from common import (
    annotate_and_adjust,
    adjust_axes_to_fit_labels,
    extract_compiler_versions,
)
from pkg_resources import parse_version
import glob
import pandas as pd
import matplotlib.pyplot as plt
import os


### Load data
# Get the directory of the current script
directory_of_this_file = os.path.dirname(os.path.abspath(__file__))
results_folder = os.path.join(directory_of_this_file, "../results")
csv_files = glob.glob(os.path.join(results_folder, "gates*.csv"))

dataframes = []


print("Loading data files...")
for file in csv_files:
    compiler_versions = {}
    with open(file, "r") as f:
        header_line = f.readline().strip()
        compiler_versions = extract_compiler_versions(header_line)

    date_label = str(file).split("_")[1].split(".")[0]
    df = pd.read_csv(file, header=1)

    df["date"] = date_label
    df["compiled_ratio"] = df["compiled_multiq_gates"] / df["raw_multiq_gates"]
    if "pytket-peep" in df["compiler"].unique():
        compiler_versions["pytket-peep"] = compiler_versions["pytket"]
        # Remove pytket from compiler_versions for this datafile
        compiler_versions.pop("pytket")
    df["compiler_version"] = df["compiler"].map(compiler_versions)
    df["compiler"] = df["compiler"].replace("qiskit", "qiskit-default")
    # Scrub semver string of any extraneous period at end
    df["compiler_version"] = df["compiler_version"].str.rstrip(".")

    dataframes.append(df)

df_dates = pd.concat(dataframes, ignore_index=True)

# Remove older implementation of pytket from the data
df_dates = df_dates[df_dates["compiler"] != "pytket"]

# Remove data from dates between 2025-02-07 through 2025-02-28 while #251 was being fixed
df_dates = df_dates[
    ~((df_dates["date"] >= "2025-02-07") & (df_dates["date"] < "2025-02-28"))
    & (df_dates["date"] != "2025-03-05")
]

# Ensure 'date' is in datetime format
df_dates["date"] = pd.to_datetime(df_dates["date"])

# Get the earliest date for each compiler version
new_version_dates = df_dates.groupby(["compiler", "compiler_version"])[
    "date"
].min()

# Get all unique first occurrence dates
unique_dates = new_version_dates.unique()

# Filter on first occurrence of each compiler version based on the date
df_dates = df_dates[df_dates["date"].isin(unique_dates)]

# Find the average compiled ratio for each compiler on each date
avg_compiled_ratio = (
    df_dates.groupby(["compiler", "date", "compiler_version"])[
        "compiled_ratio"
    ]
    .mean()
    .reset_index()
    .sort_values("date")
)
# Sort the dataframe by package, date, and parsed version
avg_compiled_ratio["parsed_version"] = avg_compiled_ratio[
    "compiler_version"
].apply(parse_version)
avg_compiled_ratio = avg_compiled_ratio.sort_values(
    by=["date", "compiler", "parsed_version"], ascending=[True, True, True]
)
avg_compiled_ratio = avg_compiled_ratio.sort_values(
    by=["date", "compiler", "compiler_version"], ascending=[True, True, True]
)
# Keep only the highest version per (date, package)
avg_compiled_ratio = avg_compiled_ratio.drop_duplicates(
    subset=["date", "compiler"], keep="last"
)

# Find the average compile time for each compiler on each date
avg_compile_time = (
    df_dates.groupby(["compiler", "date", "compiler_version"])["compile_time"]
    .mean()
    .reset_index()
    .sort_values("date")
)

# Sort the dataframe by package, date, and parsed version
avg_compile_time["parsed_version"] = avg_compile_time[
    "compiler_version"
].apply(parse_version)
avg_compile_time = avg_compile_time.sort_values(
    by=["date", "compiler", "parsed_version"], ascending=[True, True, True]
)
# Keep only the highest version per (date, package)
avg_compile_time = avg_compile_time.drop_duplicates(
    subset=["date", "compiler"], keep="last"
)

###### Plotting
# Ensure colors are consistently assigned to each compiler
unique_compilers = sorted(df_dates["compiler"].unique())
colormap = plt.get_cmap("tab10", len(unique_compilers))
color_map = {
    compiler: colormap(i) for i, compiler in enumerate(unique_compilers)
}

fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=False, dpi=150)
# Rotate x labels on axes 0
plt.setp(ax[0].xaxis.get_majorticklabels(), rotation=45)


#### Plot Compiled ratio
print("Plotting compiled ratio...")
for compiler in unique_compilers:
    compiler_data = avg_compiled_ratio[
        avg_compiled_ratio["compiler"] == compiler
    ]
    ax[0].plot(
        compiler_data["date"],
        compiler_data["compiled_ratio"],
        label=compiler,
        marker="o",
        linestyle="-",
        color=color_map[compiler],
    )

# Keep track of last compiler version seen over time to track version changes
last_version_seen = {compiler: None for compiler in unique_compilers}

previous_bboxes = []
# Now iterate over each compiler entry and annotate if it's a new version, if so label it
for date in avg_compiled_ratio["date"].unique():
    date_data = avg_compiled_ratio[avg_compiled_ratio["date"] == date]
    # Sort date_data in order of compiled_ratio
    date_data = date_data.sort_values("compiled_ratio")
    # Now iterate over each compiler entry and annotate if it's a new version
    for _, row in date_data.iterrows():
        # Get the version for this date
        current_version = row["compiler_version"]
        compiler = row["compiler"]
        compiled_ratio = row["compiled_ratio"]

        # Check if the version has changed
        if row["parsed_version"] != last_version_seen[compiler]:
            text = f"{current_version}"
            xy = (row["date"], compiled_ratio)
            color = color_map[compiler]
            # Add the annotation and adjust for overlap
            annotate_and_adjust(
                ax=ax[0],
                text=text,
                xy=xy,
                color=color,
                previous_bboxes=previous_bboxes,
                offset=(0, 17),  # Initial offset
                increment=2,  # Vertical adjustment step
                max_attempts=20,
            )
            # plt.pause(0.1)
            # Update the last seen version for this compiler
            last_version_seen[compiler] = row["parsed_version"]

# Set y axis range to be slightly larger than data range
adjust_axes_to_fit_labels(ax[0], y_scale=[1.1, 1.3])

ax[0].set_title("Average Compiled Ratio over Time")
ax[0].set_ylabel("Compiled Ratio")
ax[0].legend(title="Compiler", loc="upper center")


#### Plot Compile time
# Get runtime data only after we created GitHub Actions pipeline for standardization
avg_compile_time = avg_compile_time[avg_compile_time["date"] >= "2024-12-16"]

previous_annotations = []
last_version_seen = {compiler: None for compiler in unique_compilers}

print("Plotting compile time...")
for compiler in unique_compilers:
    compiler_data = avg_compile_time[avg_compile_time["compiler"] == compiler]
    ax[1].plot(
        compiler_data["date"],
        compiler_data["compile_time"],
        label=compiler,
        marker="o",
        linestyle="-",
        color=color_map[compiler],
    )

# Add annotations for version changes
for date in avg_compile_time["date"].unique():
    date_data = avg_compile_time[avg_compile_time["date"] == date]
    # Sort date_data in order of compiled_ratio
    date_data = date_data.sort_values("compile_time")
    for _, row in date_data.iterrows():
        # print(row, '\n')
        # Get the version for this date
        current_version = row["compiler_version"]
        compiler = row["compiler"]
        compile_time = row["compile_time"]

        # Check if the version has changed
        if current_version != last_version_seen[compiler]:
            text = f"{current_version}"
            xy = (row["date"], compile_time)
            color = color_map[compiler]

            # Add the annotation and adjust for overlap
            annotate_and_adjust(
                ax=ax[1],
                text=text,
                xy=xy,
                color=color,
                previous_bboxes=previous_bboxes,
                offset=(0, 30),  # Initial offset
                increment=2,  # Vertical adjustment step
                max_attempts=15,
            )
            # plt.pause(0.1)
            # Update the last seen version for this compiler
            last_version_seen[compiler] = current_version

ax[1].set_title("Average Compile Time over Time")
ax[1].set_ylabel("Compile Time (s)")
ax[1].set_xlabel("Date")
ax[1].set_yscale("log")
ax[1].legend(title="Compiler", loc="upper center")
adjust_axes_to_fit_labels(ax[1], y_scale=[1.0, 1.9], y_log=True)

plt.xticks(rotation=45)
plt.tight_layout()
filename = os.path.join(
    directory_of_this_file, "../avg_compiler_benchmarks_over_time.png"
)
print(f"\nSaving plot to {filename}")
fig.savefig(filename)
