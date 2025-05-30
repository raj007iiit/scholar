import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scholarly import scholarly
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="IIIT Kottayam Faculty Scholar Dashboard", layout="wide")
st.title("📚 Google Scholar Citation Growth - IIIT Kottayam Faculty")

# Load faculty names and scholar IDs
faculty_df = pd.read_csv("iiitkottayam_faculty_with_ids.csv")
faculty_names = faculty_df["Name"].tolist()
name_id_map = dict(zip(faculty_df["Name"], faculty_df["ScholarID"]))

# Sidebar selection
selected_faculty = st.sidebar.multiselect(
    "Select Faculty Members to Compare (⚠ Live scrape — keep it under 10)",
    faculty_names,
    default=faculty_names[:5]
)

# Move refresh button to main body
st.markdown("### 🔄 Click below to fetch latest data from Google Scholar")
refresh = st.button("🚀 Fetch Latest Data")

# Fetch author data from Google Scholar using ScholarID
def fetch_author_data(name):
    scholar_id = name_id_map.get(name)
    if not scholar_id or scholar_id == "Not Found" or scholar_id.startswith("Error"):
        return {"error": f"{name}: Invalid or missing Scholar ID"}
    try:
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author, sections=["basics", "indices", "counts"])
        if not author or "cites_per_year" not in author:
            return {"error": f"{name}: Citation data missing or profile private"}

        cpy = author.get("cites_per_year", {})
        df = pd.DataFrame(list(cpy.items()), columns=["Year", "Citations"])
        df["Name"] = name
        total_citations = sum(cpy.values())
        df.attrs["total_citations"] = total_citations
        return df

    except Exception as e:
        return {"error": f"{name}: {e}"}

def load_data_parallel(names):
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_author_data, name): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if isinstance(result, dict) and "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ {name} fetched successfully")
                results.append(result)
            except Exception as e:
                st.error(f"❌ {name} raised an exception: {e}")
    return results

# Live scrape on button press
if selected_faculty and refresh:
    with st.spinner("Fetching latest citation data from Google Scholar..."):
        dataframes = load_data_parallel(selected_faculty)

    clean_dfs = [df for df in dataframes if isinstance(df, pd.DataFrame)]
    if clean_dfs:
        combined = pd.concat(clean_dfs)
        st.subheader("📈 Citation Growth Over Time (Live Data)")

        # Show yearly total citations across all faculty
        yearly_totals = combined.groupby("Year")["Citations"].sum().reset_index()
        plt.figure(figsize=(10, 4))
        plt.plot(yearly_totals["Year"], yearly_totals["Citations"], marker="s", color="black")
        for i, row in yearly_totals.iterrows():
            plt.text(row["Year"], row["Citations"] + 10, str(row["Citations"]), fontsize=8, ha='center')
        plt.title("Total Citations Across the selected Faculty Per Year")
        plt.grid(True)
        st.pyplot(plt.gcf())

        # Show combined plot for all selected faculty
        st.subheader("📊 Comparison of Citation Growth Across Selected Faculty")
        plt.figure(figsize=(12, 5))
        for df_plot in clean_dfs:
            name = df_plot["Name"].iloc[0]
            plt.plot(df_plot["Year"], df_plot["Citations"], marker="o", label=name)
            for i in range(len(df_plot)):
                plt.text(df_plot["Year"].iloc[i], df_plot["Citations"].iloc[i] + 10, str(df_plot["Citations"].iloc[i]), fontsize=8, ha='center')
        plt.title("Citation Comparison")
        plt.xlabel("Year")
        plt.ylabel("Citations")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt.gcf())

        # Show individual plots
        for df_plot in clean_dfs:
            name = df_plot["Name"].iloc[0]
            total = df_plot.attrs.get("total_citations", 0)
            plt.figure(figsize=(10, 3))
            plt.plot(df_plot["Year"], df_plot["Citations"], marker="o")
            for i in range(len(df_plot)):
                plt.text(df_plot["Year"].iloc[i], df_plot["Citations"].iloc[i] + 10, str(df_plot["Citations"].iloc[i]), fontsize=8, ha='center')
            plt.title(f"{name} (Total Citations: {total})")
            plt.grid(True)
            st.pyplot(plt.gcf())

    st.warning("⚠ Some profiles may not be publicly available or could not be found.")

else:
    st.info("Please select faculty and click '🚀 Fetch Latest Data' to retrieve citation trends.")
