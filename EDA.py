import os
import pandas as pd

df = pd.read_csv("/Users/sofie/Downloads/country_info.csv")
df["written_name"] = df["official_name"].str.capitalize()
df.drop(["official_name"], axis=1, inplace=True)
df.to_csv("/Users/sofie/Downloads/country_info_lowered.csv")
#
# # i = 0
# for entry in os.scandir("./dashframework-main/jbi100_app/data/"):
#     if entry.is_file():  # check if it's a file
#         df = pd.read_csv(entry)
#         your_set = set(df["Country"])
#         un_set = set(UN_countries)
#
#         missing_from_your_list = sorted(un_set - your_set)
#         extra_in_your_list = sorted(your_set - un_set)
#         matching = sorted(your_set & un_set)
#
#         filtered = df[df["Country"].isin(matching)]
#         filtered.to_csv(f"/Users/sofie/Downloads/{entry}_filtered", index=False)
#
#
# print(str(entry), len(matching))
# print("=== MISSING FROM YOUR LIST ===")
# for x in missing_from_your_list:
#     print(x)

# print("=== EXTRA IN YOUR LIST ===")
# for x in extra_in_your_list:
#     print(x)
