## Plan: Raraa Data Management PRD

### Overview
Raraa Data Management is an integrated invoice reconciliation ecosystem designed for finance teams, built as a mobile-friendly web application with a polished dark-themed interface. It combines invoice upload, split-and-process automation, reconciliation analysis, PIC assignment, report generation, and action tracking into a single workflow.

Developed by Rad Tech Ecosystem.

### Vision
Create a seamless, easy-to-understand reconciliation platform that transforms Excel-based invoice data into actionable finance intelligence with visual dashboards, automated alerts, and audit-ready reports.

### Brand and Style
- Name: Raraa Data Management
- Tagline: Develop By Rad Tech Ecosystem
- Color palette:
  - Primary: Black, blue, white
  - Secondary: light gray
  - Accent: purple
- UI tone: modern, clean, professional, high-contrast, accessible
- Layout: responsive mobile-first design

### Target Users
- Finance staff handling invoice reconciliation
- AP/AR analysts doing GL vs billing review
- Team leads tracking discrepancies and PIC ownership
- Managers requiring summary dashboards and follow-up action items

### Core Goals
1. Provide fast upload and validation for Excel invoices.
2. Automate file splitting, data normalization, and reconciliation.
3. Surface discrepancies clearly with status, values, and accountable PIC.
4. Enable report export and communication via email/Slack.
5. Give users a visual process map and a unified report dashboard.
6. Keep UX simple for both desktop and mobile.

### User Problems Solved
- Manual invoice reconciliation across multiple files.
- Unclear responsibility for follow-up tasks.
- Lack of visible discrepancy status.
- No single dashboard for process progress and summary metrics.
- Difficulty generating audit-ready reports.

### Product Scope
#### Included
- Excel upload and validation
- Split-to-CSV processing
- Invoice extraction and normalization
- GL vs Billing reconciliation
- Discrepancy classification: match, mismatch, missing
- PIC assignment via lookup matrix
- Report generation in HTML/CSV
- Dashboard with charts and status cards
- Interactive process mindmap
- Notifications via email/Slack
- Audit trail for upload history and processing steps
- Mobile-responsive pages and controls

#### Excluded
- Full SAP API integration beyond simulated query workflow
- Advanced AI prompt builder UI
- Multi-tenant enterprise permissions
- In-app PDF generation beyond HTML export templates

### Key Features
#### 1. Upload & Validation
- File input for `.xlsx` invoice files
- Instant validation summary for required sheets and data format
- Error feedback in a compact card
- Upload history with timestamp, status, and record count

#### 2. Split & Process
- Manual or automatic split button to convert workbook sheets into CSV
- Progress stepper showing "Upload", "Split", "Reconcile", "Generate Report"
- Log panel for each stage with success and warning messages

#### 3. Reconciliation Engine
- Normalizes invoice numbers, dates, amounts
- Compares GL vs Billing and flags discrepancies
- Supports missing invoice detection
- Shows status badges: Green (Match), Yellow (Review), Red (Discrepancy)

#### 4. PIC Assignment
- Lookup PIC from Google Sheets-like matrix by invoice year or region
- Displays assigned owner and contact channel
- Enables follow-up actions with email/Slack suggestion

#### 5. Unified Report View
- Summary cards for invoice count, matched value, discrepancy total, unresolved items
- Chart section with distribution, top discrepancies, and trend comparisons
- Top 5 discrepancy table with invoice ID, value, issue, PIC, and next step
- Export controls for CSV and HTML report

#### 6. Interactive Mindmap Dashboard
- Visual flow nodes for Upload, Split, Reconcile, Report
- Node state colors: green, yellow, red
- Tap/click nodes to reveal stage detail and history
- Mobile-friendly collapsible flow diagram section

#### 7. Automation & Notifications
- Auto-generate professional follow-up suggestions using AI chain
- Send alerts to email or Slack for outstanding discrepancies
- Notify assigned PIC when issue status changes

#### 8. Audit Trail
- Store upload history and processing details
- Link data source version to report generation
- Show user actions and timestamps for traceability

### User Flows
#### Flow 1: Reconciliation Run
1. User uploads invoice Excel
2. System validates file and shows summary
3. User clicks "Process"
4. System splits sheets to CSV and normalizes data
5. Reconciliation engine compares values and assigns statuses
6. PIC matrix lookup determines owner
7. Dashboard updates with summary and charts
8. User reviews discrepancies and exports report

#### Flow 2: Follow-Up & Action
1. User views discrepancy table
2. User selects item and sees PIC owner
3. System suggests email/Slack message
4. User sends notification or downloads report

### UI Mockup Description
#### Homepage / Dashboard
- Top header with brand name, tagline, and accent purple ribbon
- Primary status cards: Total Invoices, Matched, Discrepancies, Missing
- Left column for upload control and process steps
- Right column for charts and timeline summary
- Bottom section with mindmap and report table

#### Upload Panel
- Black background card with blue button and white text
- File selector, validation summary, and big action button
- Compact mobile layout with stacked controls

#### Process Stepper
- Horizontal progress bar on desktop, vertical on mobile
- Icons for each stage with state color and description
- Real-time log entries in a collapsible panel

#### Discrepancy Report Page
- Filterable search bar and tabbed status view
- Table rows with purple accent highlighting important values
- Action buttons for follow-up and export
- Badge chips for issue type and PIC assignment

#### Mindmap Page
- Dark panel with node cards and connecting lines
- Mobile collapsible sections: Flow, Details, Logs
- Node detail drawer opens with processing summary and next steps

#### Mobile Layout
- Single-column stack for cards, charts, and tables
- Large tap targets and sticky action bar for key actions
- Responsive collapse for mindmap and logs
- Clear iconography and consistent spacing

### Technical Architecture
- Backend: Python Flask
- Data processing: Pandas, NumPy
- Storage: file system for raw/split/processed data
- External integration: OpenAI GPT API, Google Sheets API, Gmail/Slack webhook
- Frontend: HTML, CSS, JavaScript, Chart.js, Mermaid.js
- Output formats: CSV, HTML report, export-ready dashboard

### Required Pages
- Dashboard (summary + upload + mindmap)
- Reconciliation report page
- Invoice detail view with PIC and follow-up actions
- History/Audit page
- Settings / Integration page for notification channels

### Non-Functional Requirements
- Mobile-friendly: responsive CSS, accessible tap zones, stackable layout
- Performance: upload and split operations complete within seconds for normal dataset size
- Clarity: plain Bahasa Indonesia labels with concise explanations
- Consistency: black/blue/white/light gray palette with purple accent
- Accessibility: readable contrast, keyboard friendly controls

### Acceptance Criteria
- User can upload `.xlsx` and receive validation feedback
- User can run processing and see stage progress
- Dashboard displays summary cards, charts, and mindmap
- Discrepancies are classified and assigned PIC
- User can export report data to CSV/HTML
- UI works on mobile width and desktop width without layout breakage
- Brand name and tagline appear clearly in header

### Success Metrics
- Reduced manual reconciliation time
- Faster identification of discrepancies
- Improved accountability through PIC assignment
- Higher report generation completion rate
- Strong mobile adoption for finance users on the go

### Notes
- A polished mockup should use the black-blue-white theme with purple accent touches on buttons, badges, and highlights.
- Keep interactions simple: upload, process, review, export.
- The mindmap is a visual reassurance layer, not the only navigation.
