"""
BaseAgent - Abstract Base Class for All Analysis Agents
Template Method Pattern
"""
from abc import ABC, abstractmethod
from typing import List
from src.domain.models.analysis_context import AnalysisContext
from src.domain.models.finding import Finding

class BaseAgent(ABC):
    """
    Abstract base agent implementing Template Method pattern.
    All concrete agents (SecurityAgent, QualityAgent, etc) inherit from this.
    """
    
    def __init__(self, name: str, version: str, category: str):
        self.name = name
        self.version = version
        self.category = category
        self.metrics = {}
    
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Template method for analysis workflow.
        Subclasses must implement this method.
        """
        pass
    
    def get_metadata(self) -> dict:
        """Return agent metadata"""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "metrics": self.metrics
        }
    
    def log_metrics(self, key: str, value: any):
        """Log performance metrics"""
        self.metrics[key] = value
