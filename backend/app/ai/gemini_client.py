import os
import json
import re
from typing import Dict, Any, Optional
from ..utils.config import settings
from .prompts import (
    ANALYZE_LEAD_PROMPT,
    CONVERSATION_ANALYSIS_PROMPT,
    LEAD_SUMMARY_PROMPT,
    PROPOSAL_GENERATION_PROMPT
)

def clean_json_text(text: str) -> str:
    cleaned = text.strip()
    # Remove markdown code blocks like `json ... ` or ` ... `
    if cleaned.startswith("`"):
        cleaned = re.sub(r"^`(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*`$", "", cleaned)
    return cleaned.strip()

class GeminiAIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.client = None
        self._init_sdk()

    def _init_sdk(self):
        if not self.api_key:
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
        except Exception as e:
            print(f"[AI] Error initializing Gemini SDK: {e}")

    def generate_content(self, prompt: str) -> str:
        # Re-check key in case it was updated in environment
        if not self.api_key and os.getenv("GEMINI_API_KEY"):
            self.api_key = os.getenv("GEMINI_API_KEY")
            self._init_sdk()

        if self.client:
            try:
                response = self.client.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"[AI] Gemini API call failed: {e}")
                raise RuntimeError(f"Gemini API call failed: {e}")
        
        # If no API key is provided, return intelligent deterministic simulation based on inputs
        return ""

    def analyze_lead(self, lead_data: Dict[str, Any], additional_text: Optional[str] = None) -> Dict[str, Any]:
        prompt = ANALYZE_LEAD_PROMPT.format(
            company_name=lead_data.get("company_name", ""),
            contact_name=lead_data.get("contact_name", ""),
            industry=lead_data.get("industry", "Technology"),
            source=lead_data.get("source", "Upwork"),
            project_title=lead_data.get("project_title", "Custom Software"),
            project_description=lead_data.get("project_description", ""),
            budget=lead_data.get("budget", 0.0),
            currency=lead_data.get("currency", "USD"),
            expected_deadline=lead_data.get("expected_deadline", "Flexible"),
            additional_text=additional_text or "None provided"
        )

        try:
            raw_text = self.generate_content(prompt)
            if raw_text:
                cleaned = clean_json_text(raw_text)
                return json.loads(cleaned)
        except Exception as e:
            print(f"[AI] Live call error: {e}, using heuristic fallback analysis")

        # Heuristic intelligent analyzer fallback
        budget = float(lead_data.get("budget") or 0)
        curr = lead_data.get("currency", "USD")
        company = lead_data.get("company_name", "Client")
        title = lead_data.get("project_title") or "Software Project"
        desc = lead_data.get("project_description") or ""

        reqs = []
        if "auth" in (desc + title).lower() or "user" in (desc + title).lower():
            reqs.append("User authentication & role-based access control (RBAC)")
        if "api" in (desc + title).lower() or "backend" in (desc + title).lower():
            reqs.append("Secure REST/GraphQL API layer with high throughput")
        if "mobile" in (desc + title).lower() or "app" in (desc + title).lower():
            reqs.append("Cross-platform responsive client application")
        if not reqs:
            reqs = [
                f"Core workflow automation for {company}",
                "Responsive UI/UX dashboard & reporting",
                "Cloud deployment with monitoring and automated backups"
            ]

        return {
            "project_type": f"{lead_data.get('industry', 'Custom')} Web Application",
            "summary": f"Opportunity with {company} for '{title}'. Target budget is {curr} {budget:,.2f}. High alignment with Euroshub's engineering strengths.",
            "extracted_requirements": reqs,
            "complexity": "High" if budget > 30000 else ("Medium" if budget >= 10000 else "Low"),
            "potential_risks": [
                "Scope expansion during user acceptance testing",
                "Third-party API integration stability and rate limits"
            ],
            "budget_assessment": f"Budget of {curr} {budget:,.2f} is viable for MVP and phase 1 delivery.",
            "timeline_assessment": "Timeline appears feasible with 2-3 dedicated Euroshub engineers.",
            "recommended_next_action": "Schedule technical scoping call and provide formal milestone proposal."
        }

    def generate_summary(self, lead_data: Dict[str, Any], activities: list) -> str:
        act_texts = []
        for a in activities[:5]:
            act_texts.append(f"- [{a.get('type')}] {a.get('title')}: {a.get('description', '')}")
        
        prompt = LEAD_SUMMARY_PROMPT.format(
            company_name=lead_data.get("company_name", ""),
            project_title=lead_data.get("project_title", ""),
            project_description=lead_data.get("project_description", ""),
            budget=lead_data.get("budget", 0.0),
            currency=lead_data.get("currency", "USD"),
            activities_text="\n".join(act_texts) if act_texts else "No prior activities logged."
        )

        try:
            raw = self.generate_content(prompt)
            if raw and len(raw.strip()) > 10:
                return raw.strip()
        except Exception as e:
            print(f"[AI] Summary error: {e}")

        company = lead_data.get("company_name", "Client")
        title = lead_data.get("project_title", "software solution")
        budget = float(lead_data.get("budget", 0) or 0)
        curr = lead_data.get("currency", "USD")
        return f"{company} is seeking an engineering partner for '{title}' with a target budget of {curr} {budget:,.2f}. The opportunity is currently in the {lead_data.get('status', 'NEW')} stage with active stakeholder engagement."

    def analyze_conversation(self, conversation_text: str) -> Dict[str, Any]:
        prompt = CONVERSATION_ANALYSIS_PROMPT.format(conversation_text=conversation_text)

        try:
            raw = self.generate_content(prompt)
            if raw:
                cleaned = clean_json_text(raw)
                return json.loads(cleaned)
        except Exception as e:
            print(f"[AI] Conversation analysis error: {e}")

        # Heuristic parser
        reqs = []
        lines = conversation_text.split("\n")
        for line in lines:
            line_clean = line.strip()
            if any(k in line_clean.lower() for k in ["need", "want", "feature", "must", "require", "build", "integrate"]):
                reqs.append(line_clean[:120])
        if not reqs:
            reqs = ["Deliver robust web application frontend & backend", "Integrate secure user authentication", "Provide cloud hosting configuration"]

        return {
            "summary": f"Extracted conversation covering {len(lines)} message lines. The client discussed feature scope, implementation milestones, and delivery expectations.",
            "extracted_requirements": reqs[:6],
            "detected_budget": "Mentioned during conversation" if "$" in conversation_text or "budget" in conversation_text.lower() else "Not explicitly stated",
            "detected_deadline": "Specified in chat" if "month" in conversation_text.lower() or "week" in conversation_text.lower() or "deadline" in conversation_text.lower() else "Flexible/To be confirmed",
            "client_concerns": [
                "Timeline feasibility and agile sprint updates",
                "Post-launch warranty and bug-fix support period"
            ],
            "unanswered_questions": [
                "Exact third-party API credentials and sandbox access",
                "Final design assets (Figma/Adobe XD) availability"
            ],
            "recommended_next_action": "Send summary bullet points and confirm milestone payment schedule."
        }

    def generate_proposal(self, lead_data: Dict[str, Any], custom_notes: Optional[str] = None) -> Dict[str, Any]:
        prompt = PROPOSAL_GENERATION_PROMPT.format(
            company_name=lead_data.get("company_name", "Client"),
            contact_name=lead_data.get("contact_name", "Partner"),
            project_title=lead_data.get("project_title", "Enterprise Software Solution"),
            project_description=lead_data.get("project_description", ""),
            budget=lead_data.get("budget", 0.0),
            currency=lead_data.get("currency", "USD"),
            expected_deadline=lead_data.get("expected_deadline", "Flexible"),
            custom_notes=custom_notes or "None"
        )

        try:
            raw = self.generate_content(prompt)
            if raw:
                cleaned = clean_json_text(raw)
                return json.loads(cleaned)
        except Exception as e:
            print(f"[AI] Proposal generation error: {e}")

        company = lead_data.get("company_name", "Client")
        title = lead_data.get("project_title") or "Software Platform"
        budget = float(lead_data.get("budget", 0) or 0)
        curr = lead_data.get("currency", "USD")

        return {
            "project_overview": f"Euroshub is pleased to propose the design, development, and deployment of {title} for {company}. Our solution provides a high-performance, scalable foundation built with modern cloud-native technologies.",
            "client_requirements": [
                f"Scalable architecture tailored for {company}'s core operations",
                "Intuitive, modern responsive user interface optimized for desktop and mobile",
                "Secure REST API backend with automated database backups",
                "Comprehensive administrative dashboard and analytics reporting"
            ],
            "proposed_solution": "We recommend a React + TypeScript frontend paired with a high-performance Python FastAPI backend and PostgreSQL database, hosted on secure cloud infrastructure with CI/CD automation.",
            "deliverables": [
                "Sprint 1: System Architecture & Interactive UI/UX Prototypes",
                "Sprint 2: Core Business Logic, Database Schemas, & API Development",
                "Sprint 3: Frontend Integration, Quality Assurance, & Performance Testing",
                "Sprint 4: Cloud Deployment, Security Audit, & 90-Day Warranty Support"
            ],
            "timeline": "8 to 10 Weeks across 4 structured milestones",
            "pricing": f"{curr} {budget:,.2f} (Fixed Price distributed across sprint milestones)",
            "assumptions": [
                "Stakeholder feedback provided within 48 hours of milestone submission",
                "Client supplies necessary brand assets and third-party API accounts"
            ],
            "next_steps": "Approve this proposal draft, finalize Statement of Work, and schedule Sprint 0 kickoff workshop."
        }

ai_service = GeminiAIService()
