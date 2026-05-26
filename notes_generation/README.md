# Notes Generation - HVAC Service Report Automation

An n8n-based automation workflow that fetches job data from Airtable (Softr), generates AI-powered HVAC service reports, and emails them to customers.

## Overview

This project automates the process of:
1. **Polling** job submissions from Airtable every 15 minutes
2. **Structuring** raw technician notes and job data
3. **Generating** professional HVAC service reports using Claude AI
4. **Creating** PDF documents from Word templates
5. **Emailing** reports to customers

## Architecture

- **n8n**: Workflow orchestration engine (main container)
- **n8n Task Runners**: External Python and JavaScript runners for heavy processing
- **Docker**: Containerized deployment with LibreOffice for PDF conversion
- **Airtable**: Data source for job records
- **Claude API**: AI-powered report generation

## Prerequisites

- Docker & Docker Compose
- Airtable base with Jobs table
- Claude API key
- SMTP credentials for email

## File Structure

```
notes_generation/
├── docker-compose.yml              # n8n + task runners configuration
├── Dockerfile.runners              # Custom runner image with dependencies
├── n8n-task-runners.json          # Task runner configuration
├── automation_flow.json            # n8n workflow definition (Softr Jobs → AI Report → PDF Email)
├── create_pdf.py                   # Python script for DOCX to PDF conversion
├── n8n_files/
│   └── HVAC_Service_Report_Template.docx  # Word template for reports
└── n8n_data/                       # (runtime) n8n data and workflows
```

## Setup Instructions

### 1. Clone & Navigate

```bash
cd notes_generation
```

### 2. Environment Variables

Create or update the n8n data directory and set required environment variables in `docker-compose.yml`:

**Required variables** (add to n8n service environment):
- `AIRTABLE_API_KEY`: Your Airtable API key
- `AIRTABLE_BASE_ID`: Your Airtable base ID
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: For Claude AI integration
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`: Email settings

Example:
```yaml
environment:
  - AIRTABLE_API_KEY=pat_xxxxx
  - AIRTABLE_BASE_ID=appxxxxx
  - ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 3. Build & Start Containers

```bash
docker-compose up -d
```

This will:
- Build the custom runners image (installs LibreOffice, python-docx, docxtpl, lxml)
- Start n8n on `http://localhost:5678`
- Start task runners broker on `http://localhost:5679`

### 4. Import Workflow

1. Access n8n UI: `http://localhost:5678`
2. Create new workflow or import `automation_flow.json`
3. Configure variables:
   - Set API keys and credentials
   - Verify Airtable base ID and table names
4. Activate the workflow

### 5. Update the Word Template

Place your HVAC service report template at:
```
n8n_files/HVAC_Service_Report_Template.docx
```

The template should include placeholders for:
- Job information (number, title, date)
- Customer details (name, address, email)
- Equipment details
- Work performed
- Parts and labor
- Customer-facing summary

## Key Components

### automation_flow.json

The workflow performs these steps:

1. **⏱ Poll Every 15 Min** - Scheduled trigger runs every 15 minutes
2. **📋 Fetch Jobs (Airtable)** - Retrieves jobs with status "Submitted" that have notes
3. **🗂 STEP 1: Structure & Map Fields** - Python code transforms raw Airtable fields into clean schema
4. **🤖 STEP 2: Generate Report (Claude)** - AI generates professional report from technician notes
5. **📄 STEP 3: Create PDF** - Fills Word template and converts to PDF
6. **📧 STEP 4: Email Report** - Sends PDF to customer email
7. **✅ Update Status** - Marks job as "Processed" in Airtable

### Dockerfile.runners

Custom Docker image based on `n8nio/runners:2.20.9` with:
- **LibreOffice**: For DOCX → PDF conversion
- **Python libraries**:
  - `python-docx`: Word document manipulation
  - `docxtpl`: Template-based document generation
  - `lxml`: XML processing
  - `docx2pdf`: DOCX conversion (fallback)

### n8n-task-runners.json

Configures task runners:
- **Python Runner**: Executes Python code nodes with external library access
- **JavaScript Runner**: Executes JavaScript code nodes
- Both runners mount volumes for file access (`/files` and `/home/node/.n8n`)

### create_pdf.py

Standalone Python utility for PDF generation:
- Reads `.docx` template
- Locates placeholder sections by Heading 1 style
- Fills template with job data
- Removes sections with empty data (Equipment Details, Parts and Labor)
- Converts to PDF via LibreOffice CLI

## Workflow Data Flow

```
Airtable (Jobs)
    ↓
Fetch Jobs (HTTP request)
    ↓
Structure Data (Python code node)
    ↓
Generate Report (Claude AI)
    ↓
Fill PDF Template (Python - create_pdf.py)
    ↓
Send Email
    ↓
Update Airtable Status
```

## Development

### Viewing Logs

```bash
docker-compose logs -f n8n
docker-compose logs -f n8n-runners
```

### Debugging Workflows

1. Access n8n UI at `http://localhost:5678`
2. Open the workflow for editing
3. Use the test execution panel to preview node outputs
4. Check task runner logs for Python/JavaScript errors

### Modifying the Workflow

1. Edit `automation_flow.json` directly, or
2. Make changes in n8n UI and export the workflow JSON

### Testing the PDF Generation

```bash
docker exec n8n-runners python create_pdf.py \
  --template /files/HVAC_Service_Report_Template.docx \
  --output /files/test_report.pdf
```

## Troubleshooting

### LibreOffice Conversion Fails
- Check if LibreOffice is running: `docker exec n8n-runners libreoffice --version`
- Verify DOCX template is valid: try opening it in Word/LibreOffice
- Check file permissions on `/files` volume

### Python Dependencies Missing
- Rebuild runners image: `docker-compose build n8n-runners`
- Verify `n8n-task-runners.json` has correct `N8N_RUNNERS_EXTERNAL_ALLOW` setting

### Airtable Connection Issues
- Verify `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` are correct
- Check Airtable base has a "Jobs" table with expected columns
- Test HTTP endpoint manually using Postman

### PDF Not Generated
- Ensure Word template exists at `n8n_files/HVAC_Service_Report_Template.docx`
- Check n8n logs for Python errors during template filling
- Verify LibreOffice has write permissions to output directory

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AIRTABLE_API_KEY` | Yes | API key from Airtable account settings |
| `AIRTABLE_BASE_ID` | Yes | Base ID from Airtable URL: `airtable.com/base/{BASE_ID}` |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for report generation |
| `SMTP_HOST` | Yes | Email server hostname (e.g., `smtp.gmail.com`) |
| `SMTP_PORT` | Yes | Email server port (typically 587 or 465) |
| `SMTP_USER` | Yes | Email account username |
| `SMTP_PASS` | Yes | Email account password or app token |
| `GENERIC_TIMEZONE` | No | Timezone for scheduling (default: `Australia/Perth`) |
| `N8N_RUNNERS_AUTH_TOKEN` | No | Secure token for runner authentication |

## Customization

### Adding More Job Fields

1. Update Airtable base with new columns
2. Add fields to the Python structuring node in `automation_flow.json`
3. Update Word template with new placeholders
4. Modify Claude prompt to include new fields in report

### Changing Polling Interval

Edit the "⏱ Poll Every 15 Min" node:
- Change `minutesInterval` value from `15` to desired minutes

### Custom PDF Template

Replace `n8n_files/HVAC_Service_Report_Template.docx` with your template:
- Maintain Heading 1 styles for section headers
- Use field names that match the workflow's structured data
- Test template rendering before deploying

## Performance Considerations

- Polling every 15 minutes; adjust as needed for load
- LibreOffice conversion takes ~2-3 seconds per PDF
- Claude API calls add latency (typically 5-10 seconds)
- For high volume, consider increasing runner replicas

## Security Notes

- Store credentials in environment variables, not in workflows
- Use `N8N_RUNNERS_AUTH_TOKEN` to secure runner-broker communication
- Restrict file access with `N8N_RESTRICT_FILE_ACCESS_TO=/files`
- Consider using Airtable OAuth instead of API keys in production
- Rotate SMTP credentials and API keys regularly

## Support & Further Documentation

- [n8n Documentation](https://docs.n8n.io/)
- [Airtable API Reference](https://airtable.com/api)
- [Claude API Documentation](https://docs.anthropic.com/)
- [LibreOffice CLI Reference](https://help.libreoffice.org/latest/en/index.html)
