# =====================================
# src/agents/context_analysis/context_analysis_agent.py
"""
Main Context Analysis Agent
Orchestrates the entire context analysis pipeline
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ...core.base_agent import BaseAgent
from ...core.data_models import ProcessingResult, AnalysisMetadata
from ...core.exceptions import AnalysisError, ValidationError

from .analyzers.content_analyzer import ContentAnalyzer
from .analyzers.structure_analyzer import StructureAnalyzer
from .analyzers.entity_analyzer import EntityAnalyzer
from .analyzers.relationship_analyzer import RelationshipAnalyzer
from .transformers.entity_extractor import EntityExtractor
from .transformers.structure_generator import StructureGenerator
from .semantic.semantic_analyzer import SemanticAnalyzer


@dataclass
class ContextAnalysisConfig:
    """Configuration for context analysis"""
    enable_structure_analysis: bool = True
    enable_entity_extraction: bool = True
    enable_relationship_mapping: bool = True
    enable_semantic_analysis: bool = True
    confidence_threshold: float = 0.7
    max_entities: int = 1000
    max_relationships: int = 500


class ContextAnalysisAgent(BaseAgent):
    """
    Context Analysis Agent
    Performs comprehensive analysis of extracted content
    """
    
    def __init__(self, config: ContextAnalysisConfig = None):
        super().__init__()
        self.config = config or ContextAnalysisConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.content_analyzer = ContentAnalyzer()
        self.structure_analyzer = StructureAnalyzer()
        self.entity_analyzer = EntityAnalyzer()
        self.relationship_analyzer = RelationshipAnalyzer()
        
        # Initialize transformers
        self.entity_extractor = EntityExtractor()
        self.structure_generator = StructureGenerator()
        
        # Initialize semantic analyzer
        self.semantic_analyzer = SemanticAnalyzer()
        
    def process(self, data: Dict[str, Any]) -> ProcessingResult:
        """
        Main processing method for context analysis
        
        Args:
            data: Input data containing extracted content
            
        Returns:
            ProcessingResult: Enhanced JSON with context analysis
        """
        try:
            self.logger.info("Starting context analysis processing")
            
            # Step 1: Content Analysis
            content_results = self._analyze_content(data)
            
            # Step 2: Structure Analysis
            structure_results = self._analyze_structure(content_results)
            
            # Step 3: Entity Extraction
            entity_results = self._extract_entities(structure_results)
            
            # Step 4: Relationship Mapping
            relationship_results = self._map_relationships(entity_results)
            
            # Step 5: Structure Generation
            enhanced_structure = self._generate_structure(relationship_results)
            
            # Step 6: Semantic Analysis
            semantic_results = self._perform_semantic_analysis(enhanced_structure)
            
            # Create final result
            result = ProcessingResult(
                success=True,
                data=semantic_results,
                metadata=self._create_metadata(semantic_results),
                agent_name=self.__class__.__name__
            )
            
            self.logger.info("Context analysis processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Context analysis failed: {str(e)}")
            raise AnalysisError(f"Context analysis failed: {str(e)}")
    
    def _analyze_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content structure and patterns"""
        if not self.config.enable_structure_analysis:
            return data
            
        self.logger.debug("Analyzing content structure")
        return self.content_analyzer.analyze(data)
    
    def _analyze_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document structure and hierarchy"""
        self.logger.debug("Analyzing document structure")
        return self.structure_analyzer.analyze(data)
    
    def _extract_entities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from content"""
        if not self.config.enable_entity_extraction:
            return data
            
        self.logger.debug("Extracting entities")
        return self.entity_extractor.extract(data)
    
    def _map_relationships(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map relationships between entities"""
        if not self.config.enable_relationship_mapping:
            return data
            
        self.logger.debug("Mapping relationships")
        return self.relationship_analyzer.analyze(data)
    
    def _generate_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced structure"""
        self.logger.debug("Generating enhanced structure")
        return self.structure_generator.generate(data)
    
    def _perform_semantic_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic analysis"""
        if not self.config.enable_semantic_analysis:
            return data
            
        self.logger.debug("Performing semantic analysis")
        return self.semantic_analyzer.analyze(data)
    
    def _create_metadata(self, data: Dict[str, Any]) -> AnalysisMetadata:
        """Create analysis metadata"""
        return AnalysisMetadata(
            timestamp=datetime.now(),
            agent_name=self.__class__.__name__,
            processing_time=0.0,  # Will be calculated elsewhere
            confidence_score=0.0,  # Will be calculated from results
            metrics={}
        )