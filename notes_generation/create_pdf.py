#!/usr/bin/env python3
"""
HVAC Service Report generator.

Reads a .docx template, fills every section by locating the nearest
preceding Heading 1 paragraph (so data always lands in the right place),
then converts the result to PDF via LibreOffice.

Behaviour:
  - Work Performed lines: trailing "out." sentences are stripped per line
  - "Equipment Details" heading + all its paragraphs removed when every
    field value is empty
  - "Parts and Labor" heading + all its paragraphs removed when there are
    no parts used AND no missing-info items
  - "Customer-facing summary" label renamed to "Summary" and rendered bold
  - Work Performed content written as proper separate Word paragraphs
"""
import os
import subprocess

from docxtpl import DocxTemplate

# CONFIGURATION  –  edit these paths if needed
TEMPLATE_PATH = "/home/node/.n8n/HVAC_Service_Report_Template.docx"   # source template
OUTPUT_DIR    = "/home/node/.n8n/"               # directory for .docx and .pdf output
LIBREOFFICE   = "libreoffice"         # must be on PATH

SAMPLE_JOB = _item["json"]

print(SAMPLE_JOB)

# LibreOffice -> PDF
def docx_to_pdf(docx_path: str, out_dir: str) -> str:
    cmd = [
        LIBREOFFICE,
        "--headless", "--nologo", "--nofirststartwizard",
        "--convert-to", "pdf",
        "--outdir", out_dir,
        docx_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed.\nCMD: {' '.join(cmd)}\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    base    = os.path.splitext(os.path.basename(docx_path))[0]
    pdf_out = os.path.join(out_dir, base + ".pdf")
    if not os.path.exists(pdf_out):
        raise RuntimeError(f"Expected PDF not found: {pdf_out}")
    print(f"[OK] PDF saved  -> {pdf_out}")
    return pdf_out

def sanitize_keys(obj):
    if isinstance(obj, dict):
        return {k.replace(" ", "_").lower(): sanitize_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_keys(i) for i in obj]
    return obj

def fill_template_2(template_path: str, job: dict, output_docx: str) -> None:
    doc = DocxTemplate(template_path)
    doc.render(job)
    doc.save(output_docx)

# Entry point
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    job = sanitize_keys(SAMPLE_JOB)

    job_number  = (job.get("job_number") or "JOB").replace("/", "-")
    print(job_number)
    output_base = f"service_report_{job_number}"
    output_docx = os.path.join(OUTPUT_DIR, output_base + ".docx")

    # fill_template(TEMPLATE_PATH, job, ai, output_docx)
    fill_template_2(TEMPLATE_PATH, job, output_docx)
    pdf_path = docx_to_pdf(output_docx, OUTPUT_DIR)

    job_number = job.get("job_number","")

    result = {
        "pdf_path": pdf_path,
        "docx_path": output_docx
    }
    return result

return main()
