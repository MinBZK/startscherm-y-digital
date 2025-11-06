from pathlib import Path

import pandas as pd
import pdfplumber

pd.set_option('future.no_silent_downcasting', True)

def get_table_indices(df: pd.DataFrame) -> list:
    proces_indices = []
    for column in df.columns:
        if column == "2":
            break
        mask_df = df[df[column].str.contains("^Proces \\d{1,2}\\.\\d{1,2}").fillna(False)]
        df_index = mask_df.index
        proces_indices.extend(df_index)

    proces_indices = sorted(set(proces_indices))
    proces_indices.append(df.index[-1] + 1)
    return proces_indices


def split_into_individual_tables(df: pd.DataFrame, proces_indices: list[int]) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}

    for i, start in enumerate(proces_indices):
        end = proces_indices[i + 1] - 1 if i + 1 < len(proces_indices) else None

        if end is not None:
            table_name = f"table_{i + 1}"
            tables[table_name] = df.loc[start:end]
            # tables[table_name].reset_index(drop=True)

    return tables


def remove_gwr(df: pd.DataFrame) -> pd.DataFrame:
    df_new = df.copy()
    df_new[0] = df_new[0].str.replace("\\s*\\(GWR \\d{1,2}\\.\\d{1,2}\\)\\s*\\n*", "", regex=True)
    df_new[0] = df_new[0].str.replace("\\s*\\(GWR \\d{1,2}\\.\\d{1,2}.*?\\)(.*?\\))\\s*\\n*", "", regex=True)
    return df_new.reset_index(drop=True)


def separate_proces_info(df: pd.DataFrame) -> pd.DataFrame:
    df_new = df.copy()
    df_new.drop(0, axis=0, inplace=True)

    process_number = df.iloc[0,0]
    process_description = df.iloc[0,1]

    df_proces = pd.DataFrame({
        0: ["process_number", "process_description"],
        1: [process_number, process_description]
    })

    df_new = pd.concat([df_proces, df_new], axis=0).reset_index(drop=True)

    return df_new


def custom_fixes(df: pd.DataFrame) -> pd.DataFrame:
    if df[1].str.contains("VWS-monitor en jeugdmonitor").any():
        new_df = df.copy()
        mask = new_df[new_df[1].str.contains("VWS-monitor en jeugdmonitor").fillna(False)].index
        new_df.loc[mask - 1, 1] = new_df.loc[mask - 1, 1] + new_df.loc[mask, 1]
        new_df = new_df.drop(mask, axis=0)
        return new_df.reset_index(drop=True)

    if df[1].str.contains("Voor IGJ start de bewaartermijn na afsluiting van het dossier.").any():
        new_df = df.copy()
        mask = new_df[new_df[1].str.contains(
            "Voor IGJ start de bewaartermijn na afsluiting van het dossier."
        ).fillna(False)].index
        if new_df.loc[mask, 1].iloc[0] == "Voor IGJ start de bewaartermijn na afsluiting van het dossier.":
            new_df.loc[mask - 1, 1] = " ".join(
                [str(new_df.loc[mask - 1, 1].iloc[0]), str(new_df.loc[mask, 1].iloc[0])]
            )
            new_df = new_df.drop(mask, axis=0)
            return new_df.reset_index(drop=True)

    return df


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    df_new = df.copy()

    df_new = df_new.dropna(axis=1, how='all')
    df_new = df_new.dropna(axis=0, how='all')
    df_new[0] = df_new[0] \
        .str.replace("\\n", " ", regex=True) \
        .str.replace("  ", " ", regex=False) \
        .str.strip()
    df_new = remove_gwr(df_new)
    df_new = separate_proces_info(df_new)
    df_new = custom_fixes(df_new)

    return df_new.reset_index(drop=True)


def flatten_table(df: pd.DataFrame) -> pd.DataFrame:
    df_new = df.dropna(axis=1, how='all')
    rows = []

    for row in df_new.iterrows():
        rows.append(
            [cell for cell in row[1] if (
                pd.notna(cell) \
                and cell != "" \
                and cell != None
            )]
        )

    df_flat = pd.DataFrame.from_records(rows)
    df_flat = clean_table(df_flat)

    return df_flat.set_index(0, drop=True).transpose()


def flatten_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    for table_name, table in tables.items():
        tables[table_name] = flatten_table(table)

        tables[table_name] = tables[table_name].dropna(axis=1, how='all')
        tables[table_name] = tables[table_name].dropna(axis=0, how='all')
    return tables


# def consolidate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
def consolidate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    proces_indices = get_table_indices(df)
    tables = split_into_individual_tables(df, proces_indices)
    tables = flatten_tables(tables)

    df_consolidated = pd.concat(tables.values(), axis=0, ignore_index=True)
    
    df_consolidated.dropna(axis=1, how='all', inplace=True)

    return df_consolidated, tables


def extract_tables_from_pdf(pdf_path: Path, start_page: int = 0, end_page: int | None = None) -> pd.DataFrame:
    """
    Extract tables from a PDF file using pdfplumber.
    """
    end_page = end_page or start_page + 1

    print(f"{pdf_path=}, {start_page=}, {end_page=}")
    dfs = {}

    with pdfplumber.open(pdf_path) as pdf:
        df = pd.DataFrame()

        pages_to_extract = range(
            start_page, end_page
        )

        for page_number in pages_to_extract:
            print(f"Extracting table from page {page_number + 1}")

            page = pdf.pages[page_number]
            tables = page.extract_tables()

            for i, table in enumerate(tables):
                df = pd.DataFrame(table)

                with open(f"pages/output_page{page_number+1}_{i}.md", "w") as f:
                    f.write(df.to_markdown(index=False))
                    f.write("\n\n")

                df.to_csv(f"tables/output_table{page_number+1}_{i}.csv", index=False)
                dfs[f"page_{page_number + 1}_table_{i}"] = df
    
    combined_df = pd.concat(dfs.values(), ignore_index=True)

    return combined_df


def main():
    pdf_path = Path("__file__").parent / "Bijlage 7 - Doorvertaling Concernbrede selectielijst VWS voor IGJ V2.0 (1).pdf"
    df = extract_tables_from_pdf(pdf_path, 0, 31)

    # Consolidate tables
    df = consolidate_dataframe(df)

    df.to_csv("tables/processed_tables.csv", index=False)
    df.to_excel("tables/processed_tables.xlsx", index=False)

    # Export consolidated tables
    df.to_csv("tables/consolidated_tables.csv", index=False)
    df.to_excel("tables/consolidated_tables.xlsx", index=False)


if __name__ == "__main__":
    main()
