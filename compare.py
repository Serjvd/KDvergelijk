import streamlit as st
import PyPDF2
import pandas as pd
import difflib
import re
from io import BytesIO

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def preprocess_text(text):
    """Clean and preprocess the extracted text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]

def identify_sections(text):
    """Identify key sections in the document."""
    sections = {
        "kerntaken": [],
        "werkprocessen": [],
        "vakkennis": [],
        "vaardigheden": [],
        "beroepshouding": [],
        "profielen": []
    }
    
    # Find kerntaken (e.g., B1-K1, B1-K2)
    kerntaken_pattern = r'B\d+-K\d+[:\s]+([^\n]+)'
    kerntaken_matches = re.finditer(kerntaken_pattern, text)
    for match in kerntaken_matches:
        sections["kerntaken"].append(match.group(0))
    
    # Find werkprocessen (e.g., B1-K1-W1)
    werkprocessen_pattern = r'B\d+-K\d+-W\d+[:\s]+([^\n]+)'
    werkprocessen_matches = re.finditer(werkprocessen_pattern, text)
    for match in werkprocessen_matches:
        sections["werkprocessen"].append(match.group(0))
    
    # Find vakkennis en vaardigheden
    if "Vakkennis en vaardigheden" in text:
        vakkennis_section = text.split("Vakkennis en vaardigheden")[1].split("Voor")[0]
        vakkennis_items = re.findall(r'§\s*([^\n§]+)', vakkennis_section)
        
        for item in vakkennis_items:
            if item.strip().startswith("kan"):
                sections["vaardigheden"].append(item.strip())
            else:
                sections["vakkennis"].append(item.strip())
    
    # Find beroepshouding
    if "Typerende beroepshouding" in text:
        beroepshouding_section = text.split("Typerende beroepshouding")[1].split("Resultaat")[0]
        sections["beroepshouding"] = [beroepshouding_section.strip()]
    
    # Find profielen
    if "Profieldeel" in text:
        profielen_section = text.split("Profieldeel")[1].split("Basisdeel")[0] if "Basisdeel" in text.split("Profieldeel")[1] else text.split("Profieldeel")[1]
        sections["profielen"] = [profielen_section.strip()]
    
    return sections

def compare_sections(old_sections, new_sections):
    """Compare sections between old and new documents."""
    comparison_results = []
    
    # Compare kerntaken
    for i, old_kerntaak in enumerate(old_sections["kerntaken"]):
        old_code = re.search(r'(B\d+-K\d+)', old_kerntaak).group(1)
        old_description = old_kerntaak.split(":", 1)[1].strip() if ":" in old_kerntaak else old_kerntaak.split(old_code, 1)[1].strip()
        
        # Find matching kerntaak in new document
        matching_new = None
        for new_kerntaak in new_sections["kerntaken"]:
            if old_code in new_kerntaak:
                matching_new = new_kerntaak
                break
        
        if matching_new:
            new_description = matching_new.split(":", 1)[1].strip() if ":" in matching_new else matching_new.split(old_code, 1)[1].strip()
            if old_description != new_description:
                impact = f"Wijziging in kerntaak {old_code}. Dit kan impact hebben op de beroepspraktijk en examinering."
                comparison_results.append({
                    "Codering": old_code,
                    "OUD": old_description,
                    "NIEUW": new_description,
                    "Impact": impact,
                    "Pagina": f"OUD: {i+1}, NIEUW: {i+1}"
                })
        else:
            # Kerntaak removed in new document
            impact = f"Kerntaak {old_code} is verwijderd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": old_code,
                "OUD": old_description,
                "NIEUW": "Niet aanwezig in het nieuwe dossier",
                "Impact": impact,
                "Pagina": f"OUD: {i+1}, NIEUW: N.v.t."
            })
    
    # Check for new kerntaken in new document
    for i, new_kerntaak in enumerate(new_sections["kerntaken"]):
        new_code = re.search(r'(B\d+-K\d+)', new_kerntaak).group(1)
        
        # Check if this kerntaak exists in old document
        exists_in_old = False
        for old_kerntaak in old_sections["kerntaken"]:
            if new_code in old_kerntaak:
                exists_in_old = True
                break
        
        if not exists_in_old:
            new_description = new_kerntaak.split(":", 1)[1].strip() if ":" in new_kerntaak else new_kerntaak.split(new_code, 1)[1].strip()
            impact = f"Nieuwe kerntaak {new_code} toegevoegd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": new_code,
                "OUD": "Niet aanwezig in het oude dossier",
                "NIEUW": new_description,
                "Impact": impact,
                "Pagina": f"OUD: N.v.t., NIEUW: {i+1}"
            })
    
    # Similar comparisons for werkprocessen
    for i, old_wp in enumerate(old_sections["werkprocessen"]):
        old_code = re.search(r'(B\d+-K\d+-W\d+)', old_wp).group(1)
        old_description = old_wp.split(":", 1)[1].strip() if ":" in old_wp else old_wp.split(old_code, 1)[1].strip()
        
        # Find matching werkproces in new document
        matching_new = None
        for new_wp in new_sections["werkprocessen"]:
            if old_code in new_wp:
                matching_new = new_wp
                break
        
        if matching_new:
            new_description = matching_new.split(":", 1)[1].strip() if ":" in matching_new else matching_new.split(old_code, 1)[1].strip()
            if old_description != new_description:
                impact = f"Wijziging in werkproces {old_code}. Dit kan impact hebben op de beroepspraktijk en examinering."
                comparison_results.append({
                    "Codering": old_code,
                    "OUD": old_description,
                    "NIEUW": new_description,
                    "Impact": impact,
                    "Pagina": f"OUD: {i+1}, NIEUW: {i+1}"
                })
        else:
            # Werkproces removed in new document
            impact = f"Werkproces {old_code} is verwijderd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": old_code,
                "OUD": old_description,
                "NIEUW": "Niet aanwezig in het nieuwe dossier",
                "Impact": impact,
                "Pagina": f"OUD: {i+1}, NIEUW: N.v.t."
            })
    
    # Check for new werkprocessen in new document
    for i, new_wp in enumerate(new_sections["werkprocessen"]):
        new_code = re.search(r'(B\d+-K\d+-W\d+)', new_wp).group(1)
        
        # Check if this werkproces exists in old document
        exists_in_old = False
        for old_wp in old_sections["werkprocessen"]:
            if new_code in old_wp:
                exists_in_old = True
                break
        
        if not exists_in_old:
            new_description = new_wp.split(":", 1)[1].strip() if ":" in new_wp else new_wp.split(new_code, 1)[1].strip()
            impact = f"Nieuw werkproces {new_code} toegevoegd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": new_code,
                "OUD": "Niet aanwezig in het oude dossier",
                "NIEUW": new_description,
                "Impact": impact,
                "Pagina": f"OUD: N.v.t., NIEUW: {i+1}"
            })
    
    # Compare vakkennis
    for i, old_item in enumerate(old_sections["vakkennis"]):
        # Find closest match in new document
        closest_match = difflib.get_close_matches(old_item, new_sections["vakkennis"], n=1, cutoff=0.6)
        
        if closest_match:
            new_item = closest_match[0]
            if old_item != new_item:
                impact = "Wijziging in vakkennis. Dit kan impact hebben op de beroepspraktijk en examinering."
                comparison_results.append({
                    "Codering": f"Vakkennis-{i+1}",
                    "OUD": old_item,
                    "NIEUW": new_item,
                    "Impact": impact,
                    "Pagina": "N.v.t."
                })
        else:
            # Vakkennis item removed in new document
            impact = "Vakkennis item verwijderd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": f"Vakkennis-{i+1}",
                "OUD": old_item,
                "NIEUW": "Niet aanwezig in het nieuwe dossier",
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    # Check for new vakkennis items in new document
    for i, new_item in enumerate(new_sections["vakkennis"]):
        # Check if this item exists in old document (or something similar)
        exists_in_old = False
        for old_item in old_sections["vakkennis"]:
            if difflib.SequenceMatcher(None, old_item, new_item).ratio() > 0.6:
                exists_in_old = True
                break
        
        if not exists_in_old:
            impact = "Nieuwe vakkennis toegevoegd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": f"Vakkennis-Nieuw-{i+1}",
                "OUD": "Niet aanwezig in het oude dossier",
                "NIEUW": new_item,
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    # Similar comparisons for vaardigheden
    for i, old_item in enumerate(old_sections["vaardigheden"]):
        # Find closest match in new document
        closest_match = difflib.get_close_matches(old_item, new_sections["vaardigheden"], n=1, cutoff=0.6)
        
        if closest_match:
            new_item = closest_match[0]
            if old_item != new_item:
                impact = "Wijziging in vaardigheid. Dit kan impact hebben op de beroepspraktijk en examinering."
                comparison_results.append({
                    "Codering": f"Vaardigheid-{i+1}",
                    "OUD": old_item,
                    "NIEUW": new_item,
                    "Impact": impact,
                    "Pagina": "N.v.t."
                })
        else:
            # Vaardigheid item removed in new document
            impact = "Vaardigheid verwijderd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": f"Vaardigheid-{i+1}",
                "OUD": old_item,
                "NIEUW": "Niet aanwezig in het nieuwe dossier",
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    # Check for new vaardigheden in new document
    for i, new_item in enumerate(new_sections["vaardigheden"]):
        # Check if this item exists in old document (or something similar)
        exists_in_old = False
        for old_item in old_sections["vaardigheden"]:
            if difflib.SequenceMatcher(None, old_item, new_item).ratio() > 0.6:
                exists_in_old = True
                break
        
        if not exists_in_old:
            impact = "Nieuwe vaardigheid toegevoegd in het nieuwe dossier. Dit heeft impact op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": f"Vaardigheid-Nieuw-{i+1}",
                "OUD": "Niet aanwezig in het oude dossier",
                "NIEUW": new_item,
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    # Compare beroepshouding
    if old_sections["beroepshouding"] and new_sections["beroepshouding"]:
        old_bh = old_sections["beroepshouding"][0]
        new_bh = new_sections["beroepshouding"][0]
        
        if old_bh != new_bh:
            impact = "Wijziging in beroepshouding. Dit kan impact hebben op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": "Beroepshouding",
                "OUD": old_bh,
                "NIEUW": new_bh,
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    # Compare profielen
    if old_sections["profielen"] and new_sections["profielen"]:
        old_prof = old_sections["profielen"][0]
        new_prof = new_sections["profielen"][0]
        
        if old_prof != new_prof:
            impact = "Wijziging in profielen. Dit kan impact hebben op de beroepspraktijk en examinering."
            comparison_results.append({
                "Codering": "Profielen",
                "OUD": old_prof,
                "NIEUW": new_prof,
                "Impact": impact,
                "Pagina": "N.v.t."
            })
    
    return comparison_results

def main():
    st.set_page_config(page_title="Kwalificatiedossier Vergelijkingstool", page_icon="📊", layout="wide")
    
    st.title("Kwalificatiedossier Vergelijkingstool")
    st.write("""
    Upload twee kwalificatiedossiers (OUD en NIEUW) om de verschillen te analyseren.
    De tool identificeert wijzigingen in kerntaken, werkprocessen, vakkennis, vaardigheden, beroepshouding en profielen.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("OUD Kwalificatiedossier")
        old_file = st.file_uploader("Upload het OUDE kwalificatiedossier (PDF)", type=["pdf"])
    
    with col2:
        st.header("NIEUW Kwalificatiedossier")
        new_file = st.file_uploader("Upload het NIEUWE kwalificatiedossier (PDF)", type=["pdf"])
    
    if old_file and new_file:
        if st.button("Vergelijk Documenten"):
            with st.spinner("Bezig met analyseren van de documenten..."):
                # Extract text from PDFs
                old_text = extract_text_from_pdf(old_file)
                new_text = extract_text_from_pdf(new_file)
                
                # Identify sections in both documents
                old_sections = identify_sections(old_text)
                new_sections = identify_sections(new_text)
                
                # Compare sections
                comparison_results = compare_sections(old_sections, new_sections)
                
                # Create DataFrame
                df = pd.DataFrame(comparison_results)
                
                # Display results
                st.header("Vergelijkingsresultaten")
                st.dataframe(df)
                
                # Create Excel file for download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Vergelijking', index=False)
                    # Auto-adjust columns' width
                    worksheet = writer.sheets['Vergelijking']
                    for i, col in enumerate(df.columns):
                        # Find the maximum length of the column
                        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, max_len)
                
                output.seek(0)
                
                # Provide download button
                st.download_button(
                    label="Download Excel bestand",
                    data=output,
                    file_name="kwalificatiedossier_vergelijking.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Summary of key differences
                st.header("Samenvatting van belangrijke wijzigingen")
                
                # Kerntaken changes
                kerntaken_changes = [r for r in comparison_results if r["Codering"].startswith("B") and "K" in r["Codering"] and "-W" not in r["Codering"]]
                if kerntaken_changes:
                    st.subheader("Wijzigingen in kerntaken:")
                    for change in kerntaken_changes:
                        st.write(f"- **{change['Codering']}**: Van '{change['OUD']}' naar '{change['NIEUW']}'")
                
                # Werkprocessen changes
                werkprocessen_changes = [r for r in comparison_results if "-W" in r["Codering"]]
                if werkprocessen_changes:
                    st.subheader("Wijzigingen in werkprocessen:")
                    for change in werkprocessen_changes:
                        st.write(f"- **{change['Codering']}**: Van '{change['OUD']}' naar '{change['NIEUW']}'")
                
                # Vakkennis changes
                vakkennis_changes = [r for r in comparison_results if "Vakkennis" in r["Codering"]]
                if vakkennis_changes:
                    st.subheader("Wijzigingen in vakkennis:")
                    st.write(f"- {len(vakkennis_changes)} wijzigingen in vakkennis geïdentificeerd")
                
                # Vaardigheden changes
                vaardigheden_changes = [r for r in comparison_results if "Vaardigheid" in r["Codering"]]
                if vaardigheden_changes:
                    st.subheader("Wijzigingen in vaardigheden:")
                    st.write(f"- {len(vaardigheden_changes)} wijzigingen in vaardigheden geïdentificeerd")
                
                # Beroepshouding changes
                beroepshouding_changes = [r for r in comparison_results if "Beroepshouding" in r["Codering"]]
                if beroepshouding_changes:
                    st.subheader("Wijzigingen in beroepshouding:")
                    st.write("- Beroepshouding is gewijzigd")
                
                # Profielen changes
                profielen_changes = [r for r in comparison_results if "Profielen" in r["Codering"]]
                if profielen_changes:
                    st.subheader("Wijzigingen in profielen:")
                    st.write("- Profielen zijn gewijzigd")

if __name__ == "__main__":
    main()
