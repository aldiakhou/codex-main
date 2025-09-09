"""
Analysis Agent implementation using Pocket Flow
Provides data analysis and insight generation capabilities
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base import StructuredOutputAgent, AgentFactory
from mcp_agents_orchestrator.__main__ import (
    exec_approval_request,
    exec_command_begin,
    exec_command_output_delta,
    exec_command_end,
    apply_patch_approval_request,
    patch_apply_begin,
    patch_apply_end,
    get_submission_id_for_call,
    wait_for_decision,
)
import os
import uuid
from ..core.models import AIAgentRequest
from ..core.logging import get_logger

logger = get_logger(__name__)

# Define output model for analysis
class AnalysisOutput(BaseModel):
    """Structured output for analysis results"""
    summary: str = Field(description="Executive summary of the analysis")
    key_findings: List[Dict[str, Any]] = Field(description="List of key findings with supporting data")
    patterns: List[str] = Field(description="Identified patterns or trends")
    insights: List[Dict[str, str]] = Field(description="Actionable insights derived from analysis")
    recommendations: List[str] = Field(description="Recommendations based on analysis")
    confidence_level: str = Field(description="Overall confidence in the analysis: high, medium, or low")
    limitations: List[str] = Field(description="Limitations or caveats of the analysis")


class AnalysisAgent(StructuredOutputAgent):
    """AI Agent for data analysis and insight generation using Pocket Flow"""
    
    def __init__(self):
        instructions = """You are an expert data analyst and insight generator capable of analyzing complex information and extracting meaningful patterns.

CAPABILITIES:
- Analyze structured and unstructured data
- Identify patterns, trends, and anomalies
- Generate actionable insights
- Provide statistical analysis when applicable
- Create clear visualizations descriptions
- Offer strategic recommendations

ANALYSIS FRAMEWORK:
1. DATA UNDERSTANDING:
   - Assess data quality and completeness
   - Identify data types and structures
   - Recognize potential biases or limitations

2. EXPLORATORY ANALYSIS:
   - Examine distributions and relationships
   - Identify outliers and anomalies
   - Discover patterns and correlations

3. DEEP ANALYSIS:
   - Apply appropriate analytical techniques
   - Test hypotheses when relevant
   - Quantify relationships and impacts

4. INSIGHT GENERATION:
   - Transform findings into actionable insights
   - Connect analysis to business/practical implications
   - Prioritize insights by impact and feasibility

5. RECOMMENDATION DEVELOPMENT:
   - Propose evidence-based actions
   - Consider implementation feasibility
   - Anticipate potential challenges

GUIDELINES:
1. Be objective and data-driven
2. Clearly distinguish between correlation and causation
3. Acknowledge uncertainty and limitations
4. Provide confidence levels for findings
5. Use clear, non-technical language when possible
6. Support conclusions with evidence

For each analysis, provide:
- Executive summary of findings
- Detailed key findings with evidence
- Identified patterns and trends
- Actionable insights
- Strategic recommendations
- Confidence assessment
- Analysis limitations"""

        super().__init__(
            name="Analysis Agent",
            instructions=instructions,
            output_model=AnalysisOutput,
            temperature=0.3  # Lower temperature for analytical precision
        )
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for analysis"""
        data = request.context.get('data', 'No data provided')
        analysis_type = request.context.get('analysis_type', 'general')
        focus_areas = request.context.get('focus_areas', [])
        
        input_text = f"""Analysis Request:

DATA/CONTENT TO ANALYZE:
{data}

ANALYSIS TYPE: {analysis_type}
FOCUS AREAS: {', '.join(focus_areas) if focus_areas else 'Comprehensive analysis'}

Additional Context: {request.context.get('additional_context', 'None')}

Task: Perform a thorough analysis of the provided data/content.

Analysis Approach:
1. Understand the data structure and content
2. Apply appropriate analytical techniques
3. Identify key patterns and insights
4. Generate actionable recommendations

Focus on:
- Identifying meaningful patterns
- Extracting actionable insights
- Providing evidence-based recommendations
- Assessing confidence in findings"""
        
        return input_text

    async def process(self, request: AIAgentRequest):
        # Run the base structured-output analysis first
        base_result = await super().process(request)

        # Optional demo: run exec + patch approvals after analysis when requested
        demo = bool(request.context.get('demo_exec_patch') or request.context.get('demo'))
        if not demo:
            return base_result

        cwd = request.cwd or os.getcwd()
        # --- Exec phase (demo) ---
        exec_call = f"exec_{uuid.uuid4().hex[:8]}"
        exec_approval_request(exec_call, ["echo", "Analysis complete"], cwd, reason="Write analysis summary to file")
        sub_id = get_submission_id_for_call(exec_call)
        decision = wait_for_decision(sub_id or "", 120.0)
        if decision in ("approved", "approved_for_session"):
            exec_command_begin(exec_call, ["echo", "Analysis complete"], cwd)
            exec_command_output_delta(exec_call, "stdout", b"Analysis complete\n")
            exec_command_end(exec_call, 0, stdout="Analysis complete\n", formatted_output="Analysis complete\n", duration_ms=20)
        else:
            # Do not proceed to patch if exec was denied
            return {"analysis": base_result, "demo": {"exec_decision": decision or "timeout"}}

        # --- Patch phase (demo) ---
        patch_call = f"patch_{uuid.uuid4().hex[:8]}"
        file_path = os.path.join(cwd, "ANALYSIS_SUMMARY.md")
        content_lines = ["# Analysis Summary\n\n"]
        try:
            summary = getattr(base_result, 'summary', None) or base_result.get('summary')
        except Exception:
            summary = None
        if summary:
            content_lines.append(summary + "\n")
        content = "".join(content_lines) if content_lines else "Analysis complete.\n"
        changes = {file_path: {"Add": {"content": content}}}
        apply_patch_approval_request(patch_call, changes, reason="Create analysis summary file")
        sub_id2 = get_submission_id_for_call(patch_call)
        decision2 = wait_for_decision(sub_id2 or "", 120.0)
        if decision2 in ("approved", "approved_for_session"):
            patch_apply_begin(patch_call, changes, auto_approved=False)
            patch_apply_end(patch_call, True, stdout="Applied 1 file", stderr="")
        return {"analysis": base_result, "demo": {"exec_decision": decision, "patch_decision": decision2}}


# Factory function for creating analysis agent
def create_analysis_agent() -> AnalysisAgent:
    """Create an analysis agent using Pocket Flow"""
    return AnalysisAgent()
