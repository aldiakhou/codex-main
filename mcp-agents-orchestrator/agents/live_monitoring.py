"""
Live Monitoring Agent implementation using Pocket Flow with MCP integration
Provides real-time monitoring and alerting capabilities
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .base import MCPIntegratedAgent, AgentFactory
from core.models import AIAgentRequest, LiveMonitoringResponse
from core.logging import get_logger

logger = get_logger(__name__)

class LiveMonitoringAgent(MCPIntegratedAgent):
    """AI Agent for live monitoring and alerting using Pocket Flow"""
    
    def __init__(self):
        # MCP server configuration for live data access
        server_config = {
            "type": "stdio",
            "name": "Live Data Server",
            "command": "npx",
            "args": ["-y", "@kazuph/mcp-fetch"],
            "cache_tools_list": True
        }
        
        instructions = """You are a live monitoring specialist capable of tracking real-time data, identifying anomalies, and providing timely alerts.

CAPABILITIES:
- Monitor live data feeds and APIs
- Detect anomalies and unusual patterns
- Generate alerts based on thresholds
- Track trends over time
- Provide predictive insights
- Recommend preventive actions

MONITORING FRAMEWORK:
1. DATA COLLECTION:
   - Fetch current data from live sources
   - Validate data quality and completeness
   - Handle missing or corrupted data

2. ANALYSIS:
   - Compare against historical baselines
   - Identify deviations and anomalies
   - Calculate key performance indicators
   - Assess trend directions

3. ALERT GENERATION:
   - Apply threshold-based rules
   - Use pattern recognition for anomalies
   - Prioritize alerts by severity
   - Avoid alert fatigue

4. INSIGHT DEVELOPMENT:
   - Identify root causes when possible
   - Predict potential future issues
   - Recommend preventive measures
   - Suggest optimization opportunities

ALERT LEVELS:
- NORMAL: All metrics within expected ranges
- WARNING: Minor deviations or concerning trends
- CRITICAL: Significant issues requiring immediate attention

GUIDELINES:
1. Provide clear, actionable alerts
2. Include relevant context with alerts
3. Avoid false positives
4. Balance sensitivity with stability
5. Consider time-based patterns
6. Suggest specific remediation steps

Output Structure:
- Current status assessment
- Active alerts with severity
- Key metrics and values
- Trend analysis
- Actionable recommendations
- Next monitoring interval"""

        super().__init__(
            name="Live Monitoring Agent",
            instructions=instructions,
            server_configs=[server_config],
            temperature=0.2,  # Very low temperature for consistent monitoring
            output_type=LiveMonitoringResponse
        )
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for monitoring"""
        target = request.context.get('monitoring_target', '')
        metrics = request.context.get('metrics_to_track', [])
        thresholds = request.context.get('thresholds', {})
        check_interval = request.context.get('check_interval', '5 minutes')
        historical_data = request.context.get('historical_data', [])
        
        input_text = f"""Live Monitoring Request:

MONITORING TARGET: {target}
METRICS TO TRACK: {', '.join(metrics) if metrics else 'All available metrics'}
CHECK INTERVAL: {check_interval}

THRESHOLDS:
{chr(10).join([f"- {metric}: {threshold}" for metric, threshold in thresholds.items()]) if thresholds else "Default thresholds"}

RECENT HISTORICAL DATA:
{chr(10).join([str(data) for data in historical_data[-5:]]) if historical_data else "No historical data"}

Additional Context: {request.context.get('additional_context', 'None')}

Task: Monitor the specified target and provide status update.

Monitoring Process:
1. Fetch current data from live sources
2. Compare against thresholds and historical patterns
3. Identify any anomalies or concerning trends
4. Generate appropriate alerts if needed
5. Provide recommendations for action

Focus on:
- Detecting significant deviations
- Identifying emerging patterns
- Providing early warnings
- Suggesting preventive actions

Current Time: {datetime.now().isoformat()}"""
        
        return input_text


# Factory function for creating live monitoring agent
def create_live_monitoring_agent() -> LiveMonitoringAgent:
    """Create a live monitoring agent with MCP integration using Pocket Flow"""
    return LiveMonitoringAgent()
