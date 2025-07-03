# src/agents/context_analysis/semantic/semantic_analyzer.py
"""
Semantic Analyzer
Main semantic analysis orchestrator
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .disambiguation import Disambiguator
from .intent_detector import IntentDetector
from .concept_linker import ConceptLinker
from .reference_resolver import ReferenceResolver


@dataclass
class SemanticAnalysisConfig:
    """Configuration for semantic analysis"""
    enable_disambiguation: bool = True
    enable_intent_detection: bool = True
    enable_concept_linking: bool = True
    enable_reference_resolution: bool = True
    confidence_threshold: float = 0.6


class SemanticAnalyzer:
    """
    Main semantic analyzer that orchestrates all semantic analysis components
    """
    
    def __init__(self, config: SemanticAnalysisConfig = None):
        self.config = config or SemanticAnalysisConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize semantic components
        self.disambiguator = Disambiguator()
        self.intent_detector = IntentDetector()
        self.concept_linker = ConceptLinker()
        self.reference_resolver = ReferenceResolver()
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive semantic analysis
        
        Args:
            data: Input data with enhanced structure
            
        Returns:
            Dict: Data with semantic analysis results
        """
        try:
            self.logger.debug("Starting semantic analysis")
            
            enhanced_data = data.copy()
            
            # Step 1: Disambiguation
            if self.config.enable_disambiguation:
                enhanced_data = self.disambiguator.disambiguate(enhanced_data)
            
            # Step 2: Reference Resolution
            if self.config.enable_reference_resolution:
                enhanced_data = self.reference_resolver.resolve(enhanced_data)
            
            # Step 3: Concept Linking
            if self.config.enable_concept_linking:
                enhanced_data = self.concept_linker.link(enhanced_data)
            
            # Step 4: Intent Detection
            if self.config.enable_intent_detection:
                enhanced_data = self.intent_detector.detect(enhanced_data)
            
            # Add semantic analysis metadata
            enhanced_data['semantic_analysis'] = {
                'analysis_metadata': {
                    'analyzer': self.__class__.__name__,
                    'components_used': self._get_enabled_components(),
                    'confidence_threshold': self.config.confidence_threshold
                }
            }
            
            self.logger.debug("Semantic analysis completed")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Semantic analysis failed: {str(e)}")
            raise
    
    def _get_enabled_components(self) -> List[str]:
        """Get list of enabled components"""
        components = []
        if self.config.enable_disambiguation:
            components.append('disambiguation')
        if self.config.enable_intent_detection:
            components.append('intent_detection')
        if self.config.enable_concept_linking:
            components.append('concept_linking')
        if self.config.enable_reference_resolution:
            components.append('reference_resolution')
        return components
