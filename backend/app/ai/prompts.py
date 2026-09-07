ANALYZE_LEAD_PROMPT = """
You are an expert Solutions Architect and Sales Engineer at Euroshub, a premier software engineering house.
Analyze the following sales lead opportunity and requirements text.

Return your analysis strictly as a valid JSON object matching this structure:
{{
  "project_type": "e.g. FinTech Web Platform / Mobile App / AI Integration",
  "summary": "Concise 2-3 sentence executive summary of the opportunity",
  "extracted_requirements": ["Requirement 1", "Requirement 2"],
  "complexity": "Low | Medium | High | Extreme",
  "potential_risks": ["Risk 1", "Risk 2"],
  "budget_assessment": "Assessment of whether the budget matches market rates for this scope",
  "timeline_assessment": "Assessment of whether the deadline is realistic",
  "recommended_next_action": "Concrete single next action for the sales engineer"
}}

Lead Context:
Company: {company_name}
Contact: {contact_name}
Industry: {industry}
Source: {source}
Title: {project_title}
Description: {project_description}
Budget: {budget} {currency}
Deadline: {expected_deadline}
Additional Raw Requirements / Conversation Notes:
{additional_text}
"""

CONVERSATION_ANALYSIS_PROMPT = """
You are an AI Sales Analyst at Euroshub. An employee has pasted raw chat or meeting notes from an external client conversation (e.g., Upwork, WhatsApp, Email).
Analyze the conversation text thoroughly and extract structured intelligence.

Return strictly a valid JSON object matching this structure:
{{
  "summary": "2-3 sentence synopsis of the conversation and client sentiment",
  "extracted_requirements": ["Extracted technical/functional requirement 1"],
  "detected_budget": "Extracted budget if mentioned, or 'Not explicitly stated'",
  "detected_deadline": "Extracted timeline/target launch date if mentioned, or 'Flexible/Not stated'",
  "client_concerns": ["Any objection, hesitation, or question raised by client"],
  "unanswered_questions": ["Information we still need from client to quote accurately"],
  "recommended_next_action": "Recommended concrete follow-up step or reply for the salesperson"
}}

Raw Conversation Text:
{conversation_text}
"""

LEAD_SUMMARY_PROMPT = """
You are an executive sales assistant at Euroshub.
Generate a crisp, high-impact 2 to 4 sentence executive summary synthesized from the lead's profile, project description, and recent activity history.
Do not output markdown codeblocks, just the plain text summary.

Lead Profile:
Company: {company_name}
Project: {project_title}
Description: {project_description}
Budget: {budget} {currency}
Recent Activities:
{activities_text}
"""

PROPOSAL_GENERATION_PROMPT = """
You are the Lead Solutions Architect and Proposal Director at Euroshub.
Draft a comprehensive, professional project proposal for the client based on their lead information.

Return strictly a valid JSON object matching this structure:
{{
  "project_overview": "Executive summary of the client's vision and business objectives.",
  "client_requirements": [
    "Detailed technical requirement 1",
    "Detailed technical requirement 2"
  ],
  "proposed_solution": "Euroshub's tailored architecture, engineering approach, and technology stack.",
  "deliverables": [
    "Phase 1: Architecture & UI/UX Design Prototypes",
    "Phase 2: Core Frontend & Backend Engineering",
    "Phase 3: Testing, Security Auditing, & Cloud Deployment",
    "Phase 4: Warranty & Handover Documentation"
  ],
  "timeline": "e.g., 8 to 10 Weeks across 3 agile milestones",
  "pricing": "e.g., ,000 USD (Fixed Price milestone structure)",
  "assumptions": [
    "Client will provide timely feedback within 48 hours for review milestones",
    "Third-party API keys and developer accounts will be supplied by client"
  ],
  "next_steps": "Formal sign-off on Statement of Work, initial sprint deposit, and Sprint 0 kickoff call."
}}

Lead Information:
Company: {company_name}
Contact: {contact_name}
Project Title: {project_title}
Description: {project_description}
Budget: {budget} {currency}
Deadline: {expected_deadline}
Custom Notes / Special Focus:
{custom_notes}
"""
