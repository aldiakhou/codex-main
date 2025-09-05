"""
Execution policy system for Codex Python
Manages command execution policies and safety checks
"""

import asyncio
import re
import structlog
from typing import Dict, List, Set, Optional, Union, Pattern, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import hashlib
import time

logger = structlog.get_logger(__name__)


class PolicyDecision(Enum):
    """Policy decision types"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    SANDBOX = "sandbox"
    LOG_ONLY = "log_only"


class PolicySeverity(Enum):
    """Policy severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CommandPattern:
    """Command pattern for policy matching"""
    name: str
    pattern: str
    description: str
    severity: PolicySeverity = PolicySeverity.MEDIUM
    action: PolicyDecision = PolicyDecision.ALLOW
    conditions: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    confidence: float = 1.0


@dataclass
class ExecutionPolicy:
    """Execution policy definition"""
    name: str
    description: str
    patterns: List[CommandPattern] = field(default_factory=list)
    default_decision: PolicyDecision = PolicyDecision.ALLOW
    enabled: bool = True
    priority: int = 0
    timeout: float = 30.0
    environment_restrictions: Dict[str, str] = field(default_factory=dict)
    path_restrictions: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())


@dataclass
class PolicyEvaluation:
    """Result of policy evaluation"""
    decision: PolicyDecision
    confidence: float
    matched_patterns: List[CommandPattern] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for command execution"""
    command: List[str]
    working_directory: str
    environment: Dict[str, str]
    user: Optional[str] = None
    session_id: Optional[str] = None
    parent_command: Optional[str] = None
    source: Optional[str] = None  # "user", "ai", "script"


class PolicyEngine:
    """Policy engine for command execution safety"""
    
    def __init__(self):
        self.policies: List[ExecutionPolicy] = []
        self.pattern_cache: Dict[str, Pattern] = {}
        self.evaluation_history: List[Dict] = []
    
    def add_policy(self, policy: ExecutionPolicy) -> None:
        """Add an execution policy"""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    @staticmethod
    def is_known_safe_command(command: List[str]) -> bool:
        """Heuristic safe-command detector (read-only, non-destructive).

        This mirrors codex-rs intent in a simplified way:
        - allow harmless viewers and queries (ls, cat, echo, head, tail, wc, which, grep without -exec/-delete)
        - allow `git` with read-only subcommands
        - disallow likely-dangerous flags and shell operators
        """
        if not command:
            return False
        base = Path(command[0]).name
        readonly = {
            "ls", "cat", "echo", "pwd", "which", "type",
            "grep", "head", "tail", "wc", "nl",
        }
        if base in readonly:
            if base == "grep":
                # disallow grep calling external programs implicitly
                risky = {"--pre", "--search-zip", "-z"}
                return not any(any(r in arg for r in risky) for arg in command[1:])
            return True
        if base == "find":
            risky = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprintf", "-fprint", "-fprint0", "-fls"}
            return not any(any(r == arg or arg.startswith(f"{r}=") for r in risky) for arg in command[1:])
        if base == "git" and len(command) > 1 and command[1] in {"status", "log", "diff", "show", "branch"}:
            return True
        # Reject if the command line looks chained or contains redirects/substitutions
        joined = " ".join(command)
        if any(op in joined for op in ["|", "&&", ";", "`", "$(", ">", ">>"]):
            return False
        return False
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name"""
        for i, policy in enumerate(self.policies):
            if policy.name == policy_name:
                del self.policies[i]
                return True
        return False
    
    def load_default_policies(self) -> None:
        """Load default security policies"""
        
        # Dangerous system commands
        dangerous_patterns = [
            CommandPattern(
                name="rm_rf",
                pattern=r"rm\s+-rf\s+.*",
                description="Recursive force delete",
                severity=PolicySeverity.CRITICAL,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"filesystem", "destructive"}
            ),
            CommandPattern(
                name="format_disk",
                pattern=r"(mkfs|format)\s+.*",
                description="Disk formatting",
                severity=PolicySeverity.CRITICAL,
                action=PolicyDecision.DENY,
                tags={"filesystem", "destructive", "system"}
            ),
            CommandPattern(
                name="dd_overwrite",
                pattern=r"dd\s+.*of=.*",
                description="Raw disk write with dd",
                severity=PolicySeverity.HIGH,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"filesystem", "destructive"}
            ),
            CommandPattern(
                name="chmod_777",
                pattern=r"chmod\s+777\s+.*",
                description="Set world-writable permissions",
                severity=PolicySeverity.MEDIUM,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"filesystem", "permissions"}
            ),
            CommandPattern(
                name="system_shutdown",
                pattern=r"(shutdown|reboot|halt|poweroff)\s+.*",
                description="System shutdown/reboot",
                severity=PolicySeverity.HIGH,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"system", "destructive"}
            ),
        ]
        
        # Network-related commands
        network_patterns = [
            CommandPattern(
                name="port_scan",
                pattern=r"(nmap|netcat|nc)\s+.*",
                description="Network scanning tools",
                severity=PolicySeverity.MEDIUM,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"network", "security"}
            ),
            CommandPattern(
                name="packet_capture",
                pattern=r"(tcpdump|wireshark|tshark)\s+.*",
                description="Packet capture",
                severity=PolicySeverity.MEDIUM,
                action=PolicyDecision.REQUIRE_APPROVAL,
                tags={"network", "security"}
            ),
        ]
        
        # Development commands (generally safe)
        dev_patterns = [
            CommandPattern(
                name="git_operations",
                pattern=r"git\s+(commit|add|status|log|diff|branch|checkout)",
                description="Git version control operations",
                severity=PolicySeverity.LOW,
                action=PolicyDecision.ALLOW,
                tags={"development", "vcs"}
            ),
            CommandPattern(
                name="file_view",
                pattern=r"(cat|less|more|head|tail)\s+.*",
                description="File viewing commands",
                severity=PolicySeverity.LOW,
                action=PolicyDecision.ALLOW,
                tags={"filesystem", "read_only"}
            ),
            CommandPattern(
                name="build_tools",
                pattern=r"(make|cmake|ninja|cargo|npm|pip)\s+.*",
                description="Build and package management",
                severity=PolicySeverity.LOW,
                action=PolicyDecision.ALLOW,
                tags={"development", "build"}
            ),
        ]
        
        # Create default policy
        default_policy = ExecutionPolicy(
            name="default_security_policy",
            description="Default security policy for command execution",
            patterns=dangerous_patterns + network_patterns + dev_patterns,
            default_decision=PolicyDecision.ALLOW,
            priority=100
        )
        
        self.add_policy(default_policy)
        
        # Add workspace-specific policy
        workspace_policy = ExecutionPolicy(
            name="workspace_restriction",
            description="Restrict operations to workspace directory",
            default_decision=PolicyDecision.SANDBOX,
            priority=90,
            path_restrictions={"./", "./workspace", "./project"}
        )
        
        self.add_policy(workspace_policy)
    
    async def evaluate_command(
        self, 
        context: ExecutionContext,
        policies: Optional[List[ExecutionPolicy]] = None
    ) -> PolicyEvaluation:
        """Evaluate a command against policies"""
        
        command_str = ' '.join(context.command)
        command_hash = hashlib.sha256(command_str.encode()).hexdigest()
        
        # Use provided policies or default policies
        policies = policies or self.policies
        
        matched_patterns = []
        reasons = []
        decision = PolicyDecision.ALLOW
        confidence = 0.0
        
        # Allow-list quick check (read-only, safe)
        if self.is_known_safe_command(context.command):
            evaluation = PolicyEvaluation(
                decision=PolicyDecision.ALLOW,
                confidence=0.95,
                reasons=["Known safe command"],
            )
            self._record_evaluation(evaluation)
            return evaluation

        # Evaluate against each policy
        for policy in policies:
            if not policy.enabled:
                continue
            
            # Check policy conditions
            if not self._check_policy_conditions(policy, context):
                continue
            
            # Match command against patterns
            for pattern in policy.patterns:
                if self._matches_pattern(context.command, pattern.pattern):
                    matched_patterns.append(pattern)
                    confidence = max(confidence, pattern.confidence)
                    
                    # Determine action based on pattern
                    if pattern.action == PolicyDecision.DENY:
                        decision = PolicyDecision.DENY
                        reasons.append(f"Blocked by pattern '{pattern.name}': {pattern.description}")
                    elif pattern.action == PolicyDecision.REQUIRE_APPROVAL:
                        if decision != PolicyDecision.DENY:
                            decision = PolicyDecision.REQUIRE_APPROVAL
                            reasons.append(f"Requires approval: {pattern.description}")
                    elif pattern.action == PolicyDecision.SANDBOX:
                        if decision in [PolicyDecision.ALLOW, PolicyDecision.LOG_ONLY]:
                            decision = PolicyDecision.SANDBOX
                            reasons.append(f"Requires sandbox: {pattern.description}")
                    elif pattern.action == PolicyDecision.LOG_ONLY:
                        if decision == PolicyDecision.ALLOW:
                            decision = PolicyDecision.LOG_ONLY
                            reasons.append(f"Log only: {pattern.description}")
        
        # Apply default decision if no patterns matched
        if not matched_patterns:
            decision = policies[0].default_decision if policies else PolicyDecision.ALLOW
            confidence = 0.5
            reasons.append("No specific patterns matched, using default decision")
        
        # Additional safety checks
        safety_decision = await self._safety_checks(context)
        if safety_decision.decision != PolicyDecision.ALLOW:
            decision = safety_decision.decision
            reasons.extend(safety_decision.reasons)
            confidence = min(confidence, safety_decision.confidence)
        
        # Create evaluation result
        evaluation = PolicyEvaluation(
            decision=decision,
            confidence=confidence,
            matched_patterns=matched_patterns,
            reasons=reasons,
            suggested_action=self._get_suggested_action(decision),
            metadata={
                "command_hash": command_hash,
                "evaluated_at": time.time(),
                "command": command_str
            }
        )
        
        # Record evaluation
        self._record_evaluation(evaluation)
        
        return evaluation
    
    def _matches_pattern(self, command: List[str], pattern: str) -> bool:
        """Check if command matches pattern"""
        command_str = ' '.join(command)
        
        # Cache compiled patterns
        if pattern not in self.pattern_cache:
            try:
                self.pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                logger.warning("Invalid regex pattern", pattern=pattern)
                return False
        
        return bool(self.pattern_cache[pattern].search(command_str))
    
    def _check_policy_conditions(self, policy: ExecutionPolicy, context: ExecutionContext) -> bool:
        """Check if policy conditions are met"""
        
        # Check path restrictions
        if policy.path_restrictions:
            cmd_path = Path(context.working_directory)
            allowed = any(
                cmd_path.is_relative_to(Path(restriction).resolve())
                for restriction in policy.path_restrictions
            )
            if not allowed:
                return False
        
        # Check environment restrictions
        if policy.environment_restrictions:
            for key, expected_value in policy.environment_restrictions.items():
                actual_value = context.environment.get(key)
                if actual_value != expected_value:
                    return False
        
        return True
    
    async def _safety_checks(self, context: ExecutionContext) -> PolicyEvaluation:
        """Perform additional safety checks"""
        reasons = []
        
        command_str = ' '.join(context.command)
        cmd_name = Path(context.command[0]).name if context.command else ""
        
        # Check for potentially dangerous arguments
        dangerous_args = [
            ("--force", "force operation"),
            ("--no-preserve-root", "root file system modification"),
            ("-rf", "recursive force delete"),
            ("> /dev/null", "output suppression"),
            ("2>&1", "error stream redirection"),
        ]
        
        for arg, description in dangerous_args:
            if arg in command_str:
                reasons.append(f"Dangerous argument detected: {arg} ({description})")
        
        # Check command source
        if context.source == "ai" and cmd_name in ["rm", "dd", "mkfs", "format"]:
            reasons.append("AI-generated dangerous command requires review")
        
        # Check for command chaining
        if "|" in command_str or "&&" in command_str or ";" in command_str:
            reasons.append("Command chaining detected")
        
        # Determine decision
        if reasons:
            return PolicyEvaluation(
                decision=PolicyDecision.REQUIRE_APPROVAL,
                confidence=0.8,
                reasons=reasons,
                suggested_action="Review command before execution"
            )
        
        evaluation = PolicyEvaluation(
            decision=PolicyDecision.ALLOW,
            confidence=1.0,
            reasons=["Safety checks passed"]
        )
        self._record_evaluation(evaluation)
        return evaluation
    
    def _get_suggested_action(self, decision: PolicyDecision) -> str:
        """Get suggested action for policy decision"""
        actions = {
            PolicyDecision.ALLOW: "Command can be executed normally",
            PolicyDecision.DENY: "Command execution blocked",
            PolicyDecision.REQUIRE_APPROVAL: "Command requires user approval",
            PolicyDecision.SANDBOX: "Command should be executed in sandbox",
            PolicyDecision.LOG_ONLY: "Command should be logged but not executed"
        }
        return actions.get(decision, "Unknown decision")
    
    def _record_evaluation(self, evaluation: PolicyEvaluation) -> None:
        """Record policy evaluation for audit"""
        record = {
            "timestamp": time.time(),
            "decision": evaluation.decision.value,
            "confidence": evaluation.confidence,
            "reasons": evaluation.reasons,
            "metadata": evaluation.metadata
        }
        
        self.evaluation_history.append(record)
        
        # Keep only last 1000 evaluations
        if len(self.evaluation_history) > 1000:
            self.evaluation_history = self.evaluation_history[-1000:]
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get statistics about policy evaluations"""
        if not self.evaluation_history:
            return {}
        
        stats = {
            "total_evaluations": len(self.evaluation_history),
            "decisions": {},
            "avg_confidence": 0.0,
            "recent_evaluations": len([
                e for e in self.evaluation_history 
                if time.time() - e["timestamp"] < 3600  # Last hour
            ])
        }
        
        # Count decisions
        decision_counts = {}
        total_confidence = 0.0
        
        for evaluation in self.evaluation_history:
            decision = evaluation["decision"]
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
            total_confidence += evaluation["confidence"]
        
        stats["decisions"] = decision_counts
        stats["avg_confidence"] = total_confidence / len(self.evaluation_history)
        
        return stats
    
    def export_policies(self) -> List[Dict[str, Any]]:
        """Export policies to dictionary format"""
        return [
            {
                "name": policy.name,
                "description": policy.description,
                "patterns": [
                    {
                        "name": pattern.name,
                        "pattern": pattern.pattern,
                        "description": pattern.description,
                        "severity": pattern.severity.value,
                        "action": pattern.action.value,
                        "tags": list(pattern.tags),
                        "confidence": pattern.confidence
                    }
                    for pattern in policy.patterns
                ],
                "default_decision": policy.default_decision.value,
                "enabled": policy.enabled,
                "priority": policy.priority,
                "timeout": policy.timeout,
                "environment_restrictions": policy.environment_restrictions,
                "path_restrictions": list(policy.path_restrictions)
            }
            for policy in self.policies
        ]
    
    def import_policies(self, policies_data: List[Dict[str, Any]]) -> None:
        """Import policies from dictionary format"""
        for policy_data in policies_data:
            patterns = []
            for pattern_data in policy_data.get("patterns", []):
                pattern = CommandPattern(
                    name=pattern_data["name"],
                    pattern=pattern_data["pattern"],
                    description=pattern_data["description"],
                    severity=PolicySeverity(pattern_data["severity"]),
                    action=PolicyDecision(pattern_data["action"]),
                    tags=set(pattern_data.get("tags", [])),
                    confidence=pattern_data.get("confidence", 1.0)
                )
                patterns.append(pattern)
            
            policy = ExecutionPolicy(
                name=policy_data["name"],
                description=policy_data["description"],
                patterns=patterns,
                default_decision=PolicyDecision(policy_data["default_decision"]),
                enabled=policy_data.get("enabled", True),
                priority=policy_data.get("priority", 0),
                timeout=policy_data.get("timeout", 30.0),
                environment_restrictions=policy_data.get("environment_restrictions", {}),
                path_restrictions=set(policy_data.get("path_restrictions", []))
            )
            
            self.add_policy(policy)


class PolicyManager:
    """Manages execution policies and evaluations"""
    
    def __init__(self):
        self.engine = PolicyEngine()
        self.approval_cache: Dict[str, bool] = {}
        self.session_approvals: Dict[str, Set[str]] = {}
    
    async def initialize(self) -> None:
        """Initialize policy manager with default policies"""
        self.engine.load_default_policies()
    
    async def evaluate_command(
        self, 
        command: List[str],
        working_directory: str,
        environment: Dict[str, str],
        **kwargs
    ) -> PolicyEvaluation:
        """Evaluate command against policies"""
        
        context = ExecutionContext(
            command=command,
            working_directory=working_directory,
            environment=environment,
            **kwargs
        )
        
        return await self.engine.evaluate_command(context)
    
    async def request_approval(
        self,
        command: List[str],
        evaluation: PolicyEvaluation,
        approval_callback = None
    ) -> bool:
        """Request approval for command execution"""
        command_str = ' '.join(command)
        command_hash = hashlib.sha256(command_str.encode()).hexdigest()
        
        # Check approval cache
        if command_hash in self.approval_cache:
            return self.approval_cache[command_hash]
        
        # Check session approvals
        session_id = evaluation.metadata.get("session_id")
        if session_id and session_id in self.session_approvals:
            if command_hash in self.session_approvals[session_id]:
                return True
        
        # Request approval
        if approval_callback:
            approved = await approval_callback(command, evaluation)
        else:
            # Default approval logic - in real implementation, this would prompt user
            logger.warning("Command requires approval", command=command_str, reasons=evaluation.reasons)
            approved = evaluation.decision != PolicyDecision.DENY
        
        # Cache approval
        self.approval_cache[command_hash] = approved
        
        # Add to session approvals
        if session_id:
            if session_id not in self.session_approvals:
                self.session_approvals[session_id] = set()
            self.session_approvals[session_id].add(command_hash)
        
        return approved
    
    def create_session(self, session_id: str) -> None:
        """Create a new approval session"""
        self.session_approvals[session_id] = set()
    
    def close_session(self, session_id: str) -> None:
        """Close an approval session"""
        if session_id in self.session_approvals:
            del self.session_approvals[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy statistics"""
        return self.engine.get_evaluation_stats()
    
    def export_policies(self) -> List[Dict[str, Any]]:
        """Export current policies"""
        return self.engine.export_policies()
    
    def import_policies(self, policies_data: List[Dict[str, Any]]) -> None:
        """Import policies"""
        self.engine.import_policies(policies_data)
    
    def clear_approval_cache(self) -> None:
        """Clear approval cache"""
        self.approval_cache.clear()
