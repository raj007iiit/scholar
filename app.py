import streamlit as st
from scholarly import scholarly
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="IIIT Kottayam Faculty Scholar Dashboard", layout="wide")
st.title("📚 Google Scholar Citation Growth - IIIT Kottayam Faculty")

# Load faculty names
faculty_df = pd.read_csv("iiitkottayam_faculty_names.csv")
faculty_names = faculty_df["Name"].tolist()

# Sidebar: selection of faculty
selected_faculty = st.sidebar.multiselect(
    "Select Faculty Members to Compare",
    faculty_names,
    default=faculty_names[:5]  # preselect a few
)

citation_data = []

if selected_faculty:
    with st.spinner("Fetching Google Scholar data... This may take a while."):
        for name in selected_faculty:
            try:
                search_query = scholarly.search_author(name)
                author = scholarly.fill(next(search_query))
                citations_by_year = author.get("cites_per_year", {})
                df = pd.DataFrame.from_dict(citations_by_year, orient="index", columns=["Citations"])
                df.index.name = "Year"
                df.reset_index(inplace=True)
                df["Name"] = name
                citation_data.append(df)
                time.sleep(1)  # avoid throttling
            except Exception as e:
                st.warning(f"Could not fetch data for {name}: {e}")

    if citation_data:
        combined_df = pd.concat(citation_data)
        st.subheader("📈 Citation Growth Over Time")
        for name in selected_faculty:
            person_df = combined_df[combined_df["Name"] == name]
            plt.figure(figsize=(10, 3))
            plt.plot(person_df["Year"], person_df["Citations"], marker='o')
            plt.title(f"Citation Growth: {name}")
            plt.xlabel("Year")
            plt.ylabel("Citations")
            plt.grid(True)
            st.pyplot(plt.gcf())

else:
    st.info("Please select at least one faculty member to view citation growth.")
