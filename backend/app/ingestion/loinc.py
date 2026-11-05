# LOINC codes used by the HL7 Genomics Reporting profile. Check them against the version a real lab
# feed targets before going live.
VARIANT_ASSESSMENT = "69548-6"
GENE_STUDIED = "48018-6"
DNA_CHANGE_HGVS = "48004-9"
CLINICAL_SIGNIFICANCE = "53037-8"
ALLELIC_STATE = "53034-5"

# LOINC is copyright Regenstrief Institute, Inc. and the LOINC Committee. See data_sources.md.
REPORTABLE = {"LA6668-3": "P", "LA26332-9": "LP", "LA26333-7": "VUS"}
# Named explicitly. A significance code that's in neither map is refused, because silently dropping
# a code we don't recognise could lose a pathogenic finding.
NOT_REPORTABLE = frozenset({"LA6675-8", "LA26334-5"})
ZYGOSITY = {"LA6706-1": "het", "LA6705-3": "hom", "LA6707-9": "hemi"}
