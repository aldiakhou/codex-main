"""
Approval system for Codex Python
Manages user approval workflows for dangerous operations
"""

import asyncio
import json
import structlog
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib

logger = structlog.get_logger(__name__)


class ApprovalLevel(Enum):
    """Approval requirement levels"""
    NEVER = "never"                    # Never requires approval
    ON_FAILURE = "on_failure"          # Only on failure
    ON_REQUEST = "on_request"          # When requested
    UNLESS_TRUSTED = "unless_trusted"  # Unless source is trusted
    ALWAYS = "always"                  # Always requires approval


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Approval request data"""
    id: str
    operation: str
    description: str
    details: Dict[str, Any]
    level: ApprovalLevel
    requester: str
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    timeout: float = 300.0  # 5 minutes default
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalResponse:
    """Approval response data"""
    request_id: str
    status: ApprovalStatus
    responder: Optional[str] = None
    response_time: Optional[datetime] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalPolicy:
    """Approval policy configuration"""
    name: str
    description: str
    level: ApprovalLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0
    auto_approve_patterns: Set[str] = field(default_factory=set)
    auto_deny_patterns: Set[str] = field(default_factory=set)
    trusted_sources: Set[str] = field(default_factory=set)
    session_cache_duration: float = 3600.0  # 1 hour


@dataclass
class ApprovalContext:
    """Context for approval evaluation"""
    operation: str
    description: str
    details: Dict[str, Any]
    requester: str
    source: Optional[str] = None  # "ai", "user", "system"
    risk_score: float = 0.0
    previous_approvals: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ApprovalError(Exception):
    """Approval system errors"""
    pass


class ApprovalManager:
    """Manages approval workflows and requests"""
    
    def __init__(self):
        self.policies: List[ApprovalPolicy] = []
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalResponse] = []
        self.session_approvals: Dict[str, Set[str]] = {}
        self.auto_approve_cache: Dict[str, datetime] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._listeners: List[Callable[[ApprovalRequest], None]] = []
        # When False, this manager will not prompt on console; instead it waits for
        # an external response via respond_to_request().
        self._interactive: bool = True
        self._waiting: Dict[str, asyncio.Future] = {}
    
    def add_policy(self, policy: ApprovalPolicy) -> None:
        """Add an approval policy"""
        self.policies.append(policy)
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove an approval policy"""
        for i, policy in enumerate(self.policies):
            if policy.name == policy_name:
                del self.policies[i]
                return True
        return False
    
    def load_default_policies(self) -> None:
        """Load default approval policies"""
        
        # File system operations
        fs_policy = ApprovalPolicy(
            name="file_system_operations",
            description="Policy for file system operations",
            level=ApprovalLevel.UNLESS_TRUSTED,
            conditions={"operation_type": ["file_write", "file_delete", "file_move"]},
            auto_approve_patterns={"*.txt", "*.md", "*.json", "*.py"},
            trusted_sources={"user", "trusted_script"}
        )
        
        # Network operations
        network_policy = ApprovalPolicy(
            name="network_operations",
            description="Policy for network operations",
            level=ApprovalLevel.ON_REQUEST,
            conditions={"operation_type": ["network_request", "download", "upload"]},
            timeout=180.0,  # 3 minutes for network ops
            trusted_sources={"user"}
        )
        
        # System commands
        system_policy = ApprovalPolicy(
            name="system_commands",
            description="Policy for system commands",
            level=ApprovalLevel.ALWAYS,
            conditions={"operation_type": ["system_command"]},
            timeout=600.0,  # 10 minutes for system ops
            auto_deny_patterns={"rm -rf", "dd", "mkfs", "format"}
        )
        
        # AI-generated content
        ai_policy = ApprovalPolicy(
            name="ai_generated_operations",
            description="Policy for AI-generated operations",
            level=ApprovalLevel.ON_REQUEST,
            conditions={"source": "ai"},
            session_cache_duration=1800.0  # 30 minutes for AI approvals
        )
        
        self.add_policy(fs_policy)
        self.add_policy(network_policy)
        self.add_policy(system_policy)
        self.add_policy(ai_policy)
    
    async def request_approval(
        self,
        context: ApprovalContext,
        callback: Optional[Callable] = None
    ) -> ApprovalResponse:
        """Request approval for an operation"""
        
        # Evaluate approval requirements
        requires_approval, policy = await self._evaluate_approval_requirements(context)
        
        if not requires_approval:
            return ApprovalResponse(
                request_id="auto_approved",
                status=ApprovalStatus.APPROVED,
                reason="Auto-approved by policy"
            )
        
        # Check session cache
        if context.session_id and await self._check_session_cache(context):
            return ApprovalResponse(
                request_id="session_approved",
                status=ApprovalStatus.APPROVED,
                reason="Approved by session cache"
            )
        
        # Check auto-approve cache
        operation_hash = self._hash_operation(context.operation, context.details)
        if await self._check_auto_approve_cache(operation_hash):
            return ApprovalResponse(
                request_id="cache_approved",
                status=ApprovalStatus.APPROVED,
                reason="Approved by cache"
            )
        
        # Create approval request
        request = ApprovalRequest(
            id=self._generate_request_id(),
            operation=context.operation,
            description=context.description,
            details=context.details,
            level=policy.level if policy else ApprovalLevel.ON_REQUEST,
            requester=context.requester,
            session_id=context.session_id,
            timeout=policy.timeout if policy else 300.0,
            metadata={
                "source": context.source,
                "risk_score": context.risk_score,
                "policy": policy.name if policy else "default"
            }
        )
        
        # Store request
        self.pending_requests[request.id] = request

        # Register callback if provided
        if callback:
            self.callbacks[request.id] = callback

        # Notify listeners
        for listener in list(self._listeners):
            try:
                listener(request)
            except Exception:
                pass

        # Send for approval
        if self._interactive:
            response = await self._send_for_approval(request)
        else:
            # Non-interactive: wait for respond_to_request or timeout
            loop = asyncio.get_event_loop()
            fut: asyncio.Future = loop.create_future()
            self._waiting[request.id] = fut
            try:
                response = await asyncio.wait_for(fut, timeout=request.timeout)
            except asyncio.TimeoutError:
                response = ApprovalResponse(
                    request_id=request.id,
                    status=ApprovalStatus.EXPIRED,
                    reason="Approval request expired",
                )
                # Remove from pending and cleanup waiter
                if request.id in self.pending_requests:
                    del self.pending_requests[request.id]
                self._waiting.pop(request.id, None)
        
        # Cache approval if granted
        if response.status == ApprovalStatus.APPROVED:
            await self._cache_approval(context, operation_hash)
        
        # Record in history
        self.approval_history.append(response)
        
        return response

    def add_listener(self, fn: Callable[[ApprovalRequest], None]) -> None:
        self._listeners.append(fn)

    def remove_listener(self, fn: Callable[[ApprovalRequest], None]) -> None:
        try:
            self._listeners.remove(fn)
        except ValueError:
            pass
    
    async def _evaluate_approval_requirements(
        self, 
        context: ApprovalContext
    ) -> tuple[bool, Optional[ApprovalPolicy]]:
        """Evaluate if approval is required"""
        
        for policy in self.policies:
            if await self._matches_policy_conditions(policy, context):
                # Check auto-approve patterns
                if self._matches_auto_approve_patterns(policy, context):
                    return False, policy
                
                # Check auto-deny patterns
                if self._matches_auto_deny_patterns(policy, context):
                    return True, policy
                
                # Check trusted sources
                if context.source in policy.trusted_sources and policy.level == ApprovalLevel.UNLESS_TRUSTED:
                    return False, policy
                
                # Otherwise, approval is required
                return True, policy
        
        # Default: no approval required
        return False, None
    
    async def _matches_policy_conditions(self, policy: ApprovalPolicy, context: ApprovalContext) -> bool:
        """Check if context matches policy conditions"""
        
        # Check operation type
        operation_type = context.details.get("operation_type", "unknown")
        allowed_types = policy.conditions.get("operation_type", [])
        
        if allowed_types and operation_type not in allowed_types:
            return False
        
        # Check source condition
        if "source" in policy.conditions:
            required_source = policy.conditions["source"]
            if context.source != required_source:
                return False
        
        # Check risk score
        max_risk = policy.conditions.get("max_risk_score", 1.0)
        if context.risk_score > max_risk:
            return False
        
        return True
    
    def _matches_auto_approve_patterns(self, policy: ApprovalPolicy, context: ApprovalContext) -> bool:
        """Check if operation matches auto-approve patterns"""
        operation_str = context.operation
        for pattern in policy.auto_approve_patterns:
            if self._pattern_matches(operation_str, pattern):
                return True
        return False
    
    def _matches_auto_deny_patterns(self, policy: ApprovalPolicy, context: ApprovalContext) -> bool:
        """Check if operation matches auto-deny patterns"""
        operation_str = context.operation
        for pattern in policy.auto_deny_patterns:
            if self._pattern_matches(operation_str, pattern):
                return True
        return False
    
    def _pattern_matches(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (simple glob-style)"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    async def _check_session_cache(self, context: ApprovalContext) -> bool:
        """Check if operation is approved in session cache"""
        if not context.session_id:
            return False
        
        operation_hash = self._hash_operation(context.operation, context.details)
        session_approvals = self.session_approvals.get(context.session_id, set())
        
        return operation_hash in session_approvals
    
    async def _check_auto_approve_cache(self, operation_hash: str) -> bool:
        """Check if operation is in auto-approve cache"""
        if operation_hash not in self.auto_approve_cache:
            return False
        
        # Check if cache entry is still valid
        cached_time = self.auto_approve_cache[operation_hash]
        cache_duration = 3600.0  # 1 hour default
        
        if datetime.now() - cached_time > timedelta(seconds=cache_duration):
            del self.auto_approve_cache[operation_hash]
            return False
        
        return True
    
    async def _cache_approval(self, context: ApprovalContext, operation_hash: str) -> None:
        """Cache approval for future use"""
        # Cache in session
        if context.session_id:
            if context.session_id not in self.session_approvals:
                self.session_approvals[context.session_id] = set()
            self.session_approvals[context.session_id].add(operation_hash)
        
        # Cache globally
        self.auto_approve_cache[operation_hash] = datetime.now()
    
    async def _send_for_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Send request for approval"""
        
        try:
            # Set expiration
            if request.expires_at is None:
                request.expires_at = request.created_at + timedelta(seconds=request.timeout)
            
            # Check if already expired
            if datetime.now() > request.expires_at:
                return ApprovalResponse(
                    request_id=request.id,
                    status=ApprovalStatus.EXPIRED,
                    reason="Request expired"
                )
            
            # For now, implement simple console-based approval
            # In a real implementation, this would integrate with UI, web interface, etc.
            response = await self._console_approval(request)
            
            # Execute callback if registered
            if request.id in self.callbacks:
                callback = self.callbacks[request.id]
                await callback(request, response)
                del self.callbacks[request.id]
            
            return response
            
        except Exception as e:
            logger.error("Approval request failed", request_id=request.id, error=str(e))
            return ApprovalResponse(
                request_id=request.id,
                status=ApprovalStatus.CANCELLED,
                reason=f"Approval system error: {e}"
            )
    
    async def _console_approval(self, request: ApprovalRequest) -> ApprovalResponse:
        """Console-based approval (for CLI usage)"""
        
        print(f"\n{'='*60}")
        print(f"APPROVAL REQUIRED")
        print(f"{'='*60}")
        print(f"Operation: {request.operation}")
        print(f"Description: {request.description}")
        print(f"Requester: {request.requester}")
        print(f"Level: {request.level.value}")
        print(f"Expires in: {int((request.expires_at - datetime.now()).total_seconds())} seconds")
        
        if request.details:
            print(f"\nDetails:")
            for key, value in request.details.items():
                print(f"  {key}: {value}")
        
        print(f"\nOptions:")
        print(f"  [Y] Yes - Approve this operation")
        print(f"  [N] No - Deny this operation")
        print(f"  [S] Skip - Cancel this request")
        
        # Wait for user input
        start_time = datetime.now()
        while datetime.now() < request.expires_at:
            try:
                response = input("\nYour choice (Y/N/S): ").strip().lower()
                
                if response in ['y', 'yes']:
                    return ApprovalResponse(
                        request_id=request.id,
                        status=ApprovalStatus.APPROVED,
                        responder="console_user",
                        response_time=datetime.now(),
                        reason="User approved via console"
                    )
                elif response in ['n', 'no']:
                    return ApprovalResponse(
                        request_id=request.id,
                        status=ApprovalStatus.DENIED,
                        responder="console_user",
                        response_time=datetime.now(),
                        reason="User denied via console"
                    )
                elif response in ['s', 'skip']:
                    return ApprovalResponse(
                        request_id=request.id,
                        status=ApprovalStatus.CANCELLED,
                        responder="console_user",
                        response_time=datetime.now(),
                        reason="User cancelled request"
                    )
                else:
                    print("Invalid choice. Please enter Y, N, or S.")
                    
            except (KeyboardInterrupt, EOFError):
                return ApprovalResponse(
                    request_id=request.id,
                    status=ApprovalStatus.CANCELLED,
                    reason="User interrupted approval process"
                )
            
            await asyncio.sleep(0.1)
        
        # Request expired
        return ApprovalResponse(
            request_id=request.id,
            status=ApprovalStatus.EXPIRED,
            reason="Approval request expired"
        )
    
    def _hash_operation(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate hash for operation caching"""
        content = f"{operation}:{json.dumps(details, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(id(self)).encode()).hexdigest()[:8]}"
    
    def get_pending_requests(self, session_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        requests = list(self.pending_requests.values())
        
        # Filter by session if specified
        if session_id:
            requests = [r for r in requests if r.session_id == session_id]
        
        # Remove expired requests
        current_time = datetime.now()
        active_requests = []
        
        for request in requests:
            if request.expires_at and current_time > request.expires_at:
                # Remove expired request
                if request.id in self.pending_requests:
                    del self.pending_requests[request.id]
                
                # Record as expired
                self.approval_history.append(ApprovalResponse(
                    request_id=request.id,
                    status=ApprovalStatus.EXPIRED,
                    reason="Request expired"
                ))
            else:
                active_requests.append(request)
        
        return active_requests
    
    async def respond_to_request(
        self, 
        request_id: str, 
        status: ApprovalStatus, 
        responder: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Respond to a pending approval request"""
        
        if request_id not in self.pending_requests:
            # Resolve any waiter with a CANCELLED status
            fut = self._waiting.pop(request_id, None)
            if fut and not fut.done():
                fut.set_result(
                    ApprovalResponse(
                        request_id=request_id,
                        status=ApprovalStatus.CANCELLED,
                        reason="Request not found",
                    )
                )
            return False
        
        request = self.pending_requests[request_id]
        
        # Create response
        response = ApprovalResponse(
            request_id=request_id,
            status=status,
            responder=responder,
            response_time=datetime.now(),
            reason=reason
        )
        
        # Remove from pending
        del self.pending_requests[request_id]
        
        # Record in history
        self.approval_history.append(response)
        # Fulfill any waiter
        fut = self._waiting.pop(request_id, None)
        if fut and not fut.done():
            fut.set_result(response)
        
        # Execute callback if registered
        if request_id in self.callbacks:
            callback = self.callbacks[request_id]
            await callback(request, response)
            del self.callbacks[request_id]
        
        return True

    def set_interactive(self, interactive: bool) -> None:
        """Enable or disable console prompts; when disabled, wait for external responses."""
        self._interactive = interactive
    
    def create_session(self, session_id: str) -> None:
        """Create a new approval session"""
        self.session_approvals[session_id] = set()
    
    def close_session(self, session_id: str) -> None:
        """Close an approval session"""
        if session_id in self.session_approvals:
            del self.session_approvals[session_id]
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        stats = {
            "pending_requests": len(self.pending_requests),
            "total_requests": len(self.approval_history),
            "active_sessions": len(self.session_approvals),
            "cache_size": len(self.auto_approve_cache)
        }
        
        # Count by status
        status_counts = {}
        for response in self.approval_history:
            status = response.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        stats["status_distribution"] = status_counts
        
        return stats
    
    def cleanup_expired_requests(self) -> int:
        """Clean up expired requests and cache entries"""
        cleaned_count = 0
        current_time = datetime.now()
        
        # Clean expired requests
        expired_requests = []
        for request_id, request in self.pending_requests.items():
            if request.expires_at and current_time > request.expires_at:
                expired_requests.append(request_id)
        
        for request_id in expired_requests:
            del self.pending_requests[request_id]
            cleaned_count += 1
        
        # Clean expired cache entries
        expired_cache = []
        cache_duration = 3600.0  # 1 hour
        
        for operation_hash, cached_time in self.auto_approve_cache.items():
            if current_time - cached_time > timedelta(seconds=cache_duration):
                expired_cache.append(operation_hash)
        
        for operation_hash in expired_cache:
            del self.auto_approve_cache[operation_hash]
            cleaned_count += 1
        
        return cleaned_count
