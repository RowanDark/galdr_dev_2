# galdr/interceptor/backend/modules/recon/models/target.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class ReconTarget:
    """Target information for reconnaissance"""
    original_input: str
    target_type: str  # 'domain' or 'ip'
    primary_target: str
    additional_targets: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconResult:
    """Complete reconnaissance result"""
    scan_id: str
    target: ReconTarget
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Source results
    sources: Dict[str, Dict] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Processed results
    aggregated_data: Dict[str, List] = field(default_factory=dict)
    deduplicated_data: Dict[str, List] = field(default_factory=dict)
    
    # Analysis results
    analysis: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, int] = field(default_factory=dict)
    
    # Status and errors
    status: str = "running"
    errors: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'scan_id': self.scan_id,
            'target': {
                'original_input': self.target.original_input,
                'target_type': self.target.target_type,
                'primary_target': self.target.primary_target
            },
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'sources': self.sources,
            'aggregated_data': self.aggregated_data,
            'deduplicated_data': self.deduplicated_data,
            'analysis': self.analysis,
            'statistics': self.statistics,
            'status': self.status,
            'errors': self.errors,
            'error': self.error
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
